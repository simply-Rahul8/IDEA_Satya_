"""Two-pass verifier (P4): pass 1 deterministic (anchors + guardrail rules), pass 2 a separate LLM call that
checks each sentence is supported by its anchored sources. Owner: Engine."""

from __future__ import annotations

from pydantic import BaseModel

from engine import prompts, telemetry
from engine.guardrails import RuleSet, check_sentence, default_ruleset
from engine.models import ClaimStatus, Flag, PDPPack, ProductTruth, Sentence, SentenceType, Severity
from engine.normalize import nfc
from engine.providers import LLMProvider, ProviderError, get_provider
from engine.translate.service import DISCLAIMER_EN, DISCLAIMER_HI

_SYSTEM_DISCLAIMERS = frozenset({nfc(DISCLAIMER_EN), nfc(DISCLAIMER_HI)})


class VerificationReport(BaseModel):
    pack: PDPPack
    pass2_completed: bool
    pass2_error: str | None = None


def _anchor_flag(rule_id: str, reason: str, sev: Severity = Severity.RED) -> Flag:
    return Flag(rule_id=rule_id, severity=sev, reason=reason, overridable=False, source="anchor")


def is_system_disclaimer(sentence: Sentence) -> bool:
    """The fixed system disclaimer (EN or HI) is not product copy, so it needs no anchor. Exact text match on a
    LEGAL sentence only: user text never gets this exemption."""
    return sentence.type == SentenceType.LEGAL and nfc(sentence.text) in _SYSTEM_DISCLAIMERS


def anchor_sources(sentence: Sentence, truth: ProductTruth) -> tuple[list[str], list[Flag]]:
    """Resolve anchors to source texts; return (sources, anchor flags)."""
    sources: list[str] = []
    flags: list[Flag] = []
    if is_system_disclaimer(sentence):
        return [], []
    if not sentence.anchors:
        return [], [_anchor_flag("ANCHOR-MISSING", "Sentence has no anchor to the Product Truth")]
    for a in sentence.anchors:
        kind, _, ref = a.partition(":")
        if kind == "claim":
            c = truth.claim(ref)
            if c is None or c.status != ClaimStatus.CONFIRMED:
                flags.append(_anchor_flag("ANCHOR-UNCONFIRMED", f"Anchor {a} is not a confirmed claim"))
            else:
                sources.append(c.text)
        else:
            val = getattr(truth, ref, None) if ref in truth.field_names() else None
            if not val:
                flags.append(_anchor_flag("ANCHOR-INVALID", f"Anchor {a} is not a filled Product Truth field"))
            else:
                sources.append(f"{ref}: " + (", ".join(val) if isinstance(val, list) else str(val)))
    if sentence.type == SentenceType.BENEFIT_CLAIM and not any(a.startswith("claim:") for a in sentence.anchors):
        flags.append(_anchor_flag("ANCHOR-WEAK", "Benefit claim is not anchored to a confirmed claim", Severity.ORANGE))
    return sources, flags


def pass1(sentence: Sentence, truth: ProductTruth, ruleset: RuleSet) -> tuple[Sentence, list[str]]:
    """Deterministic checks for one sentence. Replaces earlier rule/anchor/verifier flags (live re-check)."""
    sources, aflags = anchor_sources(sentence, truth)
    checked = check_sentence(sentence.model_copy(update={"flags": []}), ruleset)
    return checked.model_copy(update={"flags": aflags + checked.flags}), sources


def verify_pack(
    pack: PDPPack,
    truth: ProductTruth,
    *,
    provider: LLMProvider | None = None,
    ruleset: RuleSet | None = None,
) -> VerificationReport:
    ruleset = ruleset or default_ruleset()
    sections, items = [], []
    for sec in pack.sections:
        new = []
        for s in sec.sentences:
            checked, sources = pass1(s, truth, ruleset)
            if sources and not any(f.source == "anchor" and f.severity == Severity.RED for f in checked.flags):
                items.append({"index": len(items), "text": s.text, "sources": sources, "_ref": (sec.key, len(new))})
            new.append(checked)
        sections.append(sec.model_copy(update={"sentences": new}))
    out = pack.model_copy(update={"sections": sections, "rule_set_version": ruleset.label, "verifier_passed": False})
    if not items:
        return VerificationReport(pack=out.model_copy(update={"verifier_passed": True}), pass2_completed=True)

    system, prompt = prompts.verify_prompt([{k: v for k, v in i.items() if k != "_ref"} for i in items])
    try:
        resp = telemetry.call_llm(
            provider or get_provider(), prompt, system=system,
            purpose="verify", prompt_version=prompts.VERSIONS["verify_pack"],
        )  # fmt: skip
        verdicts = {int(v["index"]): v for v in prompts.parse_json(resp.text)["verdicts"]}
    except (ProviderError, ValueError, KeyError, TypeError) as e:
        # Fail closed: an unavailable verifier means the pack cannot be approved.
        return VerificationReport(pack=out, pass2_completed=False, pass2_error=f"{type(e).__name__}: {e}"[:200])

    for i in items:
        v = verdicts.get(i["index"])
        if v is not None and v.get("supported") is True:
            continue
        key, pos = i["_ref"]
        sent = out.section(key).sentences[pos]
        reason = (v or {}).get("reason") or "Verifier returned no verdict for this sentence"
        sent.flags.append(Flag(rule_id="VERIFIER-UNSUPPORTED", severity=Severity.ORANGE, reason=str(reason),
                               suggestion="Rewrite using only what the anchored sources say",
                               overridable=True, source="verifier"))  # fmt: skip
    return VerificationReport(pack=out.model_copy(update={"verifier_passed": True}), pass2_completed=True)
