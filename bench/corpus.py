"""Corpus build and sentence-level scoring of the rule matcher (P22). Labels are DRAFT until consultant spot-check."""

`python -m bench.corpus build` regenerates data/corpus/pdp-*.json from _source.txt.
"""

import json
import sys
from pathlib import Path

from engine.rules import default_ruleset, evaluate

CORPUS = Path(__file__).resolve().parent.parent / "data" / "corpus"
LABELS = {"S": "safe", "O": "orange", "R": "red"}


def build() -> int:
    pdps, cur = [], None
    for raw in (CORPUS / "_source.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            pdp_id, category, band, brand = (p.strip() for p in line[3:].split("|"))
            cur = {
                "pdp_id": pdp_id,
                "synthetic": True,
                "source": "Fictional listing written for SAT-18 test fixtures. Not a real product.",
                "brand": brand,
                "category": category,
                "band": band,
                "labels_status": "draft",
                "sentences": [],
            }
            pdps.append(cur)
            continue
        parts = line.split("|")
        label = LABELS[parts[0]]
        rules = parts[1].split(",") if label != "safe" else []
        cur["sentences"].append({"text": parts[-1], "label": label, "rule_ids": rules})
    for p in pdps:
        (CORPUS / f"{p['pdp_id']}.json").write_text(
            json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(f"wrote {len(pdps)} PDPs, {sum(len(p['sentences']) for p in pdps)} sentences")
    return 0


def load() -> list[dict]:
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(CORPUS.glob("pdp-*.json"))]


def score() -> dict:
    """Sentence is flagged if the matcher raises any flag; label disagreements are listed for review."""
    rs = default_ruleset()
    tp = fp = fn = rule_ok = 0
    misses = []
    for p in load():
        for s in p["sentences"]:
            ids = sorted({f.rule_id for f in evaluate(s["text"], rs)})
            unsafe = s["label"] != "safe"
            if ids and unsafe:
                tp += 1
                rule_ok += set(s["rule_ids"]) <= set(ids)
            elif ids:
                fp += 1
            elif unsafe:
                fn += 1
            if bool(ids) != unsafe or (unsafe and not set(s["rule_ids"]) <= set(ids)):
                misses.append((p["pdp_id"], s["label"], s["rule_ids"], ids, s["text"]))
    return {
        "rule_set": rs.label,
        "precision": tp / (tp + fp) if tp + fp else 1.0,
        "recall": tp / (tp + fn) if tp + fn else 1.0,
        "rule_id_match": rule_ok / tp if tp else 1.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "disagreements": misses,
    }


if __name__ == "__main__":
    sys.exit(build() if sys.argv[1:] == ["build"] else 2)
