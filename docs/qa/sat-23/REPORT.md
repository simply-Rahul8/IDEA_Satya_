# SAT-23 QA review: verdict

Rule set under test: v0.1.0-draft (draft until consultant sign-off, P20). Nothing here says "compliant"; output is "no flagged risks under rule set v0.1.0-draft" only.
Reviewed at `3960374` (main merged with SAT-21), `SATYA_LLM=mock`.

**Verdict: ADVERSE.** The built pieces (engine, rules, export gate, public checker) work. The product is not yet a shippable flow, and one built page has a layout defect.

## Evidence
- `python scripts/run.py test`: 432 passed. `ruff check` and `ruff format --check`: clean.
- Lighthouse mobile (simulated, Chrome 156): checker perf 100 / a11y 100 / best-practices 81 / SEO 90 (LCP 0.9 s, TBT 90 ms, CLS 0). Review perf 97 / a11y 100 / BP 81 / SEO 90 (LCP 1.2 s, TBT 190 ms, CLS 0). Reports: `lighthouse-*-mobile.html`. Fast 3G and axe not run.
- Engine end-to-end probe: `engine_e2e_probe.py`. Security probes: curl against `uvicorn asgi:app` (commands in the task comment).

## Must-fix
1. **Review page layout is broken at >=48rem (desktop).** `web/components/sentence_row.html:77` renders only `highlight_field` and `live()` inside `.row`, but `web/static/src/final-parts.css:32-33` makes `.row` a two-column grid (2rem gutter + content) at >=48rem and nothing renders the `.gut` element. The editable sentence lands in the 2rem column, so text wraps a syllable per line ("Ro/se/wa/ter") while chips span the wide column. Repro: open `/packs/demo/review` at 1280 px (`review-1280-dark-layout-bug.png`). The same defect is visible in the committed `docs/design/built/review-1280.png`. Owner: Frontend (SAT-21). Try fix: render the gutter element, or keep one column.
2. **A Hindi pack can never be exported.** `translate_pack` appends the Hindi disclaimer as a `legal` sentence with no anchors. `verify_pack` then flags it `ANCHOR-MISSING` (red, non-overridable) and `export_csv` raises `ExportBlocked: warnings_storage[2]: red ANCHOR-MISSING`. Unverified, export is blocked too, so there is no path. Repro: last block of `engine_e2e_probe.py`. Owners: Indic/Engine. Try fix: treat the system-added fixed disclaimer as exempt from the anchor rule and add a test that a verified Hindi pack exports. Do not weaken ANCHOR rules for user text.
3. **Most of the journey is not built into the app, so `verify-satya` could not run end to end.** Present: `GET/POST /check`, `/rules/{id}/sheet`, `/packs/{id}/review` and its actions, `/healthz`. Missing: sign-in and consent, brand setup, upload/paste audit and risk report, product-type gate UI, claim confirmation (the review page has no confirm control, so the demo pack can never be approved: 3 blocked remain), generate, Hindi, export and print report, audit heat-strip, any `api/` routes. The `verify-satya` skill does not exist in the repo or skill store, so I scripted the engine path instead (`engine_e2e_probe.py`). ADR-12 says this is known and preview-only; recorded as Blocked criteria, not a regression.
4. **No authentication, CSRF protection or per-user scoping on state-changing routes.** `POST /packs/demo/approve` and `/sentences/*/check|keep|edit-reason|report` return 200 for a request with `Origin: https://evil.example` and no cookie or token; one unauthenticated call rewrote the shared demo pack. The store is one process-global dict with guessable IDs. ADR-12 forbids deploying it; this is the gate. When Platform wires auth: CSRF (token, or SameSite plus Origin check), workspace-scoped lookups, and a test for each.
5. **A signed-in member can bypass P25 at the database.** `claims_rw` (`supabase/schema.sql:280`) is `for all` with no column limits and Supabase exposes PostgREST, so a member can run `update claims set hard_blocked=false, status='confirmed'`; the only DB check (`hard_block_not_confirmed`) is satisfied by that update. Evidence rules and hard blocks are enforced only in Python. Owner: Platform. Try fix: revoke update on those columns from `authenticated` (or add a trigger) and confirm through the backend. Fix before any deploy.

## Should-fix
1. **Rate limiting trusts a spoofable IP and is per process.** Locally uvicorn trusts `X-Forwarded-For` from 127.0.0.1: 125 posts with a different XFF each never hit the limit, while 130 without it gave 118 x 200 then 12 x 429. On Vercel the header handling differs and an in-memory limiter is per instance. Pick one trusted source and use `engine.ratelimit.hit`. Only `/check` is limited; review POSTs and any future LLM route are not.
2. **Red-override evidence is free text.** `keep` accepts reason `a` as evidence for an overridable red (ADR-12 item 4 acknowledges it). The engine export gate still blocks the red, so export fails closed today.
3. **Schema gaps** (partly in ADR-8): child rows are not tied to their parent's workspace (composite FK); `evidence.file_path` is unvalidated and the schema defines no Storage bucket or storage RLS, which must exist before uploads ship. Upload handling is Blocked: no upload route exists, so size, type and CSV-import checks could not be run.
4. **`form_data` reads the whole body before checking its size** (`web/app.py`), so the 64 KB cap does not bound memory. A 70 KB body correctly returns 413. `/openapi.json` and `/docs` are public.
5. **Live extraction and prompt-injection not exercised.** The mock extractor puts the whole pasted listing into `product_name` and finds no claims, so the pack repeats that text in every section. That is mock behaviour. The injected "IGNORE ALL PREVIOUS INSTRUCTIONS" text had no effect in mock mode; by inspection the prompts wrap listing text as escaped JSON inside `<untrusted_data>`. Needs one live-mode check by the owner (no keys here).
6. **360 px layout not independently confirmed.** Headless Chrome has a minimum window width, so my 360 px screenshots were clipped. Lighthouse mobile passed and the Frontend's own 360 px screenshots exist, but a real device-emulated 360 px run should be recorded.

## Nice-to-fix
- Lighthouse best-practices 81: "Fenced Frame API deprecated" warning on both pages; no meta description (SEO 90); `label-content-name-mismatch` on `.chip-claim` buttons (aria-label does not start with the visible text).
- No gzip in the app (163 KiB and 204 KiB transferred locally); fine if the host compresses, confirm on the preview.
- `rate_limit_hit` prunes on every call; fixed window allows a 2x burst at the boundary.

## Passed (with evidence)
- Strict CSP, no inline script or style except the hashed theme snippet; `nosniff`, `no-referrer`, `no-store`. Reflected `<script>`, `<img onerror>`, `<svg onload>` in `/check` text came back escaped.
- Non-overridable rules hold over HTTP and in the engine: `keep` on EN-DRUG-001 and on the "approved by dermatologists" flag returns 403; `override_flag` on a red raises `ReviewError`; confirming a hard-blocked claim, and a test-report claim without reference, raise.
- Approve fails closed on a blocked pack; export of an unapproved or red pack raises `ExportBlocked`.
- CSV export neutralises formula injection (`'=HYPERLINK(...)`) and writes the audit record with a SHA-256.
- Checker is deterministic (no provider import), caps text at 5,000 characters, returns 429 with `Retry-After` for a single IP, 413 for oversize bodies, 404 for unknown pack or sentence.
- RLS enabled on every tenant table; helper functions revoked from anon and authenticated; `rate_limits` has no policies; `is_member` is `security definer` with a pinned search_path.
- Lighthouse mobile >= 90 on performance and accessibility for both pages.

## Design critique
Job: a catalogue owner at a D2C beauty brand checks listing copy, then reviews and approves a fixed pack. Strengths to keep: calm editorial palette, severity never by colour alone (icon plus label), clear gate line ("3 blocked and 1 needs a reason before you can approve"), progress strip, honest draft wording ("not a legal sign-off", "draft rule set").
- Must-fix: the review layout bug above.
- Should-fix: the primary job dead-ends on the review page. A blocked-anchor row offers only "Open in Product Truth", and the ledger has no confirm control. "Approve pack" looks disabled but is clickable; say why on the button or keep the reason adjacent. A flagged row stacks three boxes (anchor chip, anchor flag, rule flag) for one sentence, which is a long scroll at 360 px; fold the anchor flag into the chip.
- Nice-to-fix: record a light-theme contrast check alongside the dark one (headless defaulted to dark; a11y passed there).

## Routing
Frontend: Must 1, Should-fix design items, Nice-to-fix. Indic/Engine: Must 2, Should 5. Platform: Must 4 and 5, Should 1, 3, 4. Engine: Should 2. CTO: order the missing journey screens and a real `verify-satya` skill, then request a re-run of this review. SAT-29 (Nykaa mapping) gets the short follow-up review when it lands.
