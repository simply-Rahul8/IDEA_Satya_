"""Rule schema + loader for engine/rules/*.yaml. Rule content is owned by the Rules agent and stays DRAFT until
consultant sign-off (P20). The schema is documented in docs/engine-api.md.

    version: "0.1-draft"
    status: draft
    rules:
      - id: DRUG-001
        category: drug_treatment      # drug_treatment | dmr_disease | fairness | other
        severity: red                 # red | orange
        overridable: false            # must be false for the three hard-block categories (P17)
        language: en                  # en | hi | any
        reason: "..."
        citation: "..."
        suggestion: "..."
        patterns:                     # verb + condition (P24); or a bare `regex`
          - {verb: "cures?|treats?", condition: "acne|eczema", window: 60}
          - {regex: "dermatologically proven"}
        allowlist: ["for acne-prone skin"]
        examples: {positive: ["Cures acne in 7 days"], negative: ["Made for acne-prone skin"]}
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from engine.models import Severity

HARD_BLOCK_CATEGORIES = frozenset({"drug_treatment", "dmr_disease", "fairness"})
DEFAULT_RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


class Pattern(BaseModel):
    verb: str | None = None
    condition: str | None = None
    window: int = 80  # max characters between verb end and condition start
    regex: str | None = None

    @model_validator(mode="after")
    def _shape(self) -> Pattern:
        pair = self.verb is not None and self.condition is not None
        if pair == (self.regex is not None):
            raise ValueError("pattern needs either verb+condition or regex")
        for p in (self.verb, self.condition, self.regex):
            if p is not None:
                re.compile(p)
        return self


class Examples(BaseModel):
    positive: list[str] = Field(min_length=1)
    negative: list[str] = Field(min_length=1)


class Rule(BaseModel):
    id: str
    category: str = "other"
    severity: Literal["red", "orange"]
    overridable: bool = True
    language: Literal["en", "hi", "any"] = "any"
    reason: str
    citation: str
    suggestion: str | None = None
    patterns: list[Pattern] = Field(min_length=1)
    allowlist: list[str] = Field(default_factory=list)
    examples: Examples

    @model_validator(mode="after")
    def _guards(self) -> Rule:
        if self.category in HARD_BLOCK_CATEGORIES and (self.overridable or self.severity != "red"):
            raise ValueError(f"rule {self.id}: {self.category} rules must be severity=red, overridable=false (P17)")
        for a in self.allowlist:
            re.compile(a)
        return self

    @property
    def sev(self) -> Severity:
        return Severity(self.severity)


class RuleSet(BaseModel):
    version: str
    status: str = "draft"
    rules: list[Rule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique(self) -> RuleSet:
        ids = [r.id for r in self.rules]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate rule ids: {sorted(dupes)}")
        return self

    @property
    def label(self) -> str:
        return f"rule set v{self.version}" + (" (draft)" if self.status != "final" else "")


def load_ruleset(path: Path | str | None = None) -> RuleSet:
    """Load one YAML file, or every *.yaml in a directory (default engine/rules). Empty dir -> empty rule set.
    The set is 'final' only if every file says so; anything else is draft."""
    p = Path(path) if path else DEFAULT_RULES_DIR
    files = sorted(p.glob("*.yaml")) if p.is_dir() else [p]
    version, statuses, rules = None, [], []
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        v = str(doc.get("version", "0"))
        if version not in (None, v):
            raise ValueError(f"{f.name}: version {v} differs from {version}; all rule files must share a version")
        version = v
        statuses.append(doc.get("status", "draft"))
        rules.extend(doc.get("rules") or [])
    status = "final" if statuses and all(s == "final" for s in statuses) else "draft"
    return RuleSet(version=version or "0", status=status, rules=rules)
