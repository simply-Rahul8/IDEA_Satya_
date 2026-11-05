"""Exporters: generic CSV with column mapping, audit record, print report. Owner: Export agent.

Marketplace layouts (Nykaa, Amazon) plug in via `layouts.register_layout` once real templates arrive."""

from engine.export.audit import AuditRecord, build_audit
from engine.export.csv_export import ExportResult, export_csv
from engine.export.gate import ExportBlocked, ensure_exportable, export_blockers
from engine.export.layouts import (
    PLACEHOLDER_LAYOUT,
    SOURCES,
    ColumnSpec,
    Layout,
    MappingError,
    default_mapping,
    get_layout,
    list_layouts,
    register_layout,
    validate_mapping,
)
from engine.export.report import render_report

__all__ = [
    "PLACEHOLDER_LAYOUT", "SOURCES", "AuditRecord", "ColumnSpec", "ExportBlocked", "ExportResult", "Layout",
    "MappingError", "build_audit", "default_mapping", "ensure_exportable", "export_blockers", "export_csv",
    "get_layout", "list_layouts", "register_layout", "render_report", "validate_mapping",
]  # fmt: skip
