"""Request security for the web pages: browser sessions, CSRF, client IP and write rate limits (SAT-34).

- Every browser gets a signed, HttpOnly session cookie. `workspace_of(request)` is the single seam that scopes
  stored packs; when Supabase Auth is wired in, it returns the signed-in user's workspace id instead.
- Every state-changing request must come from this site (Origin / Referer / Sec-Fetch-Site) and carry the
  session's CSRF token (X-CSRF-Token header, set by htmx, or a `csrf_token` form field).
- The client IP is only read from a header the hosting platform sets (SATYA_TRUSTED_IP_HEADER, defaulting to
  Vercel's), never from a header the client can forge.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from engine.ratelimit import ip_key, make_limiter

COOKIE = "satya_sid"
CSRF_HEADER = "x-csrf-token"
CSRF_FIELD = "csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
RATE_EXEMPT_PATHS = {"/check"}  # has its own limiter, because a refused check must keep the visitor's text

_SECRET_ENV = "SATYA_SESSION_SECRET"
_dev_secret = secrets.token_bytes(32)


def _hosted() -> bool:
    return os.environ.get("SATYA_ENV", "local") in ("preview", "production") or bool(os.environ.get("VERCEL"))


def secret() -> bytes:
    value = os.environ.get(_SECRET_ENV, "")
    if value:
        return value.encode()
    if _hosted():
        # Fail closed: a per-process random secret would make sessions and tokens fail across instances.
        raise RuntimeError(f"{_SECRET_ENV} must be set when SATYA_ENV is preview/production")
    return _dev_secret


def _sign(msg: str) -> str:
    return hmac.new(secret(), msg.encode(), hashlib.sha256).hexdigest()[:32]


def new_sid() -> str:
    return secrets.token_hex(16)


def signed_cookie(sid: str) -> str:
    return f"{sid}.{_sign('sid:' + sid)}"


def sid_from_cookie(value: str | None) -> str | None:
    sid, _, sig = (value or "").partition(".")
    if len(sid) == 32 and sig and hmac.compare_digest(sig, _sign("sid:" + sid)):
        return sid
    return None


def csrf_token(sid: str) -> str:
    return _sign("csrf:" + sid)


class SessionMiddleware:
    """Pure ASGI (no body buffering): attaches `sid` and `csrf` to request.state, sets the cookie when new."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        cookies = {}
        for raw in Request(scope).headers.get("cookie", "").split(";"):
            k, _, v = raw.strip().partition("=")
            cookies[k] = v
        sid = sid_from_cookie(cookies.get(COOKIE))
        fresh = sid is None
        sid = sid or new_sid()
        state = scope.setdefault("state", {})
        state["sid"], state["csrf"] = sid, csrf_token(sid)
        secure = scope.get("scheme") == "https" or Request(scope).headers.get("x-forwarded-proto") == "https"

        async def send_with_cookie(message: Message) -> None:
            if fresh and message["type"] == "http.response.start":
                flags = "; Path=/; HttpOnly; SameSite=Lax" + ("; Secure" if secure else "")
                MutableHeaders(scope=message).append("set-cookie", f"{COOKIE}={signed_cookie(sid)}{flags}")
            await send(message)

        await self.app(scope, receive, send_with_cookie)


def workspace_of(request: Request) -> str:
    """The workspace every pack lookup is scoped to. Signed-in users: set `request.state.workspace_id` from the
    Supabase session (membership checked there). Until then each browser session is its own workspace."""
    return getattr(request.state, "workspace_id", None) or request.state.sid


def client_ip(request: Request) -> str:
    header = os.environ.get("SATYA_TRUSTED_IP_HEADER", "x-vercel-forwarded-for" if os.environ.get("VERCEL") else "")
    if header:
        value = request.headers.get(header, "")
        if value:
            return value.split(",")[-1].strip()  # the entry the trusted proxy appended
    return request.client.host if request.client else "unknown"


def _allowed_hosts(request: Request) -> set[str]:
    hosts = {request.headers.get("host", "")}
    for origin in os.environ.get("SATYA_ALLOWED_ORIGINS", "").split(","):
        if origin.strip():
            hosts.add(urlsplit(origin.strip()).netloc)
    hosts.discard("")
    return hosts


def same_origin(request: Request) -> bool:
    if request.headers.get("sec-fetch-site", "same-origin") not in ("same-origin", "none"):
        return False
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source or source == "null":
        return False  # a state-changing request that cannot say where it came from is refused
    return urlsplit(source).netloc in _allowed_hosts(request)


writes = make_limiter(int(os.environ.get("WRITE_RATE_LIMIT", "300")), int(os.environ.get("WRITE_RATE_WINDOW_S", "600")))


async def guard_unsafe(request: Request) -> None:
    """Router dependency: origin, CSRF token and write rate limit for every state-changing request."""
    if request.method in SAFE_METHODS:
        return
    if not same_origin(request):
        raise HTTPException(403, "Cross-site request refused")
    token = request.headers.get(CSRF_HEADER)
    if token is None:
        from web.app import form_data

        token = (await form_data(request)).get(CSRF_FIELD, "")
    if not hmac.compare_digest(token.encode(), request.state.csrf.encode()):
        raise HTTPException(403, "Missing or invalid CSRF token")
    if request.url.path not in RATE_EXEMPT_PATHS:
        key = ip_key(client_ip(request), "write")
        wait = await run_in_threadpool(writes.hit, key)
        if wait is not None:
            raise HTTPException(429, "Too many requests", headers={"Retry-After": str(wait)})
