"""Claim-confirmation guards (P25): extraction must not launder risky claims into the approved set."""

from __future__ import annotations

from engine.guardrails.ruleset import RuleSet
from engine.guardrails.runner import check_text
from engine.models import Claim, ClaimStatus, Evidence, EvidenceType


class ClaimGuardError(ValueError):
    pass


def hard_blocks(text: str, ruleset: RuleSet) -> list[str]:
    """IDs of non-overridable rules (drug/DMR/fairness) the text hits."""
    return [f.rule_id for f in check_text(text, ruleset) if not f.overridable]


def screen_claim(claim: Claim, ruleset: RuleSet) -> Claim:
    ids = hard_blocks(claim.text, ruleset)
    return claim.model_copy(update={"hard_blocked": bool(ids), "blocking_rule_ids": ids})


def confirm_claim(claim: Claim, evidence: Evidence, ruleset: RuleSet) -> Claim:
    """Return the claim confirmed with evidence, or raise ClaimGuardError. Re-screens against the rules so a
    stale or tampered `hard_blocked=False` cannot slip through."""
    ids = hard_blocks(claim.text, ruleset)
    if claim.hard_blocked or ids:
        raise ClaimGuardError(
            f"claim {claim.id} is hard-blocked ({', '.join(ids or claim.blocking_rule_ids)}) and cannot be confirmed"
        )
    if evidence.type == EvidenceType.TEST_REPORT and not (evidence.reference or "").strip():
        raise ClaimGuardError("test_report evidence needs a file or document reference")
    return claim.model_copy(update={"status": ClaimStatus.CONFIRMED, "evidence": evidence})
