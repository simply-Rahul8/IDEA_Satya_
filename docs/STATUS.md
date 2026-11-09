# Satya — project status & handoff

**As of:** 2026-11-09 · **HEAD:** `f16bdec` (`main`) · **Tests:** 669 passing (`SATYA_LLM=mock`)

Satya is a claim-safe beauty product-listing engine for Indian D2C brands. Full plan: `docs/PLAN.md` (v2.1).
This file is the honest state of the build: what's finished in code, what's left (and *why* it's left), and
what you can safely change when you pick it back up.

> **One rule carried from the plan:** regulatory content (rules in `engine/rules/*.yaml`, disclaimers, report
> wording) stays **draft** until a cosmetics-regulatory consultant signs off. Never label output "compliant" —
> use *"no flagged risks under rule set vX"*. The drug / disease (DMR Act) / fairness blocks are non-overridable;
> do not weaken them to make a test pass.

---

## 1. What is DONE (built, tested, in `main`)

The full MVP engine and UI exist and pass tests. Nothing below needs rebuilding.

### Engine (`engine/`)
| Area | Module | State |
|---|---|---|
| Data models | `models/` | Product Truth, PDP pack, evidence, audit records |
| Guardrails | `guardrails/`, `rules/*.yaml` | verb+condition matching, safe-phrase allowlist, every rule has +/- test examples |
| Non-overridable blocks | `guardrails/` | drug/treatment, DMR Act diseases, fairness — enforced at API level |
| Product-type gate | `product_type.py` | cosmetics pass; Ayurvedic/AYUSH/OTC refused with explanation |
| Claim extraction | `extract/` | LLM pre-fills Product Truth; claims start unconfirmed; hard-blocked claims can't be confirmed |
| Generation | `pipeline/`, `prompts/` | title, 5 bullets, description, how-to-use, warnings, SEO meta — each sentence anchored |
| Verifier | `verifier/` | two-pass claim anchoring (deterministic checks, then separate verifier call) |
| Providers | `providers.py` | failover; `SATYA_LLM=mock` runs with no network/keys |
| Hindi | `translate/`, `normalize/` | protected-term round-trip, Hindi lexicon, NFC normalization |
| Telemetry | `telemetry.py`, `observability.py` | `llm_calls` (provider, model, tokens, ₹ cost, latency, outcome) |
| Rate limiting | `ratelimit.py` | per-key limits; `--no-proxy-headers` hardening (SAT-50) |
| Export | `export/` | generic CSV + column-mapping, audit record per export, print report, formula-injection neutralized |
| Marketplace layouts | `export/marketplaces.py` | **best-effort** Nykaa + Amazon India beauty presets (SAT-29) — see §3 |
| Jobs | `jobs/` | stepwise client-driven bulk jobs with resume |

### Web (`web/`) — FastAPI + Jinja + HTMX + Alpine + Tailwind
- `checker.py` — public "Is my claim safe?" page (deterministic only, no login)
- `audits.py` — audit dashboard with risk heat-strip
- `fix.py` / `review.py` — claim confirmation + sentence-level review with live re-check
- `hindi.py` — Hindi output route
- `export.py` — export + column-mapping screen (the marketplace presets appear here automatically)
- `auth.py` / `account.py` — Google + email-OTP sign-in scaffold, DPDP consent
- `security.py` — security headers

### Docs & process
- `docs/PLAN.md`, `docs/ARCHITECTURE.md`, `docs/adr/` (architecture decisions), `docs/deploy.md`
- `docs/board-pack/` — ready-to-send drafts for the human-gated tasks (see §2)

---

## 2. What is LEFT — and why I could not finish it

**These are not code tasks.** Every item below is a real-world action, a credential, or a business/legal
decision that is yours by design (the plan's "human tasks" and "approval gates"). No agent can honestly
complete them, and the progress bar cannot reach 100% through code alone.

| Task | What it actually requires | Draft prepared for you |
|---|---|---|
| **Consultant sign-off** (SAT-14) | A cosmetics-regulatory consultant reviews the rules and signs. **This gates the public checker and any brand-facing report going live.** It must not be fabricated. | `docs/board-pack/consultant-signoff-template.md` |
| Book consultant (SAT-3) | Contact + engage a real consultant | `docs/board-pack/consultant-outreach.md` |
| Send review pack (SAT-24) | Email the consultant the pack | `docs/consultant-pack/` |
| Real marketplace templates (SAT-4) | Download YOUR Nykaa/Amazon seller templates (behind the seller panel) | see §3 |
| Supabase + OAuth (SAT-49) | Your Supabase project: redirect URL, Google OAuth keys, OTP smoke test | — |
| Live preview security checks (SAT-53) | Run against your deployed preview | `docs/board-pack/sat-53-runbook.md` |
| Prepayment method (SAT-6) | Decide how you collect ₹2,997 (UPI/bank + invoice) | `docs/board-pack/prepayment-plan.md` |
| Hindi native reviewer (SAT-5) | Find + engage a native speaker | `docs/board-pack/hindi-reviewer-outreach.md` |
| Outreach (SAT-16/17) | Review & send — **blocked until the consultant signs off** | drafts in board-pack |

**Fastest real path to shipping (~30 min of your time):** send the consultant email
(`docs/board-pack/consultant-outreach.md`), and set up Supabase with `docs/board-pack/sat-53-runbook.md`.
Those two unlock the public checker and the deploy.

---

## 3. What can be MODIFIED (safe change points)

Things built intentionally to be swapped or tuned later:

1. **Marketplace export headers** — `engine/export/marketplaces.py`
   The Nykaa/Amazon layouts are **best-effort guesses**, marked `placeholder=True` because the real seller
   templates aren't public. When you have a real template, replace that layout's `columns` with the exact
   headers and drop `placeholder=True`. The mapping screen (`web/export.py`) already lets a seller reconcile
   headers before export, so a wrong guess never ships silently. **Tests to keep green:** `tests/test_marketplaces.py`.

2. **Guardrail rules** — `engine/rules/*.yaml`
   Tunable *within* the draft/sign-off rule, but: (a) every rule needs one positive + one negative test example,
   (b) never weaken the non-overridable drug/disease/fairness blocks. Bump the rule-set version string when you change rules.

3. **Hindi lexicon** — `engine/translate/` / `engine/normalize/`
   Draft until a native speaker reviews (SAT-5). Add terms, but keep the protected-term round-trip test passing.

4. **Prompts & model choice** — `engine/prompts/`, `engine/providers.py`, `docs/model-choice-report.md`
   Swap models/prompts freely; keep `SATYA_LLM=mock` working with no network.

5. **Design / frontend** — `web/components/`, `web/templates/`, `web/static/`
   Theme and layout within the budget: <150 KB JS+CSS per page, WCAG 2.2 AA, works at 360px, respects
   `prefers-reduced-motion`.

6. **Repo visibility** — the repo is currently **PUBLIC**. Plan P21 wanted it private (the lexicon + prompts
   are exposed). Flip with: `gh repo edit simply-Rahul8/IDEA_Satya_ --visibility private`.

### Don't change without care
- The non-overridable blocks (drug/treatment, DMR diseases, fairness).
- The "draft until sign-off" gate on the public checker and brand reports.
- Secrets handling: keys only from env vars, placeholders in `.env.example`, never commit a real `.env`.

---

## 4. Running it

```bash
# tests (no network, no keys)
SATYA_LLM=mock uv run python scripts/run.py test
# lint
uv run ruff check
```

Local dev + deploy steps: `docs/deploy.md`. Architecture: `docs/ARCHITECTURE.md`.
