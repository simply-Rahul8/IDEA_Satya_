"""Schema, RLS isolation, job resume and rate limits, against a throwaway local Postgres (no network, no keys)."""

from pathlib import Path

import pgserver
import psycopg
import pytest

from engine.jobs.store import create_job, job_progress, step_job

SUPABASE = Path(__file__).resolve().parent.parent / "supabase"


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    server = pgserver.get_server(tmp_path_factory.mktemp("pg"), cleanup_mode="stop")
    conn = psycopg.connect(server.get_uri(), autocommit=True)
    conn.execute((SUPABASE / "local_shim.sql").read_text(encoding="utf8"))
    schema = (SUPABASE / "schema.sql").read_text(encoding="utf8")
    conn.execute(schema)
    conn.execute(schema)  # must be re-runnable
    yield conn
    conn.close()
    server.cleanup()


def as_user(conn, user_id):
    conn.execute("reset role")
    conn.execute("select set_config('request.jwt.claim.sub', %s, false)", (str(user_id) if user_id else "",))
    conn.execute("set role authenticated" if user_id else "set role anon")


def as_service(conn):
    conn.execute("reset role")
    conn.execute("set role service_role")


@pytest.fixture(scope="module")
def tenants(db):
    db.execute("reset role")
    ids = {}
    for name in ("alice", "bob"):
        email = f"{name}@example.com"
        uid = db.execute("insert into auth.users (email) values (%s) returning id", (email,)).fetchone()[0]
        ws = db.execute("select workspace_id from workspace_members where user_id = %s", (uid,)).fetchone()[0]
        prod = db.execute(
            "insert into products (workspace_id, name) values (%s, %s) returning id", (ws, f"{name}-serum")
        ).fetchone()[0]
        ids[name] = {"user": uid, "ws": ws, "product": prod}
    return ids


def test_signup_creates_profile_and_workspace(db, tenants):
    db.execute("reset role")
    for t in tenants.values():
        assert db.execute("select count(*) from profiles where id = %s", (t["user"],)).fetchone()[0] == 1


def test_rls_isolation_between_workspaces(db, tenants):
    a, b = tenants["alice"], tenants["bob"]
    as_user(db, a["user"])
    assert [r[0] for r in db.execute("select name from products").fetchall()] == ["alice-serum"]
    assert db.execute("select count(*) from workspaces").fetchone()[0] == 1
    assert db.execute("select count(*) from profiles").fetchone()[0] == 1
    assert db.execute("select count(*) from products where workspace_id = %s", (b["ws"],)).fetchone()[0] == 0
    assert db.execute("update products set name = 'x' where id = %s", (b["product"],)).rowcount == 0
    assert db.execute("delete from products where id = %s", (b["product"],)).rowcount == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("insert into products (workspace_id, name) values (%s, 'sneaky')", (b["ws"],))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("insert into workspace_members (workspace_id, user_id) values (%s, %s)", (b["ws"], a["user"]))


def test_anon_sees_nothing(db, tenants):
    as_user(db, None)
    for table in ("products", "listings", "claims", "jobs", "workspaces", "consents"):
        assert db.execute(f"select count(*) from {table}").fetchone()[0] == 0


def test_consent_is_own_and_append_only(db, tenants):
    a, b = tenants["alice"], tenants["bob"]
    sql = (
        "insert into consents (user_id, purpose, notice_version, granted) values (%s, 'terms_privacy', 'draft-1', true)"
    )
    as_user(db, a["user"])
    db.execute(sql, (a["user"],))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(sql, (b["user"],))
    assert db.execute("update consents set granted = false").rowcount == 0  # no update policy
    assert db.execute("delete from consents").rowcount == 0
    as_user(db, b["user"])
    assert db.execute("select count(*) from consents").fetchone()[0] == 0


def test_browser_cannot_write_jobs_or_call_helpers(db, tenants):
    a = tenants["alice"]
    as_user(db, a["user"])
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("insert into jobs (workspace_id, kind) values (%s, 'bulk')", (a["ws"],))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("select rate_limit_hit('k', 1, 60)")
    as_user(db, None)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("select rate_limit_hit('k', 1, 60)")


def test_hard_block_and_evidence_constraints(db, tenants):
    a = tenants["alice"]
    as_service(db)  # members are stopped earlier by claims_guard; the CHECK is the second layer (P25)
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute(
            "insert into claims (workspace_id, product_id, text, status, hard_blocked)"
            " values (%s, %s, 'cures acne', 'confirmed', true)",
            (a["ws"], a["product"]),
        )
    as_user(db, a["user"])
    claim = db.execute(
        "insert into claims (workspace_id, product_id, text) values (%s, %s, 'dermatologically tested') returning id",
        (a["ws"], a["product"]),
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute(
            "insert into evidence (workspace_id, claim_id, kind) values (%s, %s, 'test_report')", (a["ws"], claim)
        )
    db.execute(
        "insert into evidence (workspace_id, claim_id, kind, document_id) values (%s, %s, 'test_report', 'DOC-1')",
        (a["ws"], claim),
    )


def test_job_resumes_after_abandoned_step(db, tenants):
    as_service(db)
    job = create_job(db, str(tenants["alice"]["ws"]), "bulk_listings", [{"n": i} for i in range(7)])
    calls = []

    def handler(payload):
        calls.append(payload["n"])
        return {"out": payload["n"] * 2}

    p = step_job(db, job, handler, batch_size=3)
    assert (p["status"], p["done"], p["total"]) == ("running", 3, 7)

    # The tab closes mid-step: two items are claimed but never processed.
    db.execute("select * from claim_job_items(%s, 2)", (job,))
    assert job_progress(db, job)["done"] == 3
    # While the claims are fresh a new step skips them...
    p = step_job(db, job, handler, batch_size=5)
    assert p["done"] == 5 and p["status"] == "running"
    # ...once stale they are picked up again, and the job completes with nothing lost or repeated.
    db.execute("update job_items set claimed_at = now() - interval '10 minutes' where status = 'claimed'")
    p = step_job(db, job, handler, batch_size=5)
    assert p == {"status": "done", "total": 7, "done": 7, "failed": 0}
    assert sorted(calls) == list(range(7))


def test_job_item_fails_after_max_attempts(db, tenants):
    as_service(db)
    job = create_job(db, str(tenants["alice"]["ws"]), "bulk_listings", [{"n": 0}, {"n": 1}])

    def handler(payload):
        if payload["n"] == 0:
            raise ValueError("bad row")
        return {}

    for _ in range(5):
        p = step_job(db, job, handler)
    assert p == {"status": "done", "total": 2, "done": 1, "failed": 1}
    assert db.execute("select attempts from job_items where job_id = %s and position = 0", (job,)).fetchone()[0] == 3


def test_members_read_own_jobs_only(db, tenants):
    as_user(db, tenants["bob"]["user"])
    assert db.execute("select count(*) from jobs").fetchone()[0] == 0
    as_user(db, tenants["alice"]["user"])
    assert db.execute("select count(*) from jobs").fetchone()[0] == 2


def test_rate_limit_window(db):
    as_service(db)
    results = [db.execute("select rate_limit_hit('user:1', 3, 3600)").fetchone()[0] for _ in range(5)]
    assert results == [True, True, True, False, False]
    assert db.execute("select rate_limit_hit('user:2', 3, 3600)").fetchone()[0] is True


# ---- SAT-34: claims bypass, same-workspace FKs, evidence paths, storage ----
def _claim(db, t, text="dermatologically tested"):
    as_service(db)
    return db.execute(
        "insert into claims (workspace_id, product_id, text) values (%s, %s, %s) returning id",
        (t["ws"], t["product"], text),
    ).fetchone()[0]


def test_member_cannot_unblock_or_confirm_claims(db, tenants):
    a = tenants["alice"]
    as_service(db)
    blocked = db.execute(
        "insert into claims (workspace_id, product_id, text, hard_blocked, rule_id)"
        " values (%s, %s, 'cures acne', true, 'EN-DRUG-001') returning id",
        (a["ws"], a["product"]),
    ).fetchone()[0]
    as_user(db, a["user"])
    for sql in (
        "update claims set hard_blocked = false, status = 'confirmed' where id = %s",
        "update claims set hard_blocked = false where id = %s",
        "update claims set rule_id = null where id = %s",
        "update claims set status = 'confirmed' where id = %s",
    ):
        with pytest.raises((psycopg.errors.InsufficientPrivilege, psycopg.errors.CheckViolation)):
            db.execute(sql, (blocked,))
    as_service(db)
    row = db.execute("select hard_blocked, status from claims where id = %s", (blocked,)).fetchone()
    assert row == (True, "extracted")


def test_member_cannot_insert_preconfirmed_claims_but_can_reject(db, tenants):
    a = tenants["alice"]
    as_user(db, a["user"])
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "insert into claims (workspace_id, product_id, text, status) values (%s, %s, 'x', 'confirmed')",
            (a["ws"], a["product"]),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "insert into claims (workspace_id, product_id, text, rule_id) values (%s, %s, 'x', 'R')",
            (a["ws"], a["product"]),
        )
    cid = db.execute(
        "insert into claims (workspace_id, product_id, text) values (%s, %s, 'mild') returning id",
        (a["ws"], a["product"]),
    ).fetchone()[0]
    assert db.execute("update claims set status = 'rejected' where id = %s", (cid,)).rowcount == 1


def test_backend_confirms_and_member_edit_resets_confirmation(db, tenants):
    a = tenants["alice"]
    cid = _claim(db, a)
    db.execute("update claims set status = 'confirmed' where id = %s", (cid,))  # service role
    as_user(db, a["user"])
    db.execute("update claims set text = 'cures cancer' where id = %s", (cid,))
    assert db.execute("select status from claims where id = %s", (cid,)).fetchone()[0] == "extracted"


def test_children_must_share_the_parents_workspace(db, tenants):
    a, b = tenants["alice"], tenants["bob"]
    as_service(db)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute(
            "insert into claims (workspace_id, product_id, text) values (%s, %s, 'x')", (b["ws"], a["product"])
        )
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute(
            "insert into listings (workspace_id, product_id, source_text) values (%s, %s, 'x')",
            (b["ws"], a["product"]),
        )
    cid = _claim(db, a)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute("insert into evidence (workspace_id, claim_id, kind) values (%s, %s, 'other')", (b["ws"], cid))
    job = create_job(db, str(a["ws"]), "bulk", [{"n": 1}])
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute(
            "insert into job_items (job_id, workspace_id, position) values (%s, %s, 99)", (job, b["ws"])
        )


@pytest.mark.parametrize(
    "suffix,ok",
    [
        ("report.pdf", True),
        ("sub/report 1.pdf", True),
        ("../other/report.pdf", False),
        ("a/../b.pdf", False),
        ("a//b.pdf", False),
        ("dir/", False),
        ("bad\name.pdf", False),
        ("x" * 400, False),
    ],
)
def test_evidence_file_path_is_validated(db, tenants, suffix, ok):
    a, b = tenants["alice"], tenants["bob"]
    cid = _claim(db, a)
    as_service(db)
    sql = "insert into evidence (workspace_id, claim_id, kind, file_path) values (%s, %s, 'other', %s)"
    path = f"{a['ws']}/{suffix}"
    if ok:
        db.execute(sql, (a["ws"], cid, path))
    else:
        with pytest.raises(psycopg.errors.CheckViolation):
            db.execute(sql, (a["ws"], cid, path))
    with pytest.raises(psycopg.errors.CheckViolation):  # another workspace's folder
        db.execute(sql, (a["ws"], cid, f"{b['ws']}/report.pdf"))
    with pytest.raises(psycopg.errors.CheckViolation):  # no folder at all
        db.execute(sql, (a["ws"], cid, "report.pdf"))


def test_storage_bucket_is_private_and_scoped_to_workspace_folders(db, tenants):
    a, b = tenants["alice"], tenants["bob"]
    as_service(db)
    bucket = db.execute("select public, file_size_limit from storage.buckets where id = 'evidence'").fetchone()
    assert bucket == (False, 10485760)
    db.execute("insert into storage.objects (bucket_id, name) values ('evidence', %s)", (f"{a['ws']}/a.pdf",))
    db.execute("insert into storage.objects (bucket_id, name) values ('evidence', %s)", (f"{b['ws']}/b.pdf",))
    as_user(db, a["user"])
    names = [r[0] for r in db.execute("select name from storage.objects").fetchall()]
    assert names == [f"{a['ws']}/a.pdf"]
    db.execute("insert into storage.objects (bucket_id, name) values ('evidence', %s)", (f"{a['ws']}/c.pdf",))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("insert into storage.objects (bucket_id, name) values ('evidence', %s)", (f"{b['ws']}/x.pdf",))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("insert into storage.objects (bucket_id, name) values ('evidence', 'not-a-uuid/x.pdf')")
    as_user(db, None)
    assert db.execute("select count(*) from storage.objects").fetchone()[0] == 0
