# ADR-9: Rules enforcement points and the three-state product-type gate

Status: accepted (CTO, SAT-8). All rule content and wording stays draft until consultant sign-off (P20).

## Decision
- One reference matcher: `engine.rules.evaluate(text, ruleset)`. The guardrails runner (SAT-9) calls it; it does not re-implement matching.
- P17 is enforced in the rule loader (a non-overridable category that is overridable or not red fails to load) and at the API via `engine.rules.policy.check_override`. P25 uses `policy.hard_blocks` before a claim can be confirmed. A brand setting or request flag cannot flip either.
- P23 gate (`engine/product_type.py`) has three states: `allowed`, `refused`, `needs_review`. `needs_review` covers weak signals such as "Ayurveda-inspired" with no brand declaration of "cosmetic". It does not proceed. A declared "cosmetic" can resolve weak signals but never overrides a hard signal. A clean pass means "no non-cosmetic signals found", not "this is a cosmetic".
- Output wording is "No flagged risks under rule set vX. Not legal advice." The rule-set label comes from `engine/rules/meta.yaml`. Nothing says "compliant".
- The consultant pack in `docs/consultant-pack/` is generated from the rules by `python -m engine.rules.pack`; a test fails if it is stale.

## Known gaps (follow-ups)
- All citations are UNVERIFIED and the DMR disease list was written from memory (P16). Verification is a human step (SAT-24).
- English only; no look-alike character folding; matching is on words, not meaning.
- The API layer (not yet built) must call `check_override`, `require_cosmetic` and `hard_blocks`; add API tests when it lands.
