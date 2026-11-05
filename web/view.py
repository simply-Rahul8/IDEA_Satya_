"""View-model helpers shared by the checker and review pages. Pure functions, no I/O.

Engine -> UI vocabulary (docs/design/final/foundations.md section 1): engine `red` -> UI `red` (Blocked),
engine `orange` -> UI `amber` (Review). Rule-set labels always come from the RuleSet, never from literals.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass

from markupsafe import Markup, escape

from engine.rules import RuleSet
from engine.rules.matcher import Flag

UI_SEVERITY = {"red": "red", "orange": "amber"}
RISK_WORDS = {0: "No flagged risks", 2: "Moderate risk", 3: "Elevated risk", 4: "High risk", 5: "Severe risk"}


@dataclass(frozen=True)
class Mark:
    start: int
    end: int
    sev: str  # red | amber
    rule_id: str


def ui_sev(engine_severity: str) -> str:
    return UI_SEVERITY[str(engine_severity)]


def marks_from_flags(flags: Sequence[Flag]) -> list[Mark]:
    return [Mark(f.start, f.end, ui_sev(f.severity), f.rule_id) for f in flags]


def build_backdrop(text: str, marks: Sequence[Mark]) -> Markup:
    """The mirrored text with flagged ranges wrapped in <mark>. Every segment is escaped one by one.

    Offsets are Python code points (the server owns them; the client never computes offsets). Where two rules
    overlap, the more severe one colours the overlap. A trailing newline gets a space so the mirror keeps the
    textarea's height.
    """
    cuts = sorted({0, len(text), *(m.start for m in marks), *(m.end for m in marks)})
    cuts = [c for c in cuts if 0 <= c <= len(text)]
    out: list[Markup] = []
    for a, b in zip(cuts, cuts[1:], strict=False):
        seg = text[a:b]
        covering = [m for m in marks if m.start <= a and b <= m.end]
        if not covering:
            out.append(escape(seg))
            continue
        top = next((m for m in covering if m.sev == "red"), covering[0])
        out.append(
            Markup('<mark class="hl hl-{}" data-key="{}">{}</mark>').format(top.sev, f"{top.rule_id}:{seg}", seg)
        )
    if text.endswith("\n"):
        out.append(Markup(" "))
    return Markup("").join(out)


def risk_level(flags: Sequence[Flag]) -> int:
    red = sum(1 for f in flags if f.severity == "red")
    orange = sum(1 for f in flags if f.severity == "orange")
    if red >= 2:
        return 5
    if red == 1:
        return 4
    if orange >= 3:
        return 3
    if orange >= 1:
        return 2
    return 0


def tally(flags: Sequence[Flag]) -> tuple[int, int]:
    red = sum(1 for f in flags if f.severity == "red")
    return red, len(flags) - red


def result_signature(flags: Sequence[Flag]) -> str:
    """Changes only when the announced outcome changes (level + rule ids + phrases)."""
    raw = "|".join(f"{f.rule_id}:{f.text}" for f in flags)
    return hashlib.sha1(raw.encode()).hexdigest()[:10]  # noqa: S324 - change detection, not security


def announce(flags: Sequence[Flag], ruleset: RuleSet) -> str:
    if not flags:
        return f"No flagged risks under rule set {ruleset.label}."
    red, orange = tally(flags)
    parts = []
    if red:
        parts.append(f"{red} blocked")
    if orange:
        parts.append(f"{orange} to review")
    return f"{', '.join(parts)} under rule set {ruleset.label}."


def sort_flags(flags: Sequence[Flag]) -> list[Flag]:
    """Red before amber; within a severity, text order."""
    return sorted(flags, key=lambda f: (0 if f.severity == "red" else 1, f.start, f.rule_id))


def override_label(overridable: bool, severity: str, allow_red_override: bool = True) -> tuple[str, str]:
    """(short, long) policy wording for a rule (ADR-10)."""
    if not overridable:
        return "Cannot be overridden", "No. This rule cannot be overridden."
    if ui_sev(severity) == "red":
        if allow_red_override:
            return "Evidence can override", "Yes, with an evidence reference."
        return "Cannot be overridden", "No. Rewrite or remove it."
    return "Needs a reason", "Yes, with a written reason."
