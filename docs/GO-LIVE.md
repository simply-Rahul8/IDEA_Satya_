# Satya — going live on Vercel

**As of:** 2026-11-13 · **Rule set:** `v0.1.3-draft` · **Hindi word list:** `hi-v0.1.0-draft` · **Tests:** 682 passing ·
**Lighthouse (mobile):** Performance 96 · Accessibility 100 · Best Practices 100 · SEO 100

This is the step-by-step to make Satya available to the public on Vercel, and an honest answer to "is it finished,
and does it really work?". The detailed infra runbook (Supabase, auth, RLS checks) stays in [`deploy.md`](deploy.md);
this document is the go-live path on top of it.

> **Two rules from the plan still apply.** Production deploys, spend changes and anything public are the board
> user's call (you). And the regulatory rules are **draft** until a cosmetics-regulatory consultant signs them off
> (plan P20): Satya never says "compliant", only "no flagged risks under rule set vX".

---

## 1. The short answer

| Question | Answer |
|---|---|
| Does the public checker work when you paste a product description? | **Yes — in English, Hindi and Hinglish.** Tested with 10 real-style listings in a real browser, in production mode (§2). |
| Is the software production grade? | **Yes, for the public checker.** Security headers on every response, designed error pages, no crashes on unconfigured features, share card, SEO files, Lighthouse 96/100/100/100, 682 tests. |
| Is it ready for the public today? | **Only the human steps are left** (§4): the consultant sign-off your plan requires, committing and pushing, and your Vercel account. |
| Fastest way to the public? | **Option A — public checker only** (§5): no database, no AI keys, ~30–45 minutes once §4 is done. |

---

## 2. What was tested, and what happened

Every test ran against the app in **production mode** (`SATYA_ENV=production`, a session secret set, no dev demo
data), installed with **only the runtime dependencies Vercel installs**. Each listing was **pasted** into the page in
Chrome through a real browser paste event — the same path as a visitor pressing Ctrl+V.

### Pasting real product descriptions

| # | What was pasted | What Satya shows | OK? |
|---|---|---|---|
| 1 | Typical risky D2C serum ("removes dark spots permanently… 2 shades fairer… dermatologist recommended… 100% chemical-free… safe for all skin types… clinically proven to reduce acne by 90%") | **High risk, 9 flagged**: "fairer skin" **blocked**; "permanently", "removes dark spots", "Dermatologist recommended", "chemical-free", "safe for all skin types", "Clinically proven", "reduce acne", "by 90%" to review | ✅ |
| 2 | Hair oil ("stops hair fall… regrows hair… prevents premature greying… removes dandruff… trusted by 1 lakh happy customers") | **Severe risk, 5 flagged**: "regrows hair" and "prevents premature greying" **blocked**; hair fall, dandruff and "1 lakh happy customers" to review | ✅ |
| 3 | A careful, well-written moisturiser listing | **No flagged risks** — no false alarms | ✅ |
| 4 | "Oil-control face wash **for acne-prone skin**… non-comedogenic" | "acne-prone skin" correctly **not** flagged; "Non-comedogenic" to review (it needs a test report) | ✅ |
| 5 | Kumkumadi Tailam (Ayurvedic oil) | Correctly **refused**: "regulated as AYUSH drugs, not cosmetics" | ✅ |
| 6 | Cream that "treats ringworm and eczema… heals infection" | **Severe risk**, both drug claims **blocked** | ✅ |
| 7 | **Hindi**: "यह क्रीम मुंहासे जड़ से ठीक करती है और त्वचा को गोरा बनाती है।" | **Severe risk**: the cure claim and the fairness claim both **blocked**, plus a note that Hindi checks are an early draft | ✅ |
| 8 | **Hinglish**: "skin ko gora banata hai aur pimples ko jad se khatam karta hai" | **High risk**: "skin ko gora" **blocked**, plus the Hindi draft note | ✅ |
| 9 | Hostile paste: `<script>`, `<img onerror>`, "ignore all previous instructions…" | Nothing ran, nothing injected; "cures acne" still **blocked** | ✅ |
| 10 | A listing over 5,000 characters | Clear notice: "Only the first 5,000 characters were checked" | ✅ |

Clicking a flag opens the written rule ("Why it is flagged"). The checker uses **no AI model**: it needs no API keys
and costs nothing per check.

### Quality, security and production behaviour

| Check | Result |
|---|---|
| Lighthouse, mobile (throttled) | Performance **96** (LCP 2.3 s, no layout shift) · Accessibility **100** · Best Practices **100** · SEO **100** |
| Console errors | None |
| Forged form post (no CSRF token) / post from another site | Refused (403) |
| Security headers on **every** response | Strict CSP, no framing (`frame-ancestors 'none'`, `X-Frame-Options`), `nosniff`, referrer policy, permissions policy (no camera, mic, location, payments), cross-origin opener policy; **HSTS** over HTTPS |
| A wrong address | Designed **404** page (scripts still get JSON) |
| An unexpected server error | Designed **500** page with no internal details; the error is still logged |
| Signed-in pages without a database (checker-only launch) | Designed **503 "Not open yet"** page — never an anonymous workspace, never a crash |
| Dev demo data in production | Never served |
| Search engines | `robots.txt` (only `/check` is crawlable) and `sitemap.xml` |
| Sharing a link (WhatsApp, LinkedIn, X) | Preview card with a real image of the checker |
| App starts with runtime dependencies only | Yes (no test or dev tools present) |
| Automated tests | 682 passing, lint and format clean |

The accuracy benchmark reports 100% precision and recall, but its labelled corpus is **synthetic** ("an upper bound,
not a real measure"). The real-listing table above is the truer picture. Build a real labelled set from pilot brands'
listings after launch.

---

## 3. What was fixed to get here

**Deploy fixes**
1. **Catalogue audits would have crashed on Vercel**: the database driver (`psycopg`) was a dev-only tool that
   production code imports. Now a runtime dependency.
2. **`vercel.json` used the old `builds` setting**, which Vercel recommends against and which can ship only the build
   output. Vercel now detects `asgi.py` itself; the file pins the **Mumbai region (`bom1`)** and keeps Git auto-deploy
   off, so every deploy is a deliberate command.

**Correctness**
3. **Hindi and Hinglish copy was told "No flagged risks."** The public checker now also runs the Hindi word list
   (Devanagari, transliterated and Hinglish), reports each claim under its English rule so the rule panel works,
   never lists a claim twice, and adds a visible note on any Hindi copy that Hindi checks are an early draft.
4. **Number claims were missed** ("by 90%", "1 lakh customers", "10,000+ women"). The statistics rule (EN-CLAIM-006)
   now catches them — but not discounts ("up to 50% off"), ingredient strengths ("10% vitamin C") or pack sizes.
   Following the rules' own procedure, the rule set moved to **v0.1.2-draft** and the consultant pack was regenerated.

**Production hardening**
5. Baseline security headers on every response, plus HSTS over HTTPS.
6. Designed 404, 403, 429, 500 and 503 pages; unconfigured sign-in is a handled 503, not a crash.
7. Favicon (the सत्य stamp), `theme-color`, canonical link, Open Graph and Twitter cards with a real share image,
   `robots.txt` and `sitemap.xml`.
8. Best Practices 82 → 100: the bundled Alpine.js read a deprecated Chrome API while scanning globals; a one-line
   patch extends Alpine's own skip list (re-apply it if Alpine is upgraded — it's noted at the top of the file).

---

## 4. Before the public uses it

### G1. Consultant sign-off on the rules (your plan's rule, P20)
Your plan says the public checker goes live **only after** a cosmetics-regulatory consultant reviews and signs the
rule set (tasks SAT-3, SAT-24, SAT-14; drafts in [`board-pack/`](board-pack/), pack regenerated at v0.1.3-draft in
[`consultant-pack/`](consultant-pack/)). Until then the page says "Draft rule set… not yet reviewed by a regulatory
consultant… Not legal advice."
- A **preview URL** for you and testers: fine now.
- **Announcing it to the public** before sign-off: your decision and your risk. Brands may act on what it says.

### G2. Native Hindi review (SAT-5)
Hindi checks now run, but the word list is small (4 rules) and unreviewed. The page says so on every Hindi check.
One open question is waiting for the reviewer: is "jad se khatam" (eliminates from the root) a cure claim or an
efficacy claim? It's in `engine/normalize/lexicon_hi.yaml`.

### G3. Commit and push
Everything above is uncommitted. Commit it and push to GitHub so the deploy and the code match. Note: the repo
`simply-Rahul8/IDEA_Satya_` is **public**, so the rules and word lists are readable by anyone — make it private first
if that matters (`gh repo edit simply-Rahul8/IDEA_Satya_ --visibility private`).

### G4. A short privacy notice (recommended)
The checker stores nothing you paste: the text is checked in memory and the page is sent `no-store`; rate limiting
keeps only a hash of the visitor's IP address. A one-paragraph notice saying so, reviewed by your consultant or a
lawyer, is good practice for a public site in India (DPDP Act) and required before Option B collects accounts.

---

## 5. Two ways to launch

| | **Option A — public checker only** | **Option B — the full app** |
|---|---|---|
| What the public gets | "Is my claim safe?": paste copy, see flags and the rule behind each, in English, Hindi and Hinglish | Plus sign-in, catalogue audit, fix-a-listing, AI-generated copy, review, Hindi output, export |
| Needs | Vercel + 3 environment variables | Vercel + Supabase project + email sign-in (Resend SMTP) or Google + AI keys (Sarvam and/or Anthropic) + Sentry |
| Cost to run | Free on Hobby for testing; Vercel Pro (~$20/mo) for commercial use | Vercel Pro + Supabase Pro (~$25/mo) + AI usage, before taking any payment (plan P27) |
| Time | ~30–45 min after §4 | A day, plus the preview checks in `deploy.md` §4a-0 and §4a |
| Signed-in pages | Show "Not open yet" (503) | Work |

Start with **A**: it's the outreach hook in your plan, needs no keys and costs nothing per check. Add **B** when pilot
brands are lined up.

---

## 6. Step by step

### Step 0 — What you need
- A Vercel account. Hobby is free for testing; **Hobby is for personal, non-commercial use**, so move to Pro before
  using it commercially (plan P27).
- Node.js and the Vercel CLI: `npm i -g vercel` (already on this machine).
- The code committed and pushed (§4 G3).

### Step 1 — Create the Vercel project
```bash
cd ~/satya
vercel login          # opens the browser; sign in
vercel link           # create a new project, e.g. "satya"; root directory: ./
```
Vercel detects the Python app from `asgi.py` and uses Python 3.12 from `pyproject.toml`.

### Step 2 — Environment variables
Set them in the dashboard (Project → Settings → Environment Variables) or with `vercel env add NAME preview` /
`vercel env add NAME production`. **Use different secrets for Preview and Production** (plan P9). Never paste them
into chat, email or the repo.

| Variable | Option A | Option B | Value |
|---|---|---|---|
| `SATYA_ENV` | ✅ | ✅ | `preview` for Preview, `production` for Production. **Never `dev` on Vercel** (it seeds demo data). |
| `SATYA_SESSION_SECRET` | ✅ | ✅ | A long random string: `python -c "import secrets; print(secrets.token_hex(32))"`. The app refuses requests without it. |
| `SATYA_PUBLIC_URL` | ✅ | ✅ | The site's address, e.g. `https://satya.example.in` (no trailing slash). Used by share cards, the sitemap and sign-in links. |
| `SATYA_LLM` | `mock` | `live` | The public checker uses no AI; `live` turns on Sarvam with Claude as fallback for the signed-in tools. |
| `SUPABASE_DB_URL` | optional | ✅ | Pooled Postgres URL. Makes rate limits shared across Vercel instances (without it each instance counts on its own). |
| `SENTRY_DSN` | optional | ✅ | Error reporting; listing text is scrubbed. |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | — | ✅ | From the Supabase project (`deploy.md` §2). |
| `SARVAM_API_KEY` and/or `ANTHROPIC_API_KEY` | — | ✅ | AI providers for generation. |
| `SATYA_ALLOWED_ORIGINS` | rarely | rarely | Only if forms are posted from a second domain. |
| `CHECKER_RATE_LIMIT`, `CHECKER_RATE_WINDOW_S` | optional | optional | Defaults: 120 checks per 10 minutes per visitor. |

For **Option B**, first do `deploy.md` §2 (Supabase project in Mumbai, run `supabase/schema.sql`, auth, SMTP) and §3
(Sentry).

### Step 3 — Deploy a preview
```bash
vercel                # builds and deploys a PREVIEW, prints its URL
```
In the deployment's details, confirm the function region is **bom1 (Mumbai)**.

### Step 4 — Smoke-test the preview (10 minutes)
Open `<preview-url>/check` on a laptop and a phone:
1. The page loads with the SATYA logo, the big headline and the **Draft rule set v0.1.3-draft** notice.
2. Paste row 1 from §2 → **High risk**, "fairer skin" **Blocked**, "by 90%" to review.
3. Paste row 3 → **No flagged risks**.
4. Paste row 5 → refused as Ayurvedic.
5. Paste row 7 (Hindi) → **Severe risk** with the Hindi draft note.
6. Click a flagged phrase → the rule panel opens. Toggle dark mode. Click try-cell 01.
7. Open `<preview-url>/anything` → the 404 page; `<preview-url>/fix/new` → "Not open yet" (Option A).
8. Paste the preview URL into WhatsApp or LinkedIn → the Satya preview card appears.
9. Vercel dashboard → the deployment → **Logs**: no errors.

For **Option B**, also run `deploy.md` §4a-0 (rate limiter with real Supabase) and §4a (sign-in, workspace isolation,
persistence). They are required before any production deploy.

### Step 5 — Go to production
Only after §4 and a passing preview:
```bash
vercel --prod
```
**Custom domain (optional):** Project → Settings → Domains → add your domain and set the DNS records Vercel shows.
HTTPS is automatic. Set `SATYA_PUBLIC_URL` to it and redeploy.

### Step 6 — After launch
- **Rollback in one click:** Vercel → Deployments → the previous good one → *Promote to Production*.
- Health check for an uptime monitor: `<site>/healthz` returns `{"status": "ok"}`.
- Watch Vercel Logs (and Sentry if set) for the first days.
- If any secret was ever pasted anywhere outside Vercel's settings, rotate it.
- The project is connected to GitHub: every push to `main` deploys to production and other branches get preview
  links. Push to `main` only what should go live.

---

## 7. Known limits after launch (not blockers)

- The Hindi word list is small and draft; Hindi copy always carries a notice saying so (G2).
- The benchmark corpus is synthetic; replace it with real labelled pilot listings.
- Without `SUPABASE_DB_URL`, rate limits are per Vercel instance, so a determined user can exceed them.
- Signed-in pages carry the new theme but not the new layout.
- Performance is 96, not 100: the remaining cost is loading one stylesheet and two JS libraries, which strict CSP
  rules out inlining.
- The rule set stays **v0.1.3-draft** until the consultant signs (G1).
