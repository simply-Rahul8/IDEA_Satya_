"""The consultant pack is generated from the rule files and must never drift from them."""

from engine.rules import default_ruleset
from engine.rules.pack import HTML_NAME, MD_NAME, PACK_DIR, build

RS = default_ruleset()


def test_committed_pack_matches_rule_files():
    for name, content in build(RS).items():
        committed = (PACK_DIR / name).read_text(encoding="utf-8")
        assert committed == content, f"{name} is stale: run `uv run python -m engine.rules.pack` and commit"


def test_pack_covers_every_rule_with_citations_and_examples():
    md = build(RS)[MD_NAME]
    for r in RS.rules:
        assert f"#### {r.id}:" in md
        for c in r.sources:
            assert c.ref in md
        for e in (*r.examples.positive, *r.examples.negative):
            assert e in md
    assert "Scope note" in md and "Open questions" in md and "Sign-off sheet" in md
    assert RS.label in md and "DRAFT" in md


def test_pack_html_is_print_friendly_and_self_contained():
    html = build(RS)[HTML_NAME]
    assert "@media print" in html and "@page" in html
    assert "<script" not in html and "http://" not in html and "https://" not in html


def test_pack_readme_exists():
    assert (PACK_DIR / "README.md").is_file()
