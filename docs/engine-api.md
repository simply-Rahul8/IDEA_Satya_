# Engine API (internal, stable surface)

Import from `engine.api` only. Everything runs offline with `SATYA_LLM=mock`. `SATYA_LLM=live` builds a
Sarvam-primary, Claude-failover chain from `SARVAM_API_KEY` / `ANTHROPIC_API_KEY` (either alone works; none raises
`ProviderConfigError`). Optional `SARVAM_MODEL`, `ANTHROPIC_MODEL`. Output wording: "no flagged risks under rule set
vX-draft", never "compliant" (P20).

## Flow (plan section 3, steps 4-7)

```python
from engine import api

rules = api.load_ruleset()  # engine/rules/*.yaml
truth = api.extract_product_truth(listing_text, ruleset=rules)  # all claims UNCONFIRMED; hard-blocked ones marked
claim = api.confirm_claim(c, api.Evidence(type=api.EvidenceType.TEST_REPORT, reference="doc-1"), rules)
# raises ClaimGuardError (P25)
report = api.generate_verified_pack(truth, tone="professional", ruleset=rules)  # generate + two-pass verify (P4)
pack = report.pack  # report.pass2_completed False => verifier unavailable
pack = api.edit_sentence(pack, "bullet_1", 0, "new text", truth, ruleset=rules)  # live re-check, deterministic only
pack = api.override_flag(pack, "bullet_2", 0, "VERIFIER-UNSUPPORTED", "reason")  # orange only
status = api.approval_status(pack, truth)  # .approvable, .blockers (list[str])
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

## Rules (owned by the Rules agent; ADR-9)
Rule files, schema, matcher and P17/P25 policy live in `engine/rules` (`engine.rules.evaluate`, `policy.hard_blocks`).
`engine.guardrails.check_text(text, ruleset=None)` is a thin adapter that turns `engine.rules` flags into
`engine.models.Flag` (`citation` = the rule's sources + `[rule set vX-draft]`, `suggestion` = `rewrite_hint`, one flag
per rule per text). `api.load_ruleset` / `api.default_ruleset` re-export the `engine.rules` loaders;
`PDPPack.rule_set_version` holds the label (e.g. `v0.1.0-draft`).

## Telemetry (`llm_calls`, P26)
All LLM calls go through `engine.telemetry.call_llm`, which records one `LLMCall` per provider attempt (failover
produces an error row then an ok row with `failover_from`). Fields: `purpose, prompt_version, provider, model,
prompt_tokens, completion_tokens, cost_inr, latency_ms, outcome, error, failover_from`. `api.recorder` holds them in
memory; Platform attaches a DB writer via `recorder.add_sink(fn)`. Prices in `telemetry.PRICE_INR_PER_MTOK` are
estimates to verify before the cost metric is trusted.

## Prompts (P19)
`engine/prompts`: listing text only appears as JSON inside `<untrusted_data>` with `<` escaped; system prompts
state it is data. Versions in `prompts.VERSIONS`.

## Catalogue audit (`engine.audit`, plan section 3 step 3, P11/P23/P29)
Engine side only; the screen is `docs/design/final/screen-audit.md`. Deterministic, no LLM, works under `SATYA_LLM=mock`.

```python
from engine import audit

res = audit.import_catalogue(upload_bytes, kind="csv")      # kind: auto | csv (uploads) | text (paste)
job = audit.create_audit(conn, workspace_id, res.products)  # conn: service-role psycopg connection (ADR-8)
audit.step_audit(conn, job, batch_size=5)  # {status, total, done, failed, label}; the browser calls this repeatedly
audit.cancel_audit(conn, job)              # label "Stopped at 38 of 120"; finished results are kept
audit.resume_audit(conn, job)              # picks the rest up again
report = audit.audit_report(conn, job)     # AuditReport, callable at any point (partial results show `pending`)
```

**Import.** Registry order: any registered marketplace importer, then `shopify_csv` (merges variant rows by Handle,
strips HTML), then `generic_csv` (header synonyms; delimiter sniffed), and `pasted_text` (products split by blank
lines or `---`; first line is the name). Unknown headers raise `NeedsMapping(headers, suggested)`; call again with
`mapping={"name": "Col A", "description": "Col B"}` (Satya field -> their column; `name` required). Pass
`kind="csv"` for uploads so unknown layouts reach the mapping step instead of being read as pasted prose.
`ImportProblem.code` is one of `empty, too_large, unsupported_type, unreadable, bad_mapping, no_products,
needs_mapping, over_limit`; `.message` is brand-facing. Limits: 2 MB, 500 products (`OverLimit`; pass
`allow_truncate=True` to keep the first 500), 5,000 characters per cell. Every cell is data: control characters are
removed and cells starting `= + - @` get a leading `'`. XLSX is not supported yet. Nykaa and Amazon parsers wait for
the templates (SAT-4): add them with `audit.register_importer(Importer(name, matches(headers), parse(headers, rows)))`.

**Per product** (`scan_product`): the product-type gate first (non-cosmetic or unclear -> `skipped`, `note` = the gate's
explanation, no flags, excluded from risk counts); then the rule scan (`AuditFlag`: `rule_id, title, severity,
citation, matched_text`; rule severity `orange` is shown as `amber`); then Legal Metrology declaration fields. Missing
ones become flags `LM-NET-QUANTITY, LM-MRP, LM-MANUFACTURER, LM-COUNTRY-OF-ORIGIN, LM-CONSUMER-CARE`, severity
`amber`, title "Legal Metrology declaration fields (rule reference to be confirmed)", **no citation** (rule number
unconfirmed, pre-review 1c), plus plain labels in `missing_fields`. A field counts as present if its column is filled
or the listing text declares it. State = worst flag: `red | amber | green`; `pending | skipped | error` as described.

**Report.** `AuditReport{job_id, status, rule_set, counters{total, done, red, amber, green, skipped, error, pending},
progress_label, summary, items}`. `items` are `{sku, name, state, flags, missing_fields, note, position}` sorted red,
amber, green, pending, error, skipped, then catalogue order (`position`). `summary` is set only when the audit is
complete with 0 red and 0 amber: "No flagged risks under rule set vX-draft. Not legal advice. ...", never "compliant".
A product that raises is recorded as `error` in the same step (no retry loop); store-level failures after 3 attempts
also surface as `error`. `engine/jobs/store.py` gained `cancel_job`, `resume_job` and `job_items`; a cancelled job
ignores late `step_job` calls. Sample: `data/samples/audit-120.csv` (`scripts/make_audit_sample.py`).
