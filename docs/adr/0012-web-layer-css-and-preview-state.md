# ADR-12: Web layer ships plain CSS; review state is in-memory and preview-only

Status: accepted (CTO, SAT-21 review). Builds on ADR-10 (strict CSP, red overrides).

## Context
SAT-21 built checker A and review B. Two choices differ from the letter of AGENTS.md / the spec: no Tailwind build, and a process-local `PackStore` seeded with a demo pack.

## Decision
1. **No Tailwind for v1.** The spec's reference CSS is concatenated and minified in `web/assets.py` (6.5 KB gzip; page JS+CSS 50-53 KB gzip against the 150 KB budget). There is nothing to purge, no Node toolchain on a Windows host, and a test asserts severity classes are present in the built CSS. Revisit only if the CSS outgrows the budget.
2. **Review state is preview-only.** `web/review.py` `PackStore` and `web/demo.py` are in-process and unauthenticated. They must not be deployed. Platform (SAT-10) replaces the store with Supabase and RLS-scoped access, and `demo.seed()` is removed in that change. Deploy stays behind consultant sign-off and board approval (P20).
3. **Red overrides stay in the web layer for now** (engine `override_flag` refuses all reds). Policy is still enforced server-side via `check_override`, and the engine export gate (SAT-22) still sees the unresolved red, so export fails closed. Engine owner to add red-override-with-evidence before export is wired to the review screen.
4. **Evidence reference is free text today.** Validation against uploaded documents arrives with Platform file storage.

## Consequences
- Follow-ups: Platform swaps the store and rate limiter (`engine.ratelimit.hit`); Engine adds red override and `suggested_rewrite`; Platform confirms the "nothing stored" copy and `CHECKER_MAX_CHARS`; axe, Lighthouse and a Fast 3G run need the board's preview.
- Anchor flags are red and non-overridable in the engine, so those sentences show Blocked. The engine wins over the spec text.
