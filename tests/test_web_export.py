"""SAT-43 export and report routes: success, blocked, foreign workspace, download, formula neutralisation."""

import hashlib
import json
import re

import pytest
from fastapi.testclient import TestClient
from helpers import secure, secure_with_demo
from test_export import _flag, _pack, _truth

from asgi import app
from engine.models import Severity
from engine.repo import ReviewState
from engine.rules import default_ruleset
from web import packs

HX = {"HX-Request": "true"}


def _put(c, pack_id="p1", **kw):
    pack = kw.pop("pack", None) or _pack()
    state = ReviewState(pack_id, "Glow Serum", _truth(), pack, default_ruleset())
    packs.repo().put(c.owner, state)


@pytest.fixture()
def client():
    c = secure(TestClient(app))
    _put(c)
    return c


def _form(page: str) -> dict[str, str]:
    return {k: v for k, v in re.findall(r'name="(map:[^"]+)"[^>]*value="([^"]*)"', page)}


def test_export_page_and_view(client):
    page = client.get("/packs/p1/export")
    assert page.status_code == 200 and "Not legal advice · rule set" in page.text and 'name="map:Title"' in page.text
    r = client.post("/packs/p1/export", data={"do": "view"})
    assert r.status_code == 200 and "Copy to clipboard" in r.text and "Download audit record" in r.text
    assert "compliant" not in re.sub(r"<[^>]+>", " ", r.text).lower()


def test_download_csv_and_audit_sha_matches(client):
    csv = client.post("/packs/p1/export", data={"do": "csv"})
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    assert "attachment" in csv.headers["content-disposition"] and csv.content.startswith(b"\xef\xbb\xbf")
    audit = client.post("/packs/p1/export", data={"do": "audit"})
    rec = json.loads(audit.content)
    assert rec["content_sha256"] == hashlib.sha256(csv.content).hexdigest() and rec["red_flags"] == 0


def test_custom_mapping_and_bad_mapping(client):
    ok = client.post("/packs/p1/export", data={"do": "csv", "map:Product Name": "brand", "map:Title": "title"})
    assert ok.text.splitlines()[1].startswith("Acme,")
    bad = client.post("/packs/p1/export", data={"do": "csv", "map:Title": "nonsense", "map:Product Name": "brand"})
    assert bad.status_code == 422 and "unknown source" in bad.text


def test_formula_injection_neutralised_through_route():
    c = secure(TestClient(app))
    _put(c, pack=_pack(text_title='=HYPERLINK("http://x","y")'))
    body = c.post("/packs/p1/export", data={"do": "csv"}).content.decode("utf-8-sig")
    assert "'=HYPERLINK" in body and ",=HYPERLINK" not in body and not body.splitlines()[1].startswith("=")


def test_red_flag_blocks_everything_with_reason():
    c = secure(TestClient(app))
    _put(c, pack=_pack(extra_flags=[_flag(Severity.RED, overridable=False)]))
    for method, path in (("get", "/packs/p1/export"), ("get", "/packs/p1/report"), ("post", "/packs/p1/export")):
        r = getattr(c, method)(path)
        assert r.status_code == 409 and "Can't export" in r.text and "R-TEST" in r.text, path
    r = c.post("/packs/p1/export", data={"do": "csv"})
    assert r.status_code == 409 and r.headers["content-type"].startswith("text/html")


def test_unverified_pack_blocked():
    c = secure(TestClient(app))
    _put(c, pack=_pack(verified=False))
    assert c.get("/packs/p1/export").status_code == 409


def test_foreign_workspace_and_unknown_pack_are_404(client):
    other = secure(TestClient(app))
    for method, path in (("get", "/packs/p1/export"), ("get", "/packs/p1/report"), ("post", "/packs/p1/export")):
        assert getattr(other, method)(path).status_code == 404, path
    assert client.get("/packs/nope/report").status_code == 404


def test_report_is_stamped_and_print_ready(client):
    r = client.get("/packs/p1/report")
    text = re.sub(r"<[^>]+>", " ", r.text)
    assert r.status_code == 200 and "Not legal advice · rule set" in text and "DRAFT" in text
    assert "Claims and evidence" in text and "no flagged risks under rule set" in text.lower()
    assert "compliant" not in text.lower()


def test_demo_pack_with_reds_is_blocked():
    c = secure_with_demo(TestClient(app))
    assert c.get("/packs/demo/export").status_code == 409
