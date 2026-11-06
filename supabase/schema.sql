-- Satya schema (plan §5, P9/P11/P12/P25/P26). Target: Supabase Postgres, ap-south-1.
-- Apply to a fresh project with the SQL editor or `psql -f`; safe to re-run.
-- Users only ever see rows of workspaces they belong to (RLS). The FastAPI backend uses the
-- service-role key for jobs, rate limits and telemetry; that key must never reach the browser.


-- ---------- identity, consent, DPDP (P12) ----------
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  created_at timestamptz not null default now()
);

-- Consent is recorded at signup and is append-only: withdrawal is a new row with granted = false.
create table if not exists consents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  purpose text not null check (purpose in ('terms_privacy', 'product_updates', 'llm_processing')),
  notice_version text not null,           -- privacy notice version shown (draft until P20 sign-off)
  granted boolean not null,
  created_at timestamptz not null default now()
);
create index if not exists consents_user_idx on consents (user_id, purpose, created_at desc);

-- DPDP access / erasure / correction requests, handled by the board user (see docs/deploy.md).
create table if not exists data_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('erasure', 'export', 'correction')),
  status text not null default 'open' check (status in ('open', 'done', 'rejected')),
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

-- ---------- tenancy ----------
create table if not exists workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists workspace_members (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'owner' check (role in ('owner', 'member')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);
create index if not exists workspace_members_user_idx on workspace_members (user_id);
-- One brand workspace per owner in v1 (plan section 3). Also makes the backend's first-sign-in create safe under a race.
create unique index if not exists workspace_members_one_owner_idx on workspace_members (user_id) where role = 'owner';

-- security definer so policies that use it don't recurse into workspace_members' own RLS.
create or replace function is_member(ws uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from workspace_members where workspace_id = ws and user_id = auth.uid());
$$;

-- Folder names come from the client; a malformed one must read as "no workspace", not raise.
create or replace function try_uuid(v text) returns uuid language plpgsql immutable as $$
begin
  return v::uuid;
exception when others then
  return null;
end $$;

-- ---------- product truth and listings ----------
create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  name text not null,
  product_type text not null default 'cosmetic' check (product_type in ('cosmetic')),  -- P23
  truth jsonb not null default '{}'::jsonb,   -- Product Truth (brand-confirmed facts)
  created_at timestamptz not null default now()
);
create index if not exists products_ws_idx on products (workspace_id);

create table if not exists listings (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  product_id uuid references products(id) on delete cascade,
  marketplace text not null default 'generic',
  language text not null default 'en',
  source_text text not null,                  -- data, never instructions (P19)
  generated jsonb,
  rule_set_version text,
  created_at timestamptz not null default now()
);
create index if not exists listings_ws_idx on listings (workspace_id);

create table if not exists claims (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  product_id uuid not null references products(id) on delete cascade,
  text text not null,
  status text not null default 'extracted' check (status in ('extracted', 'confirmed', 'rejected')),
  hard_blocked boolean not null default false,
  rule_id text,
  created_at timestamptz not null default now(),
  -- P25: a claim that hit a hard block can never be confirmed.
  constraint hard_block_not_confirmed check (not (hard_blocked and status = 'confirmed'))
);
create index if not exists claims_product_idx on claims (product_id);

-- P25: "test report" evidence needs a file reference or a document ID.
create table if not exists evidence (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  claim_id uuid not null references claims(id) on delete cascade,
  kind text not null check (kind in ('test_report', 'certificate', 'ingredient_list', 'other')),
  file_path text,                             -- Supabase Storage object path
  document_id text,
  created_at timestamptz not null default now(),
  constraint evidence_has_reference check (kind <> 'test_report' or file_path is not null or document_id is not null)
);
-- Storage object path is '<workspace_id>/<file name>': one folder per workspace, no traversal, bounded.
-- Added separately so a re-run upgrades a database whose table predates it.
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'evidence_file_path_ok') then
    alter table evidence add constraint evidence_file_path_ok check (
      file_path is null or (
        length(file_path) <= 300
        and file_path like workspace_id::text || '/%'
        and file_path !~ '(^|/)\.\.?(/|$)'
        and file_path !~ '[^A-Za-z0-9._/ -]'
        and file_path !~ '//'
        and right(file_path, 1) <> '/'
      )
    ) not valid;  -- new and changed rows are checked; legacy rows are left for the board user to review
  end if;
end $$;
create index if not exists evidence_claim_idx on evidence (claim_id);

-- A member can only cite a file that is already in this workspace's folder of the evidence bucket. (The path
-- shape and folder are checked by evidence_file_path_ok; this checks the object exists, and the caller's own
-- storage RLS means a file in another workspace's folder reads as missing.) The backend is trusted.
create or replace function evidence_file_guard() returns trigger language plpgsql as $$
begin
  if new.file_path is null or current_user not in ('anon', 'authenticated') or to_regclass('storage.objects') is null then
    return new;
  end if;
  if not exists (select 1 from storage.objects where bucket_id = 'evidence' and name = new.file_path) then
    raise exception 'evidence file % is not in the evidence bucket', new.file_path using errcode = '23514';
  end if;
  return new;
end $$;
drop trigger if exists evidence_file_guard_trg on evidence;
create trigger evidence_file_guard_trg before insert or update of file_path on evidence
  for each row execute function evidence_file_guard();

-- ---------- stepwise bulk jobs (P11) ----------
-- The browser drives progress: each call to a step endpoint claims the next few items, processes
-- them, and records results. Nothing depends on a long-running worker or on cron.
create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  created_by uuid references auth.users(id) on delete set null,
  kind text not null,
  status text not null default 'pending' check (status in ('pending', 'running', 'done', 'failed', 'cancelled')),
  total int not null default 0,
  done int not null default 0,
  failed int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists jobs_ws_idx on jobs (workspace_id, created_at desc);

create table if not exists job_items (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references jobs(id) on delete cascade,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  position int not null,
  payload jsonb not null default '{}'::jsonb,
  result jsonb,
  status text not null default 'pending' check (status in ('pending', 'claimed', 'done', 'failed')),
  attempts int not null default 0,
  error text,
  claimed_at timestamptz,
  unique (job_id, position)
);
create index if not exists job_items_pending_idx on job_items (job_id, status, position);

-- Atomically claim up to n items. Items stuck in 'claimed' longer than stale_after (closed tab,
-- timed-out function) become claimable again: that is how a job resumes. Items that already used
-- max_attempts are marked failed instead of being retried forever.
create or replace function claim_job_items(p_job uuid, n int, stale_after interval default interval '2 minutes',
                                           max_attempts int default 3)
returns setof job_items language plpgsql as $$
begin
  update job_items set status = 'failed', error = coalesce(error, 'max attempts exceeded')
   where job_id = p_job and attempts >= max_attempts
     and (status = 'pending' or (status = 'claimed' and claimed_at < now() - stale_after));
  return query
  with picked as (
    select id from job_items
     where job_id = p_job and (status = 'pending' or (status = 'claimed' and claimed_at < now() - stale_after))
     order by position
     limit n
     for update skip locked
  )
  update job_items ji set status = 'claimed', claimed_at = now(), attempts = ji.attempts + 1
    from picked where ji.id = picked.id
  returning ji.*;
end $$;

-- Recompute counters and status from the items. Idempotent: call after every step.
create or replace function refresh_job(p_job uuid) returns jobs language plpgsql as $$
declare j jobs;
begin
  update jobs set
    done = (select count(*) from job_items where job_id = p_job and status = 'done'),
    failed = (select count(*) from job_items where job_id = p_job and status = 'failed'),
    updated_at = now(),
    status = case
      when status = 'cancelled' then status
      when exists (select 1 from job_items where job_id = p_job and status in ('pending', 'claimed')) then 'running'
      when exists (select 1 from job_items where job_id = p_job and status = 'done') or total = 0 then 'done'
      else 'failed' end
  where id = p_job returning * into j;
  return j;
end $$;

-- ---------- child rows must share the parent's workspace ----------
-- (id, workspace_id) is unique on each parent so children can reference both columns. The older
-- single-column FKs stay (harmless); these add the same-workspace guarantee.
do $$
declare r record;
begin
  for r in select * from (values
    ('products', 'products_id_ws_key'), ('claims', 'claims_id_ws_key'), ('jobs', 'jobs_id_ws_key')
  ) as v(tbl, cname) loop
    if not exists (select 1 from pg_constraint where conname = r.cname) then
      execute format('alter table %I add constraint %I unique (id, workspace_id)', r.tbl, r.cname);
    end if;
  end loop;
  for r in select * from (values
    ('listings', 'listings_product_ws_fk', 'product_id', 'products'),
    ('claims', 'claims_product_ws_fk', 'product_id', 'products'),
    ('evidence', 'evidence_claim_ws_fk', 'claim_id', 'claims'),
    ('job_items', 'job_items_job_ws_fk', 'job_id', 'jobs')
  ) as v(tbl, cname, col, parent) loop
    if not exists (select 1 from pg_constraint where conname = r.cname) then
      execute format('alter table %I add constraint %I foreign key (%I, workspace_id) references %I (id, workspace_id) on delete cascade',
                     r.tbl, r.cname, r.col, r.parent);
    end if;
  end loop;
end $$;

-- ---------- packs, audits and exports (SAT-38) ----------
-- A pack is the reviewed listing plus the review state (kept reasons, approval). Members can read their own
-- but only the backend writes them: approval must come from the server-side gate, never from the browser.
-- `truth` is a snapshot of the Product Truth the pack was checked against, so a later edit to the product
-- cannot change what an approved pack was audited under. `rev` makes concurrent saves fail instead of overwrite.
create table if not exists packs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  product_id uuid,
  name text not null,
  truth jsonb not null default '{}'::jsonb,
  pack jsonb,
  review jsonb not null default '{}'::jsonb,
  rule_set_version text,
  rev int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint packs_id_ws_key unique (id, workspace_id),
  constraint packs_product_ws_fk foreign key (product_id, workspace_id) references products (id, workspace_id)
);
create index if not exists packs_ws_idx on packs (workspace_id, created_at desc);

create or replace function packs_touch() returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists packs_touch_trg on packs;
create trigger packs_touch_trg before update on packs for each row execute function packs_touch();

-- The audit record written at approval: one row per approval, one item per sentence (append-only for members).
create table if not exists audits (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  pack_id uuid not null,
  rule_set_version text not null,             -- "no flagged risks under rule set vX", never "compliant" (P20)
  summary jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  constraint audits_id_ws_key unique (id, workspace_id),
  constraint audits_pack_ws_fk foreign key (pack_id, workspace_id) references packs (id, workspace_id) on delete cascade
);
create index if not exists audits_pack_idx on audits (pack_id, created_at desc);

create table if not exists audit_items (
  id uuid primary key default gen_random_uuid(),
  audit_id uuid not null,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  position int not null,
  section text not null,
  sentence_text text not null,
  flags jsonb not null default '[]'::jsonb,
  overrides jsonb not null default '[]'::jsonb,   -- kept reasons / evidence references
  unique (audit_id, position),
  constraint audit_items_audit_ws_fk foreign key (audit_id, workspace_id) references audits (id, workspace_id) on delete cascade
);

create table if not exists exports (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  pack_id uuid not null,
  audit_id uuid,
  layout text not null,
  file_name text not null,
  sha256 text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  constraint exports_pack_ws_fk foreign key (pack_id, workspace_id) references packs (id, workspace_id) on delete cascade,
  constraint exports_audit_ws_fk foreign key (audit_id, workspace_id) references audits (id, workspace_id)
);
create index if not exists exports_pack_idx on exports (pack_id, created_at desc);

-- ---------- telemetry (P26) ----------
create table if not exists llm_calls (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete set null,
  job_id uuid references jobs(id) on delete set null,
  provider text not null,
  model text not null,
  prompt_version text,
  input_tokens int,
  output_tokens int,
  cost_inr numeric(12, 4),
  latency_ms int,
  outcome text not null check (outcome in ('ok', 'error', 'timeout', 'fallback', 'blocked')),
  created_at timestamptz not null default now()
);
create index if not exists llm_calls_ws_idx on llm_calls (workspace_id, created_at desc);

-- ---------- rate limits (P9) ----------
-- Fixed-window counter keyed by caller (user id, or a hash of the IP for the public checker).
create table if not exists rate_limits (
  key text not null,
  window_start timestamptz not null,
  count int not null default 0,
  primary key (key, window_start)
);

-- Returns true while the caller is within p_limit hits per p_window_seconds.
create or replace function rate_limit_hit(p_key text, p_limit int, p_window_seconds int) returns boolean
language plpgsql as $$
declare w timestamptz; c int;
begin
  w := to_timestamp(floor(extract(epoch from now()) / p_window_seconds) * p_window_seconds);
  insert into rate_limits (key, window_start, count) values (p_key, w, 1)
    on conflict (key, window_start) do update set count = rate_limits.count + 1
    returning count into c;
  delete from rate_limits where window_start < now() - interval '1 day';
  return c <= p_limit;
end $$;

-- ---------- brand setup (SAT-39): one profile per workspace; restricted_phrases feed the engine as brand flags ----------
create table if not exists brand_profiles (
  workspace_id uuid primary key references workspaces(id) on delete cascade,
  tone text not null check (tone in ('warm', 'clinical', 'premium')),
  restricted_phrases jsonb not null default '[]'::jsonb check (jsonb_typeof(restricted_phrases) = 'array'),
  seller_legal_name text not null,
  address text not null,
  grievance_name text not null,
  grievance_email text not null,
  updated_at timestamptz not null default now()
);

-- ---------- signup hook: profile + first workspace ----------
create or replace function handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
declare ws uuid;
begin
  insert into profiles (id, email) values (new.id, new.email) on conflict do nothing;
  insert into workspaces (name, created_by) values (coalesce(nullif(split_part(new.email, '@', 1), ''), 'My brand'), new.id)
    returning id into ws;
  insert into workspace_members (workspace_id, user_id, role) values (ws, new.id, 'owner');
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute function handle_new_user();

-- ---------- RLS ----------
alter table profiles enable row level security;
alter table consents enable row level security;
alter table data_requests enable row level security;
alter table workspaces enable row level security;
alter table workspace_members enable row level security;
alter table products enable row level security;
alter table listings enable row level security;
alter table claims enable row level security;
alter table evidence enable row level security;
alter table jobs enable row level security;
alter table job_items enable row level security;
alter table packs enable row level security;
alter table brand_profiles enable row level security;
alter table audits enable row level security;
alter table audit_items enable row level security;
alter table exports enable row level security;
alter table llm_calls enable row level security;
alter table rate_limits enable row level security;  -- no policies: service role only

drop policy if exists profiles_select on profiles;
create policy profiles_select on profiles for select using (id = auth.uid());
drop policy if exists profiles_update on profiles;
create policy profiles_update on profiles for update using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists consents_select on consents;
create policy consents_select on consents for select using (user_id = auth.uid());
drop policy if exists consents_insert on consents;
create policy consents_insert on consents for insert with check (user_id = auth.uid());  -- append-only

drop policy if exists data_requests_select on data_requests;
create policy data_requests_select on data_requests for select using (user_id = auth.uid());
drop policy if exists data_requests_insert on data_requests;
create policy data_requests_insert on data_requests for insert
  with check (user_id = auth.uid() and status = 'open');

drop policy if exists workspaces_select on workspaces;
create policy workspaces_select on workspaces for select using (is_member(id));
drop policy if exists workspaces_update on workspaces;
create policy workspaces_update on workspaces for update using (is_member(id)) with check (is_member(id));

drop policy if exists members_select on workspace_members;
create policy members_select on workspace_members for select using (user_id = auth.uid() or is_member(workspace_id));

-- Tenant data: members get full access to their own workspace's rows.
do $$
declare t text;
begin
  foreach t in array array['products', 'listings', 'evidence'] loop
    execute format('drop policy if exists %I on %I', t || '_rw', t);
    execute format('create policy %I on %I for all using (is_member(workspace_id)) with check (is_member(workspace_id))',
                   t || '_rw', t);
  end loop;
end $$;

-- Claims: members read and write their own, but P25 is enforced by the guard trigger below, because a
-- row policy cannot restrict columns. Only the backend (service role, after it ran the rules) confirms.
drop policy if exists claims_rw on claims;
create policy claims_rw on claims for all using (is_member(workspace_id)) with check (is_member(workspace_id));

create or replace function claims_guard() returns trigger language plpgsql as $$
begin
  if current_user not in ('anon', 'authenticated') then
    return new;  -- service role / table owner: the backend has evaluated the rules
  end if;
  if tg_op = 'INSERT' then
    if new.status <> 'extracted' or new.hard_blocked or new.rule_id is not null then
      raise exception 'claims are created as extracted; confirmation and blocking are set by the backend'
        using errcode = '42501';
    end if;
  else
    if new.hard_blocked is distinct from old.hard_blocked or new.rule_id is distinct from old.rule_id then
      raise exception 'hard_blocked and rule_id are set by the backend' using errcode = '42501';
    end if;
    if new.status = 'confirmed' and old.status is distinct from 'confirmed' then
      raise exception 'claims are confirmed through the backend, which re-checks the rules' using errcode = '42501';
    end if;
    if new.text is distinct from old.text then
      new.status := 'extracted';  -- edited wording needs a fresh check; an old confirmation does not carry over
    end if;
  end if;
  return new;
end $$;
drop trigger if exists claims_guard_trg on claims;
create trigger claims_guard_trg before insert or update on claims for each row execute function claims_guard();

-- Evidence files: one private bucket, one folder per workspace (the folder name is the workspace id).
-- Skipped where the storage schema does not exist.
do $$
begin
  if to_regclass('storage.buckets') is not null then
    insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
      values ('evidence', 'evidence', false, 10485760, array['application/pdf', 'image/png', 'image/jpeg'])
      on conflict (id) do update set public = false, file_size_limit = 10485760,
        allowed_mime_types = array['application/pdf', 'image/png', 'image/jpeg'];
    drop policy if exists evidence_objects_select on storage.objects;
    create policy evidence_objects_select on storage.objects for select to authenticated
      using (bucket_id = 'evidence' and public.is_member(public.try_uuid((storage.foldername(name))[1])));
    drop policy if exists evidence_objects_insert on storage.objects;
    create policy evidence_objects_insert on storage.objects for insert to authenticated
      with check (bucket_id = 'evidence' and public.is_member(public.try_uuid((storage.foldername(name))[1])));
    drop policy if exists evidence_objects_delete on storage.objects;
    create policy evidence_objects_delete on storage.objects for delete to authenticated
      using (bucket_id = 'evidence' and public.is_member(public.try_uuid((storage.foldername(name))[1])));
  end if;
end $$;

-- Packs, audits and exports: members read their own; only the backend (service role) writes.
do $$
declare t text;
begin
  foreach t in array array['packs', 'audits', 'audit_items', 'exports', 'brand_profiles'] loop
    execute format('drop policy if exists %I on %I', t || '_select', t);
    execute format('create policy %I on %I for select using (is_member(workspace_id))', t || '_select', t);
  end loop;
end $$;

-- Jobs, items and telemetry are written by the backend (service role); members may read their own.
drop policy if exists jobs_select on jobs;
create policy jobs_select on jobs for select using (is_member(workspace_id));
drop policy if exists job_items_select on job_items;
create policy job_items_select on job_items for select using (is_member(workspace_id));
drop policy if exists llm_calls_select on llm_calls;
create policy llm_calls_select on llm_calls for select using (workspace_id is not null and is_member(workspace_id));

-- Browser roles must not call the job / rate-limit helpers directly.
revoke execute on function claim_job_items(uuid, int, interval, int) from public, anon, authenticated;
revoke execute on function refresh_job(uuid) from public, anon, authenticated;
revoke execute on function rate_limit_hit(text, int, int) from public, anon, authenticated;
