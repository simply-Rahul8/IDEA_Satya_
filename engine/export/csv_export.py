"""Generic CSV export driven by a Layout + Mapping (P29 fallback)."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from pydantic import BaseModel

from engine.export.audit import AuditRecord, build_audit
from engine.export.gate import ensure_exportable
from engine.export.layouts import (
    PLACEHOLDER_LAYOUT,
    Layout,
    Mapping,
    default_mapping,
    source_value,
    validate_mapping,
)
from engine.models import PDPPack, ProductTruth

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(text: str) -> str:
    """Neutralise spreadsheet formula injection from listing text."""
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


class ExportResult(BaseModel):
    filename: str
    content: bytes  # utf-8 with BOM so Excel reads Devanagari correctly
    audit: AuditRecord

    @property
    def audit_filename(self) -> str:
        return self.filename.removesuffix(".csv") + ".audit.json"


def export_csv(
    pack: PDPPack,
    truth: ProductTruth,
    *,
    layout: Layout = PLACEHOLDER_LAYOUT,
    mapping: Mapping | None = None,
    exported_at: datetime | None = None,
) -> ExportResult:
    """Raises ExportBlocked unless the pack is approvable and carries no red flag; MappingError on a bad mapping."""
    ensure_exportable(pack, truth)
    full = validate_mapping(layout, default_mapping(layout) if mapping is None else mapping)
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow([_safe_cell(h) for h in full])
    w.writerow([_safe_cell(source_value(src, pack, truth)) if src else "" for src in full.values()])
    content = b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
    when = (exported_at or datetime.now(UTC)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    audit = build_audit(
        fmt="csv", layout_id=layout.id, mapping=full, content=content, pack=pack, truth=truth, exported_at=when
    )
    return ExportResult(filename=f"satya-export-{layout.id}.csv", content=content, audit=audit)
