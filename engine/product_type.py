"""Product-type gate (P23): v1 is cosmetics only; Ayurvedic/AYUSH/OTC-drug are refused. Owner: Rules agent.

Signals live in engine/rules/product_type.yaml (DRAFT until consultant sign-off, P20).
The gate reads listing text as data (P19). It cannot verify a licence, so a clean pass means
"no non-cosmetic signals found", never "this is a cosmetic".
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from engine.rules.ruleset import RuleSet, default_ruleset
from engine.rules.text import Normalized, analyse, compile_term, find_term


class ProductType(StrEnum):
    COSMETIC = "cosmetic"
    OTC_DRUG = "otc_drug"
    AYUSH = "ayush"
    AYURVEDIC = "ayurvedic"
    OTHER_NON_COSMETIC = "other_non_cosmetic"


class GateStatus(StrEnum):
    ALLOWED = "allowed"
    REFUSED = "refused"
    NEEDS_REVIEW = "needs_review"  # weak signals and no brand declaration of 'cosmetic'


# Most specific regulatory regime first; the first type with a hard signal becomes the reported type.
PRECEDENCE = (ProductType.OTC_DRUG, ProductType.AYUSH, ProductType.AYURVEDIC, ProductType.OTHER_NON_COSMETIC)


@dataclass(frozen=True)
class Signal:
    product_type: ProductType
    strength: str  # "hard", "weak" or "declared"
    field: str
    matched: str


@dataclass(frozen=True)
class GateResult:
    status: GateStatus
    product_type: ProductType
    signals: tuple[Signal, ...]
    explanation: str
    rule_set: str

    @property
    def proceeds(self) -> bool:
        return self.status is GateStatus.ALLOWED


class ProductTypeRefused(Exception):
    def __init__(self, result: GateResult):
        super().__init__(result.explanation)
        self.result = result


def _hits(doc: Normalized, terms: list[str]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for t in terms:
        out.extend(find_term(doc, compile_term(t)))
    return out


def _scan(doc: Normalized, field: str, rs: RuleSet) -> list[Signal]:
    weak_spans = []
    for cfg in rs.gate.types.values():
        weak_spans.extend(_hits(doc, cfg.weak))
    signals: list[Signal] = []
    for name, cfg in rs.gate.types.items():
        ptype = ProductType(name)
        for i, j in _hits(doc, cfg.hard):
            if any(a <= i and j <= b for a, b in weak_spans):  # masked by a weaker, more specific phrase
                continue
            signals.append(Signal(ptype, "hard", field, _snippet(doc, i, j)))
        for i, j in _hits(doc, cfg.weak):
            signals.append(Signal(ptype, "weak", field, _snippet(doc, i, j)))
    return signals


def _snippet(doc: Normalized, i: int, j: int) -> str:
    s, e = doc.original_span(doc.tokens[i].start, doc.tokens[j - 1].end)
    return doc.original[s:e]


def _first_by_precedence(signals: list[Signal], strength: str) -> ProductType | None:
    present = {s.product_type for s in signals if s.strength == strength}
    return next((t for t in PRECEDENCE if t in present), None)


def check_product_type(
    *,
    name: str = "",
    category: str = "",
    description: str = "",
    declared_type: ProductType | str | None = None,
    ruleset: RuleSet | None = None,
) -> GateResult:
    """Decide whether Satya v1 can handle this product. Only ALLOWED may continue to the fix flow."""
    rs = ruleset or default_ruleset()
    declared = ProductType(declared_type) if declared_type else None  # ValueError on junk input

    signals: list[Signal] = []
    for field, text in (("name", name), ("category", category), ("description", description)):
        if text:
            signals.extend(_scan(analyse(text), field, rs))

    if declared and declared is not ProductType.COSMETIC:
        signals.insert(0, Signal(declared, "declared", "declared_type", declared.value))
        return _refused(declared, signals, rs)

    hard = _first_by_precedence(signals, "hard")
    if hard:
        return _refused(hard, signals, rs)

    weak = _first_by_precedence(signals, "weak")
    if weak:
        if declared is ProductType.COSMETIC:
            note = (
                "The listing has some non-cosmetic wording, but the brand declared the product as a cosmetic. "
                "Continuing on that declaration. Satya cannot verify the product's licence."
            )
            return GateResult(GateStatus.ALLOWED, ProductType.COSMETIC, tuple(signals), note, rs.label)
        label = rs.gate.types[weak.value].label
        note = (
            f"The listing has wording that may mean this is not a cosmetic ({label}). Satya v1 reviews cosmetics only. "
            "Confirm it is a cosmetic and remove the non-cosmetic wording, then run it again."
        )
        return GateResult(GateStatus.NEEDS_REVIEW, weak, tuple(signals), note, rs.label)

    note = (
        "No non-cosmetic signals found in the text provided. "
        "This is a text check only. Satya cannot verify the product's licence or registration."
    )
    return GateResult(GateStatus.ALLOWED, ProductType.COSMETIC, tuple(signals), note, rs.label)


def _refused(ptype: ProductType, signals: list[Signal], rs: RuleSet) -> GateResult:
    cfg = rs.gate.types[ptype.value]
    found = sorted({s.matched for s in signals if s.product_type is ptype and s.strength in ("hard", "declared")})
    detail = f" Found: {', '.join(repr(f) for f in found)}." if found else ""
    text = (
        f"Out of scope for Satya v1: {cfg.label}. {cfg.explanation}{detail} "
        "This is not a finding about whether your product is lawful."
    )
    return GateResult(GateStatus.REFUSED, ptype, tuple(signals), text, rs.label)


def require_cosmetic(**kwargs) -> GateResult:
    """API-level guard: raise ProductTypeRefused unless the product may proceed (P23)."""
    result = check_product_type(**kwargs)
    if not result.proceeds:
        raise ProductTypeRefused(result)
    return result
