# Model choice report: Sarvam vs Claude (DRAFT)

Generated 2026-11-05 by `python -m bench report`. Plan refs: P5, P8, P26, P31, section 10.
Status: DRAFT. Corpus labels are synthetic and unchecked by the consultant (P20); rule set `v0.1.0-draft`.
Output is described as "no flagged risks under rule set", never "compliant".

## Safety gate (rule matcher, independent of model)
precision 1.000 (target >= 0.90), recall 1.000 (target >= 0.95), rule-id match
1.000; tp 58, fp 0, fn 0, 0 label/matcher disagreements.
Caveat: the synthetic corpus reuses the rules' own example phrasing, so this is an upper bound until real pilot
listings are labelled.

## Pipeline arms (extract + generate + verify per PDP)
| Provider | Run | Cost / PDP (target < Rs1) | Latency p50 / p95 | Approvable | Red flags in output |
|---|---|---|---|---|---|
| sarvam | NOT MEASURED (no key / SATYA_LLM!=live in this run) | - | - | - | - |
| claude | NOT MEASURED (no key / SATYA_LLM!=live in this run) | - | - | - | - |

Cost uses the estimated price table in `engine/telemetry.py` (INR per 1M tokens): verify against current price sheets.
The mock arm is free and only proves the plumbing; it says nothing about model quality.

## Quality
Blind A/B (target >= 60% win or tie) is a human step: `python -m bench ab-prep` writes `data/ab/pairs.json`; raters
vote A, B or tie; `python -m bench ab-score <file>` computes the rate. Not yet run.

## Recommendation
No recommendation yet: run `SATYA_LLM=live python -m bench report` with both keys set, then run the blind A/B (`python -m bench ab-prep`) for quality.
