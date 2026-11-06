"""Audit screens (SAT-40; screen-audit.md, plan section 3 step 3, P11, P23): upload or paste, the stepwise job, the
heat-strip page and its HTML parts (cells, table rows, product peek).

The browser drives the job (`POST /audits/{id}/step`) and the page is server-rendered from `audit_report`, so every
cell is in the first HTML response. Each job is read through its workspace: an id from another workspace is a 404.
Listing text is data (P19): it only ever reaches templates through autoescaping. Nothing here says "compliant" (P20).
"""

from __future__ import annotations

import contextlib
import os
import re
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import HTTP
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from engine.audit import (
    MAX_BYTES,
    MAX_ROWS,
    AuditItem,
    AuditReport,
    ImportProblem,
    NeedsMapping,
    OverLimit,
    State,
    audit_report,
    cancel_audit,
    create_audit,
    import_catalogue,
    resume_audit,
    retry_errors,
    step_audit,
)
from engine.audit.importers import FIELDS
from web.app import render
from web.auth import authenticate
from web.security import guard_unsafe, workspace_of

router = APIRouter(dependencies=[Depends(guard_unsafe), Depends(authenticate)])

PAGE_SIZE = 25
STEP_BATCH = 20
BODY_OVERHEAD = 200_000  # multipart framing and the text field on top of the file limit
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

# UI vocabulary (foundations section 1): state -> (badge severity, word, icon)
STATE_UI = {
    State.RED: ("red", "Blocked", "block"),
    State.AMBER: ("amber", "Review", "warn"),
    State.GREEN: ("green", "Clear", "ok"),
    State.PENDING: ("ink", "Checking", "spin"),
    State.SKIPPED: ("ink", "Not reviewed", "info"),
    State.ERROR: ("ink", "Couldn't check", "unchecked"),
}
FILTERS = {"all": None, "red": State.RED, "amber": State.AMBER, "green": State.GREEN}
FILTER_WORDS = {"all": "All", "red": "Blocked", "amber": "Review", "green": "Clear", "na": "Not checked"}
FILTER_NOUN = {"all": "products", "red": "blocked products", "amber": "products to review", "green": "clear products",
               "na": "products that were not checked"}  # fmt: skip
MAP_FIELDS = (
    ("name", "Product name", True),
    ("description", "Description", True),
    ("sku", "SKU", False),
    ("category", "Category", False),
    ("brand", "Brand", False),
    ("net_quantity", "Net quantity", False),
    ("mrp", "MRP", False),
    ("manufacturer", "Manufacturer or packer", False),
    ("country_of_origin", "Country of origin", False),
    ("consumer_care", "Consumer care contact", False),
)


# ---------------------------------------------------------------------------------------------------- database
_connect = None


def configure_db(factory) -> None:
    """Install a connection factory (tests). Returns a service-role psycopg connection."""
    global _connect
    _connect = factory


def _factory():
    if _connect is not None:
        return _connect
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        return None
    import psycopg

    return lambda: psycopg.connect(dsn, connect_timeout=5)


@contextlib.contextmanager
def db():
    factory = _factory()
    if factory is None:
        raise HTTPException(503, "Audits need the database (SUPABASE_DB_URL is not set).")
    conn = factory()
    try:
        yield conn
    finally:
        close = getattr(conn, "close", None)
        if close:
            close()


def _owned(conn, workspace: str, job_id: str) -> None:
    """404 unless this audit job belongs to the caller's workspace (the id alone grants nothing)."""
    if not _UUID.match(job_id) or not _UUID.match(workspace):
        raise HTTPException(404, "No such audit")
    with conn.cursor() as cur:
        cur.execute(
            "select 1 from jobs where id = %s and workspace_id = %s and kind = 'catalogue_audit'", (job_id, workspace)
        )
        found = cur.fetchone()
    conn.commit()
    if not found:
        raise HTTPException(404, "No such audit")


# ---------------------------------------------------------------------------------------------------- view model
@dataclass(frozen=True)
class Cell:
    i: int  # catalogue position
    rank: int  # position in risk order
    sku: str
    name: str
    state: str
    sev: str
    label: str
    icon: str
    top: str  # the one-line reason (inspector, table)
    more: int
    aria: str
    items: tuple[tuple[str, str, str, str], ...] = ()  # (sev, rule id or "", title, matched text) for the peek


def _issues(it: AuditItem) -> list[tuple[str, str, str, str]]:
    rules = sorted((f for f in it.flags if not f.rule_id.startswith("LM-")), key=lambda f: f.severity != State.RED)
    out = [("red" if f.severity == State.RED else "amber", f.rule_id, f.title, f.matched_text or "") for f in rules]
    if it.missing_fields:
        out.append(("amber", "LM", "Missing: " + ", ".join(it.missing_fields), ""))
    return out


def cell_of(it: AuditItem, rank: int = 0) -> Cell:
    sev, label, icon = STATE_UI[it.state]
    issues = _issues(it)
    if it.state in (State.SKIPPED, State.ERROR):
        top = it.note or label
    elif it.state == State.PENDING:
        top = "Waiting to be checked"
    elif not issues:
        top = "No flagged risks"
    else:
        s, rid, title, _ = issues[0]
        top = title if rid == "LM" else f"{rid} {title}"
    more = max(0, len(issues) - 1)
    return Cell(
        it.position, rank, it.sku, it.name, it.state.value, sev, label, icon, top, more,
        f"{it.sku}, {it.name}: {label}. {top}", tuple(issues),
    )  # fmt: skip


def matches(state: str, f: str) -> bool:
    if f == "all":
        return True
    if f == "na":
        return state in ("skipped", "error")
    return state == f


@dataclass
class View:
    job_id: str
    report: AuditReport
    mode: str  # running | stopped | done
    f: str
    sort: str
    cells: list[Cell]  # in strip order
    by_risk: list[Cell]
    chips: list[tuple[str, str, int]]
    legend: list[Cell]  # one example per state present, in legend order
    skipped: int
    errors: int
    cleared: bool
    out_of_scope: bool


def build_view(report: AuditReport, f: str, sort: str) -> View:
    f = f if f in FILTER_WORDS else "all"
    c = report.counters
    mode = "running" if report.status in ("pending", "running") and c.pending else "stopped" if c.pending else "done"
    if sort not in ("risk", "cat"):
        sort = "cat" if mode == "running" else "risk"
    by_risk = [cell_of(it, n) for n, it in enumerate(report.items)]
    by_cat = sorted(by_risk, key=lambda x: x.i)
    present = {x.state for x in by_risk}
    na = c.skipped + c.error
    counts = {"all": c.total, "red": c.red, "amber": c.amber, "green": c.green, "na": na}
    chips = [(k, FILTER_WORDS[k], counts[k]) for k in ("all", "red", "amber", "green")] + (
        [("na", "Not checked", na)] if na else []
    )
    order = ("red", "amber", "green", "pending", "skipped", "error")
    legend = [next(x for x in by_risk if x.state == s) for s in order if s in present]
    return View(
        report.job_id, report, mode, f, sort, by_cat if sort == "cat" else by_risk, by_risk, chips, legend,
        c.skipped, c.error,
        cleared=mode == "done" and c.red == 0 and c.amber == 0 and c.green > 0,
        out_of_scope=c.total == 1 and c.skipped == 1,
    )  # fmt: skip


def counters_of(c) -> dict[str, int]:
    return {"red": c.red, "amber": c.amber, "green": c.green, "na": c.skipped + c.error}


def _query(request: Request) -> tuple[str, str]:
    return request.query_params.get("f", "all"), request.query_params.get("sort", "")


async def _view(request: Request, job_id: str) -> View:
    ws = workspace_of(request)

    def work() -> AuditReport:
        with db() as conn:
            _owned(conn, ws, job_id)
            return audit_report(conn, job_id)

    report = await run_in_threadpool(work)
    f, sort = _query(request)
    return build_view(report, f, sort)


# ---------------------------------------------------------------------------------------------------- upload
class TooLarge(Exception):
    pass


async def read_body(request: Request, limit: int) -> bytes:
    """The request body, refusing to buffer more than `limit` bytes (checked by Content-Length and while streaming)."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise TooLarge
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            raise TooLarge
    return bytes(body)


def parse_multipart(content_type: str, body: bytes) -> dict[str, bytes]:
    """name -> raw bytes for each part of a multipart/form-data body (stdlib only; no extra dependency)."""
    if not content_type.lower().startswith("multipart/form-data"):
        raise ValueError("not multipart")
    head = b"MIME-Version: 1.0\r\nContent-Type: " + content_type.encode("latin-1", "replace") + b"\r\n\r\n"
    msg = BytesParser(policy=HTTP).parsebytes(head + body)
    out: dict[str, bytes] = {}
    for n, part in enumerate(msg.iter_parts()):
        if n >= 40:
            break
        name = part.get_param("name", header="content-disposition")
        if isinstance(name, str):
            out[name] = part.get_payload(decode=True) or b""
    return out


def problem(request: Request, title: str, body: str, *, kind: str = "error", mapping=None, actions=(), status=422):
    ctx = {"title": title, "body": body, "kind": kind, "mapping": mapping, "actions": actions}
    return render(request, "audit/_problem.html", ctx, status=status)


def _mapping_ctx(headers: list[str], chosen: dict[str, str], error: str = "") -> dict[str, Any]:
    return {"headers": headers, "chosen": chosen, "fields": MAP_FIELDS, "error": error}


@router.get("/audits/new")
async def new_audit(request: Request):
    return render(request, "audit/new.html", {"title": "Audit your catalogue · Satya", "max_rows": MAX_ROWS})


@router.post("/audits")
async def create(request: Request):
    try:
        raw = await read_body(request, MAX_BYTES + BODY_OVERHEAD)
        fields = parse_multipart(request.headers.get("content-type", ""), raw)
    except TooLarge:
        return problem(
            request, "We couldn't read that file.", f"It is bigger than the {MAX_BYTES // 1_000_000} MB limit."
        )
    except ValueError:
        raise HTTPException(400, "Expected a form upload") from None
    file, pasted = fields.get("file", b""), fields.get("text", b"").decode("utf-8", "replace")
    if file.strip():
        data, kind = file, "csv"
    elif pasted.strip():
        data, kind = pasted.encode(), "text"
    else:
        return problem(request, "Nothing to check yet.", "Choose a file, or paste some listing text.")
    chosen = {
        k[4:]: v.decode("utf-8", "replace") for k, v in fields.items() if k.startswith("map_") and k[4:] in FIELDS
    }
    chosen = {k: v for k, v in chosen.items() if v}
    mapping = chosen or None
    what = "file" if kind == "csv" else "text"
    try:
        if mapping and not (mapping.get("name") and mapping.get("description")):
            headers = list(import_headers(data))
            ctx = _mapping_ctx(headers, chosen, "Choose a column for Product name and for Description.")
            return problem(request, "Match your columns to Satya's fields.", "", mapping=ctx)
        result = await run_in_threadpool(
            lambda: import_catalogue(data, kind=kind, mapping=mapping, allow_truncate=fields.get("truncate") == b"1")
        )
    except NeedsMapping as exc:
        ctx = _mapping_ctx(exc.headers, exc.suggested)
        return problem(
            request,
            "Match your columns to Satya's fields.",
            "We didn't recognise this file's layout.",
            kind="info",
            mapping=ctx,
        )
    except OverLimit as exc:
        limit = exc.extra["limit"]
        return problem(
            request,
            f"This {what} has {exc.extra['count']} products.",
            f"v1 checks up to {limit} at a time. Split the file, or check the first {limit}.",
            kind="info",
            actions=((f"Check the first {limit}", {"truncate": "1"}), ("Choose another file", {"again": "1"})),
        )
    except ImportProblem as exc:
        return problem(
            request, f"We couldn't read that {what}.", exc.message, actions=(("Choose another file", {"again": "1"}),)
        )

    ws, user = workspace_of(request), getattr(request.state, "user_id", None)

    def make() -> str:
        with db() as conn:
            return create_audit(conn, ws, result.products, created_by=user)

    job_id = await run_in_threadpool(make)
    return Response(status_code=200, headers={"HX-Redirect": f"/audits/{job_id}", "Cache-Control": "no-store"})


def import_headers(data: bytes):
    from engine.audit.importers import _read_table, decode

    return _read_table(decode(data))[0]


# ---------------------------------------------------------------------------------------------------- page and parts
def rows_ctx(v: View, page: int) -> dict[str, Any]:
    rows = [c for c in v.cells if matches(c.state, v.f)]
    page = max(1, min(page, 200))
    lo = (page - 1) * PAGE_SIZE
    return {
        "v": v,
        "rows": rows[lo : lo + PAGE_SIZE],
        "first_new": lo > 0,
        "left": max(0, len(rows) - lo - PAGE_SIZE),
        "next": page + 1,
    }


@router.get("/audits/{audit_id}")
async def audit_page(request: Request, audit_id: str):
    v = await _view(request, audit_id)
    return render(request, "audit/page.html", {"title": "Where your listings are at risk · Satya", **rows_ctx(v, 1)})


@router.get("/audits/{audit_id}/rows")
async def audit_rows(request: Request, audit_id: str, page: int = 1):
    return render(request, "audit/_rows.html", rows_ctx(await _view(request, audit_id), page))


@router.get("/audits/{audit_id}/cells")
async def audit_cells(request: Request, audit_id: str):
    v = await _view(request, audit_id)
    try:
        start = max(0, int(request.query_params.get("from", "0")))
    except ValueError:
        start = 0
    cells = sorted((c for c in v.by_risk if c.i >= start and c.state != "pending"), key=lambda x: x.i)
    return render(request, "audit/_cells.html", {"cells": cells, "job_id": v.job_id})


@router.get("/audits/{audit_id}/products/{position}")
async def audit_peek(request: Request, audit_id: str, position: int):
    v = await _view(request, audit_id)
    cell = next((c for c in v.by_risk if c.i == position), None)
    if cell is None:
        raise HTTPException(404, "No such product")
    return render(request, "audit/_peek.html", {"v": v, "c": cell})


# ---------------------------------------------------------------------------------------------------- job control
def _control(fn):
    async def route(request: Request, audit_id: str):
        ws = workspace_of(request)

        def work():
            with db() as conn:
                _owned(conn, ws, audit_id)
                return fn(conn, audit_id)

        progress = await run_in_threadpool(work)
        return JSONResponse(progress, headers={"Cache-Control": "no-store"})

    return route


router.add_api_route(
    "/audits/{audit_id}/step", _control(lambda c, j: step_audit(c, j, batch_size=STEP_BATCH)), methods=["POST"]
)
router.add_api_route("/audits/{audit_id}/cancel", _control(cancel_audit), methods=["POST"])
router.add_api_route("/audits/{audit_id}/resume", _control(resume_audit), methods=["POST"])


@router.post("/audits/{audit_id}/retry")
async def retry(request: Request, audit_id: str):
    ws = workspace_of(request)

    def work():
        with db() as conn:
            _owned(conn, ws, audit_id)
            return retry_errors(conn, audit_id)

    await run_in_threadpool(work)
    return Response(status_code=200, headers={"HX-Redirect": f"/audits/{audit_id}", "Cache-Control": "no-store"})
