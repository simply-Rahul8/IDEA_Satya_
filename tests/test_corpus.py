import re

from bench.corpus import load
from engine.rules import default_ruleset

IDS = {r.id for r in default_ruleset().rules}


def test_corpus_shape_and_mix():
    pdps = load()
    assert len(pdps) == 50
    bands = {b: sum(p["band"] == b for p in pdps) for b in ("clean", "borderline", "risky")}
    assert all(15 <= n <= 18 for n in bands.values()), bands
    for p in pdps:
        assert p["synthetic"] is True and p["labels_status"] == "draft"
        for s in p["sentences"]:
            assert (s["label"] == "safe") == (not s["rule_ids"])
            assert set(s["rule_ids"]) <= IDS
            assert re.search(r"\w", s["text"])
    assert {s["label"] for p in pdps for s in p["sentences"]} == {"safe", "orange", "red"}


def test_label_is_worst_severity_of_its_rules():
    sev = {r.id: r.severity.value for r in default_ruleset().rules}
    for p in load():
        for s in p["sentences"]:
            if s["rule_ids"]:
                worst = "red" if any(sev[i] == "red" for i in s["rule_ids"]) else "orange"
                assert s["label"] == worst, s
