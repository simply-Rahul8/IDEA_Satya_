"""Hindi tab of the review page: GET/POST /packs/{id}/hindi. Translate an approved English pack, re-verify the Hindi
text, show the flags and the export gate. Fails closed: no English approval or no verified Hindi, no export.
Everything Hindi is DRAFT until the native reviewer signs off (SAT-5, P20)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from engine.providers import ProviderError
from engine.translate.journey import english_digest, hindi_export_blockers, translate_and_verify
from web import packs, view
from web.app import render
from web.auth import authenticate
from web.review import SECTION_LABELS, TYPE_LABELS, _read, open_pack
from web.security import guard_unsafe

router = APIRouter(dependencies=[Depends(guard_unsafe), Depends(authenticate), Depends(packs.dev_seed)])


def build_view(state) -> dict:
    rows = []
    for sec in state.hi_pack.sections if state.hi_pack else ():
        for i, s in enumerate(sec.sentences):
            flags = [
                {
                    "rule_id": f.rule_id,
                    "sev": view.ui_sev(f.severity.value),
                    "reason": f.reason,
                    "text": f.matched_text or "",
                }
                for f in s.flags
            ]
            rows.append(
                {
                    "label": SECTION_LABELS.get(sec.key, sec.key)
                    + (f", sentence {i + 1}" if len(sec.sentences) > 1 else ""),
                    "text": s.text,
                    "type": TYPE_LABELS.get(s.type.value, s.type.value),
                    "flags": flags,
                }
            )
    blockers = hindi_export_blockers(state.approved, state.pack, state.hi_pack, state.hi_for, state.truth)
    return {
        "ruleset": state.ruleset,
        "pack_id": state.pack_id,
        "product": state.product,
        "title": f"Hindi: {state.product} · Satya",
        "rows": rows,
        "has_hindi": state.hi_pack is not None,
        "can_translate": state.approved,
        "blockers": blockers,
        "ready": not blockers,
        "error": state.hi_error,
        "lexicon": state.hi_pack.rule_set_version if state.hi_pack else "",
    }


@router.get("/packs/{pack_id}/hindi")
def hindi_page(request: Request, pack_id: str):
    return render(request, "review/hindi.html", build_view(_read(request, pack_id)))


@router.post("/packs/{pack_id}/hindi")
def translate(request: Request, pack_id: str):
    with open_pack(request, pack_id) as state:
        if not state.approved or state.pack is None:
            raise HTTPException(409, "Approve the English pack first")
        try:
            state.hi_pack, verified = translate_and_verify(state.pack, state.truth)
            state.hi_for = english_digest(state.pack)
            state.hi_error = None if verified else "The verifier could not run, so the Hindi pack stays unverified."
        except ProviderError:
            state.hi_pack, state.hi_for = None, ""
            state.hi_error = "Translation failed. Nothing was saved. Try again in a moment."
    return RedirectResponse(f"/packs/{pack_id}/hindi", status_code=303)
