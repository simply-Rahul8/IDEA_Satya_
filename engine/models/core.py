"""Pydantic v2 models shared by engine, api, web and export (plan section 5; P4, P25)."""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class Severity(StrEnum):
    SAFE = "safe"
    ORANGE = "orange"  # warning: approval needs a reason
    RED = "red"  # blocks approval


class SentenceType(StrEnum):
    PRODUCT_FACT = "product_fact"
    BENEFIT_CLAIM = "benefit_claim"
    USAGE = "usage"
    WARNING = "warning"
    STORAGE = "storage"
    LEGAL = "legal"
    DESCRIPTIVE = "descriptive"


class EvidenceType(StrEnum):
    TEST_REPORT = "test_report"  # needs a file or document reference (P25)
    INGREDIENT_LIST = "ingredient_list"
    LABEL = "label"
    BRAND_DECLARATION = "brand_declaration"
    OTHER = "other"


class ClaimStatus(StrEnum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Evidence(BaseModel):
    type: EvidenceType
    reference: str | None = None  # file upload path or document ID
    note: str | None = None


class Claim(BaseModel):
    id: str
    text: str
    status: ClaimStatus = ClaimStatus.UNCONFIRMED
    evidence: Evidence | None = None
    hard_blocked: bool = False  # hit a non-overridable rule; can never be confirmed (P17, P25)
    blocking_rule_ids: list[str] = Field(default_factory=list)


class ProductTruth(BaseModel):
    """The approved facts a PDP may be written from. LLM pre-fills; the user confirms each claim."""

    product_name: str
    brand: str | None = None
    category: str | None = None
    size: str | None = None
    ingredients: list[str] = Field(default_factory=list)
    how_to_use: str | None = None
    warnings: str | None = None
    storage: str | None = None
    manufacturer: str | None = None
    country_of_origin: str | None = None
    claims: list[Claim] = Field(default_factory=list)

    def claim(self, claim_id: str) -> Claim | None:
        return next((c for c in self.claims if c.id == claim_id), None)

    def confirmed_claims(self) -> list[Claim]:
        return [c for c in self.claims if c.status == ClaimStatus.CONFIRMED]

    def field_names(self) -> set[str]:
        return set(type(self).model_fields) - {"claims"}


ANCHOR_RE = re.compile(r"^(claim|truth):[\w.\-]+$")


class Flag(BaseModel):
    rule_id: str
    severity: Severity
    reason: str
    citation: str | None = None
    suggestion: str | None = None
    matched_text: str | None = None
    overridable: bool = True
    source: str = "rule"  # rule | anchor | verifier
    override_reason: str | None = None


class Sentence(BaseModel):
    text: str
    type: SentenceType
    anchors: list[str] = Field(default_factory=list)  # "claim:<id>" or "truth:<field>"
    flags: list[Flag] = Field(default_factory=list)

    @field_validator("anchors")
    @classmethod
    def _anchor_format(cls, v: list[str]) -> list[str]:
        for a in v:
            if not ANCHOR_RE.match(a):
                raise ValueError(f"bad anchor {a!r}; expected 'claim:<id>' or 'truth:<field>'")
        return v

    @property
    def severity(self) -> Severity:
        if any(f.severity == Severity.RED for f in self.flags):
            return Severity.RED
        if any(f.severity == Severity.ORANGE for f in self.flags):
            return Severity.ORANGE
        return Severity.SAFE


SECTION_KEYS = (
    "title", "bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5",
    "description", "how_to_use", "warnings_storage", "seo_title", "seo_description",
)  # fmt: skip


class Section(BaseModel):
    key: str
    sentences: list[Sentence]

    @field_validator("key")
    @classmethod
    def _key(cls, v: str) -> str:
        if v not in SECTION_KEYS:
            raise ValueError(f"unknown section {v!r}")
        return v


class PDPPack(BaseModel):
    sections: list[Section]
    rule_set_version: str | None = None
    verifier_passed: bool = False  # set by verify_pack; cleared by any edit

    @model_validator(mode="after")
    def _complete(self) -> PDPPack:
        keys = [s.key for s in self.sections]
        if sorted(keys) != sorted(SECTION_KEYS):
            raise ValueError(f"pack needs exactly sections {SECTION_KEYS}, got {keys}")
        return self

    def section(self, key: str) -> Section:
        return next(s for s in self.sections if s.key == key)

    def sentences(self) -> list[Sentence]:
        return [s for sec in self.sections for s in sec.sentences]
