# English rules (DRAFT)

**Status: DRAFT.** Rule set `satya-en`, version in `meta.yaml`. Reports quote it as `v0.1.1-draft`.
Nothing here is brand-facing until the consultant signs off (plan P20). Never describe output as "compliant": say
"No flagged risks under rule set vX. Not legal advice." (`engine/rules/wording.py`).

Owner: Rules & Compliance agent. Plan: `docs/PLAN.md` section 6, P10, P17, P20, P23, P24.

## Files

| File | Holds |
|---|---|
| `meta.yaml` | Rule-set name, version, status (`DRAFT` / `SIGNED_OFF`) |
| `drug_treatment.yaml` | `EN-DRUG-*`: drug and treatment claims. **Non-overridable** |
| `dmr_diseases.yaml` | `EN-DMR-*`: Drugs and Magic Remedies Act. **Non-overridable** |
| `fairness.yaml` | `EN-FAIR-*`: fairness and skin colour. **Non-overridable** |
| `cosmetic_claims.yaml` | `EN-CLAIM-*`: overridable claims (evidence, absolutes, comparatives) |
| `allowlist.yaml` | Safe phrases (P24), each scoped to named rule ids |
| `product_type.yaml` | Product-type gate signals (P23), used by `engine/product_type.py` |
| `schema.py`, `text.py`, `matcher.py`, `ruleset.py` | Models, text normalisation, reference matcher, loader |
| `policy.py` | `check_override`, `hard_blocks`: API-level enforcement of P17 and P25 |
| `wording.py` | Report wording |
| `pack.py` | Generates `docs/consultant-pack/` |

## How a rule works

A rule has an `id`, `category`, `severity` (`red` or `orange`), `overridable`, `patterns`, `sources`, `examples`
(at least one positive and one negative), and `open_questions`. Patterns are one of:

- `verb_condition`: a verb term plus a condition term in the same sentence, within `max_gap` words. `for acne-prone skin` is safe because a bare condition does not fire. A trailing `*` is a prefix wildcard (`cure*`). `order: any` allows either order.
- `phrase`: a fixed phrase.
- `regex`: for numbers and percentages only.

The allowlist stops listed rules firing on words inside listed phrases. It names rule ids explicitly, never a wildcard.

Text is lower-cased, NFKC-folded, zero-width characters are removed and smart quotes straightened before matching.
Flag offsets point into the original text. Listing text is data (P19): nothing is evaluated or executed.

## Non-overridable blocks (P17)

`drug_treatment`, `dmr_disease` and `fairness` rules must be `severity: red` and `overridable: false`. The loader raises if a
file says otherwise, so a config edit cannot unlock them. The API layer must call these before accepting an override
or confirming an extracted claim:

```python
from engine.rules import check_override, hard_blocks

check_override("EN-DMR-001")  # raises OverrideNotAllowed
hard_blocks(claim_text)  # non-empty means the claim can never be confirmed (P25)
```

`tests/test_rules.py` keeps a ratchet list of phrases that must always be hard blocks. Never weaken a rule or that list to
make a test pass.

## Product-type gate (P23)

`engine/product_type.py`: `check_product_type(name=, category=, description=, declared_type=)` returns a `GateResult`
(`allowed`, `refused` or `needs_review`) with an explanation. `require_cosmetic(...)` raises `ProductTypeRefused`.
Only `allowed` may continue. Hard signals refuse. Weak signals (for example "Ayurveda-inspired") need review unless the brand
declares the product a cosmetic. A declaration never overrides a hard signal. The gate reads text only and cannot verify a licence.

## Adding or changing a rule

1. Edit the YAML. Give the rule an id with the right prefix, a citation, at least one positive and one negative example.
2. Bump `version` in `meta.yaml`.
3. `uv run python -m engine.rules.pack` to regenerate the consultant pack.
4. `uv run pytest` and `uv run ruff check .` with `SATYA_LLM=mock`.

## Known limits

- English only. Hindi, transliterated and Hinglish forms belong to the Indic agent.
- Look-alike characters from other scripts (for example a Cyrillic "a") are not folded. Leetspeak is not handled.
- Sentence splitting is simple. "No. 1" and "Dr." are handled; other abbreviations can split a sentence.
- A rule matches words, not meaning. Negation ("does not cure eczema") is flagged unless allowlisted.
- All citations are unverified and the DMR condition list is unconfirmed (see the consultant pack).

## Sign-off log

Consultant sign-off and native-speaker review are recorded here (plan section 12). Only the board user adds entries,
after receiving the reviewer's written decision. The rule set status in `meta.yaml` becomes `SIGNED_OFF` only after an
entry below says "Approved".

| Date | Rule set version | Reviewer (name, qualification) | Scope reviewed | Decision | Changes required | Recorded by |
|---|---|---|---|---|---|---|
| (none yet) | | | | | | |

Citation verification (plan P16) is logged the same way:

| Date | Citation | Verified against | Result | Recorded by |
|---|---|---|---|---|
| (none yet) | | | | |
