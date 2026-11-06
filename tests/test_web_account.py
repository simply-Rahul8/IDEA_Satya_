"""SAT-39: sign-in, consent and brand setup routes, against a fake Supabase Auth flow and fake PostgREST."""

import re

import pytest
from fakes import FakeRest
from fastapi.testclient import TestClient

from asgi import app
from engine.brand import BrandStore, parse_phrases, restricted_flags, validate
from engine.guardrails import check_text
from web import account, auth, security

SAME = {"Origin": "http://testserver"}
ALICE = auth.AuthUser("11111111-1111-4111-8111-111111111111", "alice@example.com")
BOB = auth.AuthUser("22222222-2222-4222-8222-222222222222", "bob@example.com")
GOOD = {
    "tone": "clinical",
    "restricted_phrases": "Miracle\nanti-ageing, miracle",
    "seller_legal_name": "Acme Beauty Pvt Ltd",
    "address": "12 MG Road, Bengaluru 560001",
    "grievance_name": "Asha Rao",
    "grievance_email": "grievance@acme.in",
}
CONSENT = {"consent_terms_privacy": "on", "consent_llm_processing": "on"}


class FakeFlow:
    def __init__(self):
        self.sent, self.google = [], []

    def send_otp(self, email):
        self.sent.append(email)
        return email != "down@example.com"

    def verify_otp(self, email, code):
        users = {"alice@example.com": "alice-token", "bob@example.com": "bob-token"}
        return users.get(email) if code == "123456" else None

    def google_url(self, redirect_to, challenge):
        self.google.append((redirect_to, challenge))
        return "https://auth.example/authorize?c=" + challenge

    def exchange(self, code, verifier):
        return "alice-token" if code == "good" and verifier else None


class FakeAuth:
    def user_for_token(self, token):
        return {"alice-token": ALICE, "bob-token": BOB}.get(token)


@pytest.fixture()
def env():
    rest, flow = FakeRest(), FakeFlow()
    auth.configure(FakeAuth(), rest)
    account.configure_flow(flow)
    security.writes.reset()
    account.attempts.reset()
    yield rest, flow
    auth.reset()
    account.configure_flow(None)


def token_of(c):
    return re.search(r'name="csrf-token" content="([0-9a-f]+)"', c.get("/signin").text).group(1)


def post(c, path, data, headers=SAME):
    return c.post(path, data={**data, "csrf_token": token_of(c)}, headers=headers, follow_redirects=False)


def sign_in(c, email="alice@example.com"):
    post(c, "/signin/email", {"email": email, **CONSENT})
    return post(c, "/signin/code", {"email": email, "code": "123456"})


# ---- signed out / signed in / no brand setup ----


def test_signed_out_pages_go_to_sign_in(env):
    c = TestClient(app)
    for path in ("/", "/setup"):
        r = c.get(path, headers={"Accept": "text/html"}, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/signin", path
    assert c.get("/setup", follow_redirects=False).status_code == 401  # not a page load: plain 401
    assert c.get("/signin").status_code == 200


def test_sign_in_page_has_consent_and_both_methods(env):
    html = TestClient(app).get("/signin").text
    assert "Continue with Google" in html and "Email me a code" in html
    assert 'name="consent_terms_privacy"' in html and "Placeholder: the lawyer-reviewed" in html
    assert "compliant" not in html.lower()


def test_otp_sign_in_without_brand_goes_to_setup_and_records_consent(env):
    rest, flow = env
    c = TestClient(app)
    r = sign_in(c)
    assert r.status_code == 303 and r.headers["location"] == "/setup"
    assert flow.sent == ["alice@example.com"] and "HttpOnly" in r.headers["set-cookie"]
    got = {(x["purpose"], x["granted"]) for x in rest.tables["consents"]}
    assert got == {("terms_privacy", True), ("llm_processing", True), ("product_updates", False)}
    assert all(
        x["user_id"] == ALICE.id and x["notice_version"] == account.NOTICE_VERSION for x in rest.tables["consents"]
    )
    sign_in(c)  # signing in again does not duplicate consent rows
    assert len(rest.tables["consents"]) == 3
    assert c.get("/signin", follow_redirects=False).headers["location"] == "/setup"
    assert c.get("/", follow_redirects=False).headers["location"] == "/setup"


def test_signed_in_with_brand_setup_goes_home(env):
    c = TestClient(app)
    sign_in(c)
    assert post(c, "/setup", GOOD).headers["location"] == "/setup?saved=1"
    assert c.get("/", follow_redirects=False).headers["location"] == "/check"
    page = c.get("/setup?saved=1").text
    assert "Saved." in page and "Acme Beauty Pvt Ltd" in page and "Miracle" in page


def test_consent_is_required_and_nothing_is_sent_without_it(env):
    rest, flow = env
    c = TestClient(app)
    r = post(c, "/signin/email", {"email": "alice@example.com"})
    assert r.status_code == 422 and "Agree to the Terms" in r.text and not flow.sent
    r = post(c, "/signin/google", {})
    assert r.status_code == 422 and not flow.google
    r = post(c, "/signin/email", {"email": "nope", **CONSENT})
    assert r.status_code == 422 and "valid email" in r.text
    assert "consents" not in rest.tables


def test_wrong_code_and_missing_flow_cookie(env):
    c = TestClient(app)
    post(c, "/signin/email", {"email": "alice@example.com", **CONSENT})
    r = post(c, "/signin/code", {"email": "alice@example.com", "code": "000000"})
    assert r.status_code == 400 and "work" in r.text and "satya_at" not in r.headers.get("set-cookie", "")
    fresh = TestClient(app)  # never accepted the consent in this browser
    r = post(fresh, "/signin/code", {"email": "alice@example.com", "code": "123456"})
    assert r.status_code == 303 and r.headers["location"] == "/signin?error=expired"


def test_google_flow_uses_pkce_and_a_signed_cookie(env):
    rest, flow = env
    c = TestClient(app)
    r = post(c, "/signin/google", CONSENT)
    assert r.status_code == 303 and r.headers["location"].startswith("https://auth.example/authorize")
    assert flow.google[0][0] == "http://testserver/auth/callback"
    done = c.get("/auth/callback?code=good", follow_redirects=False)
    assert done.headers["location"] == "/setup" and len(rest.tables["consents"]) == 3
    bad = TestClient(app).get("/auth/callback?code=good", follow_redirects=False)  # no verifier cookie
    assert bad.headers["location"] == "/signin?error=expired"
    c2 = TestClient(app)
    post(c2, "/signin/google", CONSENT)
    assert c2.get("/auth/callback?code=bad", follow_redirects=False).headers["location"] == "/signin?error=failed"
    c3 = TestClient(app)
    post(c3, "/signin/google", CONSENT)
    c3.cookies.set("satya_flow", "111:abc.forged")
    assert c3.get("/auth/callback?code=good", follow_redirects=False).headers["location"] == "/signin?error=expired"


def test_send_failure_keeps_the_form_and_rate_limit_applies(env):
    c = TestClient(app)
    r = post(c, "/signin/email", {"email": "down@example.com", **CONSENT})
    assert r.status_code == 502 and 'value="down@example.com"' in r.text
    account.attempts.reset()
    codes = [post(c, "/signin/email", {"email": "alice@example.com", **CONSENT}).status_code for _ in range(12)]
    assert codes[-1] == 429


# ---- CSRF and cross-site ----


@pytest.mark.parametrize("path", ["/signin/email", "/signin/google", "/signin/code", "/signout", "/setup"])
def test_posts_need_csrf_and_same_origin(env, path):
    c = TestClient(app)
    token = re.search(r'name="csrf-token" content="([0-9a-f]+)"', c.get("/signin").text).group(1)
    body = {**GOOD, **CONSENT, "email": "alice@example.com"}
    assert c.post(path, data=body, headers=SAME).status_code == 403
    evil = {"Origin": "https://evil.example"}
    assert c.post(path, data={**body, "csrf_token": token}, headers=evil).status_code == 403
    assert not env[1].sent


def test_setup_post_with_csrf_but_signed_out_is_401_and_stores_nothing(env):
    rest, _ = env
    assert post(TestClient(app), "/setup", GOOD).status_code == 401
    assert "brand_profiles" not in rest.tables


# ---- foreign workspace ----


def test_setup_ignores_a_named_workspace_and_never_shows_another_brand(env):
    rest, _ = env
    alice, bob = TestClient(app), TestClient(app)
    sign_in(alice)
    post(alice, "/setup", GOOD)
    sign_in(bob, "bob@example.com")
    a_ws, b_ws = (m["workspace_id"] for m in rest.tables["workspace_members"])
    assert a_ws != b_ws
    assert "Acme Beauty" not in bob.get(f"/setup?workspace_id={a_ws}").text
    mine = {**GOOD, "seller_legal_name": "Bob Cosmetics LLP", "workspace_id": a_ws}
    assert post(bob, "/setup?workspace_id=" + a_ws, mine).status_code == 303
    store = BrandStore(rest)
    assert store.get(a_ws).seller_legal_name == "Acme Beauty Pvt Ltd"
    assert store.get(b_ws).seller_legal_name == "Bob Cosmetics LLP"
    assert len(rest.tables["brand_profiles"]) == 2


def test_signout_clears_the_session(env):
    c = TestClient(app)
    sign_in(c)
    r = post(c, "/signout", {})
    assert r.status_code == 303 and r.headers["location"] == "/signin"
    assert c.get("/setup", headers={"Accept": "text/html"}, follow_redirects=False).headers["location"] == "/signin"


# ---- setup form validation ----


def test_setup_errors_keep_the_answers(env):
    c = TestClient(app)
    sign_in(c)
    r = post(c, "/setup", {**GOOD, "tone": "loud", "grievance_email": "nope", "seller_legal_name": ""})
    assert r.status_code == 422
    for msg in ("Choose one of the three tones.", "valid email address", "legal name."):
        assert msg in r.text
    assert 'aria-invalid="true"' in r.text and "12 MG Road" in r.text


def test_phrase_list_is_data_and_escaped(env):
    c = TestClient(app)
    sign_in(c)
    post(c, "/setup", {**GOOD, "restricted_phrases": "<script>alert(1)</script>"})
    html = c.get("/setup").text
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_validation_limits():
    ok, _ = validate(GOOD)
    assert ok.restricted_phrases == ("Miracle", "anti-ageing")  # de-duplicated, case-insensitive, order kept
    _, e = validate({**GOOD, "restricted_phrases": "\n".join(f"p{i}" for i in range(51))})
    assert "restricted_phrases" in e
    _, e = validate({**GOOD, "restricted_phrases": "x" * 81})
    assert "restricted_phrases" in e
    assert parse_phrases(" a  b ,\n\nA B") == ["a b"]


# ---- the engine's brand-level flag source ----


def test_restricted_phrases_reach_the_engine(env):
    rest, _ = env
    c = TestClient(app)
    sign_in(c)
    post(c, "/setup", GOOD)
    ws = rest.tables["workspace_members"][0]["workspace_id"]
    phrases = BrandStore(rest).restricted_phrases(ws)
    flags = check_text("A MIRACLE serum for glowing skin.", restricted=phrases)
    brand = [f for f in flags if f.source == "brand"]
    assert len(brand) == 1 and brand[0].matched_text == "MIRACLE" and brand[0].severity.value == "orange"
    assert brand[0].overridable and brand[0].rule_id == "BRAND-RESTRICTED"
    assert not [f for f in check_text("A miraculous serum.", restricted=phrases) if f.source == "brand"]
    assert BrandStore(rest).restricted_phrases("w-other") == ()
    assert restricted_flags("anything", ()) == []
