# ADR-8: Tenancy via RLS; backend uses the service role for jobs, limits and telemetry

Status: accepted (CTO, SAT-10). Regulatory wording touched by this ADR stays draft until P20.

## Decision
- Every tenant table carries `workspace_id`; browser roles see only rows of workspaces they belong to (RLS via `is_member()`).
- Jobs, job items, rate limits and `llm_calls` are written only by the FastAPI backend using the service-role key. The key never reaches the browser; the claim/refresh/rate-limit SQL functions are revoked from `anon` and `authenticated`.
- Bulk jobs are client-driven (P11): the browser calls a step endpoint, which claims a few items, processes them and records results. Stale claims are re-claimable, so a closed tab only delays a job. No worker or cron.
- Consent rows are append-only (withdrawal = new row). Erasure = delete the auth user; data cascades (P12).
- Deploys: preview only, Vercel region bom1, Supabase ap-south-1. Production and paid tiers (P27) need board approval.

## Known gaps (follow-ups)
- Child rows (claims, evidence) are not constrained to share a workspace with their parent; harmless for reads but should be a composite FK.
- `schema.sql` v2 tables are inferred; reconcile against v2 §4 when that text is available.
- `rate_limit_hit` prunes old windows on every call; move to a periodic prune if it shows up in profiles.
