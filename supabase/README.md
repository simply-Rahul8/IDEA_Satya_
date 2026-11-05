# supabase

- `schema.sql`: tables, RLS, job and rate-limit functions. Re-runnable.
- `local_shim.sql`: fake `auth` schema and roles, used only by `tests/test_schema_rls.py` against a throwaway Postgres (pgserver).
- `config.toml`: auth settings (OTP email via Resend SMTP, Google). Secrets come from env only.

Run the tests: `python scripts/run.py test`. Deploying is a board-user step: see `docs/deploy.md`.
