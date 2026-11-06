"""Audit record that accompanies every export: claims, evidence refs, rule-set version, flags and overrides."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel

from engine.export.layouts import Mapping
from engine.models import PDPPack, ProductTruth, Severity

DISCLAIMER = "Not legal advice"


class AuditClaim(BaseModel):
    id: str
    text: str
    status: str
    evidence_type: str | None = None
    evidence_reference: str | None = None
    evidence_note: str | None = None


class AuditFlag(BaseModel):
    section: str
    sentence_index: int
    rule_id: str
    severity: str
    source: str
    matched_text: str | None = None
    citation: str | None = None
    override_reason: str | None = None  # present => overridden by the user


class AuditRecord(BaseModel):
    format: str
    layout_id: str
    mapping: Mapping
    rule_set_version: str | None
    exported_at: str
    content_sha256: str
    verifier_passed: bool
    red_flags: int  # always 0 on an export that passed the gate
    overrides: int
    claims: list[AuditClaim]
    flags: list[AuditFlag]
    disclaimer: str

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def build_audit(
    *, fmt: str, layout_id: str, mapping: Mapping, content: bytes, pack: PDPPack, truth: ProductTruth, exported_at: str
) -> AuditRecord:
    claims = [
        AuditClaim(
            id=c.id,
            text=c.text,
            status=c.status.value,
            evidence_type=c.evidence.type.value if c.evidence else None,
            evidence_reference=c.evidence.reference if c.evidence else None,
            evidence_note=c.evidence.note if c.evidence else None,
        )
        for c in truth.claims
    ]
    flags = [
        AuditFlag(
            section=sec.key,
            sentence_index=i,
            rule_id=f.rule_id,
            severity=f.severity.value,
            source=f.source,
            matched_text=f.matched_text,
            citation=f.citation,
            override_reason=f.override_reason,
        )
        for sec in pack.sections
        for i, s in enumerate(sec.sentences)
        for f in s.flags
    ]
    return AuditRecord(
        format=fmt,
        layout_id=layout_id,
        mapping=mapping,
        rule_set_version=pack.rule_set_version,
        exported_at=exported_at,
        content_sha256=hashlib.sha256(content).hexdigest(),
        verifier_passed=pack.verifier_passed,
        red_flags=sum(1 for f in flags if f.severity == Severity.RED.value),
        overrides=sum(1 for f in flags if f.override_reason),
        claims=claims,
        flags=flags,
        disclaimer=f"{DISCLAIMER} · rule set {pack.rule_set_version or 'unversioned'}",
    )
