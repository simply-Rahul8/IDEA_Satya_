"""Sign-in, consent and brand setup screens (SAT-39; plan section 3 steps 1-2, DPDP).

Sign-in runs entirely on the server against Supabase Auth, so the pages need no auth library and the CSP stays
`connect-src 'self'`: email OTP (`/auth/v1/otp`, `/auth/v1/verify`) and Google via the PKCE flow (the verifier lives
in a signed HttpOnly cookie). Both end in `web.auth.sign_in`, which verifies the token and creates the workspace.

Consent is a required checkbox on the sign-in form. The choice rides to the end of sign-in in a signed cookie and is
written to the append-only `consents` table once the user id is known. The consent wording is draft (one partial).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from engine.brand import TONES, BrandStore, validate
from engine.ratelimit import ip_key, make_limiter
from engine.repo.rest import MemoryRest, Rest
from web import auth
from web.app import form_data, render
from web.security import _sign, client_ip, guard_unsafe, workspace_of

NOTICE_VERSION = "draft-0.1"  # privacy notice version shown; stays draft until the lawyer-reviewed text lands (P20)
PURPOSES = ("terms_privacy", "llm_processing", "product_updates")  # order of the bits in the flow cookie
FLOW_COOKIE, FLOW_MAX_AGE = "satya_flow", 600
HOME = "/check"
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
_CODE = re.compile(r"^\d{4,10}$")
ERRORS = {
    "expired": "That sign-in link expired. Start again.",
    "failed": "We couldn't sign you in. Start again.",
}


class SignInFlow(Protocol):
    def send_otp(self, email: str) -> bool: ...

    def verify_otp(self, email: str, code: str) -> str | None:
        """Access token for a correct code, else None."""

    def google_url(self, redirect_to: str, challenge: str) -> str: ...

    def exchange(self, code: str, verifier: str) -> str | None:
        """Access token for a PKCE authorization code, else None."""


class SupabaseFlow:
    def __init__(self, url: str, anon_key: str, timeout: float = 8.0) -> None:
        self._base, self._anon, self._timeout = url.rstrip("/") + "/auth/v1", anon_key, timeout

    def _post(self, path: str, body: dict) -> dict | None:
        req = urllib.request.Request(
            self._base + path,
            data=json.dumps(body).encode(),
            method="POST",
            headers={"apikey": self._anon, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 (URL is env config)
                raw = resp.read()
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def send_otp(self, email: str) -> bool:
        return self._post("/otp", {"email": email, "create_user": True}) is not None

    def verify_otp(self, email: str, code: str) -> str | None:
        data = self._post("/verify", {"type": "email", "email": email, "token": code})
        return (data or {}).get("access_token") or None

    def google_url(self, redirect_to: str, challenge: str) -> str:
        query = urllib.parse.urlencode(
            {
                "provider": "google",
                "redirect_to": redirect_to,
                "code_challenge": challenge,
                "code_challenge_method": "s256",
            }
        )
        return f"{self._base}/authorize?{query}"

    def exchange(self, code: str, verifier: str) -> str | None:
        data = self._post("/token?grant_type=pkce", {"auth_code": code, "code_verifier": verifier})
        return (data or {}).get("access_token") or None


_flow: SignInFlow | None = None
_dev_rest = MemoryRest()
attempts = make_limiter(int(os.environ.get("OTP_RATE_LIMIT", "10")), int(os.environ.get("OTP_RATE_WINDOW_S", "600")))


def configure_flow(flow: SignInFlow | None) -> None:
    """Install a sign-in flow (tests), or clear it to read the environment again."""
    global _flow
    _flow = flow


def _get_flow() -> SignInFlow | None:
    if _flow is not None:
        return _flow
    url, anon = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_ANON_KEY", "")
    return SupabaseFlow(url, anon) if url and anon else None


def _setup() -> tuple[Rest, bool]:
    """The store behind brand profiles and consents, and whether real sign-in is configured."""
    configured = auth._setup()
    return (configured[1], True) if configured else (_dev_rest, False)


def _store() -> BrandStore:
    return BrandStore(_setup()[0])


# ---- the sign-in flow cookie: consent bits and the PKCE verifier, signed and HttpOnly ----


def _flow_value(bits: str, verifier: str = "") -> str:
    body = f"{bits}:{verifier}"
    return f"{body}.{_sign('flow:' + body)}"


def _read_flow(request: Request) -> tuple[str, str] | None:
    body, _, sig = request.cookies.get(FLOW_COOKIE, "").rpartition(".")
    if not body or not hmac.compare_digest(sig, _sign("flow:" + body)):
        return None
    bits, _, verifier = body.partition(":")
    return (bits, verifier) if len(bits) == len(PURPOSES) else None


def _with_flow(resp, request: Request, bits: str, verifier: str = ""):
    secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    resp.set_cookie(
        FLOW_COOKIE,
        _flow_value(bits, verifier),
        max_age=FLOW_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    return resp


def _bits(form: dict[str, str]) -> str:
    return "".join("1" if form.get(f"consent_{p}") == "on" else "0" for p in PURPOSES)


def _record_consents(rest: Rest, user_id: str, bits: str) -> None:
    """Append-only: a row is added only when this purpose has no row yet with the same notice version and answer."""
    for purpose, bit in zip(PURPOSES, bits, strict=True):
        granted = bit == "1"
        seen = rest.select("consents", {"user_id": user_id, "purpose": purpose})
        if not any(r["notice_version"] == NOTICE_VERSION and r["granted"] == granted for r in seen):
            rest.insert(
                "consents",
                {"user_id": user_id, "purpose": purpose, "notice_version": NOTICE_VERSION, "granted": granted},
            )


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303, headers={"Cache-Control": "no-store"})


def _signin_page(
    request: Request,
    *,
    status: int = 200,
    step: str = "start",
    email: str = "",
    errors=None,
    bits: str = "000",
    message: str = "",
):
    ctx = {
        "title": "Sign in · Satya",
        "step": step,
        "email": email,
        "errors": errors or {},
        "message": message,
        "ticked": dict(zip(PURPOSES, (b == "1" for b in bits), strict=True)),
        "notice_version": NOTICE_VERSION,
        "ready": _get_flow() is not None,
    }
    return render(request, "account/signin.html", ctx, status=status)


async def _me(request: Request) -> tuple[auth.AuthUser, str] | None:
    return await run_in_threadpool(auth.sign_in, auth.token_from(request))


async def _landing(ws: str) -> str:
    return HOME if await run_in_threadpool(_store().get, ws) else "/setup"


async def _finish(request: Request, token: str, bits: str):
    """Verify the token, create the workspace on first sign-in, record consent, set the cookie, go on."""
    signed = await run_in_threadpool(auth.sign_in, token)
    if signed is None:
        return _redirect("/signin?error=failed")
    user, ws = signed
    await run_in_threadpool(_record_consents, _setup()[0], user.id, bits)
    resp = _redirect(await _landing(ws))
    auth.set_session_cookie(resp, request, token)
    resp.delete_cookie(FLOW_COOKIE, path="/")
    return resp


def _throttled(request: Request, email: str = "") -> int | None:
    waits = [attempts.hit(ip_key(client_ip(request), "otp"))]
    if email:
        waits.append(attempts.hit("otp:" + hashlib.sha256(email.casefold().encode()).hexdigest()[:32]))
    return max((w for w in waits if w is not None), default=None)


def _origin(request: Request) -> str:
    return os.environ.get("SATYA_PUBLIC_URL", "").rstrip("/") or str(request.base_url).rstrip("/")


public = APIRouter()
protected = APIRouter(dependencies=[Depends(guard_unsafe)])


@public.get("/")
async def home(request: Request):
    if _get_flow() is None and not auth._setup():
        return _redirect(HOME)  # local dev with no Supabase: there is no signed-out state
    me = await _me(request)
    return _redirect(await _landing(me[1]) if me else "/signin")


@public.get("/signin")
async def signin(request: Request, error: str = ""):
    me = await _me(request)
    if me:
        return _redirect(await _landing(me[1]))
    return _signin_page(request, message=ERRORS.get(error, ""))


@protected.post("/signin/email")
async def signin_email(request: Request):
    form = await form_data(request)
    email, bits = form.get("email", "").strip(), _bits(form)
    errors = {}
    if not _EMAIL.match(email):
        errors["email"] = "Enter a valid email address, for example you@yourbrand.in."
    if bits[0] != "1":
        errors["consent"] = "Agree to the Terms and Privacy notice to continue."
    if errors:
        return _signin_page(request, status=422, email=email, errors=errors, bits=bits)
    flow = _get_flow()
    if flow is None:
        raise HTTPException(503, "Sign-in is not set up")
    wait = await run_in_threadpool(_throttled, request, email)
    if wait is not None:
        return _signin_page(
            request,
            status=429,
            email=email,
            bits=bits,
            message=f"Too many tries. Wait about {max(1, wait // 60)} minutes, then try again.",
        )
    sent = await run_in_threadpool(flow.send_otp, email)
    if not sent:
        return _signin_page(
            request,
            status=502,
            email=email,
            bits=bits,
            message="We couldn't send the code. Your details are still here. Try again in a moment.",
        )
    return _with_flow(_signin_page(request, step="code", email=email, bits=bits), request, bits)


@protected.post("/signin/code")
async def signin_code(request: Request):
    form = await form_data(request)
    email, code = form.get("email", "").strip(), "".join(form.get("code", "").split())
    flow, held = _get_flow(), _read_flow(request)
    if flow is None:
        raise HTTPException(503, "Sign-in is not set up")
    if held is None or held[0][0] != "1":
        return _redirect("/signin?error=expired")  # no consent on record for this sign-in
    wait = await run_in_threadpool(_throttled, request, email)
    if wait is not None:
        return _signin_page(
            request,
            status=429,
            step="code",
            email=email,
            bits=held[0],
            message=f"Too many tries. Wait about {max(1, wait // 60)} minutes, then try again.",
        )
    token = await run_in_threadpool(flow.verify_otp, email, code) if _EMAIL.match(email) and _CODE.match(code) else None
    if token is None:
        return _signin_page(
            request,
            status=400,
            step="code",
            email=email,
            bits=held[0],
            errors={"code": "That code didn't work. Check it, or use a different email."},
        )
    return await _finish(request, token, held[0])


@protected.post("/signin/google")
async def signin_google(request: Request):
    form = await form_data(request)
    bits, flow = _bits(form), _get_flow()
    if bits[0] != "1":
        return _signin_page(
            request, status=422, bits=bits, errors={"consent": "Agree to the Terms and Privacy notice to continue."}
        )
    if flow is None:
        raise HTTPException(503, "Sign-in is not set up")
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    resp = _redirect(flow.google_url(_origin(request) + "/auth/callback", challenge))
    return _with_flow(resp, request, bits, verifier)


@public.get("/auth/callback")
async def callback(request: Request, code: str = ""):
    flow, held = _get_flow(), _read_flow(request)
    if flow is None or held is None or not held[1] or held[0][0] != "1":
        return _redirect("/signin?error=expired")
    token = await run_in_threadpool(flow.exchange, code, held[1]) if 0 < len(code) <= 512 else None
    return await _finish(request, token, held[0]) if token else _redirect("/signin?error=failed")


@protected.post("/signout")
async def signout():
    resp = _redirect("/signin")
    resp.delete_cookie(auth.COOKIE, path="/")
    return resp


# ---- brand setup: the signed-in user's own workspace only; a workspace id in the form is never read ----

setup_router = APIRouter(dependencies=[Depends(guard_unsafe), Depends(auth.authenticate)])


def _setup_page(request: Request, values: dict, errors: dict, status: int = 200, saved: bool = False):
    return render(
        request,
        "account/setup.html",
        {
            "title": "Brand setup · Satya",
            "v": values,
            "errors": errors,
            "saved": saved,
            "tones": TONES,
            "signed_in": bool(getattr(request.state, "user_id", None)),
        },
        status=status,
    )


@setup_router.get("/setup")
async def setup(request: Request, saved: str = ""):
    p = await run_in_threadpool(_store().get, workspace_of(request))
    values = (
        {
            "tone": p.tone,
            "restricted_phrases": "\n".join(p.restricted_phrases),
            "seller_legal_name": p.seller_legal_name,
            "address": p.address,
            "grievance_name": p.grievance_name,
            "grievance_email": p.grievance_email,
        }
        if p
        else {"tone": "warm"}
    )
    return _setup_page(request, values, {}, saved=saved == "1")


@setup_router.post("/setup")
async def save_setup(request: Request):
    form = await form_data(request)
    profile, errors = validate(form)
    if profile is None:
        return _setup_page(request, form, errors, status=422)
    await run_in_threadpool(_store().save, workspace_of(request), profile)
    return _redirect("/setup?saved=1")
