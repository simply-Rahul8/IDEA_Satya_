"""Translation with protected-term placeholders (P13). Owner: Indic agent. Hindi only; DRAFT until SAT-5 signs off."""

from engine.translate.protect import PlaceholderError, Protected, protect, restore
from engine.translate.providers import (
    IndicTrans2Translator,
    MockTranslator,
    SarvamTranslator,
    Translator,
    get_translators,
)
from engine.translate.service import (
    DISCLAIMER_EN,
    DISCLAIMER_HI,
    Translation,
    TranslationFailed,
    translate_pack,
    translate_text,
    truth_protected_terms,
)

__all__ = [
    "DISCLAIMER_EN",
    "DISCLAIMER_HI",
    "IndicTrans2Translator",
    "MockTranslator",
    "PlaceholderError",
    "Protected",
    "SarvamTranslator",
    "Translation",
    "TranslationFailed",
    "Translator",
    "get_translators",
    "protect",
    "restore",
    "translate_pack",
    "translate_text",
    "truth_protected_terms",
]
