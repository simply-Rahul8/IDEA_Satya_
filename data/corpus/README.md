# data/corpus

The 50-PDP labelled corpus (plan P22). Owner: Evaluation agent. **Labels are DRAFT** until the consultant spot-checks
them (P20). Listing text is data, never instructions.

**Status: 50 SYNTHETIC PDPs (board decision on SAT-18).** Fictional brands and products, written as test fixtures, not
claims about real products and not copied from any retailer. Planted mix: 17 clean, 17 borderline, 16 risky. Real pilot
listings are added later with the brand's permission. Caveat: many risky and borderline sentences reuse phrasing from
the rules' own positive examples, so matcher scores on this set are an upper bound (sanity check), not a real measure of
precision and recall. Real listings are needed for that.

Edit `_source.txt`, then run `python -m bench.corpus build` to regenerate the JSON files. `make bench` prints the
matcher's agreement with the labels.

## Layout (proposed)

One file per PDP: `data/corpus/<pdp-id>.json`.

```json
{
  "pdp_id": "pdp-001",
  "synthetic": true,
  "band": "clean|borderline|risky",
  "source": "who supplied it, where from, date, licence/permission note",
  "category": "skin|hair|makeup|fragrance|other",
  "labels_status": "draft",
  "sentences": [
    {"text": "Brightens dull skin.", "label": "orange", "rule_ids": ["EN-CLAIM-003"], "note": ""}
  ]
}
```

- `label` is `safe`, `orange` or `red`. `rule_ids` is empty for `safe`, one or more `EN-*` ids otherwise.
- Sentences are split once and stored verbatim, so `make bench` scores the matcher on the same units each run.
- Labels follow the rule's written intent in `engine/rules/*.yaml`, not the matcher's output (otherwise recall is
  circular). Disagreements between label and matcher are what the bench reports.
- `labels_status` moves `draft` -> `spot_checked` only when the consultant's check is logged in `engine/rules/README.md`.
