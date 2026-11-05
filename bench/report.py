"""Model choice report (Sarvam vs Claude). Providers without a key in the run are written as NOT MEASURED:
the report never fills in numbers it did not measure, and never recommends from mock results."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from bench.arms import COST_TARGET_INR

OUT = Path(__file__).resolve().parent.parent / "docs" / "model-choice-report.md"
WANT = ("sarvam", "claude")


def write_report(r: dict, arms: list[dict], disagreements: list) -> Path:
    by = {a["provider"]: a for a in arms}
    rows = []
    for name in WANT:
        a = by.get(name)
        if a is None:
            rows.append(f"| {name} | NOT MEASURED (no key / SATYA_LLM!=live in this run) | - | - | - | - |")
        else:
            rows.append(
                f"| {name} ({a['model']}) | {a['pdps']} PDPs, {a['errors']} errors | Rs{a['cost_inr_per_pdp']:.3f} | "
                f"{a['latency_ms_p50']} / {a['latency_ms_p95']} ms | {a['approvable_rate']:.0%} | "
                f"{a['red_flags_in_output']} |"
            )
    measured = [n for n in WANT if n in by]
    verdict = (
        "No recommendation yet: run `SATYA_LLM=live python -m bench report` with both keys set, then run the blind "
        "A/B (`python -m bench ab-prep`) for quality."
        if len(measured) < 2
        else "Both arms measured: choose on cost and latency below, then confirm quality with the blind A/B."
    )
    text = f"""# Model choice report: Sarvam vs Claude (DRAFT)

Generated {date.today().isoformat()} by `python -m bench report`. Plan refs: P5, P8, P26, P31, section 10.
Status: DRAFT. Corpus labels are synthetic and unchecked by the consultant (P20); rule set `{r["rule_set"]}`.
Output is described as "no flagged risks under rule set", never "compliant".

## Safety gate (rule matcher, independent of model)
precision {r["precision"]:.3f} (target >= 0.90), recall {r["recall"]:.3f} (target >= 0.95), rule-id match
{r["rule_id_match"]:.3f}; tp {r["tp"]}, fp {r["fp"]}, fn {r["fn"]}, {len(disagreements)} label/matcher disagreements.
Caveat: the synthetic corpus reuses the rules' own example phrasing, so this is an upper bound until real pilot
listings are labelled.

## Pipeline arms (extract + generate + verify per PDP)
| Provider | Run | Cost / PDP (target < Rs{COST_TARGET_INR:g}) | Latency p50 / p95 | Approvable | Red flags in output |
|---|---|---|---|---|---|
{chr(10).join(rows)}

Cost uses the estimated price table in `engine/telemetry.py` (INR per 1M tokens): verify against current price sheets.
The mock arm is free and only proves the plumbing; it says nothing about model quality.

## Quality
Blind A/B (target >= 60% win or tie) is a human step: `python -m bench ab-prep` writes `data/ab/pairs.json`; raters
vote A, B or tie; `python -m bench ab-score <file>` computes the rate. Not yet run.

## Recommendation
{verdict}
"""
    OUT.write_text(text, encoding="utf-8")
    return OUT
