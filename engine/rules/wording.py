"""Report wording (DRAFT). Never says "compliant": only "no flagged risks under rule set vX"."""

from __future__ import annotations

from collections.abc import Sequence

from engine.rules.matcher import Flag
from engine.rules.ruleset import RuleSet, default_ruleset

NOT_LEGAL_ADVICE = "Not legal advice."
DRAFT_NOTE = "This rule set is a DRAFT and has not been reviewed by a regulatory consultant."


def summary_line(flags: Sequence[Flag], ruleset: RuleSet | None = None) -> str:
    rs = ruleset or default_ruleset()
    if flags:
        n = len(flags)
        what = "flagged risk" if n == 1 else "flagged risks"
        line = f"{n} {what} under rule set {rs.label}."
    else:
        line = f"No flagged risks under rule set {rs.label}."
    tail = NOT_LEGAL_ADVICE if rs.is_signed_off else f"{NOT_LEGAL_ADVICE} {DRAFT_NOTE}"
    return f"{line} {tail}"
