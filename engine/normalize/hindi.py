"""Hindi text normalisation (P6). Owner: Indic agent.

Two levels:
- `nfc` is for stored and displayed text: Unicode NFC only, so the user's own spelling survives.
- `analyse_hi` is for matching: fold nukta, chandrabindu, digits, zero-width characters and Roman spelling
  variants, keeping a map back to the caller's offsets so flags can highlight the original text.

Listing text is data (P19): nothing here evaluates it.
"""

from __future__ import annotations

import re
import unicodedata

from engine.rules.text import Normalized, Tok

NUKTA = "़"
CHANDRABINDU = "ँ"
ANUSVARA = "ं"
_DEVANAGARI_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}
_SENTENCE_END = re.compile(r"[\n\r;•।॥]|[.!?](?=\s|$)")
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")


def nfc(text: str) -> str:
    """Display form. U+0958-095F (क़ ख़ ग़ ज़ ...) are composition exclusions: NFC stores them as base + nukta."""
    return unicodedata.normalize("NFC", text)


def script_of(text: str) -> str:
    """`devanagari`, `latin`, `mixed` (Hinglish written in both scripts) or `other`."""
    dev, lat = bool(_DEVANAGARI.search(text)), bool(_LATIN.search(text))
    return "mixed" if dev and lat else "devanagari" if dev else "latin" if lat else "other"


def roman_fold(token: str) -> str:
    """Collapse common Roman spelling variants of Hindi (ilaaj/ilaj, theek/thik, twacha/tvacha). Applied to both
    the text and the lexicon terms, so only equality of folds matters."""
    t = token.lower().replace("ee", "i").replace("oo", "u").replace("w", "v").replace("z", "j")
    return re.sub(r"(.)\1+", r"\1", t)


def fold_char(ch: str) -> str:
    if ch in _DEVANAGARI_DIGITS:
        return _DEVANAGARI_DIGITS[ch]
    if ch == CHANDRABINDU:
        return ANUSVARA
    out = unicodedata.normalize("NFKC", ch).lower()
    return out.replace(NUKTA, "")  # NFKC also splits क़ into क + nukta; the nukta is dropped for matching


def _is_word_char(ch: str) -> bool:
    # str.isalnum() is False for Devanagari vowel signs and the virama (categories Mn/Mc), so a plain \w tokeniser
    # would cut every Hindi word at its matras. Marks are word characters here.
    return ch.isalnum() or unicodedata.category(ch)[0] == "M"


def normalize_hi(text: str) -> tuple[str, tuple[int, ...]]:
    chars: list[str] = []
    index: list[int] = []
    for i, ch in enumerate(text):
        if unicodedata.category(ch) == "Cf":  # ZWJ, ZWNJ, bidi marks: invisible, and a classic evasion
            continue
        if ch in "‘’":
            ch = "'"
        elif ch in "“”":
            ch = '"'
        elif ch in "‐‑‒–—":
            ch = "-"
        elif ch == " ":
            ch = " "
        for out in fold_char(ch):
            chars.append(out)
            index.append(i)
    return "".join(chars), tuple(index)


def fold_token(tok: str) -> str:
    return roman_fold(tok) if tok.isascii() else tok


def tokenise(norm: str) -> list[tuple[str, int, int]]:
    out, i, n = [], 0, len(norm)
    while i < n:
        if _is_word_char(norm[i]):
            j = i + 1
            while j < n and _is_word_char(norm[j]):
                j += 1
            out.append((fold_token(norm[i:j]), i, j))
            i = j
        else:
            i += 1
    return out


def analyse_hi(text: str) -> Normalized:
    """Same shape as `engine.rules.text.analyse`, so `find_term` works on it. Sentences end at danda, `.!?`, newline."""
    norm, index = normalize_hi(text)
    breaks = [m.start() for m in _SENTENCE_END.finditer(norm)]
    tokens: list[Tok] = []
    sentence, prev_end = 0, 0
    for word, s, e in tokenise(norm):
        if tokens and any(prev_end <= pos < s for pos in breaks):
            sentence += 1
        tokens.append(Tok(word, s, e, sentence))
        prev_end = e
    return Normalized(text, norm, index, tuple(tokens))


def compile_term_hi(term: str) -> tuple[tuple[str, bool], ...]:
    """Lexicon term to (token, is_prefix_wildcard) positions. A trailing `*` is a prefix wildcard on that token."""
    parts: list[tuple[str, bool]] = []
    for raw in term.split():
        prefix = raw.endswith("*")
        norm, _ = normalize_hi(raw.rstrip("*"))
        toks = tokenise(norm)
        if not toks:
            raise ValueError(f"lexicon term {term!r} has an empty token")
        parts.extend((w, prefix and k == len(toks) - 1) for k, (w, _, _) in enumerate(toks))
    if not parts:
        raise ValueError("empty lexicon term")
    return tuple(parts)
