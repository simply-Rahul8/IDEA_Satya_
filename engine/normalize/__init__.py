"""Text normalisation (NFC, Devanagari/transliterated/Hinglish forms) and the Hindi lexicon. Owner: Indic agent."""

from engine.normalize.hindi import analyse_hi, nfc, normalize_hi, roman_fold, script_of
from engine.normalize.lexicon import (
    HiFlag,
    Lexicon,
    LexiconError,
    check_hindi,
    default_lexicon,
    hard_blocks_hindi,
    load_lexicon,
    summary_line_hi,
)

__all__ = [
    "HiFlag",
    "Lexicon",
    "LexiconError",
    "analyse_hi",
    "check_hindi",
    "default_lexicon",
    "hard_blocks_hindi",
    "load_lexicon",
    "nfc",
    "normalize_hi",
    "roman_fold",
    "script_of",
    "summary_line_hi",
]
