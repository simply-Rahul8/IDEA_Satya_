"""Best-effort Nykaa / Amazon India beauty layouts (SAT-29). They are placeholder presets:
registered, exportable through the generic path, and editable in the mapping screen."""

from datetime import UTC, datetime

import pytest

from engine.export import (
    default_mapping,
    export_csv,
    get_layout,
    list_layouts,
    validate_mapping,
)
from engine.export.marketplaces import AMAZON_IN_BEAUTY_LAYOUT, NYKAA_BEAUTY_LAYOUT
from tests.test_export import _pack, _truth  # reuse the approved-pack fixtures

LAYOUT_IDS = ["nykaa-beauty-v0", "amazon-in-beauty-v0"]
WHEN = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize("layout_id", LAYOUT_IDS)
def test_registered(layout_id):
    assert get_layout(layout_id).id == layout_id
    assert layout_id in {lay.id for lay in list_layouts()}


@pytest.mark.parametrize("layout", [NYKAA_BEAUTY_LAYOUT, AMAZON_IN_BEAUTY_LAYOUT])
def test_marked_placeholder(layout):
    # Not the real seller template: must stay flagged so the UI warns and no one treats it as official.
    assert layout.placeholder is True


@pytest.mark.parametrize("layout", [NYKAA_BEAUTY_LAYOUT, AMAZON_IN_BEAUTY_LAYOUT])
def test_default_mapping_is_valid(layout):
    # Every default_source must be a real source and every required column must be mapped.
    validate_mapping(layout, default_mapping(layout))


@pytest.mark.parametrize("layout", [NYKAA_BEAUTY_LAYOUT, AMAZON_IN_BEAUTY_LAYOUT])
def test_export_roundtrip(layout):
    res = export_csv(_pack(), _truth(), layout=layout, exported_at=WHEN)
    text = res.content.decode("utf-8-sig")
    header, row = text.splitlines()[0], text.splitlines()[1]
    # Header is the layout's headers; the required product/title cell is populated.
    assert header.split(",")[1].strip('"') in {"Product Name", "Product Name (item_name)"}
    assert row.split(",")[1].strip('"')  # required column is non-empty
    assert res.audit.layout_id == layout.id
