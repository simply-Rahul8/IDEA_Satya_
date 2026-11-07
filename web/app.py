"""Template environment, shared view helpers and response headers for the public web pages."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from engine.rules import RuleSet, default_ruleset
from web import assets

WEB_DIR = Path(__file__).resolve().parent

# The only inline script: applies the saved theme before first paint. Allowed by hash in the CSP (ADR-10).
THEME_SNIPPET = (
    "try{var t=localStorage.getItem('satya-theme');"
    "if(t==='dark'||t==='light')document.documentElement.dataset.theme=t}catch(e){}"
)
THEME_HASH = "sha256-" + base64.b64encode(hashlib.sha256(THEME_SNIPPET.encode()).digest()).decode()

CSP = "; ".join(
    [
        "default-src 'self'",
        f"script-src 'self' '{THEME_HASH}'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "form-action 'self'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
    ]
)

HTMX_CONFIG = '{"allowEval":false,"historyCacheSize":0,"defaultSwapStyle":"outerHTML","selfRequestsOnly":true,"includeIndicatorStyles":false}'

ICONS = {
    "block": '<path d="M8.5 3h7L21 8.5v7L15.5 21h-7L3 15.5v-7z"/><path d="M8 12h8"/>',
    "warn": '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.4v.1"/>',
    "ok": '<circle cx="12" cy="12" r="9"/><path d="m8 12.3 2.8 2.8 5.5-5.6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.9v.1"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "thumbdown": '<path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>',
    "anchor": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "book": '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 21.5V4.5M8 7h8"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "pencil": '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
    "down": '<path d="M12 4v16M6 14l6 6 6-6"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
    "spin": '<path d="M12 3a9 9 0 1 0 9 9"/>',
    "error": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5V13M12 16.4v.1"/>',
    "upload": '<path d="M12 16V4M6 10l6-6 6 6"/><path d="M4 16v4h16v-4"/>',
    "unchecked": '<circle cx="12" cy="12" r="9" stroke-dasharray="3 3"/><path d="M12 11v5M12 7.9v.1"/>',
}
SPRITE = Markup(
    '<svg class="sprite" width="0" height="0" aria-hidden="true">'
    + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items())
    + "</svg>"
)


@dataclass(frozen=True)
class Page:
    """Per-request values every template needs."""

    ruleset: RuleSet
    css_url: str
    htmx_url: str
    alpine_url: str
    app_js_url: str
    js_review: str
    js_audit: str
    js_fix: str


def page_context(ruleset: RuleSet | None = None) -> dict:
    rs = ruleset or default_ruleset()
    return {
        "page": Page(
            rs,
            assets.css_url(),
            assets.js_url("htmx.min.js"),
            assets.js_url("alpine-csp.min.js"),
            assets.js_url("app.js"),
            assets.js_url("review.js"),
            assets.js_url("audit.js"),
            assets.js_url("fix.js"),
        ),
        "ruleset": rs,
        "sprite": SPRITE,
        "theme_snippet": Markup(THEME_SNIPPET),
        "htmx_config": HTMX_CONFIG,
    }


templates = Jinja2Templates(directory=[str(WEB_DIR / "templates"), str(WEB_DIR)])
templates.env.autoescape = True
templates.env.globals["e"] = escape


def render(request: Request, name: str, ctx: dict | None = None, status: int = 200, headers: dict | None = None):
    """TemplateResponse with the page context, the CSP and no-store (checker text is private to the request)."""
    context = {
        **page_context((ctx or {}).get("ruleset")),
        "csrf_token": getattr(request.state, "csrf", ""),
        **(ctx or {}),
    }
    resp = templates.TemplateResponse(request, name, context, status_code=status)
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"  # nothing leaves the site; same-origin form POSTs keep a real Origin
    for k, v in (headers or {}).items():
        resp.headers[k] = v
    return resp


async def form_data(request: Request, limit: int = 64_000) -> dict[str, str]:
    """application/x-www-form-urlencoded body as a flat dict. Needs no extra dependency.

    The size cap is enforced before the body is buffered: by Content-Length when given, and while streaming
    when not (chunked), so an oversized upload is never held in memory. Parsed once per request.
    """
    from urllib.parse import parse_qs

    from fastapi import HTTPException

    cached = getattr(request.state, "form", None)
    if cached is not None:
        return cached
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise HTTPException(413, "Request too large")
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            raise HTTPException(413, "Request too large")
    parsed = {k: v[-1] for k, v in parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True).items()}
    request.state.form = parsed
    return parsed
