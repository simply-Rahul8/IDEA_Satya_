"""Public checker (variant A, Editorial Paper): GET/POST /check and the cacheable rule sheet.

Deterministic only (P18): imports `engine.rules` and the product-type gate, never an LLM provider.
The page stores and logs nothing about the text it is given; the hero copy about that stays draft until
Platform confirms it (specs: screen-checker section 5).
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Request
from markupsafe import Markup

from engine.product_type import GateStatus, check_product_type
from engine.ratelimit import ip_key
from engine.rules import RuleSet, default_ruleset, evaluate
from engine.rules.matcher import Flag
from web import view
from web.app import form_data, render

router = APIRouter()

CHECKER_MAX_CHARS = int(
    os.environ.get("CHECKER_MAX_CHARS", "5000")
)  # placeholder cap, Platform/Engine to confirm (P18)
SAMPLE_TEXT = (
    "Glow Dew Serum. This serum cures acne scars in 7 days and is clinically proven to lighten skin tone. "
    "Our formula repairs damaged skin and gives a dewy finish. Apply two drops morning and night."
)


class RateLimiter:
    """In-process sliding window. Platform replaces this with `engine.ratelimit.hit` on the service connection."""

    def __init__(self, limit: int, window_s: int):
        self.limit, self.window_s = limit, window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """None while allowed; otherwise the seconds until the oldest hit leaves the window."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window_s:
                q.popleft()
            if len(q) >= self.limit:
                return max(1, int(self.window_s - (now - q[0])) + 1)
            q.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter(
    int(os.environ.get("CHECKER_RATE_LIMIT", "120")), int(os.environ.get("CHECKER_RATE_WINDOW_S", "600"))
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

    flags = view.sort_flags(evaluate(checked, rs))
    level = view.risk_level(flags)
    red, orange = view.tally(flags)
    items = [(f, rs.rule(f.rule_id).title, view.ui_sev(f.severity)) for f in flags]
    parts = [p for p in (f"{red} blocked" if red else "", f"{orange} to review" if orange else "") if p]
    summary = (
        f"Checked with Satya under rule set {rs.label}: {', '.join(parts)}. Not legal advice."
        if parts
        else f"Checked with Satya: no flagged risks under rule set {rs.label}. Not legal advice."
    )
    verdict = {
        "variant": "flagged" if flags else "clear",
        "sig": view.result_signature(flags),
        "level": level,
        "risk_label": view.RISK_WORDS[level],
        "rows": items,
        "red": red,
        "orange": orange,
        "summary": summary,
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
    client = request.client.host if request.client else "unknown"
    return limiter.hit(ip_key(client))


@router.get("/check")
def check_page(request: Request):
    return render(request, "checker/page.html", _page_ctx(run_check(""), True))


@router.post("/check")
async def check_post(request: Request):
    text = (await form_data(request)).get("text", "")
    htmx = request.headers.get("HX-Request") == "true"
    wait = _limited(request)
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
