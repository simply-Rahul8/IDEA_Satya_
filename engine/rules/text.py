"""Text primitives shared by the rule matcher and the product-type gate.

Offsets: `normalize` keeps a map back to the original string so flags can highlight the user's own text.
Listing text is data, never instructions (P19): nothing here evaluates or executes it.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_QUOTES = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "‐": "-",
    "‑": "-",
    "‒": "-",
    "–": "-",
    "—": "-",
    " ": " ",
}
_TOKEN = re.compile(r"[^\W_]+(?:['\-][^\W_]+)*")
_BOUNDARY = re.compile(r"[\n\r;•]|[.!?](?=\s|$)")
_ABBREVIATIONS = frozenset({"no", "dr", "mr", "mrs", "ms", "st", "vs"})


@dataclass(frozen=True)
class Tok:
    text: str
    start: int  # offsets into the normalised string
    end: int
    sentence: int


@dataclass(frozen=True)
class Normalized:
    original: str
    text: str
    index: tuple[int, ...]  # normalised char position -> original char position
    tokens: tuple[Tok, ...]

    def original_span(self, start: int, end: int) -> tuple[int, int]:
        return self.index[start], self.index[end - 1] + 1


def normalize(text: str) -> tuple[str, tuple[int, ...]]:
    chars: list[str] = []
    index: list[int] = []
    for i, ch in enumerate(text):
        if unicodedata.category(ch) == "Cf":  # zero-width joiners and friends are a classic evasion
            continue
        ch = _QUOTES.get(ch, ch)
        folded = " and " if ch == "&" else unicodedata.normalize("NFKC", ch).lower()
        for out in folded:
            chars.append(out)
            index.append(i)
    return "".join(chars), tuple(index)


def analyse(text: str) -> Normalized:
    norm, index = normalize(text)
    breaks = [(m.start(), m.group()) for m in _BOUNDARY.finditer(norm)]
    tokens: list[Tok] = []
    sentence = 0
    prev_end = 0
    for m in _TOKEN.finditer(norm):
        if tokens and any(
            prev_end <= pos < m.start() and not (mark in ".!?" and tokens[-1].text in _ABBREVIATIONS)
            for pos, mark in breaks
        ):
            sentence += 1  # "No. 1" and "Dr. Rao" are not sentence ends
        tokens.append(Tok(m.group(), m.start(), m.end(), sentence))
        prev_end = m.end()
    return Normalized(text, norm, index, tuple(tokens))


Term = tuple[tuple[str, bool], ...]  # (token, is_prefix_wildcard) per position


def compile_term(term: str) -> Term:
    parts: list[tuple[str, bool]] = []
    for raw in term.split():
        prefix = raw.endswith("*")
        norm, _ = normalize(raw.rstrip("*"))
        toks = [m.group() for m in _TOKEN.finditer(norm)]
        if not toks:
            raise ValueError(f"term {term!r} has an empty token")
        for k, tok in enumerate(toks):
            parts.append((tok, prefix and k == len(toks) - 1))
    if not parts:
        raise ValueError("empty term")
    return tuple(parts)


def find_term(doc: Normalized, term: Term) -> list[tuple[int, int]]:
    """Token index ranges [i, j) where the term matches inside one sentence."""
    toks = doc.tokens
    n = len(term)
    hits = []
    for i in range(len(toks) - n + 1):
        sentence = toks[i].sentence
        for k, (want, prefix) in enumerate(term):
            t = toks[i + k]
            if t.sentence != sentence or not (t.text.startswith(want) if prefix else t.text == want):
                break
        else:
            hits.append((i, i + n))
    return hits
