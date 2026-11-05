"""Stable internal API for Frontend and Export agents. Import from here, not from engine submodules.
Documented in docs/engine-api.md. Owner: Engine."""

from engine.extract import ExtractionError, extract_product_truth
from engine.guardrails import ClaimGuardError, RuleSet, check_text, confirm_claim, default_ruleset, load_ruleset
from engine.models import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceType,
    Flag,
    PDPPack,
    ProductTruth,
    Sentence,
    SentenceType,
    Severity,
)
from engine.pipeline import (
    ApprovalStatus,
    GenerationError,
    ReviewError,
    approval_status,
    edit_sentence,
    generate_pack,
    generate_verified_pack,
    override_flag,
)
from engine.providers import AllProvidersFailed, ProviderConfigError, ProviderError, get_provider
from engine.telemetry import LLMCall, recorder
from engine.verifier import VerificationReport, verify_pack

__all__ = [
    "AllProvidersFailed", "ApprovalStatus", "Claim", "ClaimGuardError", "ClaimStatus", "Evidence", "EvidenceType",
    "ExtractionError", "Flag", "GenerationError", "LLMCall", "PDPPack", "ProductTruth", "ProviderConfigError",
    "ProviderError", "ReviewError", "RuleSet", "Sentence", "SentenceType", "Severity", "VerificationReport",
    "approval_status", "check_text", "confirm_claim", "edit_sentence", "extract_product_truth", "generate_pack",
    "default_ruleset", "generate_verified_pack", "get_provider", "load_ruleset", "override_flag", "recorder",
    "verify_pack",
]  # fmt: skip
