"""Hindi lexicon (DRAFT until the native Hindi reviewer signs off, SAT-5 / plan P20).

`lexicon_hi.yaml` holds Hindi rules in three written forms (Devanagari, transliterated Roman, Hinglish mix). Each rule
maps to an English rule, inherits its severity and non-overridability, and ships positive and negative examples in HI
and EN. `check_hindi` is deterministic: no network, no LLM. It reads text only and never claims "compliant".
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.normalize.hindi import analyse_hi, compile_term_hi
from engine.rules import RuleSet, default_ruleset
from engine.rules.text import Normalized, find_term

LEXICON_PATH = Path(__file__).resolve().parent / "lexicon_hi.yaml"
FORMS = ("devanagari", "transliterated", "hinglish")
Form = Literal["devanagari", "transliterated", "hinglish"]
_NON_OVERRIDABLE = {"drug_treatment", "dmr_disease", "fairness"}
_PREFIX = {"drug_treatment": "HI-DRUG-", "dmr_disease": "HI-DMR-", "fairness": "HI-FAIR-"}


class LexiconError(ValueError):
    """The lexicon file is inconsistent. Fail loudly: a half-loaded lexicon must never run."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VerbCondition(_Strict):
    kind: Literal["verb_condition"]
    form: Form
    verbs: list[str] = Field(min_length=1)
    conditions: list[str] = Field(min_length=1)
    max_gap: int = Field(default=4, ge=0, le=12)
    order: Literal["verb_first", "any"] = "any"  # Hindi is verb-final: "एक्ज़िमा ठीक करे"


class Phrase(_Strict):
    kind: Literal["phrase"]
    form: Form
    phrases: list[str] = Field(min_length=1)


Pattern = Annotated[VerbCondition | Phrase, Field(discriminator="kind")]


class Example(_Strict):
    text: str
    form: Form


class Examples(_Strict):
    hi_positive: list[Example] = Field(min_length=1)
    hi_negative: list[Example] = Field(min_length=1)
    # English source sentences: positives are flagged by `maps_to` in the English rule set, negatives are not.
    en_positive: list[str] = Field(min_length=1)
    en_negative: list[str] = Field(min_length=1)


class HiRule(_Strict):
    id: str
    category: Literal["drug_treatment", "dmr_disease", "fairness"]
    maps_to: str  # English rule id this mirrors
    title: str
    severity: Literal["red"] = "red"
    overridable: bool = False
    explanation: str  # English: the product UI is English-only in v1
    rewrite_hint: str
    patterns: list[Pattern] = Field(min_length=1)
    examples: Examples
    open_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> HiRule:
        if not self.id.startswith(_PREFIX[self.category]):
            raise ValueError(f"{self.id}: id must start with {_PREFIX[self.category]}")
        if self.category in _NON_OVERRIDABLE and self.overridable:
            raise ValueError(f"{self.id}: {self.category} rules must be non-overridable (P17)")
        return self


class HiAllow(_Strict):
    id: str
    phrases: list[str] = Field(min_length=1)
    applies_to: list[str] = Field(min_length=1)
    note: str
    examples: list[str] = Field(min_length=1)


class HiMeta(_Strict):
    name: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    status: Literal["DRAFT", "SIGNED_OFF"]
    language: Literal["hi"]
    updated: str
    reviewer: str  # who must sign off; stays DRAFT until then


class HiFlag(_Strict):
    rule_id: str
    maps_to: str
    category: str
    form: str
    severity: str
    overridable: bool
    start: int  # offsets into the text the caller passed in
    end: int
    text: str
    message: str
    lexicon: str  # label such as "hi-v0.1.0-draft"


@dataclass(frozen=True)
class _CompiledPattern:
    form: str
    verbs: tuple = ()
    conditions: tuple = ()
    phrases: tuple = ()
    max_gap: int = 0
    any_order: bool = False


@dataclass(frozen=True)
class Lexicon:
    meta: HiMeta
    rules: tuple[HiRule, ...]
    allowlist: tuple[HiAllow, ...]
    _patterns: dict = None  # rule id -> tuple[_CompiledPattern]
    _allow: dict = None  # rule id -> tuple of compiled phrase terms

    @property
    def label(self) -> str:
        return f"hi-v{self.meta.version}" + ("-draft" if self.meta.status == "DRAFT" else "")

    @property
    def is_signed_off(self) -> bool:
        return self.meta.status == "SIGNED_OFF"

    def rule(self, rule_id: str) -> HiRule:
        for r in self.rules:
            if r.id == rule_id:
                return r
        raise KeyError(rule_id)


def load_lexicon(path: Path | str | None = None, english: RuleSet | None = None) -> Lexicon:
    data = yaml.safe_load(Path(path or LEXICON_PATH).read_text(encoding="utf-8")) or {}
    unknown = set(data) - {"lexicon", "rules", "allowlist"}
    if unknown:
        raise LexiconError(f"unknown top-level keys {sorted(unknown)}")
    meta = HiMeta.model_validate(data["lexicon"])
    rules = tuple(HiRule.model_validate(r) for r in data.get("rules", []))
    allow = tuple(HiAllow.model_validate(a) for a in data.get("allowlist", []))
    en = english or default_ruleset()
    ids = [r.id for r in rules]
    if len(set(ids)) != len(ids):
        raise LexiconError("duplicate Hindi rule ids")
    for r in rules:
        try:
            en_rule = en.rule(r.maps_to)
        except KeyError:
            raise LexiconError(f"{r.id}: maps_to unknown English rule {r.maps_to}") from None
        if en_rule.category.value != r.category or en_rule.overridable:
            raise LexiconError(f"{r.id}: category/overridability must match {r.maps_to} (P17)")
        missing = set(FORMS) - {p.form for p in r.patterns}
        if missing:
            raise LexiconError(f"{r.id}: no pattern for forms {sorted(missing)}")
    for a in allow:
        if set(a.applies_to) - set(ids):
            raise LexiconError(f"{a.id}: applies_to unknown Hindi rules")
    pats = {r.id: tuple(_compile(p) for p in r.patterns) for r in rules}
    allow_c = {
        r.id: tuple(compile_term_hi(ph) for a in allow if r.id in a.applies_to for ph in a.phrases) for r in rules
    }
    return Lexicon(meta, rules, allow, pats, allow_c)


def _compile(p: VerbCondition | Phrase) -> _CompiledPattern:
    if isinstance(p, Phrase):
        return _CompiledPattern(p.form, phrases=tuple(map(compile_term_hi, p.phrases)))
    return _CompiledPattern(
        p.form,
        verbs=tuple(map(compile_term_hi, p.verbs)),
        conditions=tuple(map(compile_term_hi, p.conditions)),
        max_gap=p.max_gap,
        any_order=p.order == "any",
    )


@cache
def default_lexicon() -> Lexicon:
    return load_lexicon()


def _hits(doc: Normalized, terms: tuple, masks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out = []
    for t in terms:
        for i, j in find_term(doc, t):
            s, e = doc.tokens[i].start, doc.tokens[j - 1].end
            if not any(a <= s and e <= b for a, b in masks):
                out.append((i, j))
    return out


def _spans(doc: Normalized, p: _CompiledPattern, masks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    toks, spans = doc.tokens, []
    if p.phrases:
        for i, j in _hits(doc, p.phrases, masks):
            spans.append((toks[i].start, toks[j - 1].end))
        return spans
    conds = _hits(doc, p.conditions, masks)
    for vi, vj in _hits(doc, p.verbs, masks):
        for ci, cj in conds:
            if toks[vi].sentence != toks[ci].sentence:
                continue
            if ci >= vj:
                gap = ci - vj
            elif p.any_order and vi >= cj:
                gap = vi - cj
            else:
                continue
            if gap <= p.max_gap:
                spans.append((toks[min(vi, ci)].start, toks[max(vj, cj) - 1].end))
    return spans


def _merge(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    merged: list[tuple[int, int, str]] = []
    for s, e, form in sorted(set(spans)):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]), merged[-1][2])
        else:
            merged.append((s, e, form))
    return merged


def check_hindi(text: str, lexicon: Lexicon | None = None) -> list[HiFlag]:
    """Flags for Hindi, transliterated or Hinglish `text`, ordered by position. Pure and deterministic."""
    lx = lexicon or default_lexicon()
    doc = analyse_hi(text)
    flags: list[HiFlag] = []
    for rule in lx.rules:
        masks = []
        for t in lx._allow[rule.id]:
            masks.extend((doc.tokens[i].start, doc.tokens[j - 1].end) for i, j in find_term(doc, t))
        spans = [(s, e, p.form) for p in lx._patterns[rule.id] for s, e in _spans(doc, p, masks)]
        for s, e, form in _merge(spans):
            o_start, o_end = doc.original_span(s, e)
            flags.append(
                HiFlag(
                    rule_id=rule.id,
                    maps_to=rule.maps_to,
                    category=rule.category,
                    form=form,
                    severity=rule.severity,
                    overridable=rule.overridable,
                    start=o_start,
                    end=o_end,
                    text=text[o_start:o_end],
                    message=rule.explanation,
                    lexicon=lx.label,
                )
            )
    return sorted(flags, key=lambda f: (f.start, f.rule_id))


def hard_blocks_hindi(text: str, lexicon: Lexicon | None = None) -> list[HiFlag]:
    """Non-overridable Hindi flags. A claim with any of these can never be confirmed (P17, P25)."""
    return [f for f in check_hindi(text, lexicon) if not f.overridable]


def summary_line_hi(flags: list[HiFlag], lexicon: Lexicon | None = None) -> str:
    """Report line in Hindi. Never says "compliant"/"अनुपालन": only flagged risks under a lexicon version. DRAFT."""
    lx = lexicon or default_lexicon()
    if flags:
        line = f"{len(flags)} चिह्नित जोखिम ({lx.label})।"
    else:
        line = f"{lx.label} के अंतर्गत कोई चिह्नित जोखिम नहीं।"
    draft = "" if lx.is_signed_off else " यह मसौदा है और अभी किसी हिंदी समीक्षक ने इसे मंज़ूर नहीं किया है।"
    return f"{line} यह कानूनी सलाह नहीं है।{draft}"
