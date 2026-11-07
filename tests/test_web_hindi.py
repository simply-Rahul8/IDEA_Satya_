# ruff: noqa: E501
"""Hindi step in the web journey (SAT-42): approved English pack -> translate -> verify -> gate -> export."""

import pytest
from fastapi.testclient import TestClient
from helpers import secure

from asgi import app
from engine.export import export_csv
from engine.models import Claim, ClaimStatus, Evidence, EvidenceType, ProductTruth
from engine.pipeline import generate_verified_pack
from engine.repo import ReviewState
from engine.rules import default_ruleset
from engine.translate.journey import hindi_export_blockers
from engine.translate.service import DISCLAIMER_HI
from web import packs

HX = {"HX-Request": "true"}


def make_state(approved: bool) -> ReviewState:
    truth = ProductTruth(
        product_name="Glow Serum", brand="Glow & Co", size="30 ml", ingredients=["Vitamin C"],
        how_to_use="Apply two drops.", warnings="For external use only.", storage="Store cool.",
        claims=[Claim(id="c1", text="Hydrating", status=ClaimStatus.CONFIRMED, evidence=Evidence(type=EvidenceType.BRAND_DECLARATION))],
    )  # fmt: skip
    pack = generate_verified_pack(truth).pack
    return ReviewState("p1", truth.product_name, truth, pack, default_ruleset(), approved=approved)


@pytest.fixture()
def client():
    return secure(TestClient(app))


def seed(c, approved):
    st = make_state(approved)
    assert st.pack.verifier_passed
    packs.repo().put(c.owner, st)


def test_unapproved_english_cannot_translate(client):
    seed(client, False)
    assert client.post("/packs/p1/hindi", data={}, headers=HX).status_code == 409
    html = client.get("/packs/p1/hindi").text
    assert "Approve the English pack first" in html and "Translate to Hindi" not in html
    st = packs.repo().get(client.owner, "p1")
    assert hindi_export_blockers(st.approved, st.pack, st.hi_pack, st.hi_for, st.truth)


def test_approved_pack_translates_verifies_and_exports(client):
    seed(client, True)
    r = client.post("/packs/p1/hindi", data={}, headers=HX, follow_redirects=False)
    assert r.status_code == 303
    st = packs.repo().get(client.owner, "p1")
    assert st.hi_pack.verifier_passed
    assert st.hi_pack.section("warnings_storage").sentences[-1].text == DISCLAIMER_HI
    assert st.hi_pack.section("title").sentences[0].text.endswith("Glow Serum")  # protected term survives
    assert hindi_export_blockers(st.approved, st.pack, st.hi_pack, st.hi_for, st.truth) == []
    export_csv(st.hi_pack, st.truth)  # the same gate the English export uses
    html = client.get("/packs/p1/hindi").text
    assert "DRAFT" in html and "Passes the export gate" in html and 'lang="hi"' in html and DISCLAIMER_HI in html
    assert "compliant" not in html.lower()


def test_unverified_hindi_pack_does_not_export(client):
    seed(client, True)
    client.post("/packs/p1/hindi", data={}, headers=HX)
    st = packs.repo().get(client.owner, "p1")
    unverified = st.hi_pack.model_copy(update={"verifier_passed": False})
    assert hindi_export_blockers(True, st.pack, unverified, st.hi_for, st.truth)
    assert hindi_export_blockers(False, st.pack, st.hi_pack, st.hi_for, st.truth) == ["English pack is not approved"]
    assert hindi_export_blockers(True, st.pack, st.hi_pack, "stale", st.truth) == [
        "Hindi pack is out of date with the English pack"
    ]


def test_unsafe_hindi_is_flagged_and_blocks(client, monkeypatch):
    from engine.translate import providers

    class Bad(providers.MockTranslator):
        def translate(self, text, *, source="en", target="hi"):
            return super().translate(text) + " यह क्रीम मुँहासे का इलाज करती है।"  # "treats acne": non-overridable

    seed(client, True)
    monkeypatch.setattr("engine.translate.service.get_translators", lambda: [Bad()])
    client.post("/packs/p1/hindi", data={}, headers=HX)
    st = packs.repo().get(client.owner, "p1")
    assert any(f.rule_id.startswith("HI-") for s in st.hi_pack.sentences() for f in s.flags)
    assert hindi_export_blockers(True, st.pack, st.hi_pack, st.hi_for, st.truth)
