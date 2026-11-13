"""Public checker (variant A, Editorial Paper): GET/POST /check and the cacheable rule sheet.

Deterministic only (P18): imports `engine.rules` and the product-type gate, never an LLM provider.
The page stores and logs nothing about the text it is given; the hero copy about that stays draft until
Platform confirms it (specs: screen-checker section 5).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from markupsafe import Markup
from starlette.concurrency import run_in_threadpool

from engine.brand import BRAND_RULE_ID
from engine.normalize.lexicon import check_hindi, default_lexicon
from engine.product_type import GateStatus, check_product_type
from engine.ratelimit import MemoryLimiter, ip_key, make_limiter
from engine.rules import RuleSet, default_ruleset, evaluate
from engine.rules.matcher import Flag
from web import view
from web.app import form_data, render
from web.security import client_ip, guard_unsafe

router = APIRouter(dependencies=[Depends(guard_unsafe)])

CHECKER_MAX_CHARS = int(
    os.environ.get("CHECKER_MAX_CHARS", "5000")
)  # placeholder cap, Platform/Engine to confirm (P18)
SAMPLE_TEXT = (
    "Glow Dew Serum. This serum cures acne scars in 7 days and is clinically proven to lighten skin tone. "
    "Our formula repairs damaged skin and gives a dewy finish. Apply two drops morning and night."
)


RateLimiter = MemoryLimiter  # kept for callers and tests that build their own


limiter = make_limiter(
    int(os.environ.get("CHECKER_RATE_LIMIT", "120")), int(os.environ.get("CHECKER_RATE_WINDOW_S", "600"))
)


_DEVANAGARI = re.compile("[ऀ-ॿ]")


def _hindi_flags(text: str, english: list[Flag]) -> list[Flag]:
    """Hindi, transliterated and Hinglish claims from the draft Hindi lexicon, reported under the English rule each
    maps to, so the mark, the row and the citation sheet work as for English. A phrase an English rule already
    flagged is not repeated."""
    seen = [(f.start, f.end, f.rule_id) for f in english]
    return [
        Flag(rule_id=h.maps_to, category=h.category, severity=h.severity, overridable=h.overridable,
             start=h.start, end=h.end, text=h.text, message=h.message, rule_set=h.lexicon)
        for h in check_hindi(text)
        if not any(r == h.maps_to and s < h.end and h.start < e for s, e, r in seen)
    ]  # fmt: skip


def hindi_note(text: str, flags: list[Flag]) -> str:
    """Never let Hindi copy read as fully checked: the lexicon is a small draft (SAT-5)."""
    lx = default_lexicon()
    if not (_DEVANAGARI.search(text) or any(f.rule_set == lx.label for f in flags)):
        return ""
    reviewed = "" if lx.is_signed_off else ", not yet checked by a native Hindi reviewer"
    return (
        f"Hindi checks are an early draft (word list {lx.label}{reviewed}) and cover only a few claim types. "
        "Read Hindi copy against the English rules too."
    )


@dataclass
class CheckResult:
    text: str
    count: int
    over: int
    flags: list[Flag]
    backdrop: Markup
    verdict: dict | None
    announce: str


def run_check(text: str, ruleset: RuleSet | None = None) -> CheckResult:
    rs = ruleset or default_ruleset()
    over = max(0, len(text) - CHECKER_MAX_CHARS)
    checked = text[:CHECKER_MAX_CHARS]
    if not checked.strip():
        return CheckResult(text, len(text), over, [], view.build_backdrop(text, []), None, "")

    gate = check_product_type(description=checked, ruleset=rs)
    if gate.status is not GateStatus.ALLOWED:
        refused = gate.status is GateStatus.REFUSED
        verdict = {
            "variant": "out_of_scope",
            "sig": "gate-" + gate.status.value,
            "gate_title": "Satya v1 reviews cosmetics only" if refused else "This may not be a cosmetic",
            "gate_text": gate.explanation,
        }
        say = f"Not reviewed: {verdict['gate_title']}. Rule set {rs.label}."
        return CheckResult(text, len(text), over, [], view.build_backdrop(text, []), verdict, say)

    english = evaluate(checked, rs)
    flags = view.sort_flags(english + _hindi_flags(checked, english))
    note = hindi_note(checked, flags)
    level = view.risk_level(flags)
    red, orange = view.tally(flags)
    items = [(f, rs.rule(f.rule_id).title, view.ui_sev(f.severity)) for f in flags]
    parts = [p for p in (f"{red} blocked" if red else "", f"{orange} to review" if orange else "") if p]
    summary = (
        f"Checked with Satya under rule set {rs.label}: {', '.join(parts)}. Not legal advice."
        if parts
        else f"Checked with Satya: no flagged risks under rule set {rs.label}. Not legal advice."
    ) + (f" {note}" if note else "")
    verdict = {
        "variant": "flagged" if flags else "clear",
        "sig": view.result_signature(flags),
        "level": level,
        "risk_label": view.RISK_WORDS[level],
        "rows": items,
        "red": red,
        "orange": orange,
        "summary": summary,
        "hindi_note": note,
    }
    backdrop = view.build_backdrop(text, view.marks_from_flags(flags))  # marks only exist inside the cap
    return CheckResult(text, len(text), over, flags, backdrop, verdict, view.announce(flags, rs))


def _page_ctx(result: CheckResult, full_page: bool) -> dict:
    return {
        "r": result,
        "max_chars": CHECKER_MAX_CHARS,
        "sample": SAMPLE_TEXT,
        "full_page": full_page,
        "title": "Is my claim safe? · Satya",
    }


def _limited(request: Request) -> int | None:
    return limiter.hit(ip_key(client_ip(request), "check"))


@router.get("/check")
def check_page(request: Request):
    return render(request, "checker/page.html", _page_ctx(run_check(""), True))


@router.post("/check")
async def check_post(request: Request):
    text = (await form_data(request)).get("text", "")
    htmx = request.headers.get("HX-Request") == "true"
    wait = await run_in_threadpool(_limited, request)  # may hit Postgres
    if wait is not None:
        ctx = {**_page_ctx(run_check(text), not htmx), "wait_minutes": max(1, round(wait / 60)), "rate_limited": True}
        name = "checker/_result.html" if htmx else "checker/page.html"
        return render(request, name, ctx, status=429, headers={"Retry-After": str(wait)})
    result = run_check(text)
    name = "checker/_result.html" if htmx else "checker/page.html"
    return render(request, name, _page_ctx(result, not htmx))


@router.get("/rules/{rule_id}/sheet")
def rule_sheet(request: Request, rule_id: str, v: str | None = None):
    rs = default_ruleset()
    if rule_id == BRAND_RULE_ID:  # the brand's own list from /setup: no legal source, always overridable
        rule = SimpleNamespace(
            id=BRAND_RULE_ID,
            title="Brand rule: restricted phrase",
            explanation="This is your brand's own rule, not a legal rule. You listed this phrase as restricted "
            "in your brand setup, so Satya flags it wherever it appears.",
            sources=[],
            rewrite_hint="Reword it, or keep it with a reason. Change the list in Brand setup.",
        )
        ctx = {
            "rule": rule,
            "sev": "amber",
            "override_long": "Yes. Keep it with a reason; the reason is saved with the listing.",
            "ruleset": rs,
        }
        return render(request, "rules/sheet.html", ctx, headers={"Cache-Control": "public, max-age=3600"})
    try:
        rule = rs.rule(rule_id)
    except KeyError:
        raise HTTPException(404, "Unknown rule") from None
    short, long = view.override_label(rule.overridable, rule.severity)
    ctx = {
        "rule": rule,
        "sev": view.ui_sev(rule.severity),
        "override_long": long,
        "override_short": short,
        "ruleset": rs,
    }
    # No user text in this partial, so it is safe to cache; it is keyed by the rule-set label in `v`.
    return render(request, "rules/sheet.html", ctx, headers={"Cache-Control": "public, max-age=3600"})
