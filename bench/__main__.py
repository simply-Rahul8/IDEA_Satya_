"""`make bench` entry point (P31). Matcher precision/recall gate, plus cost and latency per provider arm.

python -m bench                  gate run (exit 1 if a target is missed)
python -m bench report           also write docs/model-choice-report.md (DRAFT)
python -m bench ab-prep          write data/ab/pairs.json (blind sheet) and key.json
python -m bench ab-score FILE    win-or-tie rate from a filled-in pairs file
"""

import json
import sys
from pathlib import Path

from bench import ab
from bench.arms import COST_TARGET_INR, available_providers, run_arm
from bench.corpus import load, score
from bench.report import write_report

PRECISION_TARGET, RECALL_TARGET = 0.90, 0.95


def gate() -> tuple[dict, list[dict], list[str]]:
    r = score()
    arms = [run_arm(p, load()) for p in available_providers().values()]
    fails = []
    if r["precision"] < PRECISION_TARGET:
        fails.append(f"precision {r['precision']:.3f} < {PRECISION_TARGET}")
    if r["recall"] < RECALL_TARGET:
        fails.append(f"recall {r['recall']:.3f} < {RECALL_TARGET}")
    for a in arms:
        if a["cost_inr_per_pdp"] >= COST_TARGET_INR:
            fails.append(f"{a['provider']} cost Rs{a['cost_inr_per_pdp']:.2f}/PDP >= Rs{COST_TARGET_INR}")
        if a["red_flags_in_output"] or a["errors"]:
            fails.append(f"{a['provider']}: {a['red_flags_in_output']} red flags, {a['errors']} errors in output")
    return r, arms, fails


def main(argv: list[str]) -> int:
    if argv[:1] == ["ab-score"] and len(argv) == 2:
        doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        key = json.loads((ab.AB_DIR / "key.json").read_text(encoding="utf-8"))
        print(ab.score(doc["pairs"], key, doc["challenger"]))
        return 0
    if argv[:1] == ["ab-prep"]:
        provs = available_providers()
        if len(provs) >= 3:  # sarvam vs claude
            arms = {"sarvam": (provs["sarvam"], "professional"), "claude": (provs["claude"], "professional")}
            status = "live"
        else:  # plumbing check only: same mock, two tones. NOT a model comparison.
            arms = {"mock-professional": (provs["mock"], "professional"), "mock-friendly": (provs["mock"], "friendly")}
            status = "mock-plumbing-only"
        sheet, key = ab.prepare(load(), arms)
        ab.write(sheet, key, status)
        print(f"ab-prep: {len(sheet)} pairs ({status}) -> {ab.AB_DIR}. Raters fill 'vote' with A, B or tie.")
        return 0
    r, arms, fails = gate()
    d = r.pop("disagreements")
    print(f"bench: rule set {r['rule_set']}, labels DRAFT (synthetic corpus: upper bound, not a real measure)")
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items() if k != "rule_set"})
    for x in d:
        print("  disagreement:", x)
    for a in arms:
        print("arm:", {k: round(v, 4) if isinstance(v, float) else v for k, v in a.items()})
    if argv[:1] == ["report"]:
        print("wrote", write_report(r, arms, d))
    for f in fails:
        print("GATE FAIL:", f)
    print("bench:", "FAIL" if fails else "PASS (no flagged risks under the rule set is not a compliance claim)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
