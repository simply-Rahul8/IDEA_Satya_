# ruff: noqa: E501  (generator holds long prose strings and inline CSS)
"""Consultant review pack generator (DRAFT). Run: python -m engine.rules.pack

Builds docs/consultant-pack/ from the rule files so the pack can never drift from the rules.
Outputs a printable HTML page (save as PDF from the browser; PDF export is cut from v1) and a Markdown copy.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

from engine.rules.ruleset import RuleSet, default_ruleset
from engine.rules.schema import NON_OVERRIDABLE_CATEGORIES, Rule, Severity, VerbCondition
from engine.rules.schema import Phrase as PhrasePattern

PACK_DIR = Path(__file__).resolve().parents[2] / "docs" / "consultant-pack"
HTML_NAME = "consultant-pack.html"
MD_NAME = "consultant-pack.md"

CATEGORY_TITLES = {
    "drug_treatment": "Drug and treatment claims (non-overridable)",
    "dmr_disease": "Drugs and Magic Remedies Act diseases and conditions (non-overridable)",
    "fairness": "Fairness and skin colour (non-overridable)",
    "cosmetic_claim": "Cosmetic claims (overridable)",
}

GLOBAL_QUESTIONS = [
    "Citations: every citation below is marked UNVERIFIED. It was drafted without access to the primary texts. "
    "Please check each Act, Rule, Schedule and guideline reference, and give the correct section or rule number where it is wrong.",
    "Severity and overridability: is the split right between what can never be overridden (drug and treatment, DMR Act "
    "diseases, fairness) and what a brand may override with a reason or evidence? Should any overridable rule be locked, or any locked rule be opened?",
    "Coverage: which common claims in Indian beauty listings are missing from this rule set?",
    "False positives: which examples that we treat as safe would you flag, and which flagged examples would you accept?",
    "Ayurveda-inspired cosmetics: the gate refuses any product described as Ayurvedic and asks for review when the wording is only "
    "'inspired by Ayurveda'. Is that the right line? What evidence separates an Ayurvedic drug from a cosmetic with herbal ingredients?",
    "Report wording: is 'No flagged risks under rule set vX. Not legal advice.' acceptable on a brand-facing report, and is there any wording that must be added?",
    "Out-of-scope product types: confirm that supplements, foods, OTC drugs and AYUSH products must all be refused in v1.",
]

SCOPE = [
    "What this pack covers: English claim rules for beauty product listings (title, bullets, description) and the product-type gate. "
    "It is the draft rule set the Satya engine will run.",
    "What it does not cover: Hindi rules (a later pack), Legal Metrology label-field checks, claims printed on packs or shown in images, "
    "marketplace-specific policies, and any product that is not a cosmetic.",
    "How rules match: a rule fires on a verb plus a condition in the same sentence (for example 'cures' near 'eczema'), "
    "or on a fixed phrase. A bare condition word does not fire. 'For acne-prone skin' is safe.",
    "Safe phrases: an allowlist stops named rules firing inside named phrases, such as a standard disclaimer.",
    "Severity: RED blocks approval. ORANGE needs a written reason. Non-overridable rules are always RED and cannot be overridden by anyone.",
    "Wording: Satya never says a listing is 'compliant'. It says 'no flagged risks under rule set vX'. This is not legal advice.",
    "Status: everything here is DRAFT. Nothing is shown to a brand until you sign off and the sign-off is logged in engine/rules/README.md.",
]

ASKS = [
    "For each rule, mark Approve, Change or Remove in the decision box, and write the change.",
    "Check every citation and mark it verified, or correct it.",
    "Answer the open questions under each rule and the general questions at the end.",
    "Sign the sign-off sheet, or say what must change before you can sign.",
]


def _pattern_lines(rule: Rule) -> list[str]:
    out = []
    for p in rule.patterns:
        if isinstance(p, VerbCondition):
            order = "in either order" if p.order == "any" else "verb first"
            out.append(f"Verbs: {', '.join(p.verbs)}")
            out.append(f"Conditions: {', '.join(p.conditions)}")
            out.append(f"Match when the two are in the same sentence, {order}, with at most {p.max_gap} words between.")
        elif isinstance(p, PhrasePattern):
            out.append(f"Phrases: {', '.join(p.phrases)}")
        else:
            out.append(f"Regular expression: {p.regex}")
    return out


def _blocks(rs: RuleSet) -> list[tuple]:
    b: list[tuple] = []
    b.append(("title", "Satya consultant review pack: English rules (DRAFT)"))
    b.append(
        (
            "kv",
            [
                ("Rule set", f"{rs.meta.name} {rs.label}"),
                ("Status", f"{rs.meta.status}: not reviewed, not signed off"),
                ("Content fingerprint", rs.content_hash),
                ("Last updated", rs.meta.updated),
                (
                    "Rules",
                    f"{len(rs.rules)} rules, {len(rs.allowlist)} safe-phrase entries, {len(rs.gate.types)} product-type signals",
                ),
                ("Prepared for", "Cosmetics regulatory consultant (week-2 review, plan P20)"),
            ],
        )
    )
    b.append(("p", "This pack is not legal advice. It is a draft for expert review."))
    b.append(("h2", "1. Scope note"))
    b.append(("ul", SCOPE))
    b.append(("h2", "2. What we ask of you"))
    b.append(("ol", ASKS))
    b.append(("h2", "3. Rule table"))
    rows = []
    for r in rs.rules:
        locked = "No (locked)" if not r.overridable else "Yes"
        rows.append([r.id, r.title, r.severity.value.upper(), locked, "; ".join(c.ref for c in r.sources)])
    b.append(("table", ["ID", "Rule", "Severity", "Overridable", "Sources"], rows))

    b.append(("h2", "4. Rules in detail"))
    for cat, title in CATEGORY_TITLES.items():
        group = [r for r in rs.rules if r.category.value == cat]
        b.append(("h3", title))
        for r in group:
            b.append(("rule", r))

    b.append(("h2", "5. Safe-phrase allowlist"))
    b.append(
        (
            "p",
            "Inside these phrases the named rules do not fire. Entries that touch a non-overridable rule are marked LOCKED RULE: please look at these closely.",
        )
    )
    rows = []
    for a in rs.allowlist:
        locked = any(not rs.rule(rid).overridable for rid in a.applies_to)
        rows.append(
            [
                a.id,
                "; ".join(a.phrases),
                ", ".join(a.applies_to) + ("  (LOCKED RULE)" if locked else ""),
                a.note,
            ]
        )
    b.append(("table", ["ID", "Phrases", "Applies to", "Why"], rows))

    b.append(("h2", "6. Product-type gate"))
    b.append(
        (
            "p",
            "Satya v1 handles cosmetics only. Ayurvedic, AYUSH, OTC-drug and supplement products are refused with an explanation. "
            "The gate reads the listing text and the brand's declared type. It cannot verify a licence. "
            "Hard signals refuse the product. Weak signals ask for a review, or pass when the brand declares the product a cosmetic.",
        )
    )
    for name, cfg in rs.gate.types.items():
        b.append(("h3", f"{cfg.label} ({name})"))
        b.append(
            (
                "kv",
                [
                    ("Hard signals (refuse)", ", ".join(cfg.hard) or "none"),
                    ("Weak signals (review)", ", ".join(cfg.weak) or "none"),
                    ("Explanation shown", cfg.explanation),
                ],
            )
        )
        b.append(("examples", cfg.examples.positive, cfg.examples.negative, "Refused", "Passes"))

    b.append(("h2", "7. Open questions"))
    b.append(("p", "General questions:"))
    b.append(("ol", GLOBAL_QUESTIONS))
    per_rule = [(r.id, q) for r in rs.rules for q in r.open_questions]
    b.append(("p", f"Rule-specific questions ({len(per_rule)}), repeated here as a checklist:"))
    b.append(("table", ["Rule", "Question", "Your answer"], [[rid, q, ""] for rid, q in per_rule]))

    b.append(("h2", "8. Sign-off sheet"))
    b.append(
        (
            "kv",
            [
                ("Rule set reviewed", f"{rs.meta.name} {rs.label}, fingerprint {rs.content_hash}"),
                ("Decision", "[ ] Approved   [ ] Approved with the changes listed   [ ] Not approved"),
                ("Reviewer name and qualification", ""),
                ("Date", ""),
                ("Signature", ""),
                ("Changes required", ""),
            ],
        )
    )
    b.append(
        (
            "p",
            "The board user records the outcome in the sign-off log in engine/rules/README.md. Until then the rule set stays DRAFT.",
        )
    )
    return b


# --- Markdown ----------------------------------------------------------------------------------


def _md_cell(v: str) -> str:
    return v.replace("|", "\\|").replace("\n", " ")


def _render_md(blocks: list[tuple]) -> str:
    out: list[str] = []
    for blk in blocks:
        kind = blk[0]
        if kind == "title":
            out.append(f"# {blk[1]}\n")
        elif kind == "h2":
            out.append(f"\n## {blk[1]}\n")
        elif kind == "h3":
            out.append(f"\n### {blk[1]}\n")
        elif kind == "p":
            out.append(f"{blk[1]}\n")
        elif kind == "ul":
            out.extend(f"- {i}" for i in blk[1])
            out.append("")
        elif kind == "ol":
            out.extend(f"{n}. {i}" for n, i in enumerate(blk[1], 1))
            out.append("")
        elif kind == "kv":
            out.extend(f"- **{k}:** {v}" for k, v in blk[1])
            out.append("")
        elif kind == "table":
            out.append("| " + " | ".join(blk[1]) + " |")
            out.append("|" + "---|" * len(blk[1]))
            out.extend("| " + " | ".join(_md_cell(c) for c in row) + " |" for row in blk[2])
            out.append("")
        elif kind == "examples":
            out.append(f"**{blk[3]}:**")
            out.extend(f"- {e}" for e in blk[1])
            out.append(f"**{blk[4]}:**")
            out.extend(f"- {e}" for e in blk[2])
            out.append("")
        elif kind == "rule":
            out.extend(_rule_md(blk[1]))
    return "\n".join(out).rstrip() + "\n"


def _rule_head(r: Rule) -> str:
    lock = "NON-OVERRIDABLE" if r.category in NON_OVERRIDABLE_CATEGORIES else "overridable"
    return f"{r.id}: {r.title} [{r.severity.value.upper()}, {lock}]"


def _rule_md(r: Rule) -> list[str]:
    o = [
        f"#### {_rule_head(r)}\n",
        f"**Why it is flagged:** {r.explanation}\n",
        f"**Rewrite direction:** {r.rewrite_hint}\n",
    ]
    o.append("**Sources (UNVERIFIED unless marked):**")
    o.extend(f"- {c.ref}, {c.provision}" + ("" if not c.verified else " (verified)") for c in r.sources)
    o.append("\n**Patterns:**")
    o.extend(f"- {line}" for line in _pattern_lines(r))
    o.append("\n**Must flag (positive examples):**")
    o.extend(f"- {e}" for e in r.examples.positive)
    o.append("\n**Must not flag (negative examples):**")
    o.extend(f"- {e}" for e in r.examples.negative)
    if r.open_questions:
        o.append("\n**Open questions:**")
        o.extend(f"- {q}" for q in r.open_questions)
    o.append("\n**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______\n")
    return o


# --- HTML --------------------------------------------------------------------------------------

CSS = """
:root { color-scheme: light; }
body { font: 11pt/1.45 Georgia, 'Times New Roman', serif; color: #111; max-width: 46rem; margin: 2rem auto; padding: 0 1rem; }
h1 { font-size: 1.7rem; margin: 0 0 .5rem; }
h2 { font-size: 1.25rem; margin: 2rem 0 .5rem; border-bottom: 1px solid #444; padding-bottom: .2rem; }
h3 { font-size: 1.05rem; margin: 1.4rem 0 .4rem; }
h4 { font-size: 1rem; margin: 0 0 .4rem; }
table { border-collapse: collapse; width: 100%; font: 9.5pt/1.35 Arial, Helvetica, sans-serif; margin: .5rem 0 1rem; }
th, td { border: 1px solid #777; padding: .25rem .4rem; text-align: left; vertical-align: top; }
th { background: #eee; }
.rule { border: 1px solid #555; padding: .6rem .8rem; margin: .8rem 0; break-inside: avoid; }
.tag { font: bold 8.5pt Arial, Helvetica, sans-serif; border: 1px solid #111; padding: 0 .3rem; margin-left: .3rem; }
.box { border: 1px dashed #555; padding: .4rem .6rem; margin-top: .5rem; font: 9.5pt Arial, Helvetica, sans-serif; }
code { font: 9pt Consolas, monospace; }
ul, ol { margin: .3rem 0 .8rem 1.2rem; padding: 0; }
@media print { body { margin: 0; max-width: none; font-size: 10pt; } h2 { break-after: avoid; } h2.page { break-before: page; } a { color: inherit; } }
@page { size: A4; margin: 16mm; }
"""


def _e(s: str) -> str:
    return html.escape(s, quote=False)


def _render_html(blocks: list[tuple], rs: RuleSet) -> str:
    body: list[str] = []
    for blk in blocks:
        kind = blk[0]
        if kind == "title":
            body.append(f"<h1>{_e(blk[1])}</h1>")
        elif kind == "h2":
            body.append(f"<h2>{_e(blk[1])}</h2>")
        elif kind == "h3":
            body.append(f"<h3>{_e(blk[1])}</h3>")
        elif kind == "p":
            body.append(f"<p>{_e(blk[1])}</p>")
        elif kind in ("ul", "ol"):
            body.append(f"<{kind}>" + "".join(f"<li>{_e(i)}</li>" for i in blk[1]) + f"</{kind}>")
        elif kind == "kv":
            body.append(
                "<table>"
                + "".join(f"<tr><th scope='row'>{_e(k)}</th><td>{_e(v)}</td></tr>" for k, v in blk[1])
                + "</table>"
            )
        elif kind == "table":
            head = "".join(f"<th>{_e(h)}</th>" for h in blk[1])
            rows = "".join("<tr>" + "".join(f"<td>{_e(c)}</td>" for c in row) + "</tr>" for row in blk[2])
            body.append(f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>")
        elif kind == "examples":
            body.append(
                f"<p><strong>{_e(blk[3])}:</strong></p><ul>" + "".join(f"<li>{_e(i)}</li>" for i in blk[1]) + "</ul>"
            )
            body.append(
                f"<p><strong>{_e(blk[4])}:</strong></p><ul>" + "".join(f"<li>{_e(i)}</li>" for i in blk[2]) + "</ul>"
            )
        elif kind == "rule":
            body.append(_rule_html(blk[1]))
    title = f"Satya consultant review pack {rs.label} (DRAFT)"
    return (
        "<!doctype html>\n<html lang='en'>\n<head>\n<meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>{_e(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
        + "\n".join(body)
        + "\n</body>\n</html>\n"
    )


def _rule_html(r: Rule) -> str:
    lock = "NON-OVERRIDABLE" if r.category in NON_OVERRIDABLE_CATEGORIES else "overridable"
    sev = "RED" if r.severity is Severity.RED else "ORANGE"
    li = lambda items: "<ul>" + "".join(f"<li>{_e(i)}</li>" for i in items) + "</ul>"  # noqa: E731
    parts = [
        f"<div class='rule'><h4>{_e(r.id)}: {_e(r.title)} <span class='tag'>{sev}</span><span class='tag'>{lock}</span></h4>",
        f"<p><strong>Why it is flagged:</strong> {_e(r.explanation)}</p>",
        f"<p><strong>Rewrite direction:</strong> {_e(r.rewrite_hint)}</p>",
        "<p><strong>Sources (UNVERIFIED unless marked):</strong></p>"
        + li(f"{c.ref}, {c.provision}" + (" (verified)" if c.verified else "") for c in r.sources),
        "<p><strong>Patterns:</strong></p>" + li(_pattern_lines(r)),
        "<p><strong>Must flag (positive examples):</strong></p>" + li(r.examples.positive),
        "<p><strong>Must not flag (negative examples):</strong></p>" + li(r.examples.negative),
    ]
    if r.open_questions:
        parts.append("<p><strong>Open questions:</strong></p>" + li(r.open_questions))
    parts.append(
        "<div class='box'>Reviewer decision: &#9744; Approve &nbsp; &#9744; Change &nbsp; &#9744; Remove<br>Notes:<br><br></div></div>"
    )
    return "".join(parts)


def build(rs: RuleSet | None = None) -> dict[str, str]:
    rs = rs or default_ruleset()
    blocks = _blocks(rs)
    return {MD_NAME: _render_md(blocks), HTML_NAME: _render_html(blocks, rs)}


def write(directory: Path = PACK_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, content in build().items():
        p = directory / name
        p.write_text(content, encoding="utf-8", newline="\n")
        paths.append(p)
    return paths


if __name__ == "__main__":
    for path in write():
        print(path, file=sys.stdout)
