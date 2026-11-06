# ruff: noqa: E501
"""Preview-only demo pack so the review screen can be opened before Platform storage exists. Draft content."""

from engine import api
from engine.models import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceType,
    PDPPack,
    ProductTruth,
    Section,
    Sentence,
    SentenceType,
)
from web.review import ReviewState, store

PACK_ID = "demo"

_S = SentenceType
_ROWS = {
    "title": [("Rosewater Dew Serum, 30 ml", _S.PRODUCT_FACT, ["truth:product_name", "truth:size"])],
    "bullet_1": [("Hydrating serum with a dewy finish.", _S.BENEFIT_CLAIM, ["claim:c1"])],
    "bullet_2": [("Cures acne scars in 7 days.", _S.BENEFIT_CLAIM, ["claim:c4"])],
    "bullet_3": [("Dermatologically tested and clinically proven on sensitive skin.", _S.BENEFIT_CLAIM, ["claim:c3"])],
    "bullet_4": [("Approved by dermatologists for daily use.", _S.BENEFIT_CLAIM, ["claim:c5"])],
    "bullet_5": [("Made with rose water and glycerin.", _S.PRODUCT_FACT, [])],
    "description": [
        ("A light serum that leaves skin hydrated with a dewy finish.", _S.DESCRIPTIVE, ["claim:c1"]),
        ("Made with rose water and glycerin.", _S.PRODUCT_FACT, ["claim:c2"]),
    ],
    "how_to_use": [("Apply two drops to clean skin, morning and night.", _S.USAGE, ["truth:how_to_use"])],
    "warnings_storage": [
        ("For external use only. Store in a cool, dry place.", _S.WARNING, ["truth:warnings", "truth:storage"])
    ],
    "seo_title": [("Rosewater Dew Serum 30 ml | Hydrating Face Serum", _S.DESCRIPTIVE, ["truth:product_name"])],
    "seo_description": [("A hydrating rosewater serum with a dewy finish.", _S.DESCRIPTIVE, ["claim:c1"])],
}


def seed() -> ReviewState:
    ev = lambda t, ref=None: Evidence(type=t, reference=ref)  # noqa: E731
    truth = ProductTruth(
        product_name="Rosewater Dew Serum", size="30 ml", how_to_use="Apply two drops to clean skin.",
        warnings="For external use only.", storage="Store in a cool, dry place.",
        claims=[
            Claim(id="c1", text="Hydrating, dewy finish", status=ClaimStatus.CONFIRMED, evidence=ev(EvidenceType.BRAND_DECLARATION)),
            Claim(id="c2", text="Contains rose water and glycerin", status=ClaimStatus.CONFIRMED, evidence=ev(EvidenceType.INGREDIENT_LIST, "label-1")),
            Claim(id="c3", text="Dermatologically tested", status=ClaimStatus.CONFIRMED, evidence=ev(EvidenceType.TEST_REPORT, "doc-7")),
            Claim(id="c4", text="Cures acne scars in 7 days", hard_blocked=True, blocking_rule_ids=["EN-DRUG-001"]),
            Claim(id="c5", text="Suitable for daily use", evidence=ev(EvidenceType.TEST_REPORT)),
        ],
    )  # fmt: skip
    rs = api.default_ruleset()
    pack = PDPPack(
        sections=[
            Section(key=k, sentences=[Sentence(text=t, type=ty, anchors=a) for t, ty, a in rows])
            for k, rows in _ROWS.items()
        ],
        rule_set_version=rs.label,
    )
    for k, rows in _ROWS.items():
        for i, (t, _, _) in enumerate(rows):
            pack = api.edit_sentence(pack, k, i, t, truth, ruleset=rs)
    state = ReviewState(
        "demo",
        truth.product_name,
        truth,
        pack,
        rs,
        rewrites={"bullet_3-0": "A gentle serum made for everyday use on sensitive skin."},
    )
    store.put(state)
    return state
