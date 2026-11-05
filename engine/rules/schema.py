"""Pydantic models for rule files (DRAFT until consultant sign-off, P20)."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Severity(StrEnum):
    RED = "red"
    ORANGE = "orange"


class Category(StrEnum):
    DRUG_TREATMENT = "drug_treatment"
    DMR_DISEASE = "dmr_disease"
    FAIRNESS = "fairness"
    COSMETIC_CLAIM = "cosmetic_claim"


# P17: these can never be overridden by a user, a brand setting or an allowlist-less config flip.
NON_OVERRIDABLE_CATEGORIES = frozenset({Category.DRUG_TREATMENT, Category.DMR_DISEASE, Category.FAIRNESS})

ID_PREFIX = {
    Category.DRUG_TREATMENT: "EN-DRUG-",
    Category.DMR_DISEASE: "EN-DMR-",
    Category.FAIRNESS: "EN-FAIR-",
    Category.COSMETIC_CLAIM: "EN-CLAIM-",
}


class Citation(Strict):
    ref: str = Field(min_length=3)
    provision: str = Field(min_length=1)
    # Every citation starts unverified; the consultant flips this (and records it in README sign-off log).
    verified: bool = False


class VerbCondition(Strict):
    """A verb (action) term followed by a condition term inside the same sentence.

    Terms are whitespace-separated tokens; a trailing `*` on a token is a prefix wildcard.
    With order=any the two roles may appear in either order (used for "subject + context" pairs).
    """

    kind: Literal["verb_condition"]
    verbs: list[str] = Field(min_length=1)
    conditions: list[str] = Field(min_length=1)
    max_gap: int = Field(default=4, ge=0, le=12)  # tokens allowed between the two terms
    order: Literal["verb_first", "any"] = "verb_first"


class Phrase(Strict):
    kind: Literal["phrase"]
    phrases: list[str] = Field(min_length=1)


class RegexPattern(Strict):
    """Escape hatch for numbers and percentages. Runs on normalised lowercase text."""

    kind: Literal["regex"]
    regex: str = Field(min_length=1)


Pattern = Annotated[VerbCondition | Phrase | RegexPattern, Field(discriminator="kind")]


class Examples(Strict):
    positive: list[str] = Field(min_length=1)
    negative: list[str] = Field(min_length=1)


class Rule(Strict):
    id: str
    category: Category
    title: str
    severity: Severity
    overridable: bool
    explanation: str  # why it is flagged, shown to the user
    rewrite_hint: str  # direction for a claim-safe rewrite
    patterns: list[Pattern] = Field(min_length=1)
    sources: list[Citation] = Field(min_length=1)
    examples: Examples
    open_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> Rule:
        if not self.id.startswith(ID_PREFIX[self.category]):
            raise ValueError(f"{self.id}: id must start with {ID_PREFIX[self.category]} for {self.category}")
        if self.category in NON_OVERRIDABLE_CATEGORIES and (self.overridable or self.severity != Severity.RED):
            raise ValueError(f"{self.id}: {self.category} rules must be red and non-overridable (P17)")
        return self


class AllowEntry(Strict):
    """Safe phrases (P24). For the rules in `applies_to`, words inside one of these phrases cannot trigger a flag."""

    id: str
    phrases: list[str] = Field(min_length=1)
    applies_to: list[str] = Field(min_length=1)  # explicit rule ids only, never a wildcard
    note: str
    examples: list[str] = Field(min_length=1)  # sentences that would be flagged without this entry


class GateType(Strict):
    label: str
    hard: list[str] = Field(default_factory=list)  # any hit refuses the product
    weak: list[str] = Field(default_factory=list)  # hit needs a review or a brand declaration
    explanation: str
    examples: Examples


class GateConfig(Strict):
    version_note: str
    types: dict[str, GateType]


class Meta(Strict):
    name: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    status: Literal["DRAFT", "SIGNED_OFF"]
    language: Literal["en"]
    updated: str
