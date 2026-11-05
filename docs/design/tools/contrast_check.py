"""WCAG 2.2 contrast check for docs/design/assets/tokens.css (run: python -I tools/contrast_check.py).
Reads the CSS custom properties for light and dark and tests the pairs the UI actually uses.
Text pairs need >= 4.5:1 (AA); UI/graphic pairs need >= 3:1 (SC 1.4.11)."""
import re, sys, pathlib

css = (pathlib.Path(__file__).parent.parent / "assets" / "tokens.css").read_text(encoding="utf-8")

def block(sel_re):
    m = re.search(sel_re + r"\s*\{(.*?)\n\}", css, re.S | re.M)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", m.group(1)))

light = block(r"^:root")
dark = {**light, **block(r':root\[data-theme="dark"\]')}

def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)

TEXT = [("ink", "bg"), ("ink", "surface"), ("ink-2", "bg"), ("ink-2", "surface"), ("ink-2", "surface-2"),
        ("ink-3", "bg"), ("ink-3", "surface"), ("ink-3", "surface-2"), ("accent-ink", "bg"), ("accent-ink", "surface"),
        ("accent-ink", "accent-soft"), ("on-accent", "accent"), ("on-accent", "accent-hover"),
        ("red-fg", "red-bg"), ("amber-fg", "amber-bg"), ("green-fg", "green-bg"),
        ("red-fg", "surface"), ("amber-fg", "surface"), ("green-fg", "surface"), ("ink", "red-bg"), ("ink", "amber-bg")]
UI = [("line-strong", "surface"), ("line-strong", "bg"), ("focus", "bg"), ("focus", "surface"),
      ("red-fg", "surface"), ("amber-fg", "surface"), ("green-fg", "surface"), ("red-line", "red-bg"),
      ("amber-line", "amber-bg"), ("green-line", "green-bg")]

fails = 0
for name, t in (("light", light), ("dark", dark)):
    print(f"\n== {name} ==")
    for group, pairs, need in (("text", TEXT, 4.5), ("ui", UI, 3.0)):
        for fg, bg in pairs:
            r = ratio(t[fg], t[bg])
            ok = r >= need
            # line-* on *-bg are decorative borders (the label + icon carry meaning); report, don't fail
            soft = fg.endswith("-line") and group == "ui"
            if not ok and not soft:
                fails += 1
            print(f"{'PASS' if ok else ('info' if soft else 'FAIL')}  {group:4} {fg:12} on {bg:11} {r:5.2f}  (need {need})")
print(f"\n{fails} failing required pair(s)")
sys.exit(1 if fails else 0)
