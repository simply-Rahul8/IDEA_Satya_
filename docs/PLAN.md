# Plan v2.1: Satya MVP, a claim-safe beauty listing engine for India

## Context
Satya re-targets the doc-only "AI Content Engine" repos to India. It generates product-page copy anchored to a Product Truth record, checks it against Indian regulatory guardrails, outputs Hindi, and exports to marketplaces.
- **v2:** fixed the problems the review raised (P1–P19).
- **v2.1:** adds the essential changes from the dependency review (P20–P30), cuts v1 scope to fit a 7-week timeline, and specifies execution by a **Paperclip agent company**: a CEO and a CTO orchestrate, one agent owns each task. The frontend gets an explicit "awestruck" design bar.

**Decisions locked:**
- FastAPI + Jinja2 + HTMX from a single deploy, with Alpine.js for small interactions.
- A cosmetics-regulatory consultant reviews the rules before any brand-facing output.
- India-first, text-only, English UI, English and Hindi output.
- Supabase in Mumbai, Vercel in bom1.
- Code lives in a **new private repo `satya`**.

---

## 1. Issue register
### Carried from v2 (fixed)
| # | Fix |
|---|---|
| P1 | UI: FastAPI + HTMX (light on slow 4G, single deploy, nothing thrown away later) |
| P2 | Audit-first flow; LLM pre-fills Product Truth from the brand's own listings |
| P3 | Build and recruit in parallel; the public checker is the outreach hook |
| P4 | Two-pass claim anchoring: deterministic checks, then a separate verifier call |
| P5 | Blind A/B quality test (target ≥60% win or tie) |
| P6 | Early Hindi lexicon: Devanagari, transliterated and Hinglish forms, NFC normalisation |
| P7 | 3-month prepaid commitment (₹2,997) as the revenue test |
| P8 | Fallbacks for providers, translation and bulk uploads |
| P9 | Rate limits; separate keys per environment |
| P10 | "Not legal advice"; rule-set version shown; every rule cites its source |
| P11 | Stepwise, client-driven bulk jobs (Vercel Hobby cron runs only once a day) |
| P12 | DPDP basics for brand users' accounts |
| P13 | Protected-term placeholders around translation |
| P14 | Vercel region bom1 |
| P15 | Clean up the old repos |
| P16 | Week-0 regulatory verification |
| P17 | Drug, disease (DMR) and fairness blocks can't be overridden |
| P18 | Public checker is deterministic only, with caps |
| P19 | Uploaded text is treated as data (prompt-injection hygiene) |

### New in v2.1 (essential)
| # | Problem | Fix |
|---|---|---|
| P20 | Brand-facing reports were scheduled in the same week as the consultant review | Consultant sign-off is a **hard blocker** for the public checker and any audit report a brand sees. Book in week 0, review done by end of week 2 |
| P21 | Building in the public portfolio repo would expose the lexicon and prompts | New **private** repo `satya`. The old public repos become portfolio pointers |
| P22 | Precision and recall can't be measured without labels | Label the 50-PDP corpus sentence by sentence (safe / 🟠 / 🔴 + rule ID) in weeks 1–2. Consultant spot-checks it. This blocks the benchmark |
| P23 | One rule set would flag legitimate drug claims | **Product-type gate:** v1 handles cosmetics only. Ayurvedic, AYUSH and OTC-drug products are refused with an explanation |
| P24 | Single-word blocking causes false positives ("for acne-prone skin" is fine) | Rules match **verb + condition** patterns, plus a safe-phrase allowlist. Every rule has positive and negative test examples |
| P25 | Extraction could launder risky claims into the approved set | Claims that hit a hard block **can't be confirmed**. "Test report" evidence needs a reference (file upload or document ID) |
| P26 | No way to measure cost or debug | `llm_calls` table (provider, model, tokens, ₹ cost, latency, prompt version, outcome) plus Sentry free tier |
| P27 | Vercel Hobby is non-commercial; Supabase free projects pause after a week idle | Move to **Vercel Pro (~$20/mo) and Supabase Pro (~$25/mo) before taking any prepayment.** Budget ~$45/mo plus LLM |
| P28 | Supabase's built-in email only sends to project team members | Custom SMTP (Resend free tier) in week 4, or Google sign-in only |
| P29 | Real marketplace templates may not arrive in time | Fallback: generic CSV plus a column-mapping screen |
| P30 | No way to collect the prepaid test | Manual UPI or bank transfer plus a simple invoice (below the GST threshold). Decided in week 0 |
| P31 | Prompt or model changes can silently regress quality | The benchmark becomes a repeatable script (`make bench`), required before every deploy |

### Cut from v1 to fit 7 weeks solo
- PDF reports → a print-friendly page (save as PDF from the browser).
- Shopify JSON export → v1.1, with the Shopify app.
- Second Indic language → Hindi only.
- Hindi UI → English UI.
- Amazon exporter → only if templates arrive. Otherwise Nykaa plus generic CSV.

---

## 2. Who it's for and the job
- **User:** the catalogue or content owner at an Indian D2C beauty brand with 20–500 SKUs, selling on its own site plus Nykaa and/or Amazon.
- **Job:** *"Show me which listings could get my CDSCO registration or marketplace listing pulled, fix them with claim-safe English and Hindi copy, and export straight into my seller sheet."*

## 3. MVP v1 user journey
1. **Sign in:** Google, or email OTP through custom SMTP. Consent at signup. One brand workspace.
2. **Brand setup:** tone (3 presets), restricted phrases, seller legal name, address and grievance contact.
3. **Audit:**
   - Upload a Shopify product CSV, a Nykaa or Amazon catalogue download, or paste text.
   - Each product gets a risk report: 🔴 with rule citations, 🟠 warnings, missing Legal Metrology r.10 fields.
   - Products are sorted by risk. A print-friendly report is stamped "not legal advice · rule set vX".
4. **Product-type gate:** cosmetic → continue. Anything else → out-of-scope notice (P23).
5. **Fix with Satya:**
   - The LLM extracts a Product Truth draft. Every claim starts unconfirmed.
   - The user confirms each claim with an evidence type. Hard-blocked claims can't be confirmed, and "test report" claims need a reference (P25).
6. **Generate the PDP pack:** title, 5 bullets, description, how to use, warnings and storage, SEO meta. Every sentence carries an anchor and a type.
7. **Review:**
   - Anchor, flag, reason, citation and a suggested rewrite per sentence.
   - Live re-check as the user edits.
   - 🔴 blocks approval. 🟠 needs a reason.
   - 👎 sends a wrong-flag report to the tuning queue.
8. **Hindi:** protected terms, the Hindi lexicon re-run, and the disclaimer in the same language.
9. **Export:**
   - Nykaa XLSX (from the real template), Amazon only if its template arrives, generic CSV with column mapping, copy to clipboard.
   - The audit record goes with every export.
10. **Public "Is my claim safe?" page:** deterministic only, no login, citations shown, goes live **only after consultant sign-off**.

**Not in v1:** AI images, reviews, influencer content, competitor scraping, campaigns, social and email copy, WhatsApp, Shopify app, marketplace API push, consumer data, automated billing, non-cosmetic products, non-India rule packs, PDF and Shopify JSON exports, second Indic language, Hindi UI.

## 4. Frontend: the "awestruck" bar (within the light HTMX stack)
- **Direction:**
  - A premium, calm, trustworthy "compliance meets beauty" look.
  - Warm neutral base, one confident accent, generous whitespace, editorial serif display type paired with a highly legible sans.
  - Designed around Indian beauty retail rather than generic SaaS.
- **Signature moments:**
  1. **Public checker:** as the user types or pastes copy, risky phrases highlight inline with animated underlines. The verdict card animates in with a severity meter. Each citation opens as a calm side sheet. This is the shareable wow moment and the outreach hook.
  2. **Audit dashboard:** a risk heat-strip across the catalogue, counters that animate on load, and sort and filter without page reloads.
  3. **Review screen:** sentence-level anchor chips. Clicking one highlights the source claim. Edits re-check in under 300 ms (HTMX partial). Flags resolve with a satisfying micro-transition.
- **Constraints:**
  - Under 150 KB of JS+CSS per page: Tailwind (purged) + HTMX + Alpine.js, no SPA framework.
  - LCP under 2.5 s on Fast 3G.
  - WCAG 2.2 AA.
  - Never colour alone: every flag has an icon and a label.
  - `prefers-reduced-motion` respected.
  - Light and dark themes.
  - Mobile-first at 360 px.
- **Process:**
  - Design system and tokens via `/design-consultation`.
  - 3 variants of the checker and review screens via `/design-shotgun`. **You pick.**
  - The chosen design becomes Jinja components.
  - `/design-critique` and `/design-review` passes, plus a Lighthouse run on mobile.

## 5. Architecture
```
Browser (HTMX + Alpine, Tailwind, <150KB)
   │  HTML partials over HTTPS
FastAPI on Vercel bom1 (asgi.py) ─ web/ (Jinja components) · api/ (JSON) · engine/
   │                  │                         │                    │
 Sarvam 105B /    IndicTrans2 (Cloudflare)   Supabase ap-south-1    Sentry
 Claude failover  Sarvam Translate fallback  Postgres+Auth+Storage
```
- **Repo:** private `satya`.
- **Layout:** as in v2:
  - `engine/{models, rules/*.yaml, normalize, guardrails, verifier, extract, prompts, providers, translate, pipeline, export, jobs}`
  - `web/`, `api/`, `asgi.py`, `vercel.json` (bom1), `supabase/schema.sql`, `tests/`, `data/corpus/` (labelled), `data/samples/`
- **Added:**
  - `engine/telemetry.py` (`llm_calls`)
  - `engine/product_type.py`
  - `bench/` (`make bench`)
  - `web/components/` (design system)
- **Data model:** the v2 tables, plus `llm_calls` and `evidence` (file reference or document ID per test-report claim).
- **Bulk jobs, failure handling, security and limits:** as in v2 §4.3–4.5.

## 6. Guardrails
As in v2 §5, with three changes:
- verb + condition patterns plus an allowlist (P24);
- the product-type gate (P23);
- guards on confirming extracted claims (P25).

Each rule must ship with at least one positive and one negative example, both in tests.

## 7. Legal, DPDP, trust, cost
- Legal and DPDP as in v2 §6.
- **Consultant sign-off gates brand-facing output (P20).**
- Paid infra tiers before any prepayment (P27).
- Manual UPI plus invoice for the prepaid test (P30).

## 8. Execution as a Paperclip agent company
**Setup:**
- A local Paperclip instance (`npx paperclipai@latest onboard`) in authenticated mode.
- Company **"Satya"**, whose goal is this plan file.
- `requireBoardApprovalForNewAgents: true`.
- A per-agent monthly budget cap.
- Heartbeats wake on demand, with an interval of 30 min or more.
- Agents run the `claude_local` adapter (Claude Code) on the private `satya` repo, each in its own git workspace or branch.

**Org chart:** one owner per task.

| Agent | Reports to | Owns (one task) | Blocked by |
|---|---|---|---|
| **CEO** | Board (you) | Orchestration. Turns this plan into tasks with real `blockedByIssueIds`. Weekly status. Business tasks such as the outreach list and draft emails. **Drafts only: you send** | — |
| **CTO** | CEO | Technical orchestration. Repo scaffold, architecture decisions, code review, merges to `main` | — |
| Rules & Compliance agent | CTO | EN rules (verb+condition, allowlist, citations, tests), product-type gate, consultant review pack | — |
| Engine agent | CTO | Models, guardrails runner, extraction, generation, verifier, providers with failover, `llm_calls` | Scaffold |
| Evaluation agent | CTO | Draft labels for the 50-PDP corpus, `make bench`, model choice report, A/B pair prep | Engine (bench only) |
| Indic agent | CTO | Translation with protected terms, Hindi lexicon draft, normalisation | Engine |
| Design agent | CEO | Design system, tokens, 3 variants per signature screen → **your pick** → final specs | — |
| Frontend agent | CTO | Jinja/HTMX/Alpine components and pages to spec; performance and accessibility budget | Design pick, Engine API |
| Platform agent | CTO | Supabase schema, RLS, auth, SMTP, jobs, rate limits, Sentry, Vercel bom1 deploy (preview) | Scaffold |
| Export agent | CTO | Nykaa exporter, CSV with column mapping, audit record, print report | Templates (you), Engine |
| QA Reviewer agent | CEO | Independent review tasks: `/qa-acceptance`, `/design-critique`, security review, `verify-satya`. Publishes verdicts on its own task | Each feature it reviews |

**Human tasks** (assigned to you on the board):
- book the consultant;
- collect templates;
- find the Hindi native reviewer;
- send outreach;
- collect payments;
- approve design variants;
- approve production deploys and pushes to public repos.

**Approval gates (board = you):**
- new hires;
- design pick;
- consultant sign-off recorded before checker and report go-live;
- any production deploy;
- any push or PR to the old public repos;
- any external email or message;
- any spend change.

## 9. Timeline (week 0 + 7 weeks)
| Week | Agents | You / humans |
|---|---|---|
| 0 | CEO turns the plan into tasks. CTO scaffolds the private repo | Book consultant. Templates. Hindi reviewer. Payment method. Outreach list review |
| 1 | Rules, Engine, Platform, Design (system + variants) start in parallel. Evaluation labels the corpus | Pick design variants |
| 2 | Engine and verifier, bench and model choice, Indic | **Consultant reviews rules and spot-checks labels** |
| 3 | Frontend checker and audit screens. Export | Consultant sign-off, then checker go-live on preview |
| 4 | Frontend review screen, Platform auth/SMTP/jobs | Outreach with the checker (you send) |
| 5 | Integration, deploy (prod after your approval), QA review, Lighthouse | Book 5–10 pilot brands. Upgrade to paid tiers |
| 6 | Bug fixes | Pilot onboarding, blind A/B |
| 7 | Read-out report (CEO) | Prepaid ask, go/no-go |

Old-repo cleanup (P15) is a CTO side task in week 1. It is branch-only until you approve the push.

## 10. Success metrics
| Area | Target |
|---|---|
| Audit | ≥70% of pilot brands find an unknown 🔴 or missing field |
| Quality | ≥60% A/B win or tie |
| Safety | 0 🔴 in exports. Precision ≥90% and recall ≥95% on the labelled corpus |
| Friction | ≥80% approved with light edits. Overrides <15% |
| Cost | <₹1 per PDP (measured from `llm_calls`) |
| Frontend | Lighthouse mobile ≥90 for performance and accessibility. Checker LCP <2.5 s on Fast 3G |
| Revenue | ≥3 brands prepay ₹2,997 |

## 11. Roadmap after v1
| Version | Scope |
|---|---|
| v1.1 | Shopify app (+ JSON export), QStash jobs, Razorpay with GST, more Indic languages, Hindi UI, PDF reports, Amazon exporter (if deferred) |
| v1.2 | Team roles, marketplace rejection learning, regulatory feed, lexicon tuning from 👎 |
| v2 | Competitor intake, whitespace analysis, campaigns, social/email/ad copy, anti-imitation |
| v2.x | WhatsApp, more marketplaces, API push |
| v3 | Label OCR, AI imagery with ASCI labels, ingredient safety, dossier store |
| v3+ | EU, Nordic and GCC rule packs |

## 12. Verification
- **pytest:**
  - every rule has positive and negative examples (EN and HI);
  - non-overridable blocks are enforced at API level;
  - product-type gate;
  - claim-confirmation guards;
  - protected-term round-trip;
  - provider failover;
  - job resume;
  - RLS isolation;
  - golden-file exports.
- **`make bench`** on the labelled corpus. Its precision, recall, cost and latency report gates deploys.
- **`verify-satya`** drives the deployed app end to end in a real browser: audit → fix → generate → review → Hindi → export, plus the public checker.
- Lighthouse mobile on the checker, audit and review pages.
- QA Reviewer verdicts are recorded on their own Paperclip tasks.
- Consultant sign-off and native-speaker review are recorded in `rules/README.md`.
