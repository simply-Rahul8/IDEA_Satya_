# Variant comparison for the board user (SAT-7)

**Purpose:** help you pick one variant per screen. This note deliberately does **not** recommend a winner. Picking is your decision, tracked in the separate decision task. Final specs and Jinja components start only after the pick.

**How to look:** open [`index.html`](index.html) in a browser (double-click; no server needed). Every page is live: paste or edit text and the mock rules re-check it. Use the moon button for dark. Try a narrow window (360px) too. Screenshots of every variant, light and dark, at 360px and 1280px are in [`screenshots/`](screenshots/).

All variants share the same tokens, the same icon + label + pattern rule for flags, the same citation sheet and the same draft-rule-set wording. They differ in layout, pace and mood.

---

## Public checker · "Is my claim safe?" (journey step 10, the shareable outreach hook)

| | **A · Editorial Paper** | **B · Split Atelier** | **C · Marginalia** |
|---|---|---|---|
| File | [checker-a.html](checker-a.html?demo) | [checker-b.html](checker-b.html?demo) | [checker-c.html](checker-c.html?demo) |
| Idea | One calm column. Type on "paper"; risky phrases get animated underlines *in the text box itself*. Verdict card rises below. | Workbench. Input left; right shows a live gauge and an annotated read-out with clickable icon markers. | Plum hero with the input; the copy comes back as an editor's proof with numbered markers and a notes rail. Big counting counters. |
| Wow moment | Underline drawing as you type; verdict meter filling. | Gauge sweeping as you type; two-pane "instant" feel. | Dramatic hero, counters, proof-sheet reveal. The most screenshot-able. |
| Where the citation lives | Verdict card list → side sheet | Tap a marker in the read-out → side sheet | Numbered note → side sheet; marker in text jumps to its note |
| Mobile (360px) | Excellent: it is one column already. | Stacks; sticky bottom dock shows live counts. Slightly longer scroll. | Hero + stacked proof + notes; good, longest page. |
| Strength | Simplest, most elegant, closest to "premium and calm". Lowest build risk. Editing and seeing flags in the same place. | Fastest feedback loop; feels like a tool; the gauge communicates severity at a glance. | Strongest brand statement and best for sharing a screenshot; numbered notes read well to a non-expert. |
| Trade-off | Underlines in a textarea are patterned, but only the list below carries icon + label (the inline text has no icon). Less visual drama. | Two panes duplicate the text (input and read-out); more to build and keep in sync; busier. | Heaviest visually; the dark hero must be maintained for both themes; marker numbers can wrap awkwardly on narrow screens; text is edited in the hero, not inline. |
| Build effort (relative) | Lowest. One textarea plus an overlay layer. | Medium. Read-out partial plus gauge SVG. | Medium-high. Hero, marker numbering, notes rail. |
| JS+CSS (gzip, prototype) | 14.4 KB | 14.2 KB | 14.9 KB |

## Review screen · journey step 7 (anchor, flag, reason, citation, rewrite, live re-check)

| | **A · Sentence Cards** | **B · Truth ↔ Copy** | **C · Document + Inspector** |
|---|---|---|---|
| File | [review-a.html](review-a.html) | [review-b.html](review-b.html) | [review-c.html](review-c.html?demo) |
| Idea | One card per sentence. Flag, why, rewrite and reason sit *inside* the card. Product Truth is a side rail. | Evidence-first. The Product Truth ledger sits beside the copy; clicking an anchor highlights the source claim and every sentence that shares it. | Reads like the live product page. Select a sentence; an inspector panel explains and fixes it. A row of status squares jumps between sentences. |
| Approval | Sticky bottom bar with plain-language reason approval is blocked | Sticky gate at top with a per-sentence progress strip | Top strip; sentence status squares with icons |
| Anchor ↔ claim | Chip highlights the claim in the rail (mobile: rail is a collapsible at top) | Strongest. Two-way cross-highlight; mobile uses Copy / Truth tabs | Chip highlights the claim card in the inspector |
| Mobile (360px) | Good. Straightforward vertical list; long because every flagged card expands. | Good, but the claim ledger is a separate tab, so tracing means switching tabs. | Inspector becomes a bottom panel covering ~58% of the screen; document is partly hidden while fixing. |
| Strength | Most scannable and predictable; each sentence is self-contained; easiest to make accessible and to test. | Best communicates "every sentence is anchored to a confirmed claim", the product's core promise; best for evidence-heavy reviewers. | Most "awestruck" and closest to what the shopper will see; least visual clutter until you need detail. |
| Trade-off | Long on screen when many flags; less sense of the whole page; claim tracing is secondary. | Most complex layout; the top gate is tall on tablets; tabs on phones. | Detail is one tap away rather than visible; the mobile bottom panel is cramped; approval state is less prominent. |
| Build effort (relative) | Lowest. | Highest (two panes, tabs, cross-highlight). | Medium (selection state plus inspector). |
| JS+CSS (gzip, prototype) | 14.7 KB | 15.3 KB | 15.8 KB |

Shared across all three review variants (so this is not a differentiator): edits re-check as you type; 🔴 blocks approval; 🟠 needs a typed reason; "Use rewrite" resolves a flag with a micro-transition; 👎 "Wrong flag?" goes to the tuning queue; unanchored sentences get an explicit "No source claim" chip.

## Audit dashboard heat-strip (sketch only, not a pick)

[`audit-heatstrip.html`](audit-heatstrip.html): one square per SKU (120 sample products), sorted by risk; counters animate on load; severity filter chips and a sort toggle work without a reload; hover or focus a square for the reason; a table view of the same data is below. Fills are solid / hatched / pale **and** the legend, tooltip and table use icon + word. Cells are ≥ 24px at 360px (12 columns) and 40 columns on desktop. It reuses the same tokens, so it will sit comfortably beside whichever checker and review you choose.

## What does not change with your choice

- Tokens, type, dark mode, motion rules and the component inventory ([design-system.md](design-system.md)).
- Each page is ~15 KB gzip of CSS+JS in the prototype; with HTMX and Alpine, ~46 KB, far under the 150 KB budget, whichever you choose.
- No variant needs a SPA framework.

## Honest caveats

- Rules, reasons and sources shown are **illustrative drafts**, not consultant-reviewed. No screen says "compliant".
- The in-browser rule engine is a stand-in. The < 300 ms re-check is a production target (HTMX partial), not demonstrated here.
- Fraunces and Inter are not bundled in this draft; you will see the local serif/sans fallback. The final look will be slightly more refined with the real faces.
- Mobile screenshots are of a true 360px viewport; I have not run a real-device or Lighthouse pass yet. That belongs to the later `/design-review` step once a variant is chosen.
- I did not run the `/design-consultation` and `/design-shotgun` skills: they are not installed for this agent, so I followed their intent by hand (system first, then three distinct variants per screen).

## Your decision

For each of **checker** and **review**, choose A, B or C (or "mix: X's layout with Y's …"). The decision task is separate from this one.
