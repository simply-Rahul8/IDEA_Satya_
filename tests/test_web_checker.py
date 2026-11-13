"""Public checker (variant A): deterministic, strict-CSP, honest wording, rate-limited."""

import re

import pytest
from fastapi.testclient import TestClient
from helpers import secure

from asgi import app
from web import assets, checker

HX = {"HX-Request": "true"}
FLAGGED = "This serum cures acne scars in 7 days and is clinically proven to lighten skin tone."
BANNED = re.compile(r"\b(compliant|approved|safe)\b", re.I)


@pytest.fixture()
def client():
    checker.limiter.reset()
    return secure(TestClient(app))


DISCLAIMER = "It does not mean the listing is approved by a marketplace or a regulator."


def visible_text(html: str) -> str:
    html = re.sub(r"<(script|style|template)\b.*?</\1>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html).replace(DISCLAIMER, "").replace("Is my claim safe?", "")


def test_page_renders_with_draft_banner_and_no_inline_code(client):
    html = client.get("/check").text
    assert "Draft rule set v0.1.2-draft" in html
    assert 'style="' not in html
    assert len(re.findall(r"<script(?![^>]*\bsrc=)", html)) == 1  # the theme snippet only
    assert 'x-data="satyaChecker"' in html


def test_csp_has_no_unsafe_directives(client):
    csp = client.get("/check").headers["content-security-policy"]
    assert "unsafe-eval" not in csp and "unsafe-inline" not in csp and "sha256-" in csp


def test_self_hosted_font_is_served_and_only_whitelisted(client):
    r = client.get("/static/fonts/libre-franklin-latin.woff2")
    assert r.status_code == 200 and r.headers["content-type"] == "font/woff2" and r.content[:4] == b"wOF2"
    assert client.get("/static/fonts/OFL-LibreFranklin.txt").status_code == 404  # on disk, but not served


def test_flagged_partial_has_marks_list_and_announcement(client):
    html = client.post("/check", data={"text": FLAGGED}, headers=HX).text
    assert html.count("<mark ") == 3
    assert 'class="hl hl-red"' in html and 'class="hl hl-amber"' in html
    assert "2 blocked, 1 to review under rule set v0.1.2-draft." in html
    assert "hx-swap-oob" in html and 'id="backdrop-text"' in html


def test_red_listed_before_amber(client):
    html = client.post("/check", data={"text": "Clinically proven. It cures acne."}, headers=HX).text
    assert html.index("EN-DRUG-001") < html.index("EN-CLAIM-004")


def test_clear_result_never_says_safe_or_compliant(client):
    html = client.post("/check", data={"text": "A gentle moisturiser with ceramides."}, headers=HX).text
    assert "No flagged risks" in html and "under rule set v0.1.2-draft" in html
    assert not BANNED.search(visible_text(html))


@pytest.mark.parametrize("text", [FLAGGED, "A gentle moisturiser.", ""])
def test_no_banned_wording_anywhere(client, text):
    page = client.post("/check", data={"text": text}).text
    assert not BANNED.search(visible_text(page))


def test_listing_text_is_escaped(client):
    evil = "<img src=x onerror=alert(1)> cures acne <script>alert(2)</script>"
    html = client.post("/check", data={"text": evil}, headers=HX).text
    assert "<img" not in html and "<script>alert" not in html
    full = client.post("/check", data={"text": evil}).text
    assert "<img" not in full and "<script>alert" not in full


def test_over_cap_checks_first_chars_only(client):
    text = "x " * (checker.CHECKER_MAX_CHARS // 2) + " " + FLAGGED  # the claims sit beyond the cap
    html = client.post("/check", data={"text": text}, headers=HX).text
    assert "<mark" not in html
    assert "Only the first 5,000 characters were checked" in html and "over" in html


def test_empty_text_returns_empty_verdict_and_silent_live_region(client):
    html = client.post("/check", data={"text": "  "}, headers=HX).text
    assert '<div id="verdict"></div>' in html and 'aria-live="polite" hx-swap-oob="outerHTML"></div>' in html


def test_out_of_scope_gate_shows_gate_text_without_meter(client):
    html = client.post("/check", data={"text": "Ayurvedic tablet to cure diabetes, take two daily."}, headers=HX).text
    assert 'data-variant="out_of_scope"' in html and "Not reviewed" in html and 'class="meter"' not in html


def test_rate_limit_returns_429_with_retry_after_and_keeps_text(client, monkeypatch):
    monkeypatch.setattr(checker, "limiter", checker.RateLimiter(2, 600))
    for _ in range(2):
        assert client.post("/check", data={"text": "hi"}, headers=HX).status_code == 200
    r = client.post("/check", data={"text": "hi"}, headers=HX)
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0
    assert "Nothing you typed is lost" in r.text
    full = client.post("/check", data={"text": "keep me"})
    assert full.status_code == 429 and ">keep me</textarea>" in full.text


def test_rule_sheet_is_cacheable_and_holds_no_user_text(client):
    r = client.get("/rules/EN-DRUG-001/sheet?v=v0.1.1-draft")
    assert r.status_code == 200 and "public" in r.headers["cache-control"]
    assert "Why it is flagged" in r.text and "Not yet verified" in r.text and "cannot be overridden" in r.text
    assert client.get("/rules/NOPE/sheet").status_code == 404


def test_checker_imports_no_llm_provider():
    src = open(checker.__file__, encoding="utf-8").read()
    assert "providers" not in src and "engine.api" not in src


def test_severity_classes_survive_in_built_css():
    css = assets._css()[1].decode()
    for cls in (
        ".hl-red",
        ".hl-amber",
        ".flag-red",
        ".flag-amber",
        ".flag-green",
        ".flag-ink",
        ".fp-red",
        ".fp-amber",
        ".meter",
    ):
        assert cls in css


def test_assets_served_immutable_and_within_budget(client):
    html = client.get("/check").text
    for url in re.findall(r'(?:href|src)="(/static/[^"]+)"', html):
        r = client.get(url)
        assert r.status_code == 200 and "immutable" in r.headers["cache-control"]
    total = sum(assets.transfer_sizes().values())
    assert total < 100_000, assets.transfer_sizes()  # CI fails above 100 KB; hard cap is 150 KB (foundations 8)


# ------------------------------------------------------------------- go-live hardening (docs/GO-LIVE.md)
HINDI = "यह क्रीम मुंहासे जड़ से ठीक करती है और त्वचा को गोरा बनाती है।"


def test_hindi_and_hinglish_claims_are_flagged_under_their_english_rules(client):
    html = client.post("/check", data={"text": HINDI}, headers=HX).text
    assert 'data-sheet="/rules/EN-DRUG-001/' in html and 'data-sheet="/rules/EN-FAIR-001/' in html
    assert "Hindi checks are an early draft" in html
    hinglish = client.post("/check", data={"text": "Yeh face pack skin ko gora banata hai."}, headers=HX).text
    assert 'data-sheet="/rules/EN-FAIR-001/' in hinglish


def test_clean_hindi_never_reads_as_fully_checked(client):
    html = client.post("/check", data={"text": "हल्का मॉइस्चराइज़र, रोज़ाना इस्तेमाल के लिए।"}, headers=HX).text
    assert "No flagged risks" in html and "Hindi checks are an early draft" in html
    assert not BANNED.search(visible_text(html))


def test_english_claim_is_not_listed_twice_by_the_hindi_lexicon(client):
    html = client.post("/check", data={"text": "This serum cures acne scars in 7 days."}, headers=HX).text
    assert html.count('data-sheet="/rules/EN-DRUG-001/') == 1 and "Hindi checks" not in html


def test_browser_gets_a_designed_404_and_scripts_keep_json(client):
    page = client.get("/no-such-page", headers={"Accept": "text/html"})
    assert page.status_code == 404 and "Page not found" in page.text
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    api = client.get("/no-such-page")
    assert api.status_code == 404 and api.json() == {"detail": "Not Found"}


def test_unhandled_error_shows_a_page_not_a_traceback(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom-internal-detail")

    c = secure(TestClient(app, raise_server_exceptions=False))  # before the fault: secure() reads /check
    monkeypatch.setattr(checker, "run_check", boom)
    r = c.get("/check", headers={"Accept": "text/html"})
    assert r.status_code == 500 and "Something broke on our side" in r.text and "boom-internal-detail" not in r.text


def test_every_response_carries_baseline_security_headers(client):
    for r in (client.get("/healthz"), client.get(assets.css_url()), client.get("/no-such-page")):
        for h in ("x-content-type-options", "x-frame-options", "permissions-policy", "content-security-policy"):
            assert h in r.headers, (str(r.url), h)
    assert "script-src 'self'" in client.get("/check").headers["content-security-policy"]  # page CSP kept
    assert "strict-transport-security" not in client.get("/check").headers  # plain http
    assert "strict-transport-security" in client.get("/check", headers={"X-Forwarded-Proto": "https"}).headers


def test_robots_sitemap_and_share_card(client, monkeypatch):
    monkeypatch.setenv("SATYA_PUBLIC_URL", "https://satya.example.in/")
    robots = client.get("/robots.txt").text
    assert "Allow: /check" in robots and "Disallow: /packs/" in robots
    assert "Sitemap: https://satya.example.in/sitemap.xml" in robots
    assert "<loc>https://satya.example.in/check</loc>" in client.get("/sitemap.xml").text
    assert 'property="og:image" content="https://satya.example.in/static/og.png"' in client.get("/check").text
    img = client.get("/static/og.png")
    assert img.status_code == 200 and img.headers["content-type"] == "image/png" and img.content[:4] == b"\x89PNG"
