"""Supabase Auth session to workspace (SAT-46; plan section 3 steps 1-2, ADR-8).

Server-side and fail closed: the access token is checked by Supabase Auth itself (GET /auth/v1/user), so expiry,
signature and sign-out revocation are its call, not ours, and no JWT secret lives in this app. Anything other than
a clear "valid user" (bad, expired or missing token, Supabase unreachable) means no workspace. The workspace id is
never taken from the request: it comes from the `workspace_members` row of the verified user, which is created
together with the workspace on first sign-in.

Routes read the result through `web.security.workspace_of`. Local dev/test with no Supabase configured keeps the
per-browser-session workspace; once auth is configured, or on any hosted environment, signed-out requests get 401.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from engine.repo.rest import PostgrestClient, Rest
from web.security import _hosted, guard_unsafe

COOKIE = "satya_at"
COOKIE_MAX_AGE = 3600  # Supabase access tokens last an hour by default; the token's own `exp` is still enforced
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_MAX_TOKEN = 8192


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str = ""


class AuthClient(Protocol):
    def user_for_token(self, access_token: str) -> AuthUser | None:
        """The user the token belongs to, or None for any token that is not valid right now."""


class HttpAuthClient:
    """Asks Supabase Auth who the token belongs to. Valid answers are cached for a few seconds per token."""

    def __init__(self, url: str, anon_key: str, timeout: float = 5.0, ttl: float = 30.0) -> None:
        self._url = url.rstrip("/") + "/auth/v1/user"
        self._anon = anon_key
        self._timeout, self._ttl = timeout, ttl
        self._cache: dict[str, tuple[float, AuthUser]] = {}
        self._lock = threading.Lock()

    def user_for_token(self, access_token: str) -> AuthUser | None:
        key = hashlib.sha256(access_token.encode()).hexdigest()
        now = time.monotonic()
        with self._lock:
            hit = self._cache.get(key)
            if hit and hit[0] > now:
                return hit[1]
            self._cache = {k: v for k, v in self._cache.items() if v[0] > now}  # drop expired entries
        req = urllib.request.Request(
            self._url, headers={"apikey": self._anon, "Authorization": f"Bearer {access_token}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 (URL is env config)
                data = json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return None  # invalid token (401/403) and an unreachable Auth server look the same: no workspace
        uid = data.get("id") if isinstance(data, dict) else None
        if not isinstance(uid, str) or not _UUID.match(uid):
            return None
        user = AuthUser(uid.lower(), str(data.get("email") or ""))
        with self._lock:
            self._cache[key] = (now + self._ttl, user)
        return user


_client: AuthClient | None = None
_rest: Rest | None = None
_lock = threading.Lock()


def _configured() -> tuple[AuthClient, Rest] | None:
    url = os.environ.get("SUPABASE_URL", "")
    anon, service = os.environ.get("SUPABASE_ANON_KEY", ""), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if url and anon and service:
        return HttpAuthClient(url, anon), PostgrestClient(url, service)
    if _hosted():
        raise RuntimeError("SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY are required when hosted")
    return None


def _setup() -> tuple[AuthClient, Rest] | None:
    global _client, _rest
    with _lock:
        if _client is None or _rest is None:
            built = _configured()
            if built:
                _client, _rest = built
        return (_client, _rest) if _client is not None and _rest is not None else None


def configure(client: AuthClient, rest: Rest) -> None:
    """Install an auth client and the workspace store (tests, or an alternative backend)."""
    global _client, _rest
    with _lock:
        _client, _rest = client, rest


def reset() -> None:
    global _client, _rest
    with _lock:
        _client = _rest = None


def _first(rows: list[dict]) -> str | None:
    rows = sorted(rows, key=lambda r: (str(r.get("created_at", "")), str(r.get("workspace_id"))))
    return str(rows[0]["workspace_id"]) if rows else None


def workspace_for(rest: Rest, user: AuthUser) -> str:
    """The user's workspace id; creates the workspace and an owner membership on first sign-in.

    The schema's signup trigger normally did this already. If two first requests race, the unique owner index
    rejects the second membership and we read back the winner's workspace."""
    found = _first(rest.select("workspace_members", {"user_id": user.id}))
    if found:
        return found
    ws = str(uuid.uuid4())
    name = user.email.split("@")[0] or "My brand"
    rest.insert("workspaces", {"id": ws, "name": name, "created_by": user.id})
    try:
        rest.insert("workspace_members", {"workspace_id": ws, "user_id": user.id, "role": "owner"})
    except RuntimeError:
        found = _first(rest.select("workspace_members", {"user_id": user.id}))
        if found:
            return found
        raise
    return ws


def token_from(request: Request) -> str:
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    token = value.strip() if scheme.lower() == "bearer" else request.cookies.get(COOKIE, "")
    return token if 0 < len(token) <= _MAX_TOKEN else ""


def sign_in(token: str) -> tuple[AuthUser, str] | None:
    """Verified user and workspace for an access token, or None. Blocking (network)."""
    setup = _setup()
    if setup is None or not token:
        return None
    client, rest = setup
    user = client.user_for_token(token)
    if user is None:
        return None
    return user, workspace_for(rest, user)


async def authenticate(request: Request) -> None:
    """Router dependency for every route that serves workspace data. Sets `request.state.workspace_id` and
    `.user_id` for a verified user; otherwise 401 (no workspace), except local dev/test with no Supabase configured."""
    if _setup() is None:
        request.state.anonymous_ok = True  # local dev/test only: `_configured` raised already when hosted
        return
    signed = await run_in_threadpool(sign_in, token_from(request))
    if signed is None:
        raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    request.state.user_id, request.state.workspace_id = signed[0].id, signed[1]


def set_session_cookie(resp, request: Request, token: str) -> None:
    secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    resp.set_cookie(COOKIE, token, max_age=COOKIE_MAX_AGE, path="/", httponly=True, samesite="lax", secure=secure)


router = APIRouter(prefix="/auth", dependencies=[Depends(guard_unsafe)])


@router.post("/session")
async def start_session(request: Request):
    """Exchange a Supabase access token (Authorization: Bearer) for the HttpOnly cookie, creating the workspace
    on first sign-in. The sign-in page calls this after Supabase Auth returns a session (SAT-39)."""
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header[:7].lower() == "bearer " else ""
    signed = await run_in_threadpool(sign_in, token if 0 < len(token) <= _MAX_TOKEN else "")
    if signed is None:
        raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    resp = JSONResponse({"signed_in": True}, headers={"Cache-Control": "no-store"})
    set_session_cookie(resp, request, token)
    return resp


@router.post("/signout")
async def end_session():
    resp = JSONResponse({"signed_in": False}, headers={"Cache-Control": "no-store"})
    resp.delete_cookie(COOKIE, path="/")
    return resp
