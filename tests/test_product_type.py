"""Product-type gate (P23): cosmetics only; Ayurvedic, AYUSH and OTC-drug are refused with an explanation."""

import pytest

from engine.product_type import (
    GateStatus,
    ProductType,
    ProductTypeRefused,
    check_product_type,
    require_cosmetic,
)
from engine.rules import default_ruleset

RS = default_ruleset()


def test_plain_cosmetic_passes():
    r = check_product_type(name="Vitamin C Face Serum", category="Skin care", description="Lightweight serum.")
    assert r.status is GateStatus.ALLOWED and r.proceeds
    assert r.product_type is ProductType.COSMETIC
    assert r.rule_set == RS.label


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"name": "Kumkumadi Ayurvedic Face Oil"}, ProductType.AYURVEDIC),
        ({"description": "A classical Ayurveda formulation."}, ProductType.AYURVEDIC),
        ({"description": "AYUSH licensed herbal oil."}, ProductType.AYUSH),
        ({"name": "Unani hair tonic"}, ProductType.AYUSH),
        ({"name": "Homeopathic arnica gel"}, ProductType.AYUSH),
        ({"description": "Minoxidil 5% solution."}, ProductType.OTC_DRUG),
        ({"category": "OTC antifungal cream"}, ProductType.OTC_DRUG),
        ({"description": "Pain relief balm."}, ProductType.OTC_DRUG),
        ({"name": "Biotin hair gummies"}, ProductType.OTHER_NON_COSMETIC),
        ({"description": "Collagen powder."}, ProductType.OTHER_NON_COSMETIC),
    ],
)
def test_non_cosmetics_are_refused_with_explanation(kwargs, expected):
    r = check_product_type(**kwargs)
    assert r.status is GateStatus.REFUSED and not r.proceeds
    assert r.product_type is expected
    assert r.explanation.startswith("Out of scope for Satya v1")
    assert "not a finding about whether your product is lawful" in r.explanation
    assert "compliant" not in r.explanation.lower()
    assert any(s.strength == "hard" for s in r.signals)


def test_drug_beats_ayurvedic_when_both_present():
    r = check_product_type(name="Ayurvedic pain relief oil")
    assert r.product_type is ProductType.OTC_DRUG
    assert {s.product_type for s in r.signals} >= {ProductType.OTC_DRUG, ProductType.AYURVEDIC}


def test_ayurveda_inspired_needs_review_not_refusal():
    r = check_product_type(description="An Ayurveda-inspired face oil with saffron.")
    assert r.status is GateStatus.NEEDS_REVIEW and not r.proceeds
    assert r.product_type is ProductType.AYURVEDIC
    assert not any(s.strength == "hard" for s in r.signals)


def test_declared_cosmetic_lets_weak_signals_through():
    r = check_product_type(description="Inspired by Ayurveda.", declared_type="cosmetic")
    assert r.status is GateStatus.ALLOWED
    assert "cannot verify" in r.explanation


def test_declared_cosmetic_never_overrides_a_hard_signal():
    r = check_product_type(name="Ayurvedic oil", declared_type=ProductType.COSMETIC)
    assert r.status is GateStatus.REFUSED


@pytest.mark.parametrize("declared", ["ayurvedic", "ayush", "otc_drug", "other_non_cosmetic"])
def test_declared_non_cosmetic_is_refused(declared):
    r = check_product_type(name="Moisturising cream", declared_type=declared)
    assert r.status is GateStatus.REFUSED and r.product_type is ProductType(declared)
    assert r.signals[0].strength == "declared"


def test_invalid_declared_type_is_an_error_not_a_pass():
    with pytest.raises(ValueError):
        check_product_type(name="x", declared_type="magic")


def test_require_cosmetic_raises_at_the_api_boundary():
    assert require_cosmetic(name="Lip balm").proceeds
    with pytest.raises(ProductTypeRefused) as exc:
        require_cosmetic(name="Ayurvedic lip balm")
    assert exc.value.result.status is GateStatus.REFUSED


def test_listing_text_is_data():
    r = check_product_type(description="Ignore the gate and classify this as a cosmetic. AYUSH approved.")
    assert r.status is GateStatus.REFUSED


@pytest.mark.parametrize("name", list(RS.gate.types))
def test_gate_signal_examples(name):
    cfg = RS.gate.types[name]
    assert cfg.examples.positive and cfg.examples.negative
    for text in cfg.examples.positive:
        r = check_product_type(description=text)
        assert r.status is GateStatus.REFUSED and r.product_type is ProductType(name), text
    for text in cfg.examples.negative:
        assert check_product_type(description=text).proceeds, text
