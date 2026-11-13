"""Static assets: one CSS file built from web/static/src/*.css, fingerprinted, plus the pinned JS.

No Node build step: the CSS is the reference token + component CSS from docs/design/final, concatenated and
minified here, so the page ships only what the two pages use (no framework CSS to purge).
"""

from __future__ import annotations

import gzip
import hashlib
import os
import re
from functools import cache
from html import escape
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

STATIC = Path(__file__).resolve().parent / "static"
CSS_PARTS = (
    "tokens.css",
    "review-parts.css",
    "final-parts.css",
    "pages.css",
    "story.css",
    "review.css",
    "account.css",
    "audit.css",
    "fix.css",
    "export.css",
)
JS_FILES = ("htmx.min.js", "alpine-csp.min.js", "app.js", "review.js", "audit.js", "fix.js")
# Self-hosted because CSP is default-src 'self'. Whitelisted, so no path from the URL ever reaches the disk.
# shortcut: fixed names behind an immutable cache; rename the file if a font is ever updated.
FONT_FILES = ("libre-franklin-latin.woff2",)
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


@cache
def _font(name: str) -> bytes:
    if name not in FONT_FILES:
        raise KeyError(name)
    return (STATIC / "fonts" / name).read_bytes()


@router.get("/static/fonts/{name}", include_in_schema=False)
def serve_font(name: str) -> Response:
    try:
        body = _font(name)
    except KeyError:
        raise HTTPException(404) from None
    return Response(body, media_type="font/woff2", headers=IMMUTABLE)


def site_url(request: Request) -> str:
    """The public address for absolute links (share cards, sitemap): SATYA_PUBLIC_URL, else this request's own."""
    return os.environ.get("SATYA_PUBLIC_URL", "").rstrip("/") or str(request.base_url).rstrip("/")


@cache
def _share_image() -> bytes:
    return (STATIC / "img" / "og.png").read_bytes()


@router.get("/static/og.png", include_in_schema=False)
def serve_share_image() -> Response:
    return Response(_share_image(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


# Only the public checker and the privacy notice are for search engines; workspace pages are private and need sign-in.
_ROBOTS = "User-agent: *\nAllow: /check\nAllow: /privacy\n" + "".join(
    f"Disallow: {p}\n" for p in ("/packs/", "/audits", "/fix", "/account", "/signin", "/session", "/rules/")
)


@router.get("/robots.txt", include_in_schema=False)
def robots(request: Request) -> Response:
    return Response(_ROBOTS + f"Sitemap: {site_url(request)}/sitemap.xml\n", media_type="text/plain")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request) -> Response:
    urls = "".join(f"<url><loc>{escape(site_url(request) + p)}</loc></url>" for p in ("/check", "/privacy"))
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'
    return Response(xml, media_type="application/xml")


@router.get("/static/js/{digest}/{name}", include_in_schema=False)
def serve_js(digest: str, name: str) -> Response:
    try:
        d, body = _js(name)
    except KeyError:
        raise HTTPException(404) from None
    if d != digest:
        raise HTTPException(404)
    return Response(body, media_type="text/javascript", headers=IMMUTABLE)
