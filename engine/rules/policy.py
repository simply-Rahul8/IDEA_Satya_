"""Non-overridable enforcement (P17) and claim-confirmation guard (P25).

The API layer must call these before it accepts an override or confirms an extracted claim.
They read the rule files, so a brand setting or a request flag cannot flip them.
"""

from __future__ import annotations

from engine.rules.matcher import Flag, evaluate
from engine.rules.ruleset import RuleSet, default_ruleset


class OverrideNotAllowed(PermissionError):
    def __init__(self, rule_id: str, category: str):
        super().__init__(f"{rule_id} ({category}) is a non-overridable block and cannot be overridden")
        self.rule_id = rule_id
        self.category = category


def check_override(rule_id: str, ruleset: RuleSet | None = None) -> None:
    """Raise OverrideNotAllowed for hard blocks; KeyError for an unknown rule id."""
    rule = (ruleset or default_ruleset()).rule(rule_id)
    if not rule.overridable:
        raise OverrideNotAllowed(rule.id, rule.category.value)


def hard_blocks(text: str, ruleset: RuleSet | None = None) -> list[Flag]:
    """Non-overridable flags in `text`. A claim with any of these can never be confirmed (P25)."""
    rs = ruleset or default_ruleset()
    return [f for f in evaluate(text, rs) if not f.overridable]
