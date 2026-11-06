"""Static assets: one CSS file built from web/static/src/*.css, fingerprinted, plus the pinned JS.

No Node build step: the CSS is the reference token + component CSS from docs/design/final, concatenated and
minified here, so the page ships only what the two pages use (no framework CSS to purge).
"""

from __future__ import annotations

import gzip
import hashlib
import re
from functools import cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

STATIC = Path(__file__).resolve().parent / "static"
CSS_PARTS = ("tokens.css", "review-parts.css", "final-parts.css", "pages.css", "review.css", "account.css")
JS_FILES = ("htmx.min.js", "alpine-csp.min.js", "app.js", "review.js")
IMMUTABLE = {"Cache-Control": "public, max-age=31536000, immutable"}

router = APIRouter()


def _minify(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    return css.replace(";}", "}").strip()


@cache
def _css() -> tuple[str, bytes]:
    body = _minify("\n".join((STATIC / "src" / p).read_text(encoding="utf-8") for p in CSS_PARTS)).encode()
    return hashlib.sha256(body).hexdigest()[:10], body


@cache
def _js(name: str) -> tuple[str, bytes]:
    if name not in JS_FILES:
        raise KeyError(name)
    body = (STATIC / "js" / name).read_bytes()
    return hashlib.sha256(body).hexdigest()[:10], body


def css_url() -> str:
    return f"/static/app.{_css()[0]}.css"


def js_url(name: str) -> str:
    return f"/static/js/{_js(name)[0]}/{name}"


def transfer_sizes() -> dict[str, int]:
    """Gzip sizes in bytes of every asset a page loads (a conservative stand-in for brotli, see foundations 8)."""
    out = {"app.css": len(gzip.compress(_css()[1], 9))}
    out.update({n: len(gzip.compress(_js(n)[1], 9)) for n in JS_FILES})
    return out


@router.get("/static/app.{digest}.css", include_in_schema=False)
def serve_css(digest: str) -> Response:
    if digest != _css()[0]:
        raise HTTPException(404)
    return Response(_css()[1], media_type="text/css", headers=IMMUTABLE)


@router.get("/static/js/{digest}/{name}", include_in_schema=False)
def serve_js(digest: str, name: str) -> Response:
    try:
        d, body = _js(name)
    except KeyError:
        raise HTTPException(404) from None
    if d != digest:
        raise HTTPException(404)
    return Response(body, media_type="text/javascript", headers=IMMUTABLE)
