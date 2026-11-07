"""Export screens (SAT-43): /packs/{id}/export (generic CSV with column mapping, copy, download, audit record) and the
print-friendly /packs/{id}/report. The engine gate fails closed; its reasons are shown here. Draft content (P20)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from engine.export import (
    SOURCES,
    ExportBlocked,
    MappingError,
    default_mapping,
    export_blockers,
    export_csv,
    get_layout,
    list_layouts,
)
from engine.repo import NotFound, ReviewState
from engine.translate.journey import hindi_export_blockers
from web import packs
from web.app import form_data, render
from web.auth import authenticate
from web.security import guard_unsafe

router = APIRouter(dependencies=[Depends(guard_unsafe), Depends(authenticate), Depends(packs.dev_seed)])


def _state(request: Request, pack_id: str) -> ReviewState:
    try:
        state = packs.repo().get(packs.workspace_of(request), pack_id)
    except NotFound:
        raise HTTPException(404, "No such pack") from None
    return state


def _blocked(request: Request, state: ReviewState, blockers: list[str], what: str):
    ctx = {"title": f"{what} blocked · Satya", "state": state, "ruleset": state.ruleset, "blockers": blockers}
    return render(request, "export/blocked.html", ctx, status=409)


def _gate(request: Request, state: ReviewState, what: str, lang: str = "en"):
    """The blocked page when the pack cannot leave, else None. Hindi also needs the approved English pack it was
    translated from, so a stale or unverified Hindi pack fails closed."""
    if lang == "hi":
        blockers = hindi_export_blockers(state.approved, state.pack, state.hi_pack, state.hi_for, state.truth)
        return _blocked(request, state, blockers, what) if blockers else None
    if state.pack is None:
        return _blocked(request, state, ["This pack has no generated listing yet."], what)
    blockers = export_blockers(state.pack, state.truth)
    return _blocked(request, state, blockers, what) if blockers else None


def _pack_for(state: ReviewState, lang: str):
    return state.hi_pack if lang == "hi" else state.pack


def _mapping(data: dict[str, str], layout) -> dict[str, str | None]:
    if not any(k.startswith("map:") for k in data):
        return default_mapping(layout)  # no mapping sent: the layout's own defaults
    return {c.header: data.get(f"map:{c.header}") or None for c in layout.columns}


def _layout(data: dict[str, str]):
    return get_layout(data.get("layout") or list_layouts()[0].id)


def _page_ctx(state: ReviewState, lang: str, layout, mapping, error: str = "") -> dict:
    what = "Hindi export" if lang == "hi" else "Export"
    return {
        "title": f"{what}: {state.product} · Satya", "state": state, "ruleset": state.ruleset, "layout": layout,
        "mapping": mapping, "sources": SOURCES, "error": error, "lang": lang,
        "export_url": f"/packs/{state.pack_id}/export" + ("/hindi" if lang == "hi" else ""),
    }  # fmt: skip


def _export_page(request: Request, pack_id: str, lang: str):
    state = _state(request, pack_id)
    if (blocked := _gate(request, state, "Hindi export" if lang == "hi" else "Export", lang)) is not None:
        return blocked
    layout = list_layouts()[0]
    return render(request, "export/page.html", _page_ctx(state, lang, layout, default_mapping(layout)))


async def _export_do(request: Request, pack_id: str, lang: str):
    """`do` = view (copy and download buttons), csv (download) or audit (the audit record, JSON)."""
    data = await form_data(request)
    state = _state(request, pack_id)
    what = "Hindi export" if lang == "hi" else "Export"
    if (blocked := _gate(request, state, what, lang)) is not None:
        return blocked
    try:
        layout = _layout(data)
        mapping = _mapping(data, layout)
        result = export_csv(_pack_for(state, lang), state.truth, layout=layout, mapping=mapping, language=lang)
    except MappingError as e:
        layout = list_layouts()[0]
        ctx = _page_ctx(state, lang, layout, _mapping(data, layout), str(e))
        return render(request, "export/page.html", ctx, status=422)
    except ExportBlocked as e:  # raced with an edit between the gate above and the export
        return _blocked(request, state, e.blockers, what)
    do = data.get("do", "view")
    if do == "csv":
        return Response(result.content, media_type="text/csv; charset=utf-8", headers=_attachment(result.filename))
    if do == "audit":
        return Response(
            result.audit.to_json(), media_type="application/json", headers=_attachment(result.audit_filename)
        )
    ctx = _page_ctx(state, lang, layout, result.audit.mapping) | {
        "title": f"{what} ready: {state.product} · Satya", "result": result, "text": result.content.decode("utf-8-sig"),
    }  # fmt: skip
    return render(request, "export/done.html", ctx)


@router.get("/packs/{pack_id}/export")
def export_page(request: Request, pack_id: str):
    return _export_page(request, pack_id, "en")


@router.post("/packs/{pack_id}/export")
async def export_do(request: Request, pack_id: str):
    return await _export_do(request, pack_id, "en")


@router.get("/packs/{pack_id}/export/hindi")
def export_hindi_page(request: Request, pack_id: str):
    return _export_page(request, pack_id, "hi")


@router.post("/packs/{pack_id}/export/hindi")
async def export_hindi_do(request: Request, pack_id: str):
    return await _export_do(request, pack_id, "hi")


def _attachment(name: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff"}  # fmt: skip


@router.get("/packs/{pack_id}/report")
def report_page(request: Request, pack_id: str):
    state = _state(request, pack_id)
    if (blocked := _gate(request, state, "Report")) is not None:
        return blocked
    audit = export_csv(state.pack, state.truth).audit  # the default CSV's record: claims, flags, overrides, SHA-256
    ctx = {
        "title": f"Report: {state.product} · Satya", "state": state, "ruleset": state.ruleset, "pack": state.pack,
        "truth": state.truth, "audit": audit,
    }  # fmt: skip
    return render(request, "export/report.html", ctx)


@router.get("/audits/{job_id}/report")
async def audit_report_page(request: Request, job_id: str):
    """Print-friendly catalogue audit report. Another workspace's id is a 404."""
    from starlette.concurrency import run_in_threadpool

    from engine.audit import audit_report
    from engine.rules import default_ruleset
    from web import audits

    ws = packs.workspace_of(request)

    def work():
        with audits.db() as conn:
            audits._owned(conn, ws, job_id)
            return audit_report(conn, job_id)

    report = await run_in_threadpool(work)
    ctx = {"title": "Audit report · Satya", "ruleset": default_ruleset(), "report": report, "job_id": job_id}
    return render(request, "export/audit_report.html", ctx)
