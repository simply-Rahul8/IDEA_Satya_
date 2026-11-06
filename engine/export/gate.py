"""Export gate: nothing flagged red (or otherwise unapproved) may leave the engine (P17, P25)."""

from __future__ import annotations

from engine.models import ClaimStatus, PDPPack, ProductTruth, Severity
from engine.pipeline import approval_status


class ExportBlocked(Exception):
    def __init__(self, blockers: list[str]):
        self.blockers = blockers
        super().__init__("export blocked: " + "; ".join(blockers))


def export_blockers(pack: PDPPack, truth: ProductTruth) -> list[str]:
    """Everything stopping an export. Stricter than approval_status: it re-checks the pack itself, so a pack
    that was edited around the pipeline still cannot ship a red or non-overridable flag."""
    blockers = list(approval_status(pack, truth).blockers)
    for sec in pack.sections:
        for i, s in enumerate(sec.sentences):
            for f in s.flags:
                if not f.overridable and f.severity != Severity.RED:
                    blockers.append(f"{sec.key}[{i}]: non-overridable {f.rule_id} must be red")
                if not f.overridable and f.override_reason:
                    blockers.append(f"{sec.key}[{i}]: non-overridable {f.rule_id} carries an override")
            for a in s.anchors:
                if a.startswith("claim:"):
                    c = truth.claim(a.removeprefix("claim:"))
                    if c is None or c.status != ClaimStatus.CONFIRMED:
                        blockers.append(f"{sec.key}[{i}]: anchor {a} is not a confirmed claim")
    return list(dict.fromkeys(blockers))


def ensure_exportable(pack: PDPPack, truth: ProductTruth) -> None:
    blockers = export_blockers(pack, truth)
    if blockers:
        raise ExportBlocked(blockers)
