"""Review state for one pack, and how it is saved. Draft content: nothing here says "compliant" (P20)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.models import PDPPack, ProductTruth
from engine.rules import RuleSet, default_ruleset


@dataclass
class Keep:
    reason: str
    evidence: bool


@dataclass
class ReviewState:
    pack_id: str
    product: str
    truth: ProductTruth
    pack: PDPPack | None
    ruleset: RuleSet
    kept: dict[tuple[str, str, str], Keep] = field(default_factory=dict)  # (sid, rule_id, matched_text)
    rewrites: dict[str, str] = field(default_factory=dict)  # sid -> engine-suggested rewrite, when supplied
    reported: set[tuple[str, str]] = field(default_factory=set)  # (sid, rule_id)
    approved: bool = False
    last_edit_after_approval: bool = False
    approve_error: str | None = None
    last_announce: str = ""


def to_row(state: ReviewState) -> dict[str, Any]:
    """The JSON columns of a `packs` row (everything except ids, workspace and revision)."""
    return {
        "name": state.product,
        "truth": state.truth.model_dump(mode="json"),
        "pack": state.pack.model_dump(mode="json") if state.pack else None,
        "rule_set_version": state.ruleset.label,
        "review": {
            "kept": [
                {"sid": s, "rule_id": r, "matched": m, "reason": k.reason, "evidence": k.evidence}
                for (s, r, m), k in sorted(state.kept.items())
            ],
            "rewrites": dict(state.rewrites),
            "reported": sorted([s, r] for s, r in state.reported),
            "approved": state.approved,
            "last_edit_after_approval": state.last_edit_after_approval,
            "approve_error": state.approve_error,
            "last_announce": state.last_announce,
        },
    }


def from_row(pack_id: str, row: dict[str, Any]) -> ReviewState:
    rs = default_ruleset()
    rv = row.get("review") or {}
    # An approval given under another rule set version does not carry over: it must be re-verified.
    same_rules = row.get("rule_set_version") == rs.label
    return ReviewState(
        pack_id=pack_id,
        product=row["name"],
        truth=ProductTruth.model_validate(row["truth"]),
        pack=PDPPack.model_validate(row["pack"]) if row.get("pack") else None,
        ruleset=rs,
        kept={(k["sid"], k["rule_id"], k["matched"]): Keep(k["reason"], k["evidence"]) for k in rv.get("kept", [])},
        rewrites=dict(rv.get("rewrites", {})),
        reported={(s, r) for s, r in rv.get("reported", [])},
        approved=bool(rv.get("approved")) and same_rules,
        last_edit_after_approval=bool(rv.get("last_edit_after_approval")),
        approve_error=rv.get("approve_error"),
        last_announce=rv.get("last_announce", ""),
    )
