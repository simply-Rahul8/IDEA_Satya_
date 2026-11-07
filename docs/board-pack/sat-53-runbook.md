# SAT-53 runbook: preview checks (DRAFT, nothing has been run)

**Who:** the board user, by hand, on the **preview** project and deployment only. Never run this against production.
**Needs:** the Supabase preview project (`docs/deploy.md` section 2) and the Vercel preview deploy (section 4) already exist. If not, stop: those are human steps that come first.
**Shell:** Git Bash on Windows (the commands use `curl`, `export`, `grep`). `curl.exe` also works in PowerShell, but the variable syntax differs.
**Where results go:** copy the "paste back" items into a comment on SAT-53. **Redact every token, key and password before pasting.** Paste status lines, counts and `[]` or error codes, never the secret values.
Wording: this checks the engine's guards. Nothing here shows a listing is compliant; the product says "no flagged risks under rule set vX" only.

## Setup (once)

```bash
export PREVIEW=https://<your-preview-url>            # no trailing slash
export SUPA=https://<project-ref>.supabase.co        # Project URL from Supabase
export ANON=<anon key>                               # from Supabase > Project settings > API; never paste it back
```

Then add a test user in Supabase: Authentication > Users > Add user, tick auto-confirm, give it an email and a password. Make a second test user the same way (`user B`). Call them user A and user B.

---

## Part 1. Rate limiter (`/check`)

What the code does (`web/security.py`, `web/checker.py`): `POST /check` is limited per client IP (default 120 requests per 600 seconds; env `CHECKER_RATE_LIMIT` and `CHECKER_RATE_WINDOW_S`). On Vercel the IP comes from the `x-vercel-forwarded-for` header that Vercel sets. `X-Forwarded-For` is **never trusted**, so a caller who rotates it must still be limited. The count is shared across instances only if `SUPABASE_DB_URL` is set; otherwise it is per instance, which can make counts vary on a busy deploy.

Optional, to make the test quick: set `CHECKER_RATE_LIMIT=5` for the **Preview** environment in Vercel, redeploy preview, and use `LIMIT=5` below. Set it back (or remove it) afterwards. If you skip this, use `LIMIT=120`.

### Step 1.1: get a session cookie and CSRF token

```bash
export LIMIT=120   # or 5 if you lowered CHECKER_RATE_LIMIT
rm -f jar.txt
TOKEN=$(curl -s -c jar.txt "$PREVIEW/check" | grep -o 'name="csrf-token" content="[^"]*"' | sed 's/.*content="//;s/"$//')
echo "token length: ${#TOKEN}"
```

**Success:** `token length` is more than 20. A length of 0 means the page did not load. Open `$PREVIEW/check` in a browser and report what it shows.
**Paste back:** the `token length` line only.

### Step 1.2: rotating X-Forwarded-For must still hit 429

```bash
for i in $(seq 1 $((LIMIT+5))); do
  curl -s -o /dev/null -w "%{http_code}\n" -b jar.txt -X POST "$PREVIEW/check" \
    -H "Origin: $PREVIEW" -H "X-CSRF-Token: $TOKEN" -H "X-Forwarded-For: 10.20.30.$i" \
    --data-urlencode "text=Gentle face wash for oily skin."
done | sort | uniq -c
```

**Success:** about `LIMIT` lines of `200` and the rest `429`, for example `120 200` and `5 429`. Every request used a different `X-Forwarded-For`, and the limiter still applied.
**Failure:** all 200s (no 429) means the limiter trusts a spoofable header or is not shared. This is a security failure. Paste the whole output.
**Also acceptable:** a count of 200s a little above `LIMIT` if the deploy has several instances and `SUPABASE_DB_URL` is not set. Say whether it is set.
**Paste back:** the `uniq -c` output, and whether `SUPABASE_DB_URL` is set (yes or no).

### Step 1.3: one more request shows the retry header

```bash
curl -s -i -b jar.txt -X POST "$PREVIEW/check" -H "Origin: $PREVIEW" -H "X-CSRF-Token: $TOKEN" \
  -H "X-Forwarded-For: 203.0.113.9" --data-urlencode "text=hello" | grep -i -E "^HTTP|^retry-after"
```

**Success:** `HTTP/... 429` and a `Retry-After` number of seconds.
**Paste back:** those two lines.

### Step 1.4: a second network gets a fresh counter

Connect another device or your computer to a **different network** (mobile hotspot is simplest; the public IP must change). Check with `curl -s https://api.ipify.org` before and after, and note that the two differ. Then repeat steps 1.1 and the single request below (the second network needs its own session cookie):

```bash
rm -f jar2.txt
TOKEN2=$(curl -s -c jar2.txt "$PREVIEW/check" | grep -o 'name="csrf-token" content="[^"]*"' | sed 's/.*content="//;s/"$//')
curl -s -o /dev/null -w "%{http_code}\n" -b jar2.txt -X POST "$PREVIEW/check" \
  -H "Origin: $PREVIEW" -H "X-CSRF-Token: $TOKEN2" --data-urlencode "text=Gentle face wash for oily skin."
```

**Success:** `200`. The new network has its own counter, while the first network is still blocked (repeat step 1.3 from the first network within the same window and it still says 429).
**Failure:** `429` on the new network means the limit is global or keyed on something shared (for example a proxy IP). Paste the output.
**Paste back:** the two public IPs (you may mask the last number), and the status code.

### Step 1.5: reset (if you lowered the limit)
Remove `CHECKER_RATE_LIMIT` from the Preview environment and redeploy preview. **Paste back:** "limit restored" or the value you left.

---

## Part 2. Supabase project matches what the tests assume (`docs/deploy.md` section 2, step 2)

Run each in the Supabase SQL editor on the preview project. None changes data.

```sql
-- 2a: every row must be true
select relname, relrowsecurity from pg_class
where relname in ('packs','audits','audit_items','exports','claims','evidence','products','jobs');

-- 2b: must return false
select public from storage.buckets where id = 'evidence';

-- 2c: only packs_select
select policyname from pg_policies where tablename = 'packs';

-- 2d: three policies
select tablename, policyname from pg_policies where schemaname = 'storage' and policyname like 'evidence_objects_%';

-- 2e: three rows
select tgname from pg_trigger where tgname in ('claims_guard_trg','evidence_file_guard_trg','packs_touch_trg');
```

**Success:** 2a: 8 rows, all `true`. 2b: `false`. 2c: exactly one row, `packs_select`. 2d: 3 rows. 2e: 3 rows.
**Paste back:** the row counts and any row that is not as stated (copy the text of the result, it holds no secrets).

---

## Part 3. Authentication and sessions (`docs/deploy.md` section 4a, step 1 and 2)

### Step 3.1: get a token for user A and user B

```bash
export USER_A_TOKEN=$(curl -s -X POST "$SUPA/auth/v1/token?grant_type=password" -H "apikey: $ANON" -H "Content-Type: application/json" \
  -d '{"email":"<user A email>","password":"<user A password>"}' | sed 's/.*"access_token":"\([^"]*\)".*/\1/')
export USER_B_TOKEN=$(curl -s -X POST "$SUPA/auth/v1/token?grant_type=password" -H "apikey: $ANON" -H "Content-Type: application/json" \
  -d '{"email":"<user B email>","password":"<user B password>"}' | sed 's/.*"access_token":"\([^"]*\)".*/\1/')
echo "A token length: ${#USER_A_TOKEN}, B token length: ${#USER_B_TOKEN}"
```

**Success:** both lengths are in the hundreds (a JWT). A short string (an error message) means the sign-in failed. Check the user is confirmed and the password is right. Tokens last 1 hour.
**Paste back:** the lengths line only. Never the tokens.

### Step 3.2: create the session through the app (user A)

```bash
rm -f jarA.txt
CSRF=$(curl -s -c jarA.txt "$PREVIEW/check" | grep -o 'name="csrf-token" content="[^"]*"' | sed 's/.*content="//;s/"$//')
curl -i -X POST "$PREVIEW/auth/session" -b jarA.txt -c jarA.txt \
  -H "Authorization: Bearer $USER_A_TOKEN" -H "Origin: $PREVIEW" -H "X-CSRF-Token: $CSRF" | grep -i -E "^HTTP|set-cookie: satya_at"
```

**Success:** `HTTP/... 200` and a `satya_at` cookie with `HttpOnly`. In the SQL editor, user A has exactly one workspace: 

```sql
select count(*) from workspace_members m join auth.users u on u.id = m.user_id
where u.email = '<user A email>' and m.role = 'owner';
```

Result must be `1` (not 0, not 2).
**Paste back:** the HTTP line, whether `HttpOnly` appears on the cookie line (yes or no, not the cookie value), and the count.

### Step 3.3: a bad token is refused

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$PREVIEW/auth/session" -b jarA.txt \
  -H "Authorization: Bearer not-a-real-token" -H "Origin: $PREVIEW" -H "X-CSRF-Token: $CSRF"
```

**Success:** `401`. **Paste back:** the status code.

### Step 3.4: pack persistence and cross-user isolation (needs the sign-in screens; if SAT-39 is not merged on the preview, mark this "not testable yet")
1. In a browser, sign in as user A, create a pack, open its review page, edit a sentence, reload. **Success:** the edit is still there.
2. Copy the pack's id from the URL (`/packs/<pack-id>/review`).
3. In a private window, sign in as user B and open `$PREVIEW/packs/<pack-id>/review`. **Success:** a 404 page, not 403 and not the pack.
4. Open the same pack in two tabs as user A, edit in both, save the second. **Success:** "This pack changed in another tab" (HTTP 409), not an overwrite.

**Paste back:** pass or fail for each of the four, and for a failure the page text or status code you saw.

---

## Part 4. RLS: the browser cannot unblock a claim or approve a pack

These use Supabase's REST interface directly with each user's token and the anon key, the same way a hostile browser would.

### Step 4.1: create a hard-blocked test claim (SQL editor runs as the owner, which is allowed)

Find user A's workspace and make a product if none exists:

```sql
select m.workspace_id from workspace_members m join auth.users u on u.id = m.user_id
where u.email = '<user A email>' and m.role = 'owner';
-- if user A has no product yet:
insert into products (workspace_id, name) values ('<workspace_id>', 'SAT-53 test product') returning id;
```

Then insert a hard-blocked claim:

```sql
insert into claims (workspace_id, product_id, text, hard_blocked, rule_id)
values ('<workspace_id>', '<product_id>', 'SAT-53 test claim (synthetic)', true, 'EN-DRUG-001')
returning id;
```

Copy the returned `id` as `CLAIM_ID`.

### Step 4.2: user A tries to set `hard_blocked=false` on their own claim

```bash
export CLAIM_ID=<claim id>
curl -s -i -X PATCH "$SUPA/rest/v1/claims?id=eq.$CLAIM_ID" \
  -H "apikey: $ANON" -H "Authorization: Bearer $USER_A_TOKEN" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"hard_blocked":false}' | grep -i -E "^HTTP|hard_blocked|code|message"
```

**Success (what the schema actually does):** the request is **refused**, with an error `42501` and a message like "hard_blocked and rule_id are set by the backend" (HTTP 403). It does not return the changed row. This differs from the "returns 0 rows" expectation in the task text: the `claims_guard` trigger rejects the change outright for the claim's owner; "0 rows" is what you see when someone else's claim is targeted (step 4.4). Either of those, with the row unchanged (step 4.3), is a pass.
**Failure:** HTTP 200 with a row showing `"hard_blocked":false`. That is a serious break of rule P25/P17. Do not continue; paste the output and stop.

### Step 4.3: confirm the row did not change

```sql
select hard_blocked, status, rule_id from claims where id = '<claim id>';
```

**Success:** `true`, `extracted`, `EN-DRUG-001`.
**Paste back:** the result row.

### Step 4.4: user B tries the same on user A's claim

```bash
curl -s -i -X PATCH "$SUPA/rest/v1/claims?id=eq.$CLAIM_ID" \
  -H "apikey: $ANON" -H "Authorization: Bearer $USER_B_TOKEN" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"hard_blocked":false}' | grep -i -E "^HTTP|^\[|^\{"
```

**Success:** HTTP 200 with body `[]` (0 rows, because user B cannot see user A's rows at all). Run 4.3 again: still `true`.
**Paste back:** the HTTP line and body.

### Step 4.5: confirming a hard-blocked claim is refused too

```bash
curl -s -i -X PATCH "$SUPA/rest/v1/claims?id=eq.$CLAIM_ID" \
  -H "apikey: $ANON" -H "Authorization: Bearer $USER_A_TOKEN" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"status":"confirmed"}' | grep -i -E "^HTTP|code|message"
```

**Success:** refused (`42501` or a check violation); row still `extracted` in a re-run of 4.3.
**Paste back:** the HTTP line and error code.

### Step 4.6: a browser cannot approve a pack (`docs/deploy.md` 4a step 4)

Create a pack as user A (Part 3.4), copy its id from the URL, then:

```bash
curl -s -i -X PATCH "$SUPA/rest/v1/packs?id=eq.<pack id>" \
  -H "apikey: $ANON" -H "Authorization: Bearer $USER_A_TOKEN" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"review":{"approved":true}}' | grep -i -E "^HTTP|^\[|^\{"
```

**Success:** no changed row: `[]` (0 rows), a 204 or an error. Never a row with `approved: true`. In the SQL editor `select review->>'approved' from packs where id = '<pack id>';` must not say `true` (the Approve button in the app is the only way).
**Paste back:** the HTTP line and body, and the SQL result.

### Step 4.7: evidence upload and citation (`docs/deploy.md` 4a step 5, optional if no upload screen yet)
Upload a PDF under `<workspace-id>/` through the app, then insert an evidence row citing it (works). Insert one citing a path that was not uploaded: it must fail with a check violation.
**Paste back:** pass or fail for each, with the error text if it failed. Mark "not testable yet" if there is no upload screen.

### Step 4.8: clean up

```sql
delete from claims where text like 'SAT-53 test claim%';
delete from products where name = 'SAT-53 test product';
```

Delete the two test users in Authentication > Users if you do not need them. If the service-role key was ever pasted anywhere outside Vercel's env settings, rotate it (`docs/deploy.md` 4a step 6).
**Paste back:** "cleaned up", and whether the service-role key needed rotating (yes or no).

---

## Summary table to paste back

| Check | Result (pass / fail / not testable) | Evidence pasted |
|---|---|---|
| 1.2 rotating XFF still gets 429 | | |
| 1.3 Retry-After present | | |
| 1.4 second network gets a fresh counter | | |
| 2a to 2e Supabase state | | |
| 3.2 session create, one workspace | | |
| 3.3 bad token returns 401 | | |
| 3.4 persistence, isolation (404), 409 | | |
| 4.2 owner cannot unblock a claim | | |
| 4.4 other user gets 0 rows | | |
| 4.5 cannot confirm a hard-blocked claim | | |
| 4.6 browser cannot approve a pack | | |
| 4.7 evidence upload and citation | | |
