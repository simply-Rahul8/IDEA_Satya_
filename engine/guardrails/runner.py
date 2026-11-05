"""Deterministic guardrails runner: verb+condition patterns plus a safe-phrase allowlist (P24)."""

from __future__ import annotations

import re
import unicodedata

from engine.guardrails.ruleset import Rule, RuleSet
from engine.models import Flag, PDPPack, Sentence

_FLAGS = re.IGNORECASE | re.UNICODE


def normalize(text: str) -> str:
    """NFC so Devanagari forms compare equal (P6); whitespace collapsed."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def _spans(rule: Rule, text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for pat in rule.patterns:
        if pat.regex is not None:
            out += [m.span() for m in re.finditer(pat.regex, text, _FLAGS)]
            continue
        conds = [m.span() for m in re.finditer(pat.condition, text, _FLAGS)]
        for v in re.finditer(pat.verb, text, _FLAGS):
            for cs, ce in conds:
                if v.end() <= cs <= v.end() + pat.window and not re.search(r"[.!?\n]", text[v.end() : cs]):
                    out.append((v.start(), ce))
                    break
    return out


def check_text(text: str, ruleset: RuleSet) -> list[Flag]:
    t = normalize(text)
    flags: list[Flag] = []
    for rule in ruleset.rules:
        allowed = [m.span() for a in rule.allowlist for m in re.finditer(a, t, _FLAGS)]
        for s, e in _spans(rule, t):
            if any(a0 < e and s < a1 for a0, a1 in allowed):
                continue
            flags.append(
                Flag(
                    rule_id=rule.id,
                    severity=rule.sev,
                    reason=rule.reason,
                    citation=f"{rule.citation} [{ruleset.label}]",
                    suggestion=rule.suggestion,
                    matched_text=t[s:e],
                    overridable=rule.overridable,
                )
            )
            break  # one flag per rule per sentence
    return flags


def check_sentence(sentence: Sentence, ruleset: RuleSet) -> Sentence:
    kept = [f for f in sentence.flags if f.source != "rule"]
    return sentence.model_copy(update={"flags": kept + check_text(sentence.text, ruleset)})


def check_pack(pack: PDPPack, ruleset: RuleSet) -> PDPPack:
    sections = [
        sec.model_copy(update={"sentences": [check_sentence(s, ruleset) for s in sec.sentences]})
        for sec in pack.sections
    ]
    return pack.model_copy(update={"sections": sections, "rule_set_version": ruleset.version})


def verify_rule_examples(ruleset: RuleSet) -> list[str]:
    """Return failures: every rule must flag its positives and not flag its negatives (AGENTS.md)."""
    bad: list[str] = []
    for rule in ruleset.rules:
        one = ruleset.model_copy(update={"rules": [rule]})
        bad += [f"{rule.id}: missed positive {x!r}" for x in rule.examples.positive if not check_text(x, one)]
        bad += [f"{rule.id}: flagged negative {x!r}" for x in rule.examples.negative if check_text(x, one)]
    return bad
