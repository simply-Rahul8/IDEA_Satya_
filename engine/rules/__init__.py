"""Rule set loader and reference matcher. *.yaml rules live here; DRAFT until consultant sign-off (P20).

Owner: Rules agent. The Engine agent's guardrails runner should call `evaluate`, not re-implement matching.
"""

from engine.rules.matcher import Flag, evaluate
from engine.rules.policy import OverrideNotAllowed, check_override, hard_blocks
from engine.rules.ruleset import RuleSet, RuleSetError, default_ruleset, load_ruleset
from engine.rules.wording import summary_line

__all__ = [
    "Flag",
    "OverrideNotAllowed",
    "RuleSet",
    "RuleSetError",
    "check_override",
    "default_ruleset",
    "evaluate",
    "hard_blocks",
    "load_ruleset",
    "summary_line",
]
