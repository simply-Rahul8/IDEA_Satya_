"""Generation and review workflow: PDP pack generation, live re-check, overrides, approval gate. Owner: Engine."""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from engine import prompts, telemetry
from engine.guardrails import RuleSet, load_ruleset
from engine.models import SECTION_KEYS, ClaimStatus, PDPPack, ProductTruth, Section, Sentence, Severity
from engine.providers import LLMProvider, get_provider
from engine.verifier import VerificationReport, pass1, verify_pack

TONES = ("professional", "friendly", "premium")


class GenerationError(ValueError):
    pass


class ReviewError(ValueError):
    pass


def generate_pack(truth: ProductTruth, *, tone: str = "professional", provider: LLMProvider | None = None) -> PDPPack:
    """One LLM call. Only confirmed claims are shown to the model. The pack is NOT yet checked: run verify_pack
    (or generate_verified_pack) before showing or approving it."""
    shown = truth.model_copy(update={"claims": truth.confirmed_claims()})
    system, prompt = prompts.generate_prompt(shown.model_dump(mode="json", exclude_none=True), tone)
    resp = telemetry.call_llm(
        provider or get_provider(), prompt, system=system,
        purpose="generate", prompt_version=prompts.VERSIONS["generate_pack"],
    )  # fmt: skip
    try:
        data = prompts.parse_json(resp.text)
        got = {s["key"]: s.get("sentences") or [] for s in data["sections"]}
        sections = [Section(key=k, sentences=[Sentence(**s) for s in got.get(k, [])]) for k in SECTION_KEYS]
        return PDPPack(sections=sections)
    except (ValueError, ValidationError, KeyError, TypeError) as e:
        raise GenerationError(f"model reply could not be read as a PDP pack: {type(e).__name__}") from None


def generate_verified_pack(
    truth: ProductTruth,
    *,
    tone: str = "professional",
    provider: LLMProvider | None = None,
    ruleset: RuleSet | None = None,
) -> VerificationReport:
    provider = provider or get_provider()
    pack = generate_pack(truth, tone=tone, provider=provider)
    return verify_pack(pack, truth, provider=provider, ruleset=ruleset)


def edit_sentence(
    pack: PDPPack, key: str, index: int, new_text: str, truth: ProductTruth, *, ruleset: RuleSet | None = None
) -> PDPPack:
    """Live re-check after a user edit: deterministic only (fast). The pack must be re-verified before approval."""
    ruleset = ruleset or load_ruleset()
    sec = pack.section(key)
    if not 0 <= index < len(sec.sentences):
        raise ReviewError("no such sentence")
    edited, _ = pass1(sec.sentences[index].model_copy(update={"text": new_text}), truth, ruleset)
    sentences = list(sec.sentences)
    sentences[index] = edited
    sections = [s.model_copy(update={"sentences": sentences}) if s.key == key else s for s in pack.sections]
    return pack.model_copy(update={"sections": sections, "verifier_passed": False})


def override_flag(pack: PDPPack, key: str, index: int, rule_id: str, reason: str) -> PDPPack:
    """Record a reason against an orange flag. Red flags (incl. every non-overridable rule) cannot be overridden."""
    if not reason.strip():
        raise ReviewError("an override needs a reason")
    sentence = pack.section(key).sentences[index]
    flag = next((f for f in sentence.flags if f.rule_id == rule_id), None)
    if flag is None:
        raise ReviewError(f"no flag {rule_id} on that sentence")
    if flag.severity == Severity.RED or not flag.overridable:
        raise ReviewError(f"{rule_id} is red/non-overridable: rewrite the sentence instead")
    flags = [f.model_copy(update={"override_reason": reason.strip()}) if f is flag else f for f in sentence.flags]
    sentences = [
        s.model_copy(update={"flags": flags}) if i == index else s for i, s in enumerate(pack.section(key).sentences)
    ]
    sections = [s.model_copy(update={"sentences": sentences}) if s.key == key else s for s in pack.sections]
    return pack.model_copy(update={"sections": sections})


class ApprovalStatus(BaseModel):
    approvable: bool
    blockers: list[str]


def approval_status(pack: PDPPack, truth: ProductTruth | None = None) -> ApprovalStatus:
    """Red blocks approval; orange needs a reason; the verifier must have passed on this exact pack."""
    blockers: list[str] = []
    if not pack.verifier_passed:
        blockers.append("pack has not been verified since its last edit")
    for sec in pack.sections:
        for i, s in enumerate(sec.sentences):
            for f in s.flags:
                if f.severity == Severity.RED:
                    blockers.append(f"{sec.key}[{i}]: red {f.rule_id}")
                elif f.severity == Severity.ORANGE and not f.override_reason:
                    blockers.append(f"{sec.key}[{i}]: orange {f.rule_id} needs a reason")
    if truth is not None:
        bad = [c.id for c in truth.claims if c.status == ClaimStatus.CONFIRMED and c.hard_blocked]
        blockers += [f"claim {c} is confirmed but hard-blocked" for c in bad]
    return ApprovalStatus(approvable=not blockers, blockers=blockers)
