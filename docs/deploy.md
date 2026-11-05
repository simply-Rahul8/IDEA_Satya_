# Deploy runbook (preview only until the board approves production)

Nothing here has been done. Every step needs an account or payment, so the **board user** does it.
Status of regulatory text: draft until consultant sign-off (P20). Use separate keys per environment (P9).

## 1. Local dev (no accounts)
1. `uv sync`, copy `.env.example` to `.env`, leave `SATYA_LLM=mock`.
2. `python scripts/run.py test` runs schema, RLS, job-resume and rate-limit tests on a throwaway local Postgres.
3. `python scripts/run.py dev` starts the app at http://localhost:8000.

## 2. Supabase (preview project, ap-south-1 Mumbai)
1. Create a free project named `satya-preview`, region **ap-south-1**. Save the DB password in a password manager.
2. SQL editor: paste `supabase/schema.sql` and run. (Do not run `local_shim.sql`.)
3. Authentication > Providers: enable Email (OTP, 6 digits, 10 min expiry). Optionally enable Google (create an OAuth client in Google Cloud, redirect URI shown by Supabase).
4. Authentication > SMTP (P28): the built-in mailer only sends to team members. Create a Resend free account, verify a sending domain, create an API key, and enter host `smtp.resend.com`, port 465, user `resend`, password = the API key, from = your verified address.
5. Authentication > URL configuration: site URL = the preview URL; add `<preview-url>/auth/callback`.
6. Signup must show the privacy notice and a consent checkbox and write a `consents` row (`terms_privacy`, notice version). Notice text stays draft until P20.
7. DPDP requests: users insert into `data_requests`; the board user acts within 30 days (erasure = delete the user in Authentication, which cascades).
8. Copy Project URL, anon key, service-role key, and the pooled DB URL into Vercel env vars (below). Never commit them.

## 3. Sentry (free tier)
Create a project (Python/FastAPI), copy the DSN into `SENTRY_DSN` for preview only. `send_default_pii` is off so listing text is not sent.

## 4. Vercel preview (region bom1, P14)
1. Import the repo is not possible (no remote). Use `vercel` CLI from a clean checkout: `vercel link`, then `vercel` (preview, **not** `--prod`).
2. Set env vars for the Preview environment only: `SATYA_ENV=preview`, `SATYA_LLM` (keep `mock` until the Engine live providers exist), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `SENTRY_DSN`, `RATE_LIMIT_*`.
3. `vercel.json` pins `regions: ["bom1"]`. Check the function region in the deployment details.
4. Bulk jobs are client-driven (P11): no cron is configured, so Hobby limits do not block them.

## 5. Production (needs board approval first)
Hobby is non-commercial and free Supabase pauses when idle (P27). Move to Vercel Pro (~$20/mo) and Supabase Pro (~$25/mo) **before taking any prepayment**. That is a spend change: the board approves it in a task first. Production gets its own Supabase project, Sentry environment and keys.
