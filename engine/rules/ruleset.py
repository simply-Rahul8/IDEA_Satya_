"""Rule set loader. Reads engine/rules/*.yaml, validates it and compiles patterns once."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

from engine.rules.matcher import CompiledAllow, CompiledRule, compile_allow, compile_rule
from engine.rules.schema import AllowEntry, GateConfig, Meta, Rule

RULES_DIR = Path(__file__).resolve().parent
_ROOT_KEYS = {"rule_set": "meta", "rules": "rules", "allowlist": "allowlist", "product_type_gate": "gate"}


class RuleSetError(ValueError):
    """The rule files are inconsistent. Fail loudly: a half-loaded rule set must never run."""


@dataclass(frozen=True)
class RuleSet:
    meta: Meta
    rules: tuple[Rule, ...]
    allowlist: tuple[AllowEntry, ...]
    gate: GateConfig
    content_hash: str
    compiled_rules: tuple[CompiledRule, ...] = field(repr=False, default=())
    compiled_allow: tuple[CompiledAllow, ...] = field(repr=False, default=())

    @property
    def version(self) -> str:
        return self.meta.version

    @property
    def label(self) -> str:
        """The `vX` surfaced in reports. Carries `-draft` until the consultant signs off (P20)."""
        return f"v{self.meta.version}" + ("-draft" if self.meta.status == "DRAFT" else "")

    @property
    def is_signed_off(self) -> bool:
        return self.meta.status == "SIGNED_OFF"

    def rule(self, rule_id: str) -> Rule:
        for r in self.rules:
            if r.id == rule_id:
                return r
        raise KeyError(rule_id)


def load_ruleset(directory: Path | str | None = None) -> RuleSet:
    return _load(Path(directory) if directory else RULES_DIR)


@cache
def default_ruleset() -> RuleSet:
    return _load(RULES_DIR)


def _load(directory: Path) -> RuleSet:
    parts: dict[str, list] = {"meta": [], "rules": [], "allowlist": [], "gate": []}
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        unknown = set(data) - set(_ROOT_KEYS) - {"anchors"}
        if unknown:
            raise RuleSetError(f"{path.name}: unknown top-level keys {sorted(unknown)}")
        for key, bucket in _ROOT_KEYS.items():
            if key in data:
                value = data[key]
                parts[bucket].extend(value if isinstance(value, list) else [value])
    if len(parts["meta"]) != 1 or len(parts["gate"]) != 1:
        raise RuleSetError("expected exactly one rule_set block and one product_type_gate block")
    meta = Meta.model_validate(parts["meta"][0])
    rules = tuple(Rule.model_validate(r) for r in parts["rules"])
    allowlist = tuple(AllowEntry.model_validate(a) for a in parts["allowlist"])
    gate = GateConfig.model_validate(parts["gate"][0])

    ids = [r.id for r in rules]
    if len(set(ids)) != len(ids):
        raise RuleSetError(f"duplicate rule ids: {sorted({i for i in ids if ids.count(i) > 1})}")
    allow_ids = [a.id for a in allowlist]
    if len(set(allow_ids)) != len(allow_ids):
        raise RuleSetError("duplicate allowlist ids")
    for a in allowlist:
        missing = set(a.applies_to) - set(ids)
        if missing:
            raise RuleSetError(f"{a.id}: applies_to unknown rules {sorted(missing)}")

    canonical = json.dumps(
        {
            "meta": meta.model_dump(mode="json"),
            "rules": [r.model_dump(mode="json") for r in rules],
            "allowlist": [a.model_dump(mode="json") for a in allowlist],
            "gate": gate.model_dump(mode="json"),
        },
        sort_keys=True,
    )
    return RuleSet(
        meta=meta,
        rules=rules,
        allowlist=allowlist,
        gate=gate,
        content_hash=hashlib.sha256(canonical.encode()).hexdigest()[:12],
        compiled_rules=tuple(compile_rule(r) for r in rules),
        compiled_allow=tuple(compile_allow(a) for a in allowlist),
    )
