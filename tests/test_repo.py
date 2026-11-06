"""SAT-38: workspace-scoped pack repository (memory and Supabase-over-a-fake-client) and per-route scoping."""

import uuid

import pytest
from fakes import FakeRest
from fastapi.testclient import TestClient
from helpers import secure

from asgi import app
from engine.repo import Conflict, Keep, MemoryRepository, NotFound, SupabaseRepository, from_env
from web import devseed, packs, review

WS_A, WS_B = str(uuid.uuid4()), str(uuid.uuid4())
HX = {"HX-Request": "true"}


def uuid_pack():
    state = devseed.build()
    state.pack_id = str(uuid.uuid4())
    return state


@pytest.fixture(params=["memory", "supabase"])
def repo(request):
    return MemoryRepository() if request.param == "memory" else SupabaseRepository(FakeRest())


# ---------------------------------------------------------------------------------------- the interface
def test_foreign_workspace_id_is_not_found(repo):
    s = uuid_pack()
    repo.put(WS_A, s)
    assert repo.get(WS_A, s.pack_id).product == s.product
    assert not repo.exists(WS_B, s.pack_id)
    with pytest.raises(NotFound):
        repo.get(WS_B, s.pack_id)
    with pytest.raises(NotFound), repo.edit(WS_B, s.pack_id):
        pass


def test_edit_saves_on_success_and_not_on_error(repo):
    s = uuid_pack()
    repo.put(WS_A, s)
    with repo.edit(WS_A, s.pack_id) as st:
        st.approved, st.rewrites["x-0"] = True, "new"
        st.kept[("bullet_3-0", "R", "m")] = Keep("because", False)
        st.reported.add(("bullet_3-0", "R"))
    got = repo.get(WS_A, s.pack_id)
    assert got.approved and got.rewrites["x-0"] == "new" and got.reported == {("bullet_3-0", "R")}
    assert got.kept[("bullet_3-0", "R", "m")].reason == "because"
    assert got.pack.section("bullet_2").sentences[0].text == s.pack.section("bullet_2").sentences[0].text
    if isinstance(repo, SupabaseRepository):  # a row is only written when the block finishes cleanly
        with pytest.raises(ValueError), repo.edit(WS_A, s.pack_id) as st:
            st.approved = False
            raise ValueError("boom")
        assert repo.get(WS_A, s.pack_id).approved is True


def test_put_replaces_within_a_workspace_only(repo):
    s = uuid_pack()
    repo.put(WS_A, s)
    s.product = "Renamed"
    repo.put(WS_A, s)
    assert repo.get(WS_A, s.pack_id).product == "Renamed"
    if isinstance(repo, SupabaseRepository):  # another workspace cannot take over an existing id
        with pytest.raises(RuntimeError):
            repo.put(WS_B, s)
    assert repo.get(WS_A, s.pack_id).product == "Renamed"


# ---------------------------------------------------------------------------------------- supabase specifics
def test_supabase_queries_always_filter_on_workspace():
    rest = FakeRest()
    repo = SupabaseRepository(rest)
    s = uuid_pack()
    repo.put(WS_A, s)
    repo.get(WS_A, s.pack_id)
    with repo.edit(WS_A, s.pack_id):
        pass
    assert rest.calls and all(c[2].get("workspace_id") == WS_A for c in rest.calls)


def test_supabase_non_uuid_ids_are_not_found_and_never_queried():
    rest = FakeRest()
    repo = SupabaseRepository(rest)
    for bad in ("demo", "1; drop table packs", "../x", ""):
        with pytest.raises(NotFound):
            repo.get(WS_A, bad)
    with pytest.raises(NotFound):
        repo.get("not-a-workspace", str(uuid.uuid4()))
    assert rest.calls == []


def test_supabase_overlapping_edits_conflict_instead_of_overwriting():
    repo = SupabaseRepository(FakeRest())
    s = uuid_pack()
    repo.put(WS_A, s)
    with pytest.raises(Conflict), repo.edit(WS_A, s.pack_id):
        with repo.edit(WS_A, s.pack_id) as other:  # a second tab saves first
            other.product = "Other tab"
    assert repo.get(WS_A, s.pack_id).product == "Other tab"


def test_approval_from_another_rule_set_version_does_not_carry_over():
    rest = FakeRest()
    repo = SupabaseRepository(rest)
    s = uuid_pack()
    s.approved = True
    repo.put(WS_A, s)
    assert repo.get(WS_A, s.pack_id).approved is True
    rest.tables["packs"][0]["rule_set_version"] = "v0-old"
    assert repo.get(WS_A, s.pack_id).approved is False


def test_from_env_picks_supabase_and_fails_closed_when_hosted():
    assert isinstance(from_env({}), MemoryRepository)
    configured = {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "k"}
    assert isinstance(from_env(configured), SupabaseRepository)
    for env in ({"SATYA_ENV": "preview"}, {"SATYA_ENV": "production"}, {"VERCEL": "1"}):
        with pytest.raises(RuntimeError):
            from_env(env)


# ---------------------------------------------------------------------------------------- routes
SID = "bullet_1-0"
ROUTES = {  # every route of the review router that names a pack: (method, path template) -> form data
    ("GET", "/packs/{pack_id}/review"): {},
    ("POST", "/packs/{pack_id}/sentences/{sid}/check"): {"text": "Gentle serum."},
    ("POST", "/packs/{pack_id}/sentences/{sid}/rewrite"): {},
    ("POST", "/packs/{pack_id}/sentences/{sid}/keep"): {"reason": "because we say so"},
    ("POST", "/packs/{pack_id}/sentences/{sid}/edit-reason"): {},
    ("POST", "/packs/{pack_id}/sentences/{sid}/report"): {"rule_id": "x"},
    ("POST", "/packs/{pack_id}/approve"): {},
}


def test_the_table_above_covers_every_pack_route():
    found = {(m, r.path) for r in review.router.routes for m in r.methods if "{pack_id}" in r.path}
    assert found == set(ROUTES)


def _call(c, method, path, data, pack_id):
    url = path.format(pack_id=pack_id, sid=SID)
    return c.get(url) if method == "GET" else c.post(url, data=data, headers=HX)


@pytest.fixture(params=["memory", "supabase"])
def two_sessions(request):
    packs.reset(MemoryRepository() if request.param == "memory" else SupabaseRepository(FakeRest()))
    owner, intruder = secure(TestClient(app)), secure(TestClient(app))
    state = uuid_pack()
    packs.repo().put(owner.owner, state)
    return owner, intruder, state.pack_id


@pytest.mark.parametrize(("method", "path"), sorted(ROUTES))
def test_every_route_treats_a_foreign_pack_id_as_404(two_sessions, method, path):
    owner, intruder, pack_id = two_sessions
    data = ROUTES[(method, path)]
    before = packs.repo().get(owner.owner, pack_id).pack.model_dump()
    r = _call(intruder, method, path, data, pack_id)
    assert r.status_code == 404 and r.json()["detail"] == "No such pack"
    assert packs.repo().get(owner.owner, pack_id).pack.model_dump() == before  # and nothing changed
    mine = _call(owner, method, path, data, pack_id)  # the owner does reach the pack (report: no such flag)
    assert mine.status_code != 404 or mine.json()["detail"] != "No such pack"


def test_edits_through_the_supabase_repository_persist_and_survive_a_new_request():
    rest = FakeRest()
    packs.reset(SupabaseRepository(rest))
    c = secure(TestClient(app))
    state = uuid_pack()
    packs.repo().put(c.owner, state)
    r = c.post(f"/packs/{state.pack_id}/sentences/{SID}/check", data={"text": "Gentle serum."}, headers=HX)
    assert r.status_code == 200
    assert rest.tables["packs"][0]["pack"]["sections"][1]["sentences"][0]["text"] == "Gentle serum."
    assert "Gentle serum." in c.get(f"/packs/{state.pack_id}/review").text


# ---------------------------------------------------------------------------------------- no demo outside dev
def test_no_global_store_remains_in_the_web_layer():
    assert not hasattr(review, "store") and not hasattr(review, "PackStore")


def test_demo_pack_does_not_exist_unless_dev_env(monkeypatch):
    monkeypatch.delenv("SATYA_ENV", raising=False)
    c = secure(TestClient(app))
    assert c.get("/packs/demo/review").status_code == 404
    monkeypatch.setenv("SATYA_ENV", "preview")
    monkeypatch.setenv("SATYA_SESSION_SECRET", "x" * 32)
    assert c.get("/packs/demo/review").status_code == 404


def test_dev_env_seeds_one_demo_pack_per_workspace(monkeypatch):
    monkeypatch.setenv("SATYA_ENV", "dev")
    a, b = secure(TestClient(app)), secure(TestClient(app))
    assert a.get("/packs/demo/review").status_code == 200
    a.post("/packs/demo/sentences/bullet_1-0/check", data={"text": "Mine only."}, headers=HX)
    assert "Mine only." not in b.get("/packs/demo/review").text
    assert "Mine only." in a.get("/packs/demo/review").text


def test_dev_seed_is_skipped_with_a_supabase_repository(monkeypatch):
    monkeypatch.setenv("SATYA_ENV", "dev")
    packs.reset(SupabaseRepository(FakeRest()))
    assert secure(TestClient(app)).get("/packs/demo/review").status_code == 404
