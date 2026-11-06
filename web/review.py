"""Review screen (variant B, Truth <-> Copy): GET /packs/{id}/review and its HTMX actions.

Sentence checks are deterministic (`engine.api.edit_sentence`); Approve re-verifies the whole pack (`verify_pack`,
fail closed). Persistence and auth belong to Platform: this module talks to a `PackStore` and ships an in-memory one
seeded with a clearly-labelled demo pack so the page can be previewed. Nothing here says "compliant" (P20).
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, Request

from engine import api
from engine.models import ClaimStatus, EvidenceType, PDPPack, ProductTruth, Severity
from engine.rules import OverrideNotAllowed, RuleSet, check_override, evaluate
from web import view
from web.app import form_data, render

router = APIRouter()

SECTION_LABELS = {
    "title": "Title",
    "bullet_1": "Bullet 1",
    "bullet_2": "Bullet 2",
    "bullet_3": "Bullet 3",
    "bullet_4": "Bullet 4",
    "bullet_5": "Bullet 5",
    "description": "Description",
    "how_to_use": "How to use",
    "warnings_storage": "Warnings and storage",
    "seo_title": "SEO title tag",
    "seo_description": "Meta description",
}
GROUPS = (
    ("Title", ("title",)),
    ("Bullet points", ("bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5")),
    ("Description", ("description",)),
    ("How to use", ("how_to_use",)),
    ("Warnings and storage", ("warnings_storage",)),
    ("SEO meta", ("seo_title", "seo_description")),
)
SEO_LIMITS = {"seo_title": 60, "seo_description": 160}  # soft limits, stated as text
TYPE_LABELS = {
    "product_fact": "Product fact",
    "benefit_claim": "Benefit claim",
    "usage": "Usage",
    "warning": "Warning",
    "storage": "Storage",
    "legal": "Legal",
    "descriptive": "Descriptive",
}
MAX_REASON = 500
ALLOW_RED_OVERRIDE = True  # ADR-10: overridable reds may be kept with an evidence reference; non-overridable never


# ---------------------------------------------------------------------------------------------------- state
@dataclass
class Keep:
    reason: str
    evidence: bool


@dataclass
class ReviewState:
    pack_id: str
    product: str
    truth: ProductTruth
    pack: PDPPack | None
    ruleset: RuleSet
    kept: dict[tuple[str, str, str], Keep] = field(default_factory=dict)  # (sid, rule_id, matched_text)
    rewrites: dict[str, str] = field(default_factory=dict)  # sid -> engine-suggested rewrite, when supplied
    reported: set[tuple[str, str]] = field(default_factory=set)  # (sid, rule_id)
    approved: bool = False
    last_edit_after_approval: bool = False
    approve_error: str | None = None
    last_announce: str = ""


class PackStore:
    """In-memory stand-in for the Platform's pack storage (RLS, one brand workspace per user)."""

    def __init__(self) -> None:
        self._packs: dict[str, ReviewState] = {}
        self._lock = threading.RLock()

    def put(self, state: ReviewState) -> None:
        with self._lock:
            self._packs[state.pack_id] = state

    def get(self, pack_id: str) -> ReviewState:
        with self._lock:
            if pack_id not in self._packs:
                raise HTTPException(404, "No such pack")
            return self._packs[pack_id]

    @property
    def lock(self) -> threading.RLock:
        return self._lock


store = PackStore()


def sid_of(key: str, i: int) -> str:
    return f"{key}-{i}"


def locate(state: ReviewState, sid: str) -> tuple[str, int]:
    key, _, idx = sid.rpartition("-")
    if state.pack is None or key not in SECTION_LABELS or not idx.isdigit():
        raise HTTPException(404, "No such sentence")
    if int(idx) >= len(state.pack.section(key).sentences):
        raise HTTPException(404, "No such sentence")
    return key, int(idx)


# ---------------------------------------------------------------------------------------------------- view model
def claim_state(c) -> str:
    if c.hard_blocked:
        return "blocked"
    if c.status == ClaimStatus.CONFIRMED:
        return "confirmed"
    if c.status == ClaimStatus.REJECTED:
        return "rejected"
    if c.evidence and c.evidence.type == EvidenceType.TEST_REPORT and not c.evidence.reference:
        return "needs_reference"
    return "unconfirmed"


CLAIM_BADGE = {
    "confirmed": ("green", "Confirmed", "ok"),
    "unconfirmed": ("ink", "Not confirmed", "info"),
    "needs_reference": ("amber", "Needs reference", "warn"),
    "blocked": ("red", "Cannot confirm", "block"),
    "rejected": ("ink", "Rejected", "info"),
}


def _evidence_line(c) -> str:
    if c.hard_blocked:
        return "Hit a rule that cannot be overridden: " + ", ".join(c.blocking_rule_ids or ["see rule"])
    if c.evidence is None:
        return "No evidence yet"
    ev = c.evidence.type.value.replace("_", " ").capitalize()
    return f"{ev}: {c.evidence.reference}" if c.evidence.reference else f"{ev}: no reference attached"


def _label(key: str, i: int, n: int) -> str:
    base = SECTION_LABELS[key]
    return base if n == 1 else f"{base}, sentence {i + 1}"


def _flag_views(state: ReviewState, sid: str, sentence) -> list[dict]:
    rs = state.ruleset
    out = []
    for f in sentence.flags:
        sev = view.ui_sev(f.severity.value)
        keep = state.kept.get((sid, f.rule_id, f.matched_text or ""))
        title, kind = f.reason, f.source
        if f.source == "rule":
            try:
                title = rs.rule(f.rule_id).title
            except KeyError:
                pass
        elif f.rule_id == "ANCHOR-UNCONFIRMED":
            title = "Source claim is not confirmed"
        elif f.rule_id == "ANCHOR-MISSING":
            title = "No source claim"
        elif f.rule_id == "ANCHOR-INVALID":
            title = "Source field is empty"
        elif f.rule_id == "ANCHOR-WEAK":
            title = "Benefit claim has no confirmed source claim"
        elif f.rule_id == "VERIFIER-UNSUPPORTED":
            title = "Not supported by its sources"
        short, long = view.override_label(f.overridable, f.severity.value, ALLOW_RED_OVERRIDE)
        out.append(
            {
                "rule_id": f.rule_id,
                "sev": sev,
                "title": title,
                "why": f.reason if f.source != "rule" else rs.rule(f.rule_id).explanation,
                "text": (f.matched_text or "") if f.source == "rule" else "",
                "kind": kind,
                "overridable": f.overridable and (sev != "red" or ALLOW_RED_OVERRIDE),
                "policy": short,
                "kept": keep is not None and f.overridable,
                "reason": keep.reason if keep else "",
                "hint": f.suggestion,
                "reported": (sid, f.rule_id) in state.reported,
                "sheet": f.source == "rule",
            }
        )
    return out


def _row(state: ReviewState, key: str, i: int, sentence, n: int, truth_claims: dict) -> dict:
    sid = sid_of(key, i)
    marks = view.marks_from_flags(evaluate(sentence.text, state.ruleset))  # rule marks only: anchors have no phrase
    flags = _flag_views(state, sid, sentence)
    open_red = [f for f in flags if f["sev"] == "red" and not f["kept"]]
    open_amber = [f for f in flags if f["sev"] == "amber" and not f["kept"]]
    kept = [f for f in flags if f["kept"]]
    status = "red" if open_red else "amber" if open_amber else "kept" if kept else "ok"
    hard = any(not f["overridable"] for f in open_red)
    anchors = []
    for a in sentence.anchors:
        kind, _, ref = a.partition(":")
        if kind == "claim" and ref in truth_claims:
            c = truth_claims[ref]
            st = claim_state(c)
            anchors.append(
                {
                    "kind": "claim",
                    "id": c.id,
                    "text": c.text,
                    "state": st,
                    "label": CLAIM_BADGE[st][1],
                    "evidence": _evidence_line(c),
                }
            )
        elif kind == "claim":
            anchors.append(
                {
                    "kind": "claim",
                    "id": ref,
                    "text": "Unknown claim",
                    "state": "unconfirmed",
                    "label": "Not confirmed",
                    "evidence": "No such claim",
                }
            )
        else:
            anchors.append(
                {
                    "kind": "truth",
                    "id": ref,
                    "text": ref.replace("_", " ").capitalize(),
                    "state": "confirmed",
                    "label": "Product Truth field",
                    "evidence": "",
                }
            )
    keep_kind = None
    if open_red and not hard and ALLOW_RED_OVERRIDE:
        keep_kind = "evidence"
    elif not open_red and open_amber:
        keep_kind = "reason"
    first_kept = kept[0] if kept else None
    return {
        "sid": sid,
        "key": key,
        "label": _label(key, i, n),
        "text": sentence.text,
        "backdrop": view.build_backdrop(sentence.text, marks),
        "status": status,
        "status_word": {"red": "Blocked", "amber": "Needs a reason", "kept": "Kept with reason", "ok": "Clear"}[status],
        "type": TYPE_LABELS.get(sentence.type.value, sentence.type.value),
        "flags": flags,
        "anchors": anchors,
        "keep_kind": keep_kind,
        "hard_blocked": hard,
        "kept_reason": first_kept["reason"] if first_kept else "",
        "rewrite": state.rewrites.get(sid) if status in ("red", "amber") else None,
        "seo_limit": SEO_LIMITS.get(key),
        "length": len(sentence.text),
        "error": None,
        "prefill": "",
        "ruleset": state.ruleset,
    }


def build_view(state: ReviewState) -> dict:
    claims = {c.id: c for c in state.truth.claims}
    ctx: dict = {
        "state": state,
        "ruleset": state.ruleset,
        "pack_id": state.pack_id,
        "product": state.product,
        "title": f"Review: {state.product} · Satya",
    }
    if state.pack is None or not state.pack.sentences():
        ctx.update(empty=True, groups=[], rows=[], ledger=[], summary=summarize([], state))
        return ctx
    groups, rows = [], []
    for heading, keys in GROUPS:
        g_rows = []
        for key in keys:
            sents = state.pack.section(key).sentences
            for i, s in enumerate(sents):
                r = _row(state, key, i, s, len(sents), claims)
                g_rows.append(r)
                rows.append(r)
        groups.append({"heading": heading, "rows": g_rows})
    used: dict[str, list[dict]] = {cid: [] for cid in claims}
    for r in rows:
        for a in r["anchors"]:
            if a["kind"] == "claim" and a["id"] in used:
                used[a["id"]].append({"sid": r["sid"], "label": r["label"]})
    ledger = []
    for c in state.truth.claims:
        st = claim_state(c)
        sev, word, icon = CLAIM_BADGE[st]
        ledger.append(
            {
                "id": c.id,
                "text": c.text,
                "state": st,
                "sev": sev,
                "word": word,
                "icon": icon,
                "evidence": _evidence_line(c),
                "used": used[c.id],
            }
        )
    ctx.update(empty=False, groups=groups, rows=rows, ledger=ledger, summary=summarize(rows, state))
    return ctx


def summarize(rows: list[dict], state: ReviewState) -> dict:
    n = {"red": 0, "amber": 0, "kept": 0, "ok": 0}
    for r in rows:
        n[r["status"]] += 1
    parts = []
    if n["red"]:
        parts.append(f"{n['red']} blocked")
    if n["amber"]:
        parts.append(f"{n['amber']} need{'s' if n['amber'] == 1 else ''} a reason")
    blocked = bool(n["red"] or n["amber"])
    approved = state.approved and not blocked
    if state.last_edit_after_approval and not approved:
        note = "Edited since approval: check again."
    elif blocked:
        note = " and ".join(parts) + " before you can approve."
    elif state.approve_error:
        note = state.approve_error
    else:
        note = f"Ready to approve. No flagged risks under rule set {state.ruleset.label}."
    strip_label = (
        f"Sentences: {n['red']} blocked, {n['amber']} to review, {n['kept']} kept with reason, {n['ok']} clear"
    )
    order = [r for r in rows if r["status"] == "red"] + [r for r in rows if r["status"] == "amber"]
    return {
        **n,
        "total": len(rows),
        "blocked": blocked,
        "ready": not blocked,
        "approved": approved,
        "note": note,
        "dock_note": " · ".join(
            [
                p
                for p in (f"{n['red']} blocked" if n["red"] else "", f"{n['amber']} to review" if n["amber"] else "")
                if p
            ]
        )
        or "Ready to approve",
        "strip": [r["status"] for r in rows],
        "strip_label": strip_label,
        "first_blocker": order[0]["sid"] if order else "",
        "announce": ("Ready to approve." if not blocked else "Approval blocked: " + " and ".join(parts) + "."),
    }


# ---------------------------------------------------------------------------------------------------- actions
def _trigger(**events) -> dict[str, str]:
    return {"HX-Trigger": json.dumps(events)}


def _live_response(
    request: Request,
    state: ReviewState,
    sid: str,
    *,
    say: str | None = None,
    extra_events: dict | None = None,
    error: str | None = None,
    prefill: str = "",
):
    """Row partial plus OOB parts. Announces only when the outcome changed (never per keystroke)."""
    ctx = build_view(state)
    row = next(r for r in ctx["rows"] if r["sid"] == sid)
    row["error"] = error
    row["prefill"] = prefill
    announce = ctx["summary"]["announce"]
    if say is None and announce != state.last_announce:
        say = announce
    state.last_announce = announce
    events = {"satya:say": say} if say else {}
    events.update(extra_events or {})
    return render(request, "review/_live.html", {**ctx, "row": row}, headers=_trigger(**events))


def _sentence(state: ReviewState, sid: str):
    key, i = locate(state, sid)
    return key, i, state.pack.section(key).sentences[i]


def _apply_text(state: ReviewState, sid: str, text: str) -> None:
    """Re-check `text` deterministically and keep reasons/evidence whose flagged wording is unchanged."""
    key, i = locate(state, sid)
    state.pack = api.edit_sentence(state.pack, key, i, text, state.truth, ruleset=state.ruleset)
    new_flags = {(sid, f.rule_id, f.matched_text or "") for f in state.pack.section(key).sentences[i].flags}
    for k in list(state.kept):
        if k[0] == sid and k not in new_flags:
            del state.kept[k]  # the flagged wording changed: the old reason no longer applies
    if state.approved:
        state.approved, state.last_edit_after_approval = False, True


@router.get("/packs/{pack_id}/review")
def review_page(request: Request, pack_id: str):
    state = store.get(pack_id)
    return render(request, "review/page.html", build_view(state))


@router.post("/packs/{pack_id}/sentences/{sid}/check")
async def check_sentence(request: Request, pack_id: str, sid: str):
    state = store.get(pack_id)
    text = (await form_data(request)).get("text", "")
    with store.lock:
        _apply_text(state, sid, text)
        resp = _live_response(request, state, sid)
    return resp


@router.post("/packs/{pack_id}/sentences/{sid}/rewrite")
async def use_rewrite(request: Request, pack_id: str, sid: str):
    state = store.get(pack_id)
    with store.lock:
        key, i, sentence = _sentence(state, sid)
        new = state.rewrites.get(sid)
        if not new:
            raise HTTPException(409, "No rewrite was supplied for this sentence")
        label = _label(key, i, len(state.pack.section(key).sentences))
        _apply_text(state, sid, new)
        del state.rewrites[sid]
        row = next(r for r in build_view(state)["rows"] if r["sid"] == sid)
        clear = row["status"] == "ok"
        say = (
            f"{label} rewritten. Re-checked: no flagged risks."
            if clear
            else f"{label} rewritten. Re-checked: it still has flagged phrases."
        )
        events = {"satya:settext": {"id": f"t-{sid}", "text": new}, "satya:focus": f"t-{sid}", "satya:say": say}
        if clear:
            events.update({"satya:resolve": sid, "satya:toast": "Rewrite applied. Re-checked, no flagged risks."})
        return _live_response(request, state, sid, say=say, extra_events=events)


@router.post("/packs/{pack_id}/sentences/{sid}/keep")
async def keep(request: Request, pack_id: str, sid: str):
    state = store.get(pack_id)
    data = await form_data(request)
    reason = data.get("reason", "").strip()[:MAX_REASON]
    with store.lock:
        key, i, sentence = _sentence(state, sid)
        label = _label(key, i, len(state.pack.section(key).sentences))
        open_flags = [
            f
            for f in sentence.flags
            if (sid, f.rule_id, f.matched_text or "") not in state.kept and f.severity != Severity.SAFE
        ]
        for f in open_flags:  # the server never trusts the UI: policy decides (ADR-9, P17)
            if not f.overridable:
                raise HTTPException(403, f"{f.rule_id} cannot be overridden")
            if f.source == "rule":
                try:
                    check_override(f.rule_id, state.ruleset)
                except OverrideNotAllowed as e:
                    raise HTTPException(403, str(e)) from None
            if f.severity == Severity.RED and not ALLOW_RED_OVERRIDE:
                raise HTTPException(403, f"{f.rule_id} cannot be overridden")
        evidence = any(f.severity == Severity.RED for f in open_flags)
        if not reason:
            msg = (
                "Add an evidence reference: a document ID or an uploaded file."
                if evidence
                else "Add a reason to keep this wording."
            )
            return _live_response(
                request, state, sid, say=msg, error=msg, extra_events={"satya:focus": f"reason-{sid}"}
            )
        for f in open_flags:
            state.kept[(sid, f.rule_id, f.matched_text or "")] = Keep(reason, f.severity == Severity.RED)
            if f.severity == Severity.ORANGE:
                state.pack = api.override_flag(state.pack, key, i, f.rule_id, reason)
        if state.approved:
            state.approved, state.last_edit_after_approval = False, True
        say = f"{label} kept with your {'evidence reference' if evidence else 'reason'}."
        return _live_response(request, state, sid, say=say, extra_events={"satya:focus": f"t-{sid}", "satya:say": say})


@router.post("/packs/{pack_id}/sentences/{sid}/edit-reason")
async def edit_reason(request: Request, pack_id: str, sid: str):
    state = store.get(pack_id)
    with store.lock:
        _sentence(state, sid)
        old = next((v.reason for k, v in state.kept.items() if k[0] == sid), "")
        for k in [k for k in state.kept if k[0] == sid]:
            del state.kept[k]
        return _live_response(
            request, state, sid, say="Editing the reason.", prefill=old, extra_events={"satya:focus": f"reason-{sid}"}
        )


@router.post("/packs/{pack_id}/sentences/{sid}/report")
async def report_flag(request: Request, pack_id: str, sid: str):
    state = store.get(pack_id)
    data = await form_data(request)
    rule_id = data.get("rule_id", "")
    with store.lock:
        _, _, sentence = _sentence(state, sid)
        if rule_id not in {f.rule_id for f in sentence.flags}:
            raise HTTPException(404, "No such flag")
        if data.get("undo"):
            state.reported.discard((sid, rule_id))
        else:
            state.reported.add((sid, rule_id))  # tuning queue; changes no status and unblocks nothing
        return _live_response(
            request, state, sid, say="Reported as a wrong flag." if not data.get("undo") else "Report withdrawn."
        )


@router.post("/packs/{pack_id}/approve")
async def approve(request: Request, pack_id: str):
    state = store.get(pack_id)
    data = await form_data(request)
    with store.lock:
        # Texts the browser holds that the server never checked (a failed re-check) are re-checked now.
        for sid, text in data.items():
            if sid.startswith("text-"):
                real = sid[5:]
                key, i, s = _sentence(state, real)
                if s.text != text:
                    _apply_text(state, real, text)
        ctx = build_view(state)
        state.approve_error = None
        if ctx["summary"]["blocked"]:
            first = ctx["summary"]["first_blocker"]
            ctx = build_view(state)
            return render(
                request,
                "review/_gate_parts.html",
                ctx,
                headers=_trigger(**{"satya:say": ctx["summary"]["announce"], "satya:focus": f"t-{first}"}),
            )
        report = api.verify_pack(state.pack, state.truth, ruleset=state.ruleset)
        state.pack = report.pack
        ctx = build_view(state)
        if not report.pass2_completed:
            state.approve_error = "The verifier could not run, so approval stays off. Try again in a moment."
        elif ctx["summary"]["blocked"]:
            pass  # the verifier raised a new flag; rows below are re-rendered by the reload trigger
        else:
            state.approved, state.last_edit_after_approval = True, False
        ctx = build_view(state)
        events = {
            "satya:say": "Approved. The audit record is attached to your export."
            if ctx["summary"]["approved"]
            else ctx["summary"]["note"]
        }
        if ctx["summary"]["blocked"]:
            events["satya:reload"] = True  # new flags from the verifier: reload so every row shows them
        return render(request, "review/_gate_parts.html", ctx, headers=_trigger(**events))
