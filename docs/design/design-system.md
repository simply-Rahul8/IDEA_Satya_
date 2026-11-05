# Satya design system, draft v0.1 (SAT-7)

Status: **draft for board review.** Tokens are stable enough to prototype against; the final spec is written after the board picks variants (separate task). Source of truth for values: [`assets/tokens.css`](assets/tokens.css). Visual specimen: [`system.html`](system.html).

Plan references: §4 (the "awestruck" bar), §3 journey steps 3, 7, 10.

## 1. Direction

Premium, calm, trustworthy: *compliance meets beauty*, built for Indian beauty retail rather than generic SaaS.

| Decision | Choice | Why |
|---|---|---|
| Base | Warm paper neutrals (`#faf6f0` bg, `#fffcf8` surface), warm charcoal in dark (never pure black) | Feels like a beauty counter or magazine, not a dashboard. Easy on long review sessions. |
| Accent | **Jamun**, a deep plum (`#6a2c5e`; `#e3b0d8` in dark) | Confident and beauty-adjacent. Deliberately *not* red, amber or green, so it can never be mistaken for severity. |
| Display type | Editorial serif: Fraunces, fallback Newsreader / Georgia | Gives the "awestruck" moments a magazine voice, and makes sentence text in review read as copy. |
| Body type | Inter, fallback Noto Sans / system | Legible at 16px on cheap Android screens. |
| Hindi | Noto Sans Devanagari / Nirmala UI, 1.75 line-height | Ready for step 8 (Hindi output). Hindi UI stays out of v1 (plan §1, cut list). |
| Voice | Plain, specific, never "compliant". Says "no flagged risks under rule set vX". | AGENTS.md hard rule and plan P20. |

## 2. Tokens

### Colour (light / dark)

| Token | Light | Dark | Use |
|---|---|---|---|
| `bg` | `#faf6f0` | `#151110` | page |
| `surface` / `surface-2` / `sunken` | `#fffcf8` / `#f3ece2` / `#ece2d4` | `#1e1815` / `#272019` / `#120e0c` | cards / wells / meter track |
| `line` / `line-strong` | `#e2d7c8` / `#85755f` | `#3a2f27` / `#8f7f6c` | dividers / control borders (≥ 3:1) |
| `ink` / `ink-2` / `ink-3` | `#261e19` / `#4f443a` / `#6b5e52` | `#f4ece3` / `#cbbdaf` / `#ad9e8f` | primary / secondary / smallest text |
| `accent`, `accent-hover`, `accent-soft`, `on-accent` | `#6a2c5e`, `#55224b`, `#f2e5ef`, `#fff` | `#e3b0d8`, `#efc6e6`, `#3a2336`, `#2b0f27` | actions, selected state, source-claim highlight |
| `focus` | `#1d5fd1` | `#8cb4ff` | focus ring: 3px, 2px offset, always visible |
| `red-*` / `amber-*` / `green-*` (`fg`, `bg`, `line`) | see CSS | see CSS | **severity only** |

**Severity is never colour alone.** Each state has its own icon, word and pattern:

| State | Icon | Word | Inline pattern | Meaning |
|---|---|---|---|---|
| Red | octagon-stop | **Blocked** | solid thick underline | non-overridable or hard block; stops approval |
| Amber | triangle | **Review** | dashed underline, dashed left edge | needs a reason or evidence |
| Green | circle-check | **Clear** | none | "no flagged risks under rule set vX" (never "compliant") |

**Contrast, verified.** `python -I tools/contrast_check.py` tests 21 text pairs (≥ 4.5:1) and 10 UI pairs (≥ 3:1) in both themes; result: **0 failing required pairs** ([`tools/contrast_report.txt`](tools/contrast_report.txt)). The only sub-3:1 values are decorative badge borders (`*-line`); the badge text and icon inside them are ≥ 4.5:1.

### Type scale

Fluid from 360px, ratio ~1.25, 16px floor for anything a user must read, 13px floor for labels.

`xs 13 · sm 15 · base 16 · md 18 · lg 20–24 · xl 24–32 · 2xl 32–52 · 3xl 40–72`. Line-height 1.1 (display), 1.3 (snug), 1.6 (body). Measure 66ch. Display headings use `text-wrap: balance`.

### Space, radii, targets

Space is a 4px base: `s-1 .25rem … s-9 6rem`. Radii: `sm 6 · md 12 · lg 20 · pill`. Minimum touch target 44px (`--tap`), above WCAG 2.2 SC 2.5.8's 24px floor. Dense data cells (heat-strip) use ≥ 24px.

### Motion

Durations `120 / 220 / 420 / 700 ms`, one ease-out curve `cubic-bezier(.2,.8,.2,1)`. Used for: underline draw (700), meter grow (420, staggered 70ms), verdict rise (420), counters (700), sheet slide (420), flag-resolve pulse (700). `prefers-reduced-motion: reduce` collapses every animation and transition to ~0ms (one rule in `tokens.css`) and JS counters jump to the final value. Nothing is essential to understanding that depends on motion.

### Themes

Light and dark are *designed*, not inverted: the dark ramps are separate steps validated against the dark surface. Default follows `prefers-color-scheme`; a toggle sets `data-theme` and persists in `localStorage`.

## 3. Layout and responsive rules

- Mobile-first at **360px**; verified by rendering each screen in a true 360px viewport (`tools/shots.sh`).
- Content width `min(100% - 2rem, 72rem)`. Two-column layouts begin at 60–64rem; below that, side panels become tabs, drawers or bottom sheets.
- Citation sheet: right-hand sheet ≥ 48rem, bottom sheet below. Focus moves in, Esc and scrim close, focus returns to the opener, Tab is trapped while open.

## 4. Accessibility rules (WCAG 2.2 AA)

1. Every flag = icon + word (+ rule id); highlights also differ by pattern.
2. All interactive things are real `button`/`a`/`input`, or have a role, label and key handler (Enter/Space) where a `mark` is used.
3. Live regions (`aria-live="polite"`) announce re-check results and approval state; errors use `role="alert"`.
4. Focus ring never removed; skip link on every page; one `h1` per page.
5. Status and results are available without hover (tooltips in the heat-strip duplicate an `aria-label` and a table view).
6. Disabled-looking *Approve* uses `aria-disabled` and explains why in text next to it, so it stays focusable and the reason is discoverable.
7. No information by colour alone; no motion required; zoom to 200% reflows (no fixed-width containers).

## 5. Component inventory (to become Jinja components in `web/components/`)

| Component | Notes |
|---|---|
| `Button` (primary / secondary / ghost / small) | pill, 44px, `aria-disabled` pattern |
| `FlagBadge` | icon + label + optional rule id; red / amber / green / ink |
| `Chip` (anchor, type, filter, unanchored) | `aria-pressed` for toggles |
| `InlineHighlight` | `mark.hl.hl-red/amber`; draws in with the underline animation |
| `SeverityMeter` | 5 segments plus text label; `role="img"` with label |
| `CitationSheet` | rule label, quote, why, source, what to do, override rule, DRAFT banner |
| `FlagPanel` | flag list, reason, citation button, suggested rewrite, keep-with-reason, "wrong flag?" 👎 |
| `ClaimItem` | Product Truth claim with state badge and evidence |
| `ApprovalBar` / `Tally` | explains exactly what blocks approval |
| `DraftBanner` | regulatory text is DRAFT until consultant sign-off |
| `Toast`, `TopBar`, `ThemeToggle` | |
| `HeatStripCell`, `DataTable` | audit dashboard (sketch) |
| `Field` / `Label` | 1.5px `line-strong` border |

The prototype's `FlagPanel`, `ClaimItem`, anchor chips and sheet are shared across all three review variants, which is the point: the variants differ in layout and mood, not in the parts.

## 6. Performance budget

Measured on the prototypes (CSS + JS, gzip): **≈ 14–16 KB** per page (`tokens.css`, `review-parts.css`, `proto.js` and inline page code). Adding HTMX (~14 KB gz) and Alpine (~16 KB gz) puts the worst case near **~46 KB, under a third of the 150 KB budget**. The production Tailwind purge should land in the same range because the prototype CSS is already hand-minimal. No SPA framework.

Fonts are not counted in the JS+CSS budget but matter for LCP: ship Fraunces (display, two weights, Latin subset) and Inter (variable, Latin subset) as self-hosted WOFF2 with `font-display: swap` and preload the display face only. Devanagari loads on demand with `:lang(hi)`. This draft uses the local fallback stack so the board can open files offline.

## 7. Tailwind mapping (for implementation)

Expose each token as a CSS variable (as in `tokens.css`) and reference them from `tailwind.config.js`, so light/dark is one class swap and Tailwind's purge stays effective:

```js
theme: { extend: {
  colors: { bg: 'var(--bg)', surface: 'var(--surface)', ink: 'var(--ink)', accent: 'var(--accent)',
            red: { fg: 'var(--red-fg)', bg: 'var(--red-bg)' } /* amber, green likewise */ },
  fontFamily: { display: 'var(--font-display)', sans: 'var(--font-sans)' },
  borderRadius: { sm: 'var(--r-sm)', md: 'var(--r-md)', lg: 'var(--r-lg)' },
}}
```

## 8. Known gaps and assumptions (draft)

- Rule labels, reasons and sources in the prototypes are **illustrative and unreviewed**; they must be replaced by consultant-signed rule text before anything is brand-facing (P20). Source names are placeholders to show the layout of a citation, not legal citations.
- The prototype rule engine (`assets/proto.js`) is a ~6-rule stand-in, not `engine/guardrails`. Highlighting in production will come from the real engine over HTMX partials; the < 300 ms re-check target applies there. The prototype shows a measured in-browser re-check time only to demonstrate the affordance.
- Hindi review view, bulk-upload screens, export screens and onboarding are not designed yet; they will reuse these components.
- Fonts not bundled (see §6). Fraunces and Inter are open-licence (OFL); the licence check is a trivial human step if the board wants it logged.
