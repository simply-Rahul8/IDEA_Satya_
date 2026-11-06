"""Catalogue audit service on the stepwise job store (ADR-8, P11). Owner: Engine.

    result = import_catalogue(upload_bytes)
    job_id = create_audit(conn, workspace_id, result.products)
    while step_audit(conn, job_id)["status"] == "running": ...   # the browser drives this
    report = audit_report(conn, job_id)                          # callable at any point, partial results included

Each step resolves a few products deterministically (no LLM). A product that raises is recorded as `error` in the
same step rather than retried, so a poisoned row can never loop. Cancelling keeps finished results ("Stopped at n
of N"); `resume_audit` picks the rest up again.
"""

from __future__ import annotations

from typing import Any

from engine.audit.models import STATE_ORDER, AuditItem, AuditReport, Counters, ProductRecord, State
from engine.audit.scan import scan_product
from engine.jobs.store import cancel_job, create_job, job_items, job_progress, resume_job, step_job
from engine.rules import RuleSet, default_ruleset, summary_line

KIND = "catalogue_audit"
DEFAULT_BATCH = 5
ERROR_NOTE = "We couldn't check this product."


def create_audit(conn, workspace_id: str, products: list[ProductRecord], created_by: str | None = None) -> str:
    payloads = [{"product": p.model_dump()} for p in products]
    return create_job(conn, workspace_id, KIND, payloads, created_by)


def _handler(ruleset: RuleSet):
    def handle(payload: dict[str, Any]) -> dict[str, Any]:
        product = ProductRecord.model_validate(payload["product"])
        try:
            item = scan_product(product, ruleset=ruleset)
        except Exception as exc:  # deterministic code: retrying would not change the outcome
            item = AuditItem(
                sku=product.sku, name=product.name, state=State.ERROR, note=f"{ERROR_NOTE} ({type(exc).__name__})"
            )
        return item.model_dump(mode="json")

    return handle


def step_audit(conn, job_id: str, batch_size: int = DEFAULT_BATCH, ruleset: RuleSet | None = None) -> dict[str, Any]:
    """Resolve up to batch_size products. Returns {status, total, done, failed, label}."""
    progress = step_job(conn, job_id, _handler(ruleset or default_ruleset()), batch_size=batch_size)
    return {**progress, "label": _label(progress["status"], progress["done"] + progress["failed"], progress["total"])}


def cancel_audit(conn, job_id: str) -> dict[str, Any]:
    p = cancel_job(conn, job_id)
    return {**p, "label": _label(p["status"], p["done"] + p["failed"], p["total"])}


def resume_audit(conn, job_id: str) -> dict[str, Any]:
    p = resume_job(conn, job_id)
    return {**p, "label": _label(p["status"], p["done"] + p["failed"], p["total"])}


def retry_errors(conn, job_id: str) -> dict[str, Any]:
    """Put products that errored back in the queue ("Retry 5", screen-audit A3). Finished results stay as they are."""
    with conn.cursor() as cur:
        cur.execute(
            "update job_items set status = 'pending', result = null, error = null, attempts = 0, claimed_at = null "
            "where job_id = %s and (status = 'failed' or result->>'state' = 'error')",
            (job_id,),
        )
    conn.commit()
    p = job_progress(conn, job_id)
    return {**p, "label": _label(p["status"], p["done"] + p["failed"], p["total"])}


def _label(status: str, n: int, total: int) -> str:
    if status == "cancelled":
        return f"Stopped at {n} of {total}"
    if status in ("done", "failed"):
        return f"Checked {total} products"
    return f"Checking {n} of {total} products"


def sort_items(items: list[AuditItem]) -> list[AuditItem]:
    rank = {s: i for i, s in enumerate(STATE_ORDER)}
    return sorted(items, key=lambda it: (rank[it.state], it.position))


def audit_report(conn, job_id: str, ruleset: RuleSet | None = None) -> AuditReport:
    rs = ruleset or default_ruleset()
    progress = job_progress(conn, job_id)
    items: list[AuditItem] = []
    for row in job_items(conn, job_id):
        product = row["payload"]["product"]
        if row["status"] == "done" and row["result"]:
            item = AuditItem.model_validate(row["result"])
        elif row["status"] == "failed":
            item = AuditItem(sku=product["sku"], name=product["name"], state=State.ERROR, note=ERROR_NOTE)
        else:
            item = AuditItem(sku=product["sku"], name=product["name"], state=State.PENDING)
        items.append(item.model_copy(update={"position": row["position"]}))

    counts = Counters(total=len(items))
    for it in items:
        setattr(counts, it.state.value, getattr(counts, it.state.value) + 1)
    counts.done = counts.total - counts.pending
    complete = counts.pending == 0
    summary = None
    if complete and counts.red == 0 and counts.amber == 0 and counts.green > 0:
        summary = summary_line([], rs)  # "No flagged risks under rule set vX. Not legal advice. ..." never "compliant"
    return AuditReport(
        job_id=job_id,
        status=progress["status"],
        rule_set=rs.label,
        counters=counts,
        progress_label=_label(progress["status"], counts.done, counts.total),
        summary=summary,
        items=sort_items(items),
    )
