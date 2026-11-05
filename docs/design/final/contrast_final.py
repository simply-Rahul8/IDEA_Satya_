"""Contrast check for the colour pairs the SAT-13 final specs add on top of the SAT-7 set.
Run: python -I docs/design/final/contrast_final.py   (exit 1 on any failing required pair)
Text >= 4.5:1 (AA); UI/graphic >= 3:1 (SC 1.4.11). Reads ../assets/tokens.css, light and dark."""

import pathlib
import re
import sys

css = (pathlib.Path(__file__).resolve().parent.parent / "assets" / "tokens.css").read_text(encoding="utf-8")


def block(sel_re):
    m = re.search(sel_re + r"\s*\{(.*?)\n\}", css, re.S | re.M)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", m.group(1)))


light = block(r"^:root")
dark = {**light, **block(r':root\[data-theme="dark"\]')}


def lum(h):
    c = [int(h[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# (foreground, background, where it is used)
TEXT = [
    ("ink", "accent-soft", "linked sentence row"),
    ("ink-2", "accent-soft", "highlighted claim, used-in text"),
    ("ink-3", "accent-soft", "claim evidence line while highlighted (small text)"),
    ("ink-3", "surface-2", "inspector secondary text"),
    ("ink-2", "surface-2", "notice, kept-with-reason panel, flag-ink"),
    ("ink", "surface-2", "inspector, notice body"),
    ("bg", "ink", "toast (inverse)"),
    ("red-fg", "surface", "over-limit counter"),
    ("ink-2", "sunken", "progress legend on track"),
    ("accent-ink", "surface-2", "ghost button on well"),
    ("amber-fg", "surface", "unanchored chip text on surface"),
    ("on-accent", "accent", "pressed anchor chip"),
]
UI = [
    ("ink-2", "bg", "progress segment: kept"),
    ("green-fg", "bg", "progress segment: clear; clear cell outline"),
    ("green-fg", "surface", "clear cell outline on card"),
    ("red-fg", "surface", "progress/heat: blocked"),
    ("amber-fg", "surface", "heat: review hatch"),
    ("line-strong", "surface", "pending cell outline, dropzone border"),
    ("ink-3", "surface-2", "skipped cell dots"),
    ("ink-2", "surface-2", "error cell stripes"),
    ("ink", "surface", "current-cell ring"),
    ("accent", "surface", "source-claim outline"),
    ("accent", "bg", "source-claim outline on page"),
    ("ink-2", "surface", "kept row dotted edge"),
]

fails = 0
for name, t in (("light", light), ("dark", dark)):
    print(f"\n== {name} ==")
    for group, pairs, need in (("text", TEXT, 4.5), ("ui", UI, 3.0)):
        for fg, bg, use in pairs:
            r = ratio(t[fg], t[bg])
            ok = r >= need
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {group:4} {fg:11} on {bg:11} {r:5.2f}  (need {need})  {use}")
print(f"\n{fails} failing required pair(s)")
sys.exit(1 if fails else 0)
