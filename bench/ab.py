"""Blind A/B pair prep (P5; target >=60% win or tie). Writes a rater sheet with no provider names and a separate
key file; `score` turns filled-in votes into the win-or-tie rate. Raters are humans: this module only prepares and
scores, it contacts nobody."""

from __future__ import annotations

import json
import random
from pathlib import Path

from bench.arms import run_pdp
from engine.models import PDPPack

AB_DIR = Path(__file__).resolve().parent.parent / "data" / "ab"
TARGET = 0.60


def render(pack: PDPPack) -> str:
    return "\n".join(
        f"[{sec.key}] " + " ".join(s.text for s in sec.sentences) for sec in pack.sections if sec.sentences
    )


def prepare(pdps: list[dict], arms: dict[str, tuple], seed: int = 5) -> tuple[list[dict], list[dict]]:
    """arms: {label: (provider, tone)}; exactly two. Returns (sheet, key). Position of each arm is shuffled per PDP."""
    (la, (pa, ta)), (lb, (pb, tb)) = arms.items()
    rng = random.Random(seed)
    sheet, key = [], []
    for p in pdps:
        packs = {la: run_pdp(p, pa, ta)[0], lb: run_pdp(p, pb, tb)[0]}
        if None in packs.values():
            continue  # a failed arm cannot be rated; the arm's error rate is in the bench report
        order = [la, lb]
        rng.shuffle(order)
        sheet.append(
            {"pdp_id": p["pdp_id"], "A": render(packs[order[0]]), "B": render(packs[order[1]]), "vote": None}
        )  # fmt: skip  (rater fills "A", "B" or "tie")
        key.append({"pdp_id": p["pdp_id"], "A": order[0], "B": order[1]})
    return sheet, key


def write(sheet: list[dict], key: list[dict], status: str) -> None:
    AB_DIR.mkdir(parents=True, exist_ok=True)
    (AB_DIR / "pairs.json").write_text(
        json.dumps({"status": status, "pairs": sheet}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (AB_DIR / "key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")


def score(pairs: list[dict], key: list[dict], challenger: str) -> dict:
    """Win-or-tie rate of `challenger` over votes cast. Unvoted pairs are ignored and reported."""
    k = {x["pdp_id"]: x for x in key}
    win = tie = loss = 0
    for p in pairs:
        v = p.get("vote")
        if v is None:
            continue
        if v == "tie":
            tie += 1
        elif k[p["pdp_id"]][v] == challenger:
            win += 1
        else:
            loss += 1
    n = win + tie + loss
    rate = (win + tie) / n if n else 0.0
    return {"challenger": challenger, "votes": n, "unvoted": len(pairs) - n, "win": win, "tie": tie, "loss": loss,
            "win_or_tie": rate, "meets_target": n > 0 and rate >= TARGET}  # fmt: skip
