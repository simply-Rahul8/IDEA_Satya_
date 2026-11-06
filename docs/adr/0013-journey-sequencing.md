# ADR-13: Order of the missing journey screens; `api/` stays a stub; citation fixes are DRAFT-only

Status: accepted (CTO, SAT-35). Builds on ADR-12 (preview-only review state) and the SAT-23 QA report (`docs/qa/sat-23/REPORT.md`, must-fix 3).

## Context
QA found the engine, rules, export gate and public checker work, but the app only serves `/check`, the review page and `/healthz`. Sign-in, brand setup, audit, claim confirmation, generate, Hindi, export, print report and the heat-strip are not wired, so the journey in PLAN section 3 cannot run end to end. Three fix tasks are already open from the same report: SAT-32 (review layout and UX, incl. the confirm control), SAT-33 (Hindi disclaimer blocks export), SAT-34 (auth, CSRF, scoping, claims RLS, rate limiter, body size).

## Decision
1. **Sequence (one owner per task, blockers are real `blockedByIssueIds`):**

   | Task | Owner | Blocked by | Needs board user's templates |
   |---|---|---|---|
   | SAT-36 Rules: citation fixes, DRAFT-only | Rules & Compliance | none | no |
   | SAT-37 Engine: catalogue audit service | Engine | none | Nykaa/Amazon importers wait for SAT-4; Shopify CSV and paste do not |
   | SAT-38 Platform: workspace-scoped persistence, remove `demo.seed` | Platform | SAT-34 | no |
   | SAT-39 Frontend: sign-in, consent, brand setup | Frontend | SAT-34, SAT-38, SAT-32 | no |
   | SAT-40 Frontend: audit screens and heat-strip | Frontend | SAT-37, SAT-39 | no |
   | SAT-41 Frontend: Product Truth, claim confirmation, generate | Frontend | SAT-40, SAT-38 | no |
   | SAT-42 Indic: Hindi step in the web flow | Indic | SAT-33, SAT-41 | no (native reviewer SAT-5 signs off the copy, not the build) |
   | SAT-43 Export: export and print-report screens | Export | SAT-41, SAT-33 | **Nykaa XLSX stays in SAT-29, blocked on SAT-4** |
   | SAT-44 QA: re-run of SAT-23 fixes | QA | SAT-32, SAT-33, SAT-34 | no |
   | SAT-45 QA: write `verify-satya`, full journey review | QA | SAT-40, SAT-41, SAT-42, SAT-43 | no |

   The Frontend tasks are chained on purpose: they share `web/templates` and `web/review.py`, and parallel branches would conflict.
2. **No standalone `api/` task.** v1 is HTML over HTMX. The audit step, cells and rows endpoints are specified under `web/` (`screen-audit.md` section 1), so nothing in the v1 journey consumes a JSON API. `api/` stays an empty package until a consumer exists (Shopify app in v1.1, or a marketplace push). A JSON API with no consumer is scope creep against the PLAN cut list, and it widens the attack surface QA just flagged.
3. **`verify-satya` is written by QA (SAT-45)**, as `scripts/verify_satya.py` plus `docs/qa/verify-satya.md`, once the journey exists. It runs on `SATYA_LLM=mock`.
4. **The SAT-31 pre-review fixes are citation text only (SAT-36).** `G.S.R. 426(E)` becomes `763(E)`; EN-DMR-003 keeps its red, non-overridable behaviour while its text stops claiming a DMR Schedule basis (premature greying is not in the Schedule); EN-CLAIM-009 drops the Cosmetics Rules cite (no SPF provision). The rule-set version bumps to 0.1.1-draft. Phrase widening, new rules and the non-Schedule EN-DMR-001 conditions wait for the consultant (SAT-24): the pre-review used mirrors and secondary sources, and a locked rule must not be edited on an agent's reading.

## Consequences
- The persistence swap (SAT-38) is the critical path for every screen after sign-in. Its Supabase side cannot be exercised without a project, so it ships tested against a fake client with human steps listed in `docs/deploy.md`.
- Live LLM mode, real Supabase, the Nykaa template and consultant sign-off remain Blocked criteria in QA's final report, not defects.
- Legal Metrology "r.10" in PLAN section 3 is probably Rule 6(1) and 6(10) (pre-review 1c). The audit shows the missing-fields flag without a rule number until the Gazette text is checked.
