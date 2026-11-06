"""SAT-34: sessions, CSRF, per-session scoping, client IP, write limits and body size on the web layer."""

import pytest
from fastapi.testclient import TestClient
from helpers import secure

from asgi import app
from web import review, security

HX = {"HX-Request": "true"}
SAME = {"Origin": "http://testserver"}


@pytest.fixture()
def raw():
    security.writes.reset()
    return TestClient(app)


@pytest.fixture()
def client(raw):
    return secure(raw)


def pack(c):
    return review.store.get(c.owner, "demo")


def bullet(c):
    return pack(c).pack.section("bullet_1").sentences[0].text


def test_foreign_origin_without_token_cannot_rewrite_the_pack(client):
    before = bullet(client)
    bare = TestClient(app, cookies=client.cookies)  # same session cookie, but a cross-site page's headers
    r = bare.post(
        "/packs/demo/sentences/bullet_1-0/check",
        data={"text": "Cures cancer"},
        headers={"Origin": "https://evil.example"},
    )
    assert r.status_code == 403
    assert bullet(client) == before


@pytest.mark.parametrize(
    "headers,why",
    [
        ({"Origin": "https://evil.example"}, "foreign origin"),
        ({}, "no origin or referer"),
        ({"Origin": "null"}, "opaque origin"),
        ({"Referer": "https://evil.example/page"}, "foreign referer"),
        ({"Origin": "http://testserver", "Sec-Fetch-Site": "cross-site"}, "fetch metadata says cross-site"),
    ],
)
def test_cross_site_requests_are_refused_even_with_a_valid_token(client, headers, why):
    token = client.headers["X-CSRF-Token"]
    c = TestClient(app, cookies=client.cookies)
    r = c.post("/packs/demo/sentences/bullet_1-0/check", data={"text": "x"}, headers={"X-CSRF-Token": token, **headers})
    assert r.status_code == 403, why


def test_missing_or_wrong_token_is_refused(raw):
    raw = TestClient(app, cookies=secure(raw).cookies)  # session cookie only, no token header
    base = {"Origin": "http://testserver"}
    assert raw.post("/check", data={"text": "hi"}, headers=base).status_code == 403
    assert raw.post("/check", data={"text": "hi"}, headers={**base, "X-CSRF-Token": "0" * 32}).status_code == 403
    other = secure(TestClient(app)).headers["X-CSRF-Token"]  # another session's token
    assert raw.post("/check", data={"text": "hi"}, headers={**base, "X-CSRF-Token": other}).status_code == 403


def test_no_cookie_post_is_refused_and_creates_nothing_shared(raw):
    r = raw.post("/packs/demo/approve", headers={**SAME, **HX})
    assert r.status_code == 403


def test_token_in_form_field_works_for_the_no_javascript_form(raw):
    c = secure(raw)
    token = c.headers.pop("X-CSRF-Token")
    ok = c.post("/check", data={"text": "hi", "csrf_token": token})
    assert ok.status_code == 200
    assert c.post("/check", data={"text": "hi", "csrf_token": "bad"}).status_code == 403


def test_pages_carry_the_token_for_htmx_and_forms(client):
    html = client.get("/check").text
    token = client.headers["X-CSRF-Token"]
    assert f'hx-headers=\'{{"X-CSRF-Token": "{token}"}}\'' in html
    assert f'name="csrf_token" value="{token}"' in html
    assert "HttpOnly" in TestClient(app).get("/check").headers["set-cookie"]


def test_each_session_has_its_own_pack(client):
    other = secure(TestClient(app))
    assert client.owner != other.owner
    r = client.post("/packs/demo/sentences/bullet_1-0/check", data={"text": "Gentle serum."}, headers=HX)
    assert r.status_code == 200
    assert bullet(client) == "Gentle serum."
    assert bullet(other) == "Hydrating serum with a dewy finish."
    assert "Gentle serum." not in other.get("/packs/demo/review").text


def test_forged_or_tampered_cookie_is_replaced(raw):
    raw.cookies.set("satya_sid", "a" * 32 + "." + "b" * 32)
    r = raw.get("/check")
    assert "set-cookie" in r.headers and r.headers["set-cookie"].split(";")[0].split("=")[1].split(".")[0] != "a" * 32


def test_unknown_pack_is_404_per_owner(client):
    assert client.get("/packs/someone-elses/review").status_code == 404


def test_xff_is_ignored_unless_a_trusted_header_is_configured(client, monkeypatch):
    class R:
        headers = {"x-forwarded-for": "9.9.9.9", "x-vercel-forwarded-for": "5.5.5.5"}
        client = type("C", (), {"host": "1.2.3.4"})()

    monkeypatch.delenv("SATYA_TRUSTED_IP_HEADER", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    assert security.client_ip(R()) == "1.2.3.4"
    monkeypatch.setenv("VERCEL", "1")
    assert security.client_ip(R()) == "5.5.5.5"
    monkeypatch.setenv("SATYA_TRUSTED_IP_HEADER", "x-real-ip")  # configured header absent: fall back, not XFF
    assert security.client_ip(R()) == "1.2.3.4"


def test_spoofed_xff_does_not_evade_the_checker_limit(client, monkeypatch):
    from web import checker

    monkeypatch.delenv("SATYA_TRUSTED_IP_HEADER", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(checker, "limiter", checker.RateLimiter(2, 600))
    codes = [
        client.post("/check", data={"text": "hi"}, headers={**HX, "X-Forwarded-For": f"10.0.0.{i}"}).status_code
        for i in range(4)
    ]
    assert codes == [200, 200, 429, 429]


def test_review_writes_are_rate_limited_too(client, monkeypatch):
    from engine.ratelimit import MemoryLimiter

    monkeypatch.setattr(security, "writes", MemoryLimiter(3, 600))
    codes = [
        client.post("/packs/demo/sentences/bullet_1-0/report", data={"rule_id": "x"}, headers=HX).status_code
        for _ in range(5)
    ]
    assert codes[3:] == [429, 429] and "retry-after" in client.post("/packs/demo/approve", headers=HX).headers


def test_oversized_form_is_rejected_by_content_length_and_while_streaming(client):
    big = "text=" + "a" * 70_000
    r = client.post("/check", content=big, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 413

    def chunks():  # chunked: no Content-Length, so the cap must apply while reading
        for _ in range(20):
            yield b"text=" + b"a" * 5_000

    r = client.post("/check", content=chunks(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 413


def test_form_data_stops_reading_at_the_limit():
    import asyncio

    from starlette.requests import Request

    from web.app import form_data

    sent = []

    async def receive():
        sent.append(1)
        return {"type": "http.request", "body": b"x" * 1000, "more_body": True}

    req = Request({"type": "http", "method": "POST", "headers": [], "state": {}}, receive)
    with pytest.raises(Exception) as e:
        asyncio.run(form_data(req, limit=2500))
    assert getattr(e.value, "status_code", None) == 413 and len(sent) == 3


@pytest.mark.parametrize("ref,kept", [("x", False), ("..", False), ("a1", False), ("doc-7", True)])
def test_red_override_needs_a_real_evidence_reference(client, ref, kept):
    r = client.post("/packs/demo/sentences/bullet_3-0/keep", data={"reason": ref}, headers=HX)
    assert r.status_code == 200
    assert ('data-status="kept"' in r.text) is kept


def test_production_without_a_session_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("SATYA_SESSION_SECRET", raising=False)
    monkeypatch.setenv("SATYA_ENV", "production")
    with pytest.raises(RuntimeError):
        security.secret()
