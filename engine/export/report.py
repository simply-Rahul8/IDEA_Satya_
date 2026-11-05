"""Print-friendly report. Always stamped 'Not legal advice · rule set vX'; never claims compliance (P20)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from engine.export.audit import AuditRecord
from engine.export.gate import ensure_exportable
from engine.models import PDPPack, ProductTruth

_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape(["html"]))


def render_report(pack: PDPPack, truth: ProductTruth, audit: AuditRecord) -> str:
    ensure_exportable(pack, truth)
    return _env.get_template("report.html").render(
        pack=pack, truth=truth, audit=audit, stamp=audit.disclaimer,
        version=pack.rule_set_version or "unversioned",
    )  # fmt: skip
