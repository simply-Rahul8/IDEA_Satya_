"""Pipeline arm: runs extract -> generate -> verify on corpus PDPs with one provider and measures cost and latency
(P26, P31). Cost and latency come from engine.telemetry, so bench and production use the same numbers."""

from __future__ import annotations

import os
import statistics

from engine import prompts, telemetry
from engine.models import Claim, ClaimStatus, PDPPack, ProductTruth, Severity
from engine.pipeline import approval_status, generate_verified_pack
from engine.providers import ClaudeProvider, LLMProvider, MockProvider, ProviderError, SarvamProvider
from engine.rules import default_ruleset, evaluate

COST_TARGET_INR = 1.0


def available_providers() -> dict[str, LLMProvider]:
    """Mock is always there; live providers only when their key is in the environment (never printed)."""
    out: dict[str, LLMProvider] = {"mock": MockProvider()}
    if os.environ.get("SATYA_LLM", "mock") == "live":
        for cls in (SarvamProvider, ClaudeProvider):
            if os.environ.get(cls.env_key):
                out[cls.name] = cls()
    return out


def listing_text(pdp: dict) -> str:
    return "\n".join(s["text"] for s in pdp["sentences"])


def build_truth(pdp: dict, provider: LLMProvider) -> ProductTruth:
    """Extract a Product Truth from the listing text, then confirm every claim the rules do not flag red.
    This stands in for the brand's confirm step; flagged claims stay unconfirmed and never reach generation."""
    system, prompt = prompts.extract_prompt(listing_text(pdp))
    data = prompts.parse_json(
        telemetry.call_llm(provider, prompt, system=system, purpose="extract",
                           prompt_version=prompts.VERSIONS["extract_product_truth"]).text
    )  # fmt: skip
    rs = default_ruleset()
    claims = []
    for i, c in enumerate(data.pop("claims", None) or []):
        text = c.get("text", "") if isinstance(c, dict) else str(c)
        red = any(f.severity == Severity.RED for f in evaluate(text, rs))
        claims.append(Claim(id=f"c{i}", text=text, status=ClaimStatus.UNCONFIRMED if red else ClaimStatus.CONFIRMED))
    data = {k: v for k, v in data.items() if k in ProductTruth.model_fields and v is not None}
    data.setdefault("product_name", pdp["sentences"][0]["text"][:120])
    return ProductTruth(**data, claims=claims)


def run_pdp(pdp: dict, provider: LLMProvider, tone: str = "professional") -> tuple[PDPPack | None, dict]:
    """One PDP end to end. Returns (pack or None, metrics). Errors are counted, not raised: no retries (budget)."""
    n0 = len(telemetry.recorder.calls)
    pack, err, approvable = None, None, False
    try:
        truth = build_truth(pdp, provider)
        report = generate_verified_pack(truth, tone=tone, provider=provider)
        pack = report.pack
        approvable = approval_status(pack, truth).approvable and report.pass2_completed
    except (ProviderError, ValueError) as e:
        err = type(e).__name__
    calls = telemetry.recorder.calls[n0:]
    reds = (
        sum(f.severity == Severity.RED for sec in pack.sections for s in sec.sentences for f in s.flags) if pack else 0
    )
    return pack, {
        "pdp_id": pdp["pdp_id"], "calls": len(calls), "cost_inr": sum(c.cost_inr for c in calls),
        "latency_ms": sum(c.latency_ms for c in calls), "error": err, "red_flags": reds, "approvable": approvable,
    }  # fmt: skip


def run_arm(provider: LLMProvider, pdps: list[dict], tone: str = "professional") -> dict:
    rows = [run_pdp(p, provider, tone)[1] for p in pdps]
    lat = sorted(r["latency_ms"] for r in rows)
    cost = [r["cost_inr"] for r in rows]
    n = len(rows) or 1
    return {
        "provider": provider.name, "model": provider.model, "pdps": len(rows),
        "errors": sum(r["error"] is not None for r in rows),
        "cost_inr_per_pdp": sum(cost) / n, "cost_inr_max": max(cost, default=0.0),
        "latency_ms_p50": int(statistics.median(lat)) if lat else 0,
        "latency_ms_p95": lat[min(len(lat) - 1, int(0.95 * len(lat)))] if lat else 0,
        "approvable_rate": sum(r["approvable"] for r in rows) / n,
        "red_flags_in_output": sum(r["red_flags"] for r in rows),
    }  # fmt: skip
