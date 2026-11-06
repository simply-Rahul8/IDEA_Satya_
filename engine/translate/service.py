"""English to Hindi with protected terms, NFC, the Hindi lexicon re-run and a same-language disclaimer (plan section 3
step 8). Owner: Indic agent. Everything here is DRAFT until the native Hindi reviewer signs off (SAT-5, P20)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from engine.models import Flag, PDPPack, ProductTruth, Section, Sentence, SentenceType, Severity
from engine.normalize import HiFlag, Lexicon, check_hindi, default_lexicon, nfc
from engine.providers import ProviderError
from engine.translate.protect import PlaceholderError, protect, restore
from engine.translate.providers import Translator, get_translators

# DRAFT wording, awaiting the native reviewer. Same meaning as the English standard disclaimer ("not intended to
# diagnose, treat, cure or prevent any disease"). AL-HI-001 in the lexicon allowlists it so the re-run stays clean.
DISCLAIMER_EN = "This product is not intended to diagnose, treat, cure or prevent any disease."
DISCLAIMER_HI = "यह उत्पाद किसी रोग के निदान, उपचार, इलाज या रोकथाम के लिए नहीं है।"
DISCLAIMER_HI_STATUS = "DRAFT"


class TranslationFailed(ProviderError):
    """Every translator failed or mangled the protected terms. Carries the attempts for telemetry."""

    def __init__(self, attempts: list[TranslationAttempt]):
        self.attempts = attempts
        super().__init__("translation failed: " + "; ".join(f"{a.provider}: {a.error or a.outcome}" for a in attempts))


@dataclass
class TranslationAttempt:
    provider: str
    outcome: str  # ok | error | placeholder_mismatch
    latency_ms: int
    error: str | None = None


@dataclass
class Translation:
    source: str
    text: str  # Hindi, NFC, protected terms restored verbatim
    provider: str
    attempts: list[TranslationAttempt]
    protected_terms: tuple[str, ...]
    flags: list[HiFlag] = field(default_factory=list)  # Hindi lexicon re-run (P6)

    @property
    def hard_blocked(self) -> bool:
        return any(not f.overridable for f in self.flags)


def translate_text(
    text: str,
    protected_terms: list[str] | tuple[str, ...] = (),
    *,
    translators: list[Translator] | None = None,
    lexicon: Lexicon | None = None,
) -> Translation:
    """Translate one unit of listing text to Hindi. Listing text is data (P19): it is only ever passed as the string
    to translate. Tries each translator once, in order; no retry loops (spend). A result whose placeholders are not
    each present exactly once counts as a failed attempt."""
    chain = translators if translators is not None else get_translators()
    # Protect on the raw text: a protected term is restored exactly as the brand wrote it, even if it is not NFC.
    prot = protect(text, protected_terms)
    attempts: list[TranslationAttempt] = []
    for tr in chain:
        t0 = time.perf_counter()
        try:
            raw = tr.translate(prot.text, source="en", target="hi")
            out = restore(nfc(raw), prot)  # NFC before restore: protected terms are never rewritten
        except PlaceholderError as e:
            attempts.append(TranslationAttempt(tr.name, "placeholder_mismatch", _ms(t0), str(e)))
            continue
        except ProviderError as e:
            attempts.append(TranslationAttempt(tr.name, "error", _ms(t0), str(e)))
            continue
        attempts.append(TranslationAttempt(tr.name, "ok", _ms(t0)))
        return Translation(text, out, tr.name, attempts, prot.terms, check_hindi(out, lexicon))
    raise TranslationFailed(attempts)


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def truth_protected_terms(truth: ProductTruth) -> list[str]:
    """Names and facts that must not be translated or re-spelt."""
    vals = [truth.product_name, truth.brand, truth.size, truth.manufacturer, *truth.ingredients]
    return [v for v in vals if v]


def _flag(f: HiFlag, lx: Lexicon) -> Flag:
    return Flag(
        rule_id=f.rule_id,
        severity=Severity.RED,
        reason=f.message,
        citation=f"Hindi lexicon {f.lexicon} (mirrors {f.maps_to}) [DRAFT, awaiting native reviewer]",
        suggestion=lx.rule(f.rule_id).rewrite_hint,
        matched_text=f.text,
        overridable=f.overridable,
    )


def translate_pack(
    pack: PDPPack,
    truth: ProductTruth,
    *,
    translators: list[Translator] | None = None,
    lexicon: Lexicon | None = None,
) -> PDPPack:
    """Hindi copy of an English pack: same sections, types and anchors, each sentence translated with the truth's
    names protected, the Hindi lexicon re-run on every sentence, and the Hindi disclaimer appended to
    `warnings_storage`. `verifier_passed` is False: the Hindi pack has not been verified."""
    lx = lexicon or default_lexicon()
    chain = translators if translators is not None else get_translators()
    terms = truth_protected_terms(truth)
    sections: list[Section] = []
    for sec in pack.sections:
        sents = []
        for s in sec.sentences:
            tr = translate_text(s.text, terms, translators=chain, lexicon=lx)
            sents.append(s.model_copy(update={"text": tr.text, "flags": [_flag(f, lx) for f in tr.flags]}))
        if sec.key == "warnings_storage":
            sents.append(
                Sentence(
                    text=DISCLAIMER_HI,
                    type=SentenceType.LEGAL,
                    flags=[_flag(f, lx) for f in check_hindi(DISCLAIMER_HI, lx)],
                )
            )
        sections.append(Section(key=sec.key, sentences=sents))
    return PDPPack(sections=sections, rule_set_version=lx.label, verifier_passed=False)
