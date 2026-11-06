"""Deterministic per-product scan: product-type gate (P23), rule scan with citations, Legal Metrology fields.

No LLM and no network. Listing text is data (P19). Wording never says "compliant" (P20).
"""

from __future__ import annotations

import re

from engine.audit.models import AuditFlag, AuditItem, ProductRecord, State
from engine.guardrails import check_text
from engine.models import Severity
from engine.product_type import check_product_type
from engine.rules import RuleSet, default_ruleset

# The rule number is unconfirmed (agent pre-review 1c suggests Rule 6(1) and 6(10)): cite none until the
# consultant confirms it. Severity is amber until a rule says otherwise (screen-audit section 1).
LM_TITLE = "Legal Metrology declaration fields (rule reference to be confirmed)"

# rule id, ProductRecord field, plain label, text that also counts as a declaration when found in the listing
_QTY = r"\b\d+(?:\.\d+)?\s?(?:ml|g|gm|gms|kg|l|oz|litre|liter)\b"
LM_FIELDS = (
    ("LM-NET-QUANTITY", "net_quantity", "net quantity", re.compile(_QTY, re.I)),
    ("LM-MRP", "mrp", "MRP", re.compile(r"\b(?:mrp|m\.r\.p)\b|₹\s?\d|\brs\.?\s?\d", re.I)),
    ("LM-MANUFACTURER", "manufacturer", "manufacturer or packer name and address",
     re.compile(r"\b(?:manufactured|marketed|packed|imported)\s+by\b", re.I)),
    ("LM-COUNTRY-OF-ORIGIN", "country_of_origin", "country of origin",
     re.compile(r"\b(?:made in|country of origin)\b", re.I)),
    ("LM-CONSUMER-CARE", "consumer_care", "consumer care contact",
     re.compile(r"\b(?:consumer|customer) care\b|\bgrievance\b", re.I)),
)  # fmt: skip


def missing_lm_fields(p: ProductRecord) -> list[tuple[str, str]]:
    """(rule_id, label) for each declaration field absent from both its own column and the listing text."""
    text = f"{p.name} {p.description}"
    return [
        (rid, label)
        for rid, fld, label, pattern in LM_FIELDS
        if not getattr(p, fld).strip() and not pattern.search(text)
    ]


def _severity(sev: Severity) -> State:
    return State.RED if sev is Severity.RED else State.AMBER


def worst(states) -> State:
    states = set(states)
    return State.RED if State.RED in states else State.AMBER if State.AMBER in states else State.GREEN


def scan_product(p: ProductRecord, position: int = 0, ruleset: RuleSet | None = None) -> AuditItem:
    rs = ruleset or default_ruleset()
    gate = check_product_type(name=p.name, category=p.category, description=p.description, ruleset=rs)
    if not gate.proceeds:
        return AuditItem(sku=p.sku, name=p.name, state=State.SKIPPED, note=gate.explanation, position=position)

    flags: list[AuditFlag] = []
    for text in (p.name, p.description):
        for f in check_text(text, rs):
            if all(x.rule_id != f.rule_id for x in flags):
                flags.append(
                    AuditFlag(
                        rule_id=f.rule_id,
                        title=rs.rule(f.rule_id).title,
                        severity=_severity(f.severity),
                        citation=f.citation,
                        matched_text=f.matched_text,
                    )
                )
    missing = missing_lm_fields(p)
    flags.extend(AuditFlag(rule_id=rid, title=LM_TITLE, severity=State.AMBER) for rid, _ in missing)
    state = worst(f.severity for f in flags) if flags else State.GREEN
    return AuditItem(
        sku=p.sku, name=p.name, state=state, flags=flags, missing_fields=[label for _, label in missing],
        position=position,
    )  # fmt: skip
