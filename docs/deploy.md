# Deploy runbook (preview only until the board approves production)

Nothing here has been done. Every step needs an account or payment, so the **board user** does it.
Status of regulatory text: draft until consultant sign-off (P20). Use separate keys per environment (P9).

## 1. Local dev (no accounts)
1. `uv sync`, copy `.env.example` to `.env`, leave `SATYA_LLM=mock`.
2. `python scripts/run.py test` runs schema, RLS, job-resume and rate-limit tests on a throwaway local Postgres.
3. `python scripts/run.py dev` starts the app at http://localhost:8000.

## 2. Supabase (preview project, ap-south-1 Mumbai)
1. Create a free project named `satya-preview`, region **ap-south-1**. Save the DB password in a password manager.
2. SQL editor: paste `supabase/schema.sql` and run (re-running upgrades an existing project; it also creates the private `evidence` Storage bucket and its policies; check Storage shows it as private). (Do not run `local_shim.sql`.)
   Then run these once, in the SQL editor, to confirm the project matches what the tests assume (all should return the stated result; none changes data):
   - `select relrowsecurity from pg_class where relname in ('packs','audits','audit_items','exports','claims','evidence','products','jobs');` : every row `true`.
   - `select public from storage.buckets where id = 'evidence';` : `false`.
   - `select policyname from pg_policies where tablename = 'packs';` : only `packs_select` (browsers cannot write packs, so they cannot set approval).
   - `select tablename, policyname from pg_policies where schemaname = 'storage' and policyname like 'evidence_objects_%';` : three policies.
   - `select tgname from pg_trigger where tgname in ('claims_guard_trg','evidence_file_guard_trg','packs_touch_trg');` : three rows.
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
2. Set env vars for the Preview environment only: `SATYA_ENV=preview`, `SATYA_LLM` (keep `mock` until the Engine live providers exist), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `SENTRY_DSN`, `RATE_LIMIT_*`, and **`SATYA_SESSION_SECRET`** (long random string; the app refuses to start requests without it when `SATYA_ENV` is preview/production). Add `SATYA_ALLOWED_ORIGINS` only if the site is served from a custom domain besides the Vercel host. `SUPABASE_DB_URL` also makes rate limits shared across instances; without it they are per instance.
   Pack persistence (SAT-38) needs only `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: with them the app stores packs in Supabase; without them a preview/production deploy refuses to serve pack pages (the in-memory store is for local use only). Never set `SATYA_ENV=dev` on a hosted environment: it seeds a demo pack, and only into an in-memory store.
3. `vercel.json` pins `regions: ["bom1"]`. Check the function region in the deployment details.
4. Bulk jobs are client-driven (P11): no cron is configured, so Hobby limits do not block them.

## 4a. Persistence checks after the first preview deploy (board user, once a preview project exists)
The Supabase repository is tested against a fake client only. After section 2 and 4 are done, check these by hand and report any failure in the SAT-38 task:
1. Packs have no creator yet: until sign-in (Supabase Auth) sets `request.state.workspace_id` to the signed-in user's workspace, the web layer uses the browser session id as the workspace, which does not exist in `workspaces`. So the first end-to-end check needs the auth task merged. After that: sign in, create a pack, reload the review page, edit a sentence, reload again: the edit persists.
2. Sign in as a second user (another email) and open the first user's `/packs/<pack-id>/review`: it must be a 404, not a 403 and not the pack.
3. Open the same pack in two tabs, edit in both: the second save shows "This pack changed in another tab" (HTTP 409) rather than overwriting the first.
4. In the Supabase Table editor, a `packs` row's `review.approved` only changes through the app's Approve button. Using the anon key against `/rest/v1/packs` with a user's JWT, a PATCH must change 0 rows.
5. Upload a PDF to the `evidence` bucket under `<workspace-id>/` through the app, then insert evidence citing it (works); citing a path that was not uploaded must fail with a check violation.
6. Rotate the service-role key if it was ever pasted anywhere outside Vercel's env settings.

## 5. Production (needs board approval first)
Hobby is non-commercial and free Supabase pauses when idle (P27). Move to Vercel Pro (~$20/mo) and Supabase Pro (~$25/mo) **before taking any prepayment**. That is a spend change: the board approves it in a task first. Production gets its own Supabase project, Sentry environment and keys.
