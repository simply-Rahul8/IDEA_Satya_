"""Extraction: the LLM pre-fills a Product Truth draft; every claim starts unconfirmed (P2, P25). Owner: Engine."""

from __future__ import annotations

from pydantic import ValidationError

from engine import prompts, telemetry
from engine.guardrails import RuleSet, default_ruleset, screen_claim
from engine.models import Claim, ClaimStatus, ProductTruth
from engine.providers import LLMProvider, get_provider


class ExtractionError(ValueError):
    pass


def extract_product_truth(
    listing_text: str, *, provider: LLMProvider | None = None, ruleset: RuleSet | None = None
) -> ProductTruth:
    """One LLM call, no retries. Claims are forced to `unconfirmed` whatever the model says, and screened against
    the hard-block rules so the UI can show them as un-confirmable up front."""
    ruleset = ruleset or default_ruleset()
    system, prompt = prompts.extract_prompt(listing_text)
    resp = telemetry.call_llm(
        provider or get_provider(), prompt, system=system,
        purpose="extract", prompt_version=prompts.VERSIONS["extract_product_truth"],
    )  # fmt: skip
    try:
        data = prompts.parse_json(resp.text)
        raw_claims = data.pop("claims", None) or []
        truth = ProductTruth(**{k: v for k, v in data.items() if k in ProductTruth.model_fields and k != "claims"})
        claims = [
            Claim(id=f"c{i}", text=str(c["text"] if isinstance(c, dict) else c).strip(), status=ClaimStatus.UNCONFIRMED)
            for i, c in enumerate(raw_claims, 1)
        ]
    except (ValueError, ValidationError, KeyError, TypeError) as e:
        raise ExtractionError(f"model reply could not be read as a Product Truth: {type(e).__name__}") from None
    claims = [screen_claim(c, ruleset) for c in claims if c.text]
    return truth.model_copy(update={"claims": claims})
