"""Brand setup (plan section 3 step 2): tone, restricted phrases, seller identity and grievance contact.

One profile per workspace. The restricted-phrase list is also a brand-level flag source for the engine:
`restricted_flags(text, phrases)` returns review-level flags (never red, never a block) so a brand can mark
words it does not want in its own copy. It cannot weaken or replace a rule from the rule set (P17).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from engine.models import Flag, Severity
from engine.repo.rest import Rest

TONES = {
    "warm": "Warm and friendly",
    "clinical": "Clinical and precise",
    "premium": "Premium and minimal",
}
MAX_PHRASES, MAX_PHRASE_LEN = 50, 80
BRAND_RULE_ID = "BRAND-RESTRICTED"
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


@dataclass(frozen=True)
class BrandProfile:
    tone: str = "warm"
    restricted_phrases: tuple[str, ...] = ()
    seller_legal_name: str = ""
    address: str = ""
    grievance_name: str = ""
    grievance_email: str = ""


def parse_phrases(raw: str) -> list[str]:
    """One phrase per line (commas also split), trimmed, de-duplicated case-insensitively, order kept."""
    seen: dict[str, str] = {}
    for part in re.split(r"[\n,]", raw):
        phrase = " ".join(part.split())
        if phrase:
            seen.setdefault(phrase.casefold(), phrase)
    return list(seen.values())


def validate(form: dict[str, str]) -> tuple[BrandProfile | None, dict[str, str]]:
    """The profile when the form is valid, else (None, {field: message}). Text is data and is never interpreted."""
    get = lambda k: _CONTROL.sub("", form.get(k, "")).strip()  # noqa: E731
    errors: dict[str, str] = {}
    tone = get("tone")
    if tone not in TONES:
        errors["tone"] = "Choose one of the three tones."
    phrases = parse_phrases(_CONTROL.sub("", form.get("restricted_phrases", "")))
    if len(phrases) > MAX_PHRASES:
        errors["restricted_phrases"] = f"Add at most {MAX_PHRASES} phrases."
    elif any(len(p) > MAX_PHRASE_LEN for p in phrases):
        errors["restricted_phrases"] = f"Keep each phrase under {MAX_PHRASE_LEN} characters."
    limits = {
        "seller_legal_name": (120, "the seller's legal name"),
        "address": (400, "the registered address"),
        "grievance_name": (120, "the grievance officer's name"),
    }
    values = {k: get(k) for k in limits}
    for key, (cap, what) in limits.items():
        if not values[key]:
            errors[key] = f"Enter {what}."
        elif len(values[key]) > cap:
            errors[key] = f"Keep this under {cap} characters."
    email = get("grievance_email")
    if not _EMAIL.match(email) or len(email) > 254:
        errors["grievance_email"] = "Enter a valid email address, for example grievance@yourbrand.in."
    if errors:
        return None, errors
    return BrandProfile(
        tone, tuple(phrases), values["seller_legal_name"], values["address"], values["grievance_name"], email
    ), {}


class BrandStore:
    """Profiles keyed by workspace id. Every call takes the workspace id, so one workspace cannot reach another's."""

    def __init__(self, rest: Rest) -> None:
        self._rest = rest

    def get(self, workspace_id: str) -> BrandProfile | None:
        rows = self._rest.select("brand_profiles", {"workspace_id": workspace_id})
        if not rows:
            return None
        r = rows[0]
        return BrandProfile(
            r["tone"],
            tuple(r.get("restricted_phrases") or ()),
            r["seller_legal_name"],
            r["address"],
            r["grievance_name"],
            r["grievance_email"],
        )

    def save(self, workspace_id: str, p: BrandProfile) -> None:
        values = {
            "tone": p.tone,
            "restricted_phrases": list(p.restricted_phrases),
            "seller_legal_name": p.seller_legal_name,
            "address": p.address,
            "grievance_name": p.grievance_name,
            "grievance_email": p.grievance_email,
        }
        if not self._rest.update("brand_profiles", {"workspace_id": workspace_id}, values):
            self._rest.insert("brand_profiles", {"workspace_id": workspace_id, **values})

    def restricted_phrases(self, workspace_id: str) -> tuple[str, ...]:
        """The engine's brand-level flag source: what `restricted_flags` takes."""
        p = self.get(workspace_id)
        return p.restricted_phrases if p else ()


def restricted_flags(text: str, phrases: tuple[str, ...] | list[str]) -> list[Flag]:
    """One review-level flag per restricted phrase found in `text` (case-insensitive, whole words)."""
    flags = []
    for phrase in phrases:
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in phrase.split()) + r"(?!\w)"
        m = re.search(pattern, text, re.I)
        if m:
            flags.append(
                Flag(
                    rule_id=BRAND_RULE_ID,
                    severity=Severity.ORANGE,
                    source="brand",
                    overridable=True,
                    reason=f"Your brand restricted the phrase \u201c{phrase}\u201d.",
                    matched_text=m.group(0),
                    suggestion="Reword it, or keep it with a reason.",
                )
            )
    return flags
