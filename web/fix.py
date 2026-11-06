"""Fix with Satya (SAT-41; plan section 3 steps 5 and 6, P2, P25, P19): from an audit row or a pasted listing, extract a
Product Truth draft, confirm each claim with evidence, then generate the PDP pack stepwise and land on review.

Order of events: product-type gate (P23) -> extraction (every claim starts unconfirmed) -> `/packs/{id}/truth` ->
`/packs/{id}/generate` (two client-driven steps, cancellable) -> `/packs/{id}/review`.

Listing text is data (P19): it reaches the model only inside the prompt's `<untrusted_data>` payload (engine.prompts)
and reaches templates only through autoescaping. Hard-blocked claims are refused by the engine guard (P25), never by
the UI alone. Nothing here says "compliant" (P20). Packs are read and saved through the workspace-scoped repository.
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from engine import api
from engine.audit import ProductRecord
from engine.guardrails.claims import ClaimGuardError, confirm_claim, hard_blocks
from engine.jobs.store import job_items
from engine.models import Claim, ClaimStatus, Evidence, EvidenceType, PDPPack
from engine.pipeline import TONES
from engine.product_type import check_product_type
from engine.providers import ProviderError
from engine.repo import ReviewState
from engine.repo.evidence import MAX_BYTES, EvidenceError
from web import account, audits, packs, review
from web.app import form_data, render
from web.auth import authenticate
from web.security import guard_unsafe, workspace_of

router = APIRouter(dependencies=[Depends(guard_unsafe), Depends(authenticate)])

MAX_LISTING = 20_000  # characters of pasted listing text
MAX_REFERENCE = 300
MIN_REFERENCE_CHARS = 4  # 'doc-7' is the shortest real document id
TOTAL_STEPS = 2
TONE_FOR = {"warm": "friendly", "clinical": "professional", "premium": "premium"}  # brand setup -> prompt tone
EVIDENCE_CHOICES = (
    (EvidenceType.TEST_REPORT, "Test report"),
    (EvidenceType.INGREDIENT_LIST, "Ingredient list"),
    (EvidenceType.LABEL, "Label"),
    (EvidenceType.BRAND_DECLARATION, "Brand declaration"),
    (EvidenceType.OTHER, "Other"),
)
FIELD_LABELS = (
    ("brand", "Brand"),
    ("category", "Category"),
    ("size", "Size"),
    ("ingredients", "Ingredients"),
    ("how_to_use", "How to use"),
    ("warnings", "Warnings"),
    ("storage", "Storage"),
    ("manufacturer", "Manufacturer"),
    ("country_of_origin", "Country of origin"),
)
GEN_LABELS = {
    0: "Writing the copy · step 1 of 2",
    1: "Checking every sentence against its sources · step 2 of 2",
}


# ---------------------------------------------------------------------------------------------------- helpers
def _problem(request: Request, title: str, body: str, kind: str = "error", status: int = 422):
    return audits.problem(request, title, body, kind=kind, status=status)


def _read(request: Request, pack_id: str) -> ReviewState:
    return review._read(request, pack_id)


def _tone(request: Request) -> str:
    try:
        profile = account._store().get(workspace_of(request))
    except Exception:  # noqa: BLE001 (a brand-profile hiccup must not stop generation; the default tone is safe)
        profile = None
    tone = TONE_FOR.get(profile.tone, "professional") if profile else "professional"
    return tone if tone in TONES else "professional"


def _reason_line(rule_id: str, ruleset) -> dict[str, str]:
    try:
        rule = ruleset.rule(rule_id)
    except KeyError:
        return {"id": rule_id, "title": "A rule that cannot be overridden", "why": ""}
    return {"id": rule_id, "title": rule.title, "why": rule.explanation}


def claim_view(state: ReviewState, c: Claim, *, error: str = "", field: str = "", values: dict | None = None) -> dict:
    st = review.claim_state(c)
    sev, word, icon = review.CLAIM_BADGE[st]
    used = sum(
        f"claim:{c.id}" in s.anchors for s in (state.pack.sentences() if state.pack else [])
    )  # sentences that already use it
    return {
        "id": c.id,
        "text": c.text,
        "state": st,
        "sev": sev,
        "word": word if st != "rejected" else "Left out",
        "icon": icon,
        "evidence": review._evidence_line(c),
        "reasons": [_reason_line(r, state.ruleset) for r in c.blocking_rule_ids] if st == "blocked" else [],
        "can_confirm": st in ("unconfirmed", "needs_reference", "rejected"),
        "used": used,
        "error": error,
        "error_field": field,
        "values": values or {},
        "pack_id": state.pack_id,
    }


def summary_of(state: ReviewState) -> dict[str, Any]:
    claims = state.truth.claims
    n = {"confirmed": 0, "open": 0, "blocked": 0, "left_out": 0}
    for c in claims:
        st = review.claim_state(c)
        key = {"confirmed": "confirmed", "blocked": "blocked", "rejected": "left_out"}.get(st, "open")
        n[key] += 1
    if not claims:
        note = "No claims were found in the listing. Satya will write from the product facts only."
    else:
        parts = [f"{n['confirmed']} of {len(claims)} claims confirmed"]
        if n["blocked"]:
            parts.append(f"{n['blocked']} cannot be confirmed")
        left = n["open"] + n["left_out"] + n["blocked"]
        note = ", ".join(parts) + "." + (" Claims that are not confirmed are left out of the copy." if left else "")
    return {**n, "total": len(claims), "note": note, "has_pack": bool(state.pack and state.pack.sentences())}


def truth_ctx(state: ReviewState, **extra) -> dict:
    t = state.truth
    facts = []
    for name, label in FIELD_LABELS:
        v = getattr(t, name)
        facts.append({"label": label, "value": ", ".join(v) if isinstance(v, list) else (v or "")})
    return {
        "title": f"Product Truth: {state.product} · Satya",
        "ruleset": state.ruleset,
        "pack_id": state.pack_id,
        "product": state.product,
        "facts": facts,
        "claims": [claim_view(state, c) for c in t.claims],
        "summary": summary_of(state),
        "evidence_choices": EVIDENCE_CHOICES,
        "max_mb": MAX_BYTES // 1_000_000,
        **extra,
    }


# ---------------------------------------------------------------------------------------------------- start
@router.get("/fix/new")
async def new_fix(request: Request):
    return render(request, "fix/new.html", {"title": "Fix a listing with Satya · Satya", "max_chars": MAX_LISTING})


def _audit_record(ws: str, audit_id: str, position: int) -> tuple[ProductRecord, str | None]:
    """The product at `position` of one of this workspace's audits, and the gate note when the audit skipped it."""
    with audits.db() as conn:
        audits._owned(conn, ws, audit_id)
        rows = [r for r in job_items(conn, audit_id) if r["position"] == position]
    if not rows:
        raise HTTPException(404, "No such product")
    skipped = (rows[0]["result"] or {}).get("state") == "skipped"
    return ProductRecord.model_validate(rows[0]["payload"]["product"]), (
        (rows[0]["result"] or {}).get("note") if skipped else None
    )


def _listing_text(p: ProductRecord) -> str:
    return "\n".join(x for x in (p.name, p.description) if x.strip())


@router.post("/fix")
async def start(request: Request):
    data = await form_data(request, limit=MAX_LISTING * 4 + 4_000)
    ws = workspace_of(request)
    if data.get("audit"):
        try:
            position = int(data.get("position", ""))
        except ValueError:
            raise HTTPException(400, "Choose a product") from None
        record, skipped = await run_in_threadpool(_audit_record, ws, data["audit"], position)
        if skipped:
            return _problem(request, "This product isn't in scope for Satya v1.", skipped, kind="info")
    else:
        text = data.get("text", "").strip()
        if not text:
            return _problem(request, "Nothing to read yet.", "Paste the product's listing text first.")
        if len(text) > MAX_LISTING:
            return _problem(
                request, "That listing is too long.", f"Paste up to {MAX_LISTING:,} characters for one product."
            )
        name, _, rest = text.partition("\n")
        record = ProductRecord(sku="", name=name.strip()[:200], description=rest.strip())

    listing = _listing_text(record)[:MAX_LISTING]
    gate = check_product_type(name=record.name, category=record.category, description=record.description)
    if not gate.proceeds:  # P23: a refused product never reaches extraction
        return _problem(request, "This product isn't in scope for Satya v1.", gate.explanation, kind="info")
    try:
        truth = await run_in_threadpool(api.extract_product_truth, listing)
    except (api.ExtractionError, ProviderError, api.AllProvidersFailed, api.ProviderConfigError):
        return _problem(
            request,
            "We couldn't read that listing.",
            "The reader did not answer in time. Nothing was saved. Try again.",
        )
    pack_id = str(uuid.uuid4())
    packs.repo().put(ws, ReviewState(pack_id, truth.product_name, truth, None, api.default_ruleset()))
    return Response(status_code=200, headers={"HX-Redirect": f"/packs/{pack_id}/truth", "Cache-Control": "no-store"})


# ---------------------------------------------------------------------------------------------------- truth screen
@router.get("/packs/{pack_id}/truth")
def truth_page(request: Request, pack_id: str):
    return render(request, "fix/truth.html", truth_ctx(_read(request, pack_id)))


def _claim_response(request: Request, state: ReviewState, claim_id: str, *, say: str = "", status: int = 200, **kw):
    ctx = truth_ctx(state)
    claim = next(c for c in ctx["claims"] if c["id"] == claim_id)
    if kw:
        claim = claim_view(state, state.truth.claim(claim_id), **kw)
    headers = review._trigger(**{"satya:say": say}) if say else None
    return render(request, "fix/_claim_live.html", {**ctx, "c": claim}, status=status, headers=headers)


def _set_claim(request: Request, state: ReviewState, new: Claim) -> None:
    """Replace the claim and re-check every sentence that cites it (a claim change can open or close flags)."""
    state.truth = state.truth.model_copy(update={"claims": [new if c.id == new.id else c for c in state.truth.claims]})
    if state.pack:
        for key in review.SECTION_LABELS:
            for i, sent in enumerate(state.pack.section(key).sentences):
                if f"claim:{new.id}" in sent.anchors:
                    review._apply_text(state, review.sid_of(key, i), sent.text, review._phrases(request))


async def _confirm_fields(request: Request) -> dict[str, Any]:
    """Text fields and the optional evidence file from the multipart form (nothing is stored yet)."""
    try:
        raw = await audits.read_body(request, MAX_BYTES + audits.BODY_OVERHEAD)
    except audits.TooLarge:
        return {"too_large": True}
    ctype = request.headers.get("content-type", "")
    if ctype.lower().startswith("application/x-www-form-urlencoded"):  # no file: a plain form post
        plain = parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
        fields = {k: v[-1].encode() for k, v in plain.items()}
    else:
        try:
            fields = audits.parse_multipart(ctype, raw)
        except ValueError:
            raise HTTPException(400, "Expected a form") from None
    return {
        "type": fields.get("evidence_type", b"").decode("utf-8", "replace").strip(),
        "reference": " ".join(fields.get("reference", b"").decode("utf-8", "replace").split())[:MAX_REFERENCE],
        "file": fields.get("file", b""),
    }


@router.post("/packs/{pack_id}/truth/{claim_id}/confirm")
async def confirm(request: Request, pack_id: str, claim_id: str):
    ws = workspace_of(request)
    f = await _confirm_fields(request)
    state = _read(request, pack_id)
    claim = state.truth.claim(claim_id)
    if claim is None:
        raise HTTPException(404, "No such claim")
    values = {"type": f.get("type", ""), "reference": f.get("reference", "")}

    def refuse(msg: str, field: str, status: int = 422):
        return _claim_response(request, state, claim_id, status=status, error=msg, field=field, values=values, say=msg)

    if f.get("too_large"):
        return refuse(f"That file is bigger than the {MAX_BYTES // 1_000_000} MB limit.", "file")
    if claim.hard_blocked or hard_blocks(claim.text, state.ruleset):  # P25: the server decides, not the form
        return refuse(
            "This claim hits a rule that cannot be overridden, so it cannot be confirmed. "
            "Leave it out and write what the product does in other words.",
            "",
            status=403,
        )
    try:
        etype = EvidenceType(f["type"])
    except ValueError:
        return refuse("Choose an evidence type.", "type")
    typed, upload = f["reference"], f["file"]
    if typed.lower().startswith("file:"):
        return refuse("Upload the file instead of typing a file path.", "reference")
    if etype == EvidenceType.TEST_REPORT and not upload and sum(ch.isalnum() for ch in typed) < MIN_REFERENCE_CHARS:
        return refuse("A test report needs a document ID, or upload the report (PDF, PNG or JPEG).", "reference")
    reference, note = typed or None, None
    if upload:
        try:
            path = await run_in_threadpool(packs.evidence().put, ws, "evidence", upload)
        except EvidenceError as e:
            return refuse(str(e), "file")
        reference, note = f"file:{path}", typed or None
    try:
        confirmed = confirm_claim(claim, Evidence(type=etype, reference=reference, note=note), state.ruleset)
    except ClaimGuardError as e:
        return refuse(str(e), "reference", status=403)
    with review.open_pack(request, pack_id) as live:
        _set_claim(request, live, confirmed)
        return _claim_response(request, live, claim_id, say=f"Claim {claim_id.upper()} confirmed.")


@router.post("/packs/{pack_id}/truth/{claim_id}/reject")
async def reject(request: Request, pack_id: str, claim_id: str):
    with review.open_pack(request, pack_id) as state:
        claim = state.truth.claim(claim_id)
        if claim is None:
            raise HTTPException(404, "No such claim")
        _set_claim(request, state, claim.model_copy(update={"status": ClaimStatus.REJECTED, "evidence": None}))
        return _claim_response(request, state, claim_id, say=f"Claim {claim_id.upper()} left out of the copy.")


# ---------------------------------------------------------------------------------------------------- generate
def progress_of(state: ReviewState) -> dict[str, Any]:
    gen = state.gen or {}
    status, step = gen.get("status", "idle"), int(gen.get("step", 0))
    label = {
        "running": GEN_LABELS.get(step, GEN_LABELS[TOTAL_STEPS - 1]),
        "done": "Your pack is ready",
        "cancelled": "Stopped. Nothing was changed.",
        "failed": gen.get("error") or "We couldn't write the pack.",
        "idle": "Ready to write",
    }[status]
    done = TOTAL_STEPS if status == "done" else step
    return {
        "status": status,
        "step": step,
        "total": TOTAL_STEPS,
        "done": done,
        "label": label,
        "next": f"/packs/{state.pack_id}/review" if status == "done" else "",
    }


def _json(state: ReviewState) -> JSONResponse:
    return JSONResponse(progress_of(state), headers={"Cache-Control": "no-store"})


@router.get("/packs/{pack_id}/generate")
def generate_page(request: Request, pack_id: str):
    state = _read(request, pack_id)
    s = summary_of(state)
    status = (state.gen or {}).get("status", "idle")
    has_pack = s["has_pack"]
    ctx = {
        "title": f"Generate the PDP pack: {state.product} · Satya",
        "ruleset": state.ruleset,
        "pack_id": pack_id,
        "product": state.product,
        "summary": s,
        "progress": progress_of(state),
        "groups": [g for g, _ in review.GROUPS],
        "has_pack": has_pack,
        "auto": not has_pack and status in ("idle", "running"),
    }
    return render(request, "fix/generate.html", ctx)


@router.post("/packs/{pack_id}/generate/start")
async def generate_start(request: Request, pack_id: str):
    with review.open_pack(request, pack_id) as state:
        if any(c.status == ClaimStatus.CONFIRMED and c.hard_blocked for c in state.truth.claims):
            raise HTTPException(409, "A blocked claim is marked as confirmed")
        state.gen = {"status": "running", "step": 0}
        return _json(state)


def _fail(state: ReviewState, message: str) -> None:
    state.gen = {"status": "failed", "step": int((state.gen or {}).get("step", 0)), "error": message}


@router.post("/packs/{pack_id}/generate/step")
async def generate_step(request: Request, pack_id: str):
    state = _read(request, pack_id)
    gen = state.gen or {}
    if gen.get("status") != "running":
        return _json(state)  # idle, cancelled, failed or done: a late step from the browser changes nothing
    step, tone = int(gen.get("step", 0)), _tone(request)
    error = ""
    produced: PDPPack | None = None
    try:
        if step == 0:
            produced = await run_in_threadpool(api.generate_pack, state.truth, tone=tone)
        else:
            draft = PDPPack.model_validate(gen["draft"])
            report = await run_in_threadpool(api.verify_pack, draft, state.truth, ruleset=state.ruleset)
            produced = report.pack
    except (api.GenerationError, ProviderError, api.AllProvidersFailed, api.ProviderConfigError):
        error = "We couldn't write the pack. Nothing was changed. Try again."
    except (KeyError, ValueError):
        error = "The draft was lost. Start again."
    with review.open_pack(request, pack_id) as live:
        if (live.gen or {}).get("status") != "running":  # cancelled while the model was working: drop the result
            return _json(live)
        if error or produced is None:
            _fail(live, error)
        elif step == 0:
            live.gen = {"status": "running", "step": 1, "draft": produced.model_dump(mode="json")}
        else:
            live.pack = produced
            live.kept.clear()
            live.rewrites.clear()
            live.reported.clear()
            live.approved = live.last_edit_after_approval = False
            live.approve_error, live.last_announce = None, ""
            live.gen = {"status": "done", "step": TOTAL_STEPS}
        return _json(live)


@router.post("/packs/{pack_id}/generate/cancel")
async def generate_cancel(request: Request, pack_id: str):
    with review.open_pack(request, pack_id) as state:
        if (state.gen or {}).get("status") == "running":
            state.gen = {"status": "cancelled", "step": int(state.gen.get("step", 0))}  # the draft is dropped
        return _json(state)
