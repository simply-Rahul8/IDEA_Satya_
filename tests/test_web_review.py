"""Review screen (variant B): server-side behaviour of the HTMX actions and the approval gate."""

import re

import pytest
from fastapi.testclient import TestClient
from helpers import secure_with_demo

from asgi import app
from web import packs, review

HX = {"HX-Request": "true"}
CURRENT: dict[str, str] = {}
BANNED = re.compile(r"\b(compliant|safe)\b", re.I)


@pytest.fixture()
def client():
    c = secure_with_demo(TestClient(app))  # a new session and its own demo pack
    CURRENT["owner"] = c.owner
    return c


def demo_state():
    return packs.repo().get(CURRENT["owner"], "demo")


def post(c, path, **data):
    return c.post(f"/packs/demo/{path}", data=data, headers=HX)


def status(sid):
    return next(r["status"] for r in review.build_view(demo_state())["rows"] if r["sid"] == sid)


def test_page_renders_gate_rows_ledger_and_strict_markup(client):
    html = client.get("/packs/demo/review").text
    assert "Does every sentence trace to a confirmed claim?" in html
    assert "3 blocked and 1 needs a reason before you can approve." in html
    assert html.count('class="row"') == 12 and html.count('class="claim"') == 5
    assert 'style="' not in html and len(re.findall(r"<script(?![^>]*\bsrc=)", html)) == 1
    assert "unsafe" not in client.get("/packs/demo/review").headers["content-security-policy"]
    assert not BANNED.search(re.sub(r"<[^>]+>", " ", html))


def test_unknown_pack_and_sentence_404(client):
    assert client.get("/packs/nope/review").status_code == 404
    assert post(client, "sentences/bullet_9-0/check", text="x").status_code == 404


def test_recheck_returns_oob_parts_and_marks_without_swapping_textarea(client):
    r = post(client, "sentences/bullet_1-0/check", text="Cures eczema fast.")
    assert 'id="live-bullet_1-0"' in r.text and 'hx-swap-oob="outerHTML"' in r.text
    assert "<textarea" not in r.text and "<mark" in r.text
    assert status("bullet_1-0") == "red"


def test_non_overridable_red_renders_no_override_control_and_api_refuses(client):
    html = client.get("/packs/demo/review").text
    live = html[html.index('id="live-bullet_2-0"') : html.index('id="s-bullet_3-0"')]
    assert "Cannot be overridden. Rewrite or remove it." in live and 'name="reason"' not in live
    assert post(client, "sentences/bullet_2-0/keep", reason="we have a report").status_code == 403
    assert status("bullet_2-0") == "red"


def test_keep_with_reason_needs_text_then_becomes_kept(client):
    empty = post(client, "sentences/bullet_3-0/keep", reason="  ")
    assert "Add a reason to keep this wording." in empty.text and 'aria-invalid="true"' in empty.text
    ok = post(client, "sentences/bullet_3-0/keep", reason="Test report doc-7 covers it.")
    assert 'data-status="kept"' in ok.text and "Your reason" in ok.text and "Kept with reason" in ok.text
    assert "Clear" not in re.sub(r"<[^>]+>", " ", ok.text).split("Kept with reason")[0][-40:]
    assert "kept with your reason" in ok.headers["hx-trigger"]


def test_reason_survives_recheck_only_while_flagged_wording_stands(client):
    post(client, "sentences/bullet_3-0/keep", reason="Covered by doc-7")
    same = post(
        client, "sentences/bullet_3-0/check", text="Dermatologically tested and clinically proven on sensitive skin!"
    )
    assert 'data-status="kept"' in same.text
    gone = post(client, "sentences/bullet_3-0/check", text="Gentle on sensitive skin.")
    assert 'data-status="ok"' in gone.text


def test_overridable_red_keeps_only_with_evidence(client):
    post(client, "sentences/bullet_1-0/check", text="Absolutely safe with zero side effects.")
    row = next(r for r in review.build_view(demo_state())["rows"] if r["sid"] == "bullet_1-0")
    assert row["status"] == "red" and row["keep_kind"] == "evidence" and not row["hard_blocked"]
    bad = post(client, "sentences/bullet_1-0/keep", reason="")
    assert "Add an evidence reference" in bad.text
    assert 'data-status="kept"' in post(client, "sentences/bullet_1-0/keep", reason="doc-9").text


def test_use_rewrite_replaces_text_rechecks_and_focuses_textarea(client):
    r = post(client, "sentences/bullet_3-0/rewrite")
    trig = r.headers["hx-trigger"]
    assert '"satya:focus": "t-bullet_3-0"' in trig and "A gentle serum" in trig and "no flagged risks" in trig
    assert 'data-status="ok"' in r.text
    assert post(client, "sentences/bullet_3-0/rewrite").status_code == 409  # rewrite is single-use


def test_wrong_flag_report_unblocks_nothing_and_can_be_undone(client):
    r = post(client, "sentences/bullet_2-0/report", rule_id="EN-DRUG-001")
    assert "Reported as a wrong flag. Thanks." in r.text and status("bullet_2-0") == "red"
    assert "Wrong flag?" in post(client, "sentences/bullet_2-0/report", rule_id="EN-DRUG-001", undo="1").text


def test_approve_blocked_then_ready_then_edit_reopens(client):
    blocked = post(client, "approve")
    assert 'aria-disabled="true"' in blocked.text and "before you can approve" in blocked.text
    assert demo_state().approved is False
    st = demo_state()
    for sid, text in (
        ("bullet_2-0", "Smooth, even-looking skin."),
        ("bullet_4-0", "Gentle daily serum."),
        ("bullet_5-0", "Rose water serum."),
    ):
        post(client, f"sentences/{sid}/check", text=text)
    post(client, "sentences/bullet_3-0/rewrite")
    # anchors still point at unconfirmed claims, so engine anchor flags keep them blocked until the claim is confirmed
    assert st.approved is False
    for key in ("bullet_2-0", "bullet_4-0"):
        assert status(key) == "red"


def test_approve_succeeds_on_a_clean_pack_and_edit_reopens_gate(client):
    state = demo_state()
    for sec in state.pack.sections:
        for i in range(len(sec.sentences)):
            sid = review.sid_of(sec.key, i)
            post(
                client,
                f"sentences/{sid}/check",
                text="Hydrating serum with a dewy finish." if sec.key.startswith("bullet") else sec.sentences[i].text,
            )
    for c in state.truth.claims:  # confirm the rest so anchors resolve
        c.status = review.ClaimStatus.CONFIRMED
        c.hard_blocked = False
    for sid in ("bullet_2-0", "bullet_4-0", "bullet_5-0"):
        post(client, f"sentences/{sid}/check", text="Hydrating serum with a dewy finish.")
    state.pack.section("bullet_5").sentences[0].anchors.append("claim:c1")
    post(client, "sentences/bullet_5-0/check", text="Hydrating serum with a dewy finish.")
    r = post(client, "approve", **{"text-bullet_1-0": "Hydrating serum with a dewy finish."})
    assert state.approved and "Approved." in r.text
    post(client, "sentences/bullet_1-0/check", text="Hydrating serum.")
    assert not state.approved and state.last_edit_after_approval


def test_empty_pack_state(client):
    demo_state().pack = None
    html = client.get("/packs/demo/review").text
    assert "Nothing to review yet." in html and "Generate PDP pack" in html and 'role="tab"' not in html
