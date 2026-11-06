"""Guardrails runner: a thin adapter from the reference matcher (engine.rules.evaluate, ADR-9) to engine Flags."""

from __future__ import annotations

from engine.brand import restricted_flags
from engine.models import Flag, PDPPack, Sentence, Severity
from engine.rules import RuleSet, default_ruleset, evaluate


def check_text(text: str, ruleset: RuleSet | None = None, restricted: tuple[str, ...] = ()) -> list[Flag]:
    """One flag per rule per text, then the brand's restricted phrases (review-level, source 'brand').

    Rule citations carry the rule's sources and the rule-set label (never 'compliant')."""
    rs = ruleset or default_ruleset()
    flags: list[Flag] = []
    for f in evaluate(text, rs):
        if any(x.rule_id == f.rule_id for x in flags):
            continue
        rule = rs.rule(f.rule_id)
        sources = "; ".join(f"{s.ref} {s.provision}" for s in rule.sources)
        flags.append(
            Flag(
                rule_id=f.rule_id,
                severity=Severity(f.severity.value),
                reason=f.message,
                citation=f"{sources} [rule set {rs.label}]",
                suggestion=rule.rewrite_hint,
                matched_text=f.text,
                overridable=f.overridable,
            )
        )
    return flags + restricted_flags(text, restricted)


def check_sentence(sentence: Sentence, ruleset: RuleSet | None = None, restricted: tuple[str, ...] = ()) -> Sentence:
    kept = [f for f in sentence.flags if f.source not in ("rule", "brand")]
    return sentence.model_copy(update={"flags": kept + check_text(sentence.text, ruleset, restricted)})


def check_pack(pack: PDPPack, ruleset: RuleSet | None = None, restricted: tuple[str, ...] = ()) -> PDPPack:
    rs = ruleset or default_ruleset()
    sections = [
        sec.model_copy(update={"sentences": [check_sentence(s, rs, restricted) for s in sec.sentences]})
        for sec in pack.sections
    ]
    return pack.model_copy(update={"sections": sections, "rule_set_version": rs.label})
