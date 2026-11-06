# ADR-11: Hindi lexicon is a separate file; MT providers live in engine/translate

Status: accepted (CTO, SAT-28 review of SAT-20). Lexicon (`hi-v0.1.0-draft`) and the Hindi disclaimer stay DRAFT until the native Hindi reviewer signs off (SAT-5, P20).

## Context
Plan P6 and §3 step 8 need a Hindi lexicon (Devanagari, transliterated and Hinglish forms) re-run on translated copy, plus protected-term translation (P13). The English loader in `engine/rules` enforces `language: en` and `EN-` ids, and Hindi needs its own normalisation (nukta, chandrabindu, digits, zero-width characters, Roman spelling variants).

## Decision
1. **The Hindi lexicon is `engine/normalize/lexicon_hi.yaml`, loaded by `engine/normalize/lexicon.py`**, not `engine/rules/*.yaml`. Each Hindi rule maps to an English rule (`maps_to`), is red, and is non-overridable; the loader rejects an overridable rule in a non-overridable category (P17, ADR-9, ADR-10). It reuses `engine.rules.text` matching types so offsets map back to the original text.
2. **MT providers (IndicTrans2 on Cloudflare, then Sarvam Translate) live in `engine/translate/providers.py`.** They reuse the `engine.providers` transport and errors and honour `SATYA_LLM=mock` (offline stub, no keys). They are MT endpoints, not chat LLMs, so they do not go through the LLM-call ledger path.
3. **Translation fails closed.** A result that drops, duplicates or invents a protected-term placeholder is rejected, never repaired. Each translator is tried once; no retry loops (spend).
4. **Hindi output never claims "compliant"**: reports say "no flagged risks under lexicon vX".

## Consequences
- Wiring `translate_pack` into the API and pipeline step 8 is a separate task; SAT-20 delivers the engine pieces only.
- The IndicTrans2 Worker and Sarvam request/response shapes are assumed, not tested live. They must be checked against the real endpoints before `SATYA_LLM=live` is used for Hindi (board user: needs keys and a deployed Worker).
- The SAT-5 reviewer owns each rule's `open_questions` and should confirm the AL-HI-001 allowlist cannot let a claim through.
