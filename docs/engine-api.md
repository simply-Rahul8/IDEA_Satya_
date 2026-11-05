# Engine API (internal, stable surface)

Import from `engine.api` only. Everything runs offline with `SATYA_LLM=mock`. `SATYA_LLM=live` builds a
Sarvam-primary, Claude-failover chain from `SARVAM_API_KEY` / `ANTHROPIC_API_KEY` (either alone works; none raises
`ProviderConfigError`). Optional `SARVAM_MODEL`, `ANTHROPIC_MODEL`. Output wording: "no flagged risks under rule set
vX (draft)", never "compliant" (P20).

## Flow (plan section 3, steps 4-7)

```python
from engine import api

rules = api.load_ruleset()                                   # engine/rules/*.yaml
truth = api.extract_product_truth(listing_text, ruleset=rules)   # all claims UNCONFIRMED; hard-blocked ones marked
claim = api.confirm_claim(c, api.Evidence(type=api.EvidenceType.TEST_REPORT, reference="doc-1"), rules)
                                                              # raises ClaimGuardError (P25)
report = api.generate_verified_pack(truth, tone="professional", ruleset=rules)   # generate + two-pass verify (P4)
pack = report.pack                                           # report.pass2_completed False => verifier unavailable
pack = api.edit_sentence(pack, "bullet_1", 0, "new text", truth, ruleset=rules)  # live re-check, deterministic only
pack = api.override_flag(pack, "bullet_2", 0, "VERIFIER-UNSUPPORTED", "reason")  # orange only
status = api.approval_status(pack, truth)                    # .approvable, .blockers (list[str])
```

Replace the confirmed claim into `truth.claims` yourself (models are immutable-by-convention copies).
Calling `verify_pack(pack, truth)` after edits re-runs both passes and restores `verifier_passed`.

## Models (`engine.models`)
- `ProductTruth` (fields + `claims: list[Claim]`), `Claim` (`status`, `evidence`, `hard_blocked`, `blocking_rule_ids`),
  `Evidence` (`type`, `reference`, `note`).
- `PDPPack.sections`: exactly `title, bullet_1..bullet_5, description, how_to_use, warnings_storage, seo_title,
  seo_description`; each section has `sentences: list[Sentence]`.
- `Sentence`: `text`, `type` (`product_fact|benefit_claim|usage|warning|storage|legal|descriptive`),
  `anchors` (`claim:<id>` / `truth:<field>`), `flags`, `.severity` (`safe|orange|red`).
- `Flag`: `rule_id, severity, reason, citation, suggestion, matched_text, overridable, source (rule|anchor|verifier),
  override_reason`.

## Approval rules
Red blocks approval and cannot be overridden (all non-overridable rules are red). Orange needs `override_reason`.
The pack must be `verifier_passed` (cleared by any edit). `override_flag` raises `ReviewError` on red.
Failed verifier call => fail closed (`pass2_completed=False`).

## Rule file schema (agreed with Rules agent; see `engine/guardrails/ruleset.py`)
Top level `version`, `status` (`draft|final`), `rules[]`. Per rule: `id`, `category`
(`drug_treatment|dmr_disease|fairness|other`), `severity` (`red|orange`), `overridable`, `language`, `reason`,
`citation`, `suggestion`, `patterns[]` (`{verb, condition, window}` or `{regex}`), `allowlist[]` (regexes; a match
overlapping the flagged span suppresses it), `examples: {positive[], negative[]}` (both required).
The three hard-block categories MUST be `severity: red, overridable: false` or the loader rejects the file.
All files in `engine/rules/` must share one `version`. `tests/test_engine_core.py` runs every shipped YAML's
examples automatically. Test fixture: `tests/fixtures/rules_test.yaml`.

## Telemetry (`llm_calls`, P26)
All LLM calls go through `engine.telemetry.call_llm`, which records one `LLMCall` per provider attempt (failover
produces an error row then an ok row with `failover_from`). Fields: `purpose, prompt_version, provider, model,
prompt_tokens, completion_tokens, cost_inr, latency_ms, outcome, error, failover_from`. `api.recorder` holds them in
memory; Platform attaches a DB writer via `recorder.add_sink(fn)`. Prices in `telemetry.PRICE_INR_PER_MTOK` are
estimates to verify before the cost metric is trusted.

## Prompts (P19)
`engine/prompts`: listing text only appears as JSON inside `<untrusted_data>` with `<` escaped; system prompts
state it is data. Versions in `prompts.VERSIONS`.
