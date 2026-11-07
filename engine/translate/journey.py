"""The Hindi step of the journey (plan section 3 step 8): translate an approved English pack, re-verify the Hindi
text, and gate the export. DRAFT until the native Hindi reviewer signs off (SAT-5, P20). Fails closed."""

from __future__ import annotations

import hashlib

from engine.export.gate import export_blockers
from engine.models import PDPPack, ProductTruth
from engine.normalize import Lexicon
from engine.providers import LLMProvider
from engine.rules import RuleSet
from engine.translate.providers import Translator
from engine.translate.service import translate_pack
from engine.verifier import verify_pack


def english_digest(pack: PDPPack) -> str:
    """Identifies the English wording a Hindi pack was made from."""
    return hashlib.sha256("\n".join(s.text for s in pack.sentences()).encode()).hexdigest()


def translate_and_verify(
    pack: PDPPack,
    truth: ProductTruth,
    *,
    translators: list[Translator] | None = None,
    lexicon: Lexicon | None = None,
    ruleset: RuleSet | None = None,
    provider: LLMProvider | None = None,
) -> tuple[PDPPack, bool]:
    """(Hindi pack, verifier ran). The verifier's pass 1 resets flags with the English rules, so the Hindi lexicon
    flags from translation are put back on each sentence afterwards (P6)."""
    hi = translate_pack(pack, truth, translators=translators, lexicon=lexicon)
    hindi_flags = [[list(s.flags) for s in sec.sentences] for sec in hi.sections]
    report = verify_pack(hi, truth, provider=provider, ruleset=ruleset)
    out = report.pack
    for sec, per_sec in zip(out.sections, hindi_flags, strict=True):
        for s, fl in zip(sec.sentences, per_sec, strict=True):
            s.flags.extend(fl)
    return out.model_copy(update={"rule_set_version": hi.rule_set_version}), report.pass2_completed


def hindi_export_blockers(
    english_approved: bool, english: PDPPack | None, hindi: PDPPack | None, hindi_for: str, truth: ProductTruth
) -> list[str]:
    """Everything stopping a Hindi export: English must be approved, the Hindi pack must come from that exact
    English text, and it must pass the same gate (verified, no open flags)."""
    out = [] if english_approved else ["English pack is not approved"]
    if hindi is None:
        return [*out, "no Hindi pack has been generated"]
    if english is None or hindi_for != english_digest(english):
        out.append("Hindi pack is out of date with the English pack")
    return [*out, *export_blockers(hindi, truth)]
