"""Reference matcher: verb + condition patterns, phrases and regexes, minus the safe-phrase allowlist (P24)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from engine.rules.schema import AllowEntry, Category, Phrase, RegexPattern, Rule, Severity, VerbCondition
from engine.rules.text import Normalized, Term, analyse, compile_term, find_term

if TYPE_CHECKING:
    from engine.rules.ruleset import RuleSet

Span = tuple[int, int]  # normalised char offsets


@dataclass(frozen=True)
class Flag:
    rule_id: str
    category: Category
    severity: Severity
    overridable: bool
    start: int  # offsets into the text the caller passed in
    end: int
    text: str
    message: str
    rule_set: str  # label such as "v0.1.0-draft"


@dataclass(frozen=True)
class CompiledRule:
    rule: Rule
    verb_condition: tuple[tuple[VerbCondition, tuple[Term, ...], tuple[Term, ...]], ...]
    phrases: tuple[Term, ...]
    regexes: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class CompiledAllow:
    entry: AllowEntry
    phrases: tuple[Term, ...]


def compile_rule(rule: Rule) -> CompiledRule:
    vcs, phrases, regexes = [], [], []
    for p in rule.patterns:
        if isinstance(p, VerbCondition):
            vcs.append((p, tuple(map(compile_term, p.verbs)), tuple(map(compile_term, p.conditions))))
        elif isinstance(p, Phrase):
            phrases.extend(map(compile_term, p.phrases))
        elif isinstance(p, RegexPattern):
            regexes.append(re.compile(p.regex))
    return CompiledRule(rule, tuple(vcs), tuple(phrases), tuple(regexes))


def compile_allow(entry: AllowEntry) -> CompiledAllow:
    return CompiledAllow(entry, tuple(map(compile_term, entry.phrases)))


def _spans(doc: Normalized, terms: tuple[Term, ...]) -> list[tuple[int, int]]:
    out = []
    for t in terms:
        out.extend(find_term(doc, t))
    return out


def _tok_span(doc: Normalized, i: int, j: int) -> Span:
    return doc.tokens[i].start, doc.tokens[j - 1].end


def _visible(doc: Normalized, hits: list[tuple[int, int]], masks: list[Span]) -> list[tuple[int, int]]:
    """Drop term hits that lie inside an allowlisted phrase (P24)."""
    out = []
    for i, j in hits:
        s, e = _tok_span(doc, i, j)
        if not any(a <= s and e <= b for a, b in masks):
            out.append((i, j))
    return out


def _rule_spans(doc: Normalized, cr: CompiledRule, masks: list[Span]) -> list[Span]:
    spans: list[Span] = []
    for p, verbs, conds in cr.verb_condition:
        cond_hits = _visible(doc, _spans(doc, conds), masks)
        for vi, vj in _visible(doc, _spans(doc, verbs), masks):
            for ci, cj in cond_hits:
                if doc.tokens[vi].sentence != doc.tokens[ci].sentence:
                    continue
                if ci >= vj:
                    gap = ci - vj
                elif p.order == "any" and vi >= cj:
                    gap = vi - cj
                else:
                    continue
                if gap <= p.max_gap:
                    spans.append(_tok_span(doc, min(vi, ci), max(vj, cj)))
    spans.extend(_tok_span(doc, i, j) for i, j in _visible(doc, _spans(doc, cr.phrases), masks))
    for rx in cr.regexes:
        spans.extend(m.span() for m in rx.finditer(doc.text) if m.end() > m.start())
    return [s for s in spans if not any(a <= s[0] and s[1] <= b for a, b in masks)]


def _merge(spans: list[Span]) -> list[Span]:
    merged: list[Span] = []
    for s, e in sorted(set(spans)):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    return merged


def evaluate(text: str, ruleset: RuleSet) -> list[Flag]:
    """Return flags for `text`, ordered by position. Pure and deterministic; no network, no LLM."""
    doc = analyse(text)
    allow = [(a, _allow_spans(doc, a)) for a in ruleset.compiled_allow]
    flags: list[Flag] = []
    for cr in ruleset.compiled_rules:
        masks = [span for a, spans in allow if cr.rule.id in a.entry.applies_to for span in spans]
        for s, e in _merge(_rule_spans(doc, cr, masks)):
            o_start, o_end = doc.original_span(s, e)
            flags.append(
                Flag(
                    rule_id=cr.rule.id,
                    category=cr.rule.category,
                    severity=cr.rule.severity,
                    overridable=cr.rule.overridable,
                    start=o_start,
                    end=o_end,
                    text=text[o_start:o_end],
                    message=cr.rule.explanation,
                    rule_set=ruleset.label,
                )
            )
    return sorted(flags, key=lambda f: (f.start, f.rule_id))


def _allow_spans(doc: Normalized, allow: CompiledAllow) -> list[Span]:
    return [_tok_span(doc, i, j) for i, j in _spans(doc, allow.phrases)]
