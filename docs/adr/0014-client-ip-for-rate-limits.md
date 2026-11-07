# ADR-14: Client IP for rate limits is pinned at the server, not trusted from X-Forwarded-For

Status: accepted (CTO, SAT-50). Evidence: QA SAT-44 `docs/qa/sat-35-rerun/REPORT.md`, Should-fix 1.

## Context
The app already ignores `X-Forwarded-For` (ADR-12 era SAT-34). But uvicorn's `ProxyHeadersMiddleware` runs before the app, trusts the header from 127.0.0.1 by default and rewrites `request.client`, so under plain `uvicorn asgi:app` a rotating header gave 130 x 200 on `/check`. With `--no-proxy-headers` the same run gives 120 x 200 then 429.

## Decision
1. Every uvicorn launch passes `--no-proxy-headers`. `scripts/run.py` keeps the list as `SERVER_ARGS` and the `dev` task uses it. `tests/test_proxy_headers.py` starts real uvicorn and asserts the limiter holds, and that default uvicorn does not (so a change in uvicorn's default is noticed).
2. The IP the limiter keys on is `SATYA_TRUSTED_IP_HEADER` (default `x-vercel-forwarded-for` on Vercel, last entry) or `request.client`. Nothing else.
3. Vercel runs the ASGI app without uvicorn, so the flag is moot there; the Vercel header and the Postgres limiter are confirmed on a preview by the board user (`docs/deploy.md` 4a-0), with QA re-testing.

## Consequences
A host behind a reverse proxy must set `SATYA_TRUSTED_IP_HEADER` to a proxy-only header; otherwise all callers share the proxy's address. The app cannot detect a mis-launched uvicorn from inside (the scope is already rewritten), so the runbook and the test are the guard.
