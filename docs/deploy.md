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
   The schema now has a unique index so a user owns at most one workspace (SAT-46). Re-running it on a project where a user already owns two would fail on that index; `select user_id from workspace_members where role = 'owner' group by 1 having count(*) > 1;` should return no rows first.
   Then run these once, in the SQL editor, to confirm the project matches what the tests assume (all should return the stated result; none changes data):
   - `select relrowsecurity from pg_class where relname in ('packs','audits','audit_items','exports','claims','evidence','products','jobs');` : every row `true`.
   - `select public from storage.buckets where id = 'evidence';` : `false`.
   - `select policyname from pg_policies where tablename = 'packs';` : only `packs_select` (browsers cannot write packs, so they cannot set approval).
   - `select tablename, policyname from pg_policies where schemaname = 'storage' and policyname like 'evidence_objects_%';` : three policies.
   - `select tgname from pg_trigger where tgname in ('claims_guard_trg','evidence_file_guard_trg','packs_touch_trg');` : three rows.
3. Authentication > Providers (SAT-46 verifies the session by asking Supabase Auth, so no JWT secret is copied anywhere): enable Email (OTP, 6 digits, 10 min expiry). Optionally enable Google (create an OAuth client in Google Cloud, redirect URI shown by Supabase).
4. Authentication > SMTP (P28): the built-in mailer only sends to team members. Create a Resend free account, verify a sending domain, create an API key, and enter host `smtp.resend.com`, port 465, user `resend`, password = the API key, from = your verified address.
5. Authentication > URL configuration: site URL = the preview URL; add `<preview-url>/auth/callback`.
6. Signup must show the privacy notice and a consent checkbox and write a `consents` row (`terms_privacy`, notice version). Notice text stays draft until P20.
7. DPDP requests: users insert into `data_requests`; the board user acts within 30 days (erasure = delete the user in Authentication, which cascades).
8. Copy Project URL, anon key, service-role key, and the pooled DB URL into Vercel env vars (below). Never commit them.

## 3. Sentry (free tier)
Create a project (Python/FastAPI), copy the DSN into `SENTRY_DSN` for preview only. `send_default_pii` is off so listing text is not sent.

## 4. Vercel preview (region bom1, P14)
1. Use the `vercel` CLI from a clean, pushed checkout: `vercel link`, then `vercel` (preview, **not** `--prod`). Git auto-deploy is off in `vercel.json`, so every deploy is deliberate. The go-live path is in [`GO-LIVE.md`](GO-LIVE.md).
2. Set env vars for the Preview environment only: `SATYA_ENV=preview`, `SATYA_LLM` (keep `mock` until the Engine live providers exist), `SUPABASE_URL`, `SUPABASE_ANON_KEY` (now required: the app uses it to ask Supabase Auth who a token belongs to), `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `SENTRY_DSN`, `RATE_LIMIT_*`, and **`SATYA_SESSION_SECRET`** (long random string; the app refuses to start requests without it when `SATYA_ENV` is preview/production). Add `SATYA_ALLOWED_ORIGINS` only if the site is served from a custom domain besides the Vercel host. `SUPABASE_DB_URL` also makes rate limits shared across instances; without it they are per instance.
   Pack persistence (SAT-38) needs only `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: with them the app stores packs in Supabase; without them a preview/production deploy refuses to serve pack pages (the in-memory store is for local use only). With any of the three Supabase variables missing, a hosted deploy answers pack routes with 500 rather than serving an anonymous workspace. Never set `SATYA_ENV=dev` on a hosted environment: it seeds a demo pack, and only into an in-memory store.
3. `vercel.json` pins `regions: ["bom1"]`. Check the function region in the deployment details.
4. Bulk jobs are client-driven (P11): no cron is configured, so Hobby limits do not block them.

## 4-bis. Client IP for rate limits (SAT-50, ADR-14)
The checker and write limiters key on a hash of the caller's IP (`web/security.py: client_ip`). The app never reads `X-Forwarded-For`. It reads the header named in `SATYA_TRUSTED_IP_HEADER` (default `x-vercel-forwarded-for` when `VERCEL` is set, last entry), and otherwise `request.client`.
- **uvicorn trusts `X-Forwarded-For` from 127.0.0.1 by default and rewrites `request.client`**, so a rotating header bypasses the limiter (QA SAT-44: 130 x 200). **Anywhere the app is served by uvicorn, pass `--no-proxy-headers`** (`scripts/run.py` holds this as `SERVER_ARGS`, and `python scripts/run.py dev` uses it). Do not set `FORWARDED_ALLOW_IPS` or `--forwarded-allow-ips` to anything wider than a proxy you control.
- **Vercel** runs `asgi.py` directly through its Python runtime (zero-config entrypoint detection), not uvicorn, so the flag does not apply there; the limiter relies on `x-vercel-forwarded-for`, which Vercel sets and overwrites on every request. No `SATYA_TRUSTED_IP_HEADER` is needed.
- **Any other host behind a proxy** (not planned): run uvicorn with `--no-proxy-headers` and set `SATYA_TRUSTED_IP_HEADER` to a header that only the proxy can set, with the proxy stripping any client-supplied copy.
- `tests/test_proxy_headers.py` starts real uvicorn and fails if the pinned arguments stop blocking a rotating header.

## 4a-0. Preview checks for the rate limiter and a real-Supabase run (board user, before any deploy)
These could only be tested with local stand-ins (QA SAT-44), so one preview run is required **before any production deploy**; QA re-tests after it.
1. Limiter keys on the Vercel header and uses Postgres. With `SUPABASE_DB_URL` set on the preview, post to `/check` (with the page's CSRF token and cookie) more than `CHECKER_RATE_LIMIT` times with a different `X-Forwarded-For` on each: expect 429 after the limit, not 200s. Then repeat from a second network (phone hotspot): it gets its own fresh count, so the key is the caller's address and not a shared proxy address. In the Supabase SQL editor, `select key, window_start, count from rate_limits order by window_start desc limit 5;` should show `ip:check:` rows (hashed, no raw IPs). If no rows appear, the app fell back to the per-process limiter: check `SUPABASE_DB_URL`.
2. Auth and RLS against the real project: run the section 4a checks 1 to 4 and the section 2 verification queries, and in addition confirm that as an `authenticated` user a PATCH on `claims` setting `hard_blocked=false` or `status='confirmed'` changes 0 rows (QA ran this only on a local Postgres with `local_shim.sql`).
3. Report results in the SAT-50 task. Rule set stays `v0.1.2-draft`: never describe output as compliant.

## 4a. Persistence checks after the first preview deploy (board user, once a preview project exists)
The Supabase repository is tested against a fake client only. After section 2 and 4 are done, check these by hand and report any failure in the SAT-38 task:
1. Sign-in (SAT-46, backend only; SAT-39 builds the screens): until SAT-39 merges there is no sign-in page, so get a session by hand. In Authentication > Users, add a test user (or sign in with email OTP from any client), copy that user's access token (valid 1 hour) and call `curl -i -X POST <preview-url>/auth/session -H "Authorization: Bearer <token>" -H "Origin: <preview-url>" -H "X-CSRF-Token: <value of the csrf-token meta tag on /check, with that page's satya_sid cookie>" -b <cookie-jar>`. Expect 200, a `satya_at` HttpOnly cookie, and one new `workspaces` row plus one `workspace_members` row (role `owner`) for that user (the signup trigger may have created them already; there must still be exactly one). Calling a pack route with a bad, expired or missing token must be 401. After that: create a pack, reload the review page, edit a sentence, reload again: the edit persists.
2. Sign in as a second user (another email) and open the first user's `/packs/<pack-id>/review`: it must be a 404, not a 403 and not the pack.
3. Open the same pack in two tabs, edit in both: the second save shows "This pack changed in another tab" (HTTP 409) rather than overwriting the first.
4. In the Supabase Table editor, a `packs` row's `review.approved` only changes through the app's Approve button. Using the anon key against `/rest/v1/packs` with a user's JWT, a PATCH must change 0 rows.
5. Upload a PDF to the `evidence` bucket under `<workspace-id>/` through the app, then insert evidence citing it (works); citing a path that was not uploaded must fail with a check violation.
6. Rotate the service-role key if it was ever pasted anywhere outside Vercel's env settings.

## 5. Production (needs board approval first)
Hobby is non-commercial and free Supabase pauses when idle (P27). Move to Vercel Pro (~$20/mo) and Supabase Pro (~$25/mo) **before taking any prepayment**. That is a spend change: the board approves it in a task first. Production gets its own Supabase project, Sentry environment and keys.
