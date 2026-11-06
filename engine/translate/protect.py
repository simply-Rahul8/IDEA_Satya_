"""Protected-term placeholders around machine translation (P13). Owner: Indic agent.

Brand names, product names, ingredient names, sizes and numbers must come out of translation byte-for-byte. They are
swapped for ASCII placeholders before the call and restored afterwards; a translation that drops, repeats or invents a
placeholder is rejected, never repaired by guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PREFIX, _SUFFIX = "QPT", "Q"
_DEV_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}
# MT may insert spaces inside a token or turn digits into Devanagari digits; both are tolerated on the way back.
_PLACEHOLDER_RE = re.compile(r"Q\s?PT\s?([0-9०-९]+)\s?Q")
# Quantities that must never be re-rendered: 50 ml, 2%, SPF 30, PA+++, 100 g
_QUANTITY = (
    r"(?<!\w)(?:SPF\s?\d{1,3}\+?|PA\+{1,4}|pH\s?\d+(?:\.\d+)?"
    r"|\d+(?:\.\d+)?\s?(?:%|ml|l|g|gm|kg|mg|oz|fl\.?\s?oz))(?!\w)"
)


class PlaceholderError(ValueError):
    """The translation lost, duplicated or invented a placeholder."""


@dataclass(frozen=True)
class Protected:
    text: str  # source text with placeholders
    terms: tuple[str, ...]  # index -> surface text to restore


def _norm_digits(s: str) -> str:
    return "".join(_DEV_DIGITS.get(c, c) for c in s)


def protect(text: str, terms: list[str] | tuple[str, ...] = (), *, quantities: bool = True) -> Protected:
    """Replace each occurrence of a protected term (case-insensitive, whole word, longest first) and, by default, each
    quantity with a placeholder. The surface text found in `text` is what gets restored, so casing is preserved."""
    if _PLACEHOLDER_RE.search(text):
        raise PlaceholderError("source text already contains a placeholder-like token")
    clean = sorted({t.strip() for t in terms if t and t.strip()}, key=len, reverse=True)
    parts = [rf"(?<!\w){re.escape(t)}(?!\w)" for t in clean]
    if quantities:
        parts.append(_QUANTITY)
    if not parts:
        return Protected(text, ())
    rx = re.compile("|".join(f"(?:{p})" for p in parts), re.IGNORECASE)
    found: list[str] = []

    def sub(m: re.Match[str]) -> str:
        found.append(m.group())
        return f"{_PREFIX}{len(found) - 1}{_SUFFIX}"

    return Protected(rx.sub(sub, text), tuple(found))


def restore(translated: str, protected: Protected) -> str:
    """Put the protected terms back. Raises PlaceholderError unless every placeholder appears exactly once."""
    seen: dict[int, int] = {}
    for m in _PLACEHOLDER_RE.finditer(translated):
        k = int(_norm_digits(m.group(1)))
        seen[k] = seen.get(k, 0) + 1
    expected = set(range(len(protected.terms)))
    if set(seen) - expected:
        raise PlaceholderError(f"translation invented placeholders {sorted(set(seen) - expected)}")
    bad = sorted(k for k in expected if seen.get(k, 0) != 1)
    if bad:
        raise PlaceholderError(f"placeholders {bad} missing or duplicated in translation")
    return _PLACEHOLDER_RE.sub(lambda m: protected.terms[int(_norm_digits(m.group(1)))], translated)
