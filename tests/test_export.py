"""Export tests (SAT-22). Golden files live in tests/golden/export; regenerate with UPDATE_GOLDEN=1."""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from engine.export import (
    PLACEHOLDER_LAYOUT,
    ExportBlocked,
    MappingError,
    default_mapping,
    export_csv,
    render_report,
    validate_mapping,
)
from engine.models import (
    SECTION_KEYS,
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceType,
    Flag,
    PDPPack,
    ProductTruth,
    Section,
    Sentence,
    SentenceType,
    Severity,
)

GOLDEN = Path(__file__).parent / "golden" / "export"
WHEN = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


def _truth(**kw) -> ProductTruth:
    claim = Claim(
        id="c1",
        text="Contains 2% niacinamide",
        status=ClaimStatus.CONFIRMED,
        evidence=Evidence(type=EvidenceType.INGREDIENT_LIST, reference="doc-1", note="label p2"),
    )
    return ProductTruth(
        product_name="Glow Serum",
        brand="Acme",
        category="Skincare",
        size="30 ml",
        ingredients=["Water", "Niacinamide"],
        manufacturer="Acme Labs, Pune",
        country_of_origin="India",
        claims=[claim],
        **kw,
    )


def _pack(
    extra_flags: list[Flag] | None = None, verified: bool = True, text_title: str = "Glow Serum 30 ml"
) -> PDPPack:
    secs = []
    for key in SECTION_KEYS:
        if key == "title":
            s = Sentence(text=text_title, type=SentenceType.PRODUCT_FACT, anchors=["truth:product_name"])
        elif key == "bullet_1":
            s = Sentence(
                text="Contains 2% niacinamide.",
                type=SentenceType.BENEFIT_CLAIM,
                anchors=["claim:c1"],
                flags=extra_flags or [],
            )
        else:
            s = Sentence(text=f"Text for {key}.", type=SentenceType.DESCRIPTIVE)
        secs.append(Section(key=key, sentences=[s]))
    return PDPPack(sections=secs, rule_set_version="v0.1.1-draft", verifier_passed=verified)


def _flag(sev: Severity, overridable: bool = True, reason: str | None = None) -> Flag:
    return Flag(rule_id="R-TEST", severity=sev, reason="r", overridable=overridable, override_reason=reason)


def _golden(name: str, actual: str | bytes):
    path = GOLDEN / name
    data = actual if isinstance(actual, bytes) else actual.encode("utf-8")
    if os.environ.get("UPDATE_GOLDEN") or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    assert data == path.read_bytes().replace(b"\r\n", b"\n")


def test_csv_and_audit_golden():
    res = export_csv(_pack([_flag(Severity.ORANGE, reason="brand supplied lab note")]), _truth(), exported_at=WHEN)
    _golden("generic-v0.csv", res.content)
    _golden("generic-v0.audit.json", res.audit.to_json())
    assert res.audit.red_flags == 0 and res.audit.overrides == 1
    assert res.audit.claims[0].evidence_reference == "doc-1"


def test_report_golden_and_wording():
    pack, truth = _pack(), _truth()
    res = export_csv(pack, truth, exported_at=WHEN)
    html = render_report(pack, truth, res.audit)
    _golden("report.html", html)
    assert "Not legal advice · rule set v0.1.1-draft" in html
    assert "compliant" not in html.lower()


def test_red_flag_blocks_export():
    with pytest.raises(ExportBlocked):
        export_csv(_pack([_flag(Severity.RED, overridable=False)]), _truth(), exported_at=WHEN)


def test_red_flag_blocks_report():
    pack = _pack([_flag(Severity.RED)])
    good = export_csv(_pack(), _truth(), exported_at=WHEN)
    with pytest.raises(ExportBlocked):
        render_report(pack, _truth(), good.audit)


def test_non_overridable_cannot_be_downgraded_or_overridden():
    for flag in (_flag(Severity.ORANGE, overridable=False, reason="x"), _flag(Severity.ORANGE, overridable=False)):
        with pytest.raises(ExportBlocked):
            export_csv(_pack([flag]), _truth(), exported_at=WHEN)


def test_orange_without_reason_blocks():
    with pytest.raises(ExportBlocked):
        export_csv(_pack([_flag(Severity.ORANGE)]), _truth(), exported_at=WHEN)


def test_unverified_pack_blocks():
    with pytest.raises(ExportBlocked):
        export_csv(_pack(verified=False), _truth(), exported_at=WHEN)


def test_unconfirmed_or_hard_blocked_claim_blocks():
    truth = _truth()
    truth.claims[0] = truth.claims[0].model_copy(update={"status": ClaimStatus.UNCONFIRMED})
    with pytest.raises(ExportBlocked):
        export_csv(_pack(), truth, exported_at=WHEN)
    truth = _truth()
    truth.claims[0] = truth.claims[0].model_copy(update={"hard_blocked": True})
    with pytest.raises(ExportBlocked):
        export_csv(_pack(), truth, exported_at=WHEN)


def test_custom_mapping_and_blank_column():
    m = default_mapping(PLACEHOLDER_LAYOUT) | {"Brand": None, "Size": "bullet_1"}
    res = export_csv(_pack(), _truth(), mapping=m, exported_at=WHEN)
    rows = res.content.decode("utf-8-sig").splitlines()
    assert "Contains 2% niacinamide." in rows[1]
    assert res.audit.mapping["Brand"] is None


def test_mapping_validation():
    with pytest.raises(MappingError):
        validate_mapping(PLACEHOLDER_LAYOUT, {"Nope": "title"})
    with pytest.raises(MappingError):
        validate_mapping(PLACEHOLDER_LAYOUT, {"Brand": "not_a_source"})
    with pytest.raises(MappingError):
        validate_mapping(PLACEHOLDER_LAYOUT, default_mapping(PLACEHOLDER_LAYOUT) | {"Title": None})


def test_formula_injection_neutralised():
    res = export_csv(_pack(text_title="=HYPERLINK(1)"), _truth(), exported_at=WHEN)
    assert "'=HYPERLINK(1)" in res.content.decode("utf-8-sig")
