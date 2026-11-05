# Hindi lexicon and translation (DRAFT)

**Status: DRAFT.** Lexicon `satya-hi`, version in `lexicon_hi.yaml`; reports quote it as `hi-v0.1.0-draft`.
Nothing here is brand-facing until the native Hindi reviewer (SAT-5) signs off (plan P20). Output is never "compliant":
only "no flagged risks under lexicon vX" (`summary_line_hi`). Owner: Indic agent. Hindi only.

| Where | What |
|---|---|
| `hindi.py` | `nfc` (stored text), `normalize_hi`/`analyse_hi` (matching: nukta, chandrabindu, digits, zero-width, Roman spelling variants, offsets back to the original) |
| `lexicon_hi.yaml`, `lexicon.py` | Rules `HI-DRUG/DMR/FAIR-*` in three forms (devanagari, transliterated, hinglish). Each maps to an English rule and is red and non-overridable (P17). `check_hindi`, `hard_blocks_hindi` |
| `../translate/protect.py` | `protect`/`restore`: protected-term placeholders (P13). A dropped, duplicated or invented placeholder rejects the translation |
| `../translate/providers.py` | IndicTrans2 (Cloudflare, `INDICTRANS2_URL`/`INDICTRANS2_TOKEN`) then Sarvam Translate (`SARVAM_API_KEY`). `SATYA_LLM=mock` uses an offline stub |
| `../translate/service.py` | `translate_text`, `translate_pack`: translate, NFC, restore, re-run the lexicon, append the Hindi disclaimer |

Every rule has Hindi positive and negative examples (per form) and English positive and negative examples, all tested in
`tests/test_hindi.py`. Open questions for the reviewer sit in each rule's `open_questions`.

## Known limits

- Word matching, not meaning: "इलाज नहीं करता" style negation outside the allowlisted disclaimers is flagged.
- Hindi inflection is handled with prefix wildcards (`ठीक कर*`), not a morphological analyser.
- The IndicTrans2 Worker contract and the Sarvam Translate request shape are assumed, not verified against live calls.
- Disclaimer wording (`DISCLAIMER_HI`) is a draft translation of the English standard disclaimer.

## Sign-off log

Only the board user adds entries, after the reviewer's written decision. `status` in `lexicon_hi.yaml` becomes
`SIGNED_OFF` only after an entry below says "Approved".

| Date | Lexicon version | Reviewer (name, qualification) | Scope reviewed | Decision | Changes required | Recorded by |
|---|---|---|---|---|---|---|
| (none yet) | | | | | | |
