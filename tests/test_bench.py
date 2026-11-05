from bench import ab
from bench.__main__ import gate, main
from bench.arms import run_arm
from bench.corpus import load
from engine.providers import MockProvider


def test_gate_passes_in_mock():
    r, arms, fails = gate()
    assert not fails, fails
    assert arms[0]["provider"] == "mock" and arms[0]["pdps"] == 50 and arms[0]["cost_inr_per_pdp"] == 0


def test_run_arm_counts_cost_and_latency():
    a = run_arm(MockProvider(), load()[:3])
    assert a["pdps"] == 3 and a["errors"] == 0 and a["latency_ms_p95"] >= 0


def test_ab_prep_is_blind_and_scores(tmp_path, monkeypatch):
    monkeypatch.setattr(ab, "AB_DIR", tmp_path)
    m = MockProvider()
    sheet, key = ab.prepare(load()[:6], {"x": (m, "professional"), "y": (m, "friendly")})
    assert len(sheet) == len(key) == 6
    assert all(set(p) == {"pdp_id", "A", "B", "vote"} for p in sheet)  # no provider names on the sheet
    for p in sheet:
        p["vote"] = "A"
    res = ab.score(sheet, key, "x")
    assert res["votes"] == 6 and res["win"] + res["loss"] == 6
    sheet[0]["vote"] = "tie"
    sheet[1]["vote"] = None
    assert ab.score(sheet, key, "x")["unvoted"] == 1


def test_ab_target():
    pairs = [{"pdp_id": "p", "vote": "tie"}]
    assert ab.score(pairs, [{"pdp_id": "p", "A": "x", "B": "y"}], "x")["meets_target"]


def test_main_report_exit_zero(capsys):
    assert main([]) == 0
