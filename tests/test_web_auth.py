"""SAT-46: Supabase Auth session to workspace_id, against a fake Auth client and fake PostgREST (no project)."""

import re

import pytest
from fakes import FakeRest
from fastapi.testclient import TestClient

from asgi import app
from web import auth, devseed, packs, security

SAME = {"Origin": "http://testserver"}
ALICE = auth.AuthUser("11111111-1111-4111-8111-111111111111", "alice@example.com")
BOB = auth.AuthUser("22222222-2222-4222-8222-222222222222", "bob@example.com")
PACK = "33333333-3333-4333-8333-333333333333"


class FakeAuth:
    def __init__(self):
        self.tokens = {"alice-token": ALICE, "bob-token": BOB}  # "expired-token" and anything else are unknown

    def user_for_token(self, token):
        return self.tokens.get(token)


@pytest.fixture()
def rest():
    r = FakeRest()
    auth.configure(FakeAuth(), r)
    security.writes.reset()
    yield r
    auth.reset()


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def csrf(c):
    return re.search(r'name="csrf-token" content="([0-9a-f]+)"', c.get("/check").text).group(1)


def workspace_rows(rest, user):
    return [r for r in rest.tables.get("workspace_members", []) if r["user_id"] == user.id]


def test_first_sign_in_creates_one_workspace_and_owner_membership(rest):
    c = TestClient(app)
    r = c.get(f"/packs/{PACK}/review", headers=bearer("alice-token"))
    assert r.status_code == 404  # signed in, no such pack: not a 401
    rows = workspace_rows(rest, ALICE)
    assert len(rows) == 1 and rows[0]["role"] == "owner"
    assert [w["id"] for w in rest.tables["workspaces"]] == [rows[0]["workspace_id"]]
    assert rest.tables["workspaces"][0]["created_by"] == ALICE.id
    c.get(f"/packs/{PACK}/review", headers=bearer("alice-token"))
    assert len(rest.tables["workspaces"]) == 1  # second request reuses it


def test_existing_membership_is_reused_not_recreated(rest):
    rest.tables["workspace_members"] = [{"workspace_id": "w-existing", "user_id": ALICE.id, "role": "owner"}]
    assert auth.sign_in("alice-token")[1] == "w-existing"
    assert "workspaces" not in rest.tables


@pytest.mark.parametrize("headers", [{}, bearer("expired-token"), bearer("garbage"), {"Authorization": "Basic abc"}])
def test_signed_out_or_invalid_token_gets_no_workspace(rest, headers):
    c = TestClient(app)
    r = c.get(f"/packs/{PACK}/review", headers=headers)
    assert r.status_code == 401
    assert "workspaces" not in rest.tables and "workspace_members" not in rest.tables
    assert not any(call[0] == "insert" for call in rest.calls)


def test_signed_out_does_not_fall_back_to_the_browser_session_workspace(rest):
    c = TestClient(app)
    csrf(c)  # gets a session cookie
    sid = c.cookies["satya_sid"].split(".")[0]
    devseed.seed(packs.repo(), sid)
    assert c.get("/packs/demo/review").status_code == 401


def test_foreign_workspace_pack_is_404_for_a_signed_in_user(rest):
    a_ws, b_ws = auth.sign_in("alice-token")[1], auth.sign_in("bob-token")[1]
    assert a_ws != b_ws
    devseed.seed(packs.repo(), a_ws)
    c = TestClient(app)
    assert c.get("/packs/demo/review", headers=bearer("alice-token")).status_code == 200
    r = c.get("/packs/demo/review", headers=bearer("bob-token"))
    assert r.status_code == 404  # not 403, and not the pack


def test_client_cannot_name_its_own_workspace(rest):
    a_ws = auth.sign_in("alice-token")[1]
    devseed.seed(packs.repo(), a_ws)
    c = TestClient(app)
    h = {**bearer("bob-token"), "X-Workspace-Id": a_ws}
    assert c.get(f"/packs/demo/review?workspace_id={a_ws}", headers=h).status_code == 404


def test_session_cookie_signs_in_and_signout_clears_it(rest):
    c = TestClient(app)
    token = csrf(c)
    post = {**SAME, "X-CSRF-Token": token}
    r = c.post("/auth/session", headers={**post, **bearer("alice-token")})
    assert r.status_code == 200
    set_cookie = r.headers["set-cookie"]
    assert "HttpOnly" in set_cookie and "SameSite=lax" in set_cookie
    assert c.get(f"/packs/{PACK}/review").status_code == 404  # cookie alone now signs the browser in
    c.post("/auth/signout", headers=post)
    assert c.get(f"/packs/{PACK}/review").status_code == 401


def test_session_endpoint_refuses_invalid_token_and_cross_site(rest):
    c = TestClient(app)
    token = csrf(c)
    r = c.post("/auth/session", headers={**SAME, "X-CSRF-Token": token, **bearer("expired-token")})
    assert r.status_code == 401 and "set-cookie" not in r.headers and "workspaces" not in rest.tables
    r = c.post(
        "/auth/session", headers={"Origin": "https://evil.example", "X-CSRF-Token": token, **bearer("alice-token")}
    )
    assert r.status_code == 403


def test_lost_race_on_first_sign_in_uses_the_winners_workspace(rest):
    real_insert = rest.insert

    def racing(table, row):
        if table == "workspace_members":  # another request got there first
            real_insert(table, {"workspace_id": "w-winner", "user_id": ALICE.id, "role": "owner"})
            raise RuntimeError("duplicate key")
        return real_insert(table, row)

    rest.insert = racing
    assert auth.sign_in("alice-token")[1] == "w-winner"


def test_http_auth_client_fails_closed(monkeypatch):
    client = auth.HttpAuthClient("http://127.0.0.1:9", "anon", timeout=0.2)  # nothing listens: unreachable
    assert client.user_for_token("anything") is None


def test_hosted_without_supabase_config_fails_closed(monkeypatch):
    auth.reset()
    for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SATYA_ENV", "preview")
    monkeypatch.setenv("SATYA_SESSION_SECRET", "x" * 32)
    with pytest.raises(RuntimeError):
        auth._setup()
