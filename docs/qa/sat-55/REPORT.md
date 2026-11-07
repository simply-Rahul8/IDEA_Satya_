# SAT-55 QA re-run: Origin: null form POSTs (SAT-45 Must-fix 1)

Branch `SAT-55-...` at bf4b195. Harness copied untracked from the SAT-45 branch (`scripts/verify_satya.py`,
`docs/qa/sat-35-journey/browser_journey.py`), run with `SATYA_LLM=mock`, then removed. No product code edited.

## Verdict: PASS for Must-fix 1. SAT-55 can merge.

| Check | Result |
|---|---|
| `verify_satya.py`: "same-origin form POST that arrives with `Origin: null` (Sec-Fetch-Site: same-origin) is accepted" | PASS |
| `verify_satya.py` cross-site / bad-CSRF / signed-out refusals (CSRF block) | all PASS |
| `browser_journey.py` (no `--fix-origin`), Edge, 1280 and 360 px | gets through sign-in email + code, setup, audit, fix, truth, review, Hindi: every POST accepted. |
| `SATYA_LLM=mock uv run pytest` | 651 passed |

`verify_satya.py` totals: 143 passed, 3 failed, 16 blocked. The 3 FAILs are not this fix: export forms have no
`csrf_token` field (2 checks, SAT-56 / Must-fix 2) and the Hindi pack has no web export route (SAT-57).
In the browser run the only 403 is `POST /packs/<id>/export` (same SAT-56 cause). The 422s are the journey's
deliberate error screens (empty consent, setup validation, fix/truth gates).

## Code review of the diff (security)
- `same_origin()` accepts `Origin: null` only with an explicit `Sec-Fetch-Site: same-origin`. That header is a
  browser-set forbidden header, so a page cannot forge it. A sandboxed or cross-site frame sends `cross-site`.
  Missing metadata with `null` is refused. `guard_unsafe` still requires the CSRF token. No cross-site check weakened.
- `Referrer-Policy: same-origin` still sends no referrer cross-site.
- Observation (not a defect): in the browser run the Origin on every POST was the real origin, so the header change
  alone fixes Edge; the `null` branch is defence in depth, covered by verify_satya and `tests/test_web_security.py`
  but not exercised by a real browser here.

## Not covered
Other browsers (Firefox, Safari) not run; Edge/Chromium only. Other SAT-45 findings are tracked separately.
