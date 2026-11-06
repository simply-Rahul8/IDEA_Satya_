"""Audit data model (screen-audit.md section 1). Owner: Engine."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class State(StrEnum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    PENDING = "pending"
    SKIPPED = "skipped"
    ERROR = "error"


# Sort order: risk first, then what still needs attention, then what was not reviewed.
STATE_ORDER = (State.RED, State.AMBER, State.GREEN, State.PENDING, State.ERROR, State.SKIPPED)
RISK_STATES = (State.RED, State.AMBER, State.GREEN)


class ProductRecord(BaseModel):
    """One catalogue row after import. Every field is data (P19), never an instruction."""

    sku: str
    name: str
    description: str = ""
    category: str = ""
    brand: str = ""
    net_quantity: str = ""
    mrp: str = ""
    manufacturer: str = ""
    country_of_origin: str = ""
    consumer_care: str = ""


class AuditFlag(BaseModel):
    rule_id: str
    title: str
    severity: State  # red | amber
    citation: str | None = None
    matched_text: str | None = None


class AuditItem(BaseModel):
    sku: str
    name: str
    state: State = State.PENDING
    flags: list[AuditFlag] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    note: str | None = None  # gate explanation for skipped, error text for error
    position: int = 0  # catalogue order


class Counters(BaseModel):
    total: int = 0
    done: int = 0
    red: int = 0
    amber: int = 0
    green: int = 0
    skipped: int = 0  # not cosmetics (P23); excluded from risk counts
    error: int = 0
    pending: int = 0


class AuditReport(BaseModel):
    job_id: str
    status: str  # pending | running | done | failed | cancelled
    rule_set: str
    counters: Counters
    progress_label: str  # "Checking 38 of 120 products" / "Stopped at 38 of 120" / "Checked 120 products"
    summary: str | None = None  # "No flagged risks ..." wording, only when complete with 0 red/amber
    items: list[AuditItem]  # sorted by risk, then catalogue order
