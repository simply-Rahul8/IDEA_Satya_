# Foundations (v1.0 final)

Applies to all three screens. Tokens live in [`../assets/tokens.css`](../assets/tokens.css) (v0.1 values unchanged, v1.0 additions appended). Component CSS reference values live in [`final-parts.css`](final-parts.css). Everything is **draft regulatory content** until consultant sign-off (P20).

## 1. Engine → UI vocabulary (this fixes three prototype assumptions)

The prototypes used `red/amber` and "red = never overridable". The real rule schema (`engine/rules/schema.py`) differs, so the UI is built on this table. Rule IDs look like `EN-DRUG-001`, not `DRG-01`.

| Engine `severity` | `overridable` | UI state (`data-s`) | Word | Icon | Inline pattern | Resolves by |
|---|---|---|---|---|---|---|
| `red` | `false` (drug, DMR disease, fairness) | `red` | **Blocked** + "Cannot be overridden" | octagon (`block`) | solid underline, solid start edge | Rewrite or remove only. No override control is rendered at all. |
| `red` | `true` (e.g. EN-CLAIM-001, "regulator approval") | `red` | **Blocked** + "Evidence can override" | `block` | same as above | Rewrite, remove, or keep **with an evidence reference** (file upload or document ID, like P25). |
| `orange` | `true` | `amber` (token name stays `amber`) | **Review** / "Needs a reason" | triangle (`warn`) | dashed underline, dashed start edge | Rewrite, remove, or keep with a typed reason. |
| none | | `green` | **Clear** | `ok` | none | n/a |
| (sentence, resolved by user) | | `kept` | **Kept with reason** | `check` in ink | dotted start edge | Edit the reason, or edit the text (re-checks). |

Rules that follow from this:
- **"Kept with reason" is never green and never says "Clear".** Green means "no flagged risks under rule set vX". A kept sentence still carries a flag; it is shown in ink with its reason visible.
- Non-overridable flags render **no** reason or evidence field. The API also refuses (`policy.check_override`, ADR-9). The UI must not rely on that alone, and must not rely on hiding alone either.
- **Open question for the CTO (plan vs rules):** plan §10 says "0 🔴 in exports", while overridable reds can be kept with evidence. The specs build the evidence path behind one setting, `allow_red_override`. If the CTO decides reds never export, set it to false: the evidence field disappears and the note reads "Rewrite or remove it." Nothing else changes.
- Rule-set label: always `rule_set.label` from the engine (`v0.1.0-draft`). Never hard-code it.

### Display fields a rule/flag must provide
| Field | From | Used in |
|---|---|---|
| `rule_id`, `severity`, `overridable`, `category` | `Flag` | badge, sheet, policy text |
| `title` | `Rule.title` | flag list, sheet heading |
| `explanation` | `Rule.explanation` | "Why it is flagged" |
| `rewrite_hint` | `Rule.rewrite_hint` | "What to do" (checker) |
| `sources[]` `{ref, provision, verified}` | `Rule.sources` | "Source". `verified: false` shows a "Not yet verified" tag (all are unverified today, P16). |
| `text` | `Flag.text` | quote |
| `suggested_rewrite` | Engine generation (review only) | rewrite card. Not available in the public checker, which is deterministic only (P18). |
| `rule_set.label`, `rule_set.is_signed_off` | `RuleSet` | stamps, draft banner |

## 2. Tokens

Unchanged from `design-system.md` §2 (colour, type, space, radii, motion). **Additions** (already appended to `tokens.css`):

| Token | Value | Why |
|---|---|---|
| `--z-gate/dock/scrim/sheet/toast` | 20 / 30 / 40 / 50 / 60 | one z-scale; the prototypes used scattered numbers |
| `--tap-coarse` | 2.75rem (44px) | chips and small buttons grow on `pointer: coarse`. The prototype chips were 28px, below the design system's own 44px rule. |
| `--cell` | 1.625rem (26px) | heat-strip minimum. The prototype cells were about 21px at 360px, under SC 2.5.8's 24px. |
| `--sheet-w` | 26rem | citation sheet width |
| `--gate-h`, `--dock-h` | runtime px | set by a `ResizeObserver` so sticky offsets and `scroll-padding` are never magic numbers (the prototype hard-coded `9.5rem`) |

Colour pairs added by the final specs are verified in both themes: [`contrast_final.txt`](contrast_final.txt) (`python -I docs/design/final/contrast_final.py`, 0 failing; combined with the SAT-7 report there are 0 failing required pairs).

**Severity colours are for severity only.** System notices (errors, rate limits, "couldn't check") use the neutral `Notice` component: ink border, `error`/`info` icon, a plain sentence. Red never means "the app broke".

## 3. Layout

- Mobile-first at **360px**; content width `min(100% - 2rem, 72rem)`; nothing fixed-width; reflows at 200% zoom and 320px.
- Breakpoints (rem, so they follow user font size): `30rem` flag list stacks · `48rem` gate becomes sticky, dock hides, sheet becomes a right panel, gutter icon appears · `60rem` review becomes two columns and tabs disappear.
- `html { scroll-padding-top: var(--gate-h)+0.75rem; scroll-padding-bottom: var(--dock-h)+0.75rem }` so a sticky bar never covers a focused element (WCAG 2.2 SC 2.4.11).
- Hindi (journey step 8) is not designed here, but nothing may break it: no fixed line heights on text, `:lang(hi)` already sets Devanagari and 1.75 line-height, containers grow with content.

## 4. Themes

Light and dark are designed ramps. Default follows `prefers-color-scheme`. A toggle sets `data-theme` on `<html>`, persisted in `localStorage` (`satya-theme`). To avoid a flash, an inline 6-line script in `<head>` reads it before first paint (the only inline script; allowed by hash if a CSP is added). Theme toggle is a `button` with `aria-pressed` reflecting dark, and a visible-to-AT label "Dark theme".

## 5. Motion catalogue (all collapse under `prefers-reduced-motion: reduce`)

| Moment | Where | Duration / curve | Reduced-motion behaviour |
|---|---|---|---|
| Underline draw | new highlight only (not existing ones) | 700ms `--ease`, `background-size` | underline is just present |
| Verdict rise | checker verdict | 420ms translateY 14px + fade | appears |
| Meter grow | verdict meter | 420ms, 70ms stagger | full |
| Counters | audit totals | 700ms ease-out cubic, once per load | final value at once. Screen readers get the final value in a visually hidden element; the animating digits are `aria-hidden`. |
| Resolve pulse | sentence/claim after "Use rewrite" / "Keep" | 700ms box-shadow ring | status text and live-region message only |
| Source-claim pulse | ledger claim on anchor select | 700ms outline-offset | outline present, no pulse |
| Sheet | citation, product peek | 420ms transform | appears |
| Skeleton shimmer, spinner | loading | 1.4s / 900ms loop | static skeleton, static spinner glyph + the word "Checking…" |
| Smooth scroll to claim/sentence | trace, next issue | browser smooth | `behavior: auto` (`matchMedia` check) |

No motion carries meaning on its own; every transition ends in a state that has an icon, a word and a live-region message. No auto-playing loops except the two loading indicators, which stop when loading stops.

## 6. HTMX and Alpine conventions (so the Frontend agent has no questions)

**Division of labour.** The server renders all markup, including highlights (the server knows normalisation and offsets; Python offsets are code points and JS strings are UTF-16, so the client must never compute offsets). Alpine owns only local UI state: tabs, sheet open/close, anchor selection, theme, condensed gate, counters, roving focus. HTMX owns every round trip.

**Re-check request.** Sentence textarea:
```html
<textarea name="text" hx-post="/review/{pack}/sentences/{id}/check"
  hx-trigger="input changed delay:150ms, blur" hx-sync="this:replace"
  hx-target="#flags-{id}" hx-swap="outerHTML" hx-indicator="#row-{id}" ...>
```
- `hx-sync="this:replace"` aborts the stale request when typing continues. The response may arrive late: it carries `data-rev` (a hash of the checked text) and Alpine drops a response whose `rev` no longer matches the textarea (`htmx:beforeSwap` → `shouldSwap=false`).
- **The textarea is never swapped**, so caret, selection and IME composition survive. Only the backdrop, flag panel, status badge, progress strip, gate and live region are replaced, using **out-of-band swaps** (`hx-swap-oob="outerHTML:#backdrop-{id}"`, etc.).
- While a request is in flight: the backdrop shows the plain mirrored text (no marks, so nothing is misaligned), the row has `aria-busy="true"` and shows "Checking…". Marks come back with the response. Known limit: on a very slow link marks disappear while typing continues; acceptable, and a client-side matcher is out of scope.
- Target: re-check server time under 300ms p95 (plan §4). Measure with `Server-Timing`.
- `htmx.config`: `allowEval: false`, `historyCacheSize: 0` (no listing text in the history cache), `defaultSwapStyle: "outerHTML"`, `selfRequestsOnly: true`, `includeIndicatorStyles: false` (we ship our own).
- Non-JS fallback: the checker is a real `<form method="post">`; HTMX enhances it. The review and audit pages require JS.
- Auth pages carry the CSRF token via `hx-headers` on `<body>` (Platform agent supplies it). The public checker needs none but is rate-limited (`engine/ratelimit.py`).

**Alpine.** Use the **CSP build** (`@alpinejs/csp`) so no `unsafe-eval` is ever needed: every behaviour is a named `Alpine.data('satyaX', …)` in `web/static/js/app.js`; templates use `x-data="satyaTabs"`, not inline expressions. Components: `satyaTheme`, `satyaSheet`, `satyaTabs`, `satyaTrace`, `satyaGate`, `satyaGrid`, `satyaCounter`, `satyaUpload`. Whole app JS ≤ 6 KB gzip. Self-host pinned versions of HTMX 2.x and Alpine 3.x, no CDN (privacy: a brand's listing text page must not call third parties).

**Focus management rule (most common a11y bug in HTMX apps).** HTMX replaces the element that had focus. Therefore:
1. After any action that removes the activated control (Use rewrite, Keep with reason, Retry), focus goes to the **sentence textarea** (or, for Retry on the audit, the status line) and a message is written to the live region.
2. Never move focus on a plain re-check (the user is typing).
3. Opening a dialog focuses its close button; closing returns focus to the opener, and if the opener was removed, to the nearest surviving ancestor with `tabindex="-1"`.

**One live region per page**, `<div id="sr-status" role="status" aria-live="polite" class="sr-only">`, updated by OOB swap. Announce only changes in counts or outcomes, never per keystroke, never the "checked in N ms" text (that text is aria-hidden). Strings:

| Event | Message |
|---|---|
| checker result | "3 blocked, 2 to review under rule set v0.1.0-draft." / "No flagged risks under rule set v0.1.0-draft." |
| re-check changes status | "Bullet 2: now clear." / "Bullet 2: blocked, 1 flagged phrase." |
| rewrite applied | "Bullet 4 rewritten. Re-checked: no flagged risks." |
| kept | "Bullet 2 kept with your reason." |
| anchor selected | "Source claim highlighted: Hydrating, dewy finish." |
| approval | "Ready to approve." / "Approval blocked: 2 blocked, 2 need a reason." |
| audit progress | every 25%: "Checked 30 of 120 products." and on finish "Audit finished: 21 blocked, 42 to review, 57 clear." |

## 7. Accessibility baseline (WCAG 2.2 AA)

Carries `design-system.md` §4 and adds:
- **Landmarks:** `header` (banner), `main#main`, `footer`; skip link first; one `h1`; heading levels never skip. `<html lang="en-IN">`; Hindi fragments `lang="hi"`.
- **Targets:** 44px on `pointer: coarse`, 24px minimum everywhere (SC 2.5.8). Dense heat-strip cells are 26px.
- **No hover-only content** (SC 1.4.13): the audit's floating tooltip is replaced by an always-present inspector line.
- **Focus appearance** (SC 2.4.13 is AAA, but we meet it): 3px `--focus` ring, 2px offset, ≥ 3:1 against adjacent colours in both themes. Never removed. `:focus-visible` only.
- **Consistent help** (SC 3.2.6): the "Not legal advice · rule set vX" stamp and the draft banner sit in the same place on every page (footer of `main`).
- **Redundant entry** (SC 3.3.7): a reason or evidence the user typed is kept across re-checks while the flag stands; rate-limit and error states never clear the textarea.
- **Accessible authentication** (SC 3.3.8): Google sign-in or email OTP: no cognitive tests (Platform).
- **Forms:** every input has a visible `<label>`; errors are text, linked with `aria-describedby`, `aria-invalid="true"`, announced via `role="alert"`; required is stated in words ("(required)"), not by colour or `*` alone.
- **Dialogs:** native `<dialog>` with `showModal()` (focus trap, Esc, inert background for free). `aria-labelledby` its heading. Closing: Esc, scrim click, close button.
- **Text alternatives:** icons are `aria-hidden` and always sit next to a word. The severity meter and progress strip are `role="img"` with a full sentence label.
- **Zoom/spacing:** survives 200% zoom and WCAG text-spacing overrides (no fixed-height text containers; `min-height` only).

## 8. Performance budget (plan §4: < 150 KB JS+CSS per page, LCP < 2.5 s on Fast 3G)

**Definition.** Budget is **compressed transfer size** (brotli) of all JS and CSS a page loads, measured on the deployed preview. Fonts, HTML and images are budgeted separately below.

| Page | CSS | HTMX | Alpine (CSP) | App JS | **Total JS+CSS** | Hard cap |
|---|---|---|---|---|---|---|
| Checker | ≤ 12 KB | ~16 KB | ~17 KB | ≤ 3 KB | **~48 KB target** | 150 KB |
| Audit | ≤ 14 KB | ~16 KB | ~17 KB | ≤ 5 KB | ~52 KB target | 150 KB |
| Review | ≤ 14 KB | ~16 KB | ~17 KB | ≤ 6 KB | ~53 KB target | 150 KB |

One shared CSS file and one shared JS bundle across pages (cache once). The SAT-7 prototypes measured 14–16 KB gzip of CSS+JS before adding HTMX and Alpine, so these targets have about 3× headroom. Fail the build above **100 KB** (a warning well before the cap).

**Critical path for LCP < 2.5 s on Fast 3G** (measure: Lighthouse mobile, throttling RTT 562.5 ms, 1.6 Mbps down, 750 Kbps up, 4× CPU, on the Vercel bom1 preview, and again from a real mid-range Android over throttled network):
1. **LCP element is text**: the checker `h1`. No hero image, no carousel, no webfont-dependent layout. Audit LCP: the `h1`; review LCP: the gate heading. None waits on JS.
2. **HTML ≤ 14 KB compressed**, so it arrives in the first TCP congestion window. Server-render everything above the fold. Do not hide LCP content with `x-cloak`; `x-cloak` is for dialogs only.
3. **At most two render-blocking requests after the HTML**: one CSS file, and nothing else. JS is `defer`; HTMX first, Alpine after (`defer`, in that order). No inline `<script>` apart from the theme snippet.
4. **Fonts** (not in the JS+CSS budget, but on the LCP path): self-hosted WOFF2, Latin subset, `font-display: swap`. Fraunces: 2 static weights (400, 500) ≤ 26 KB each, **preload only the 500 face**. Inter: one variable file ≤ 50 KB, loaded after first paint. Devanagari loads only under `:lang(hi)`. Total critical fonts ≤ 110 KB. Provide metric-matched fallbacks (`size-adjust`, `ascent-override` on a local `Georgia`/`Arial` face) so the swap moves text by < 1px and CLS stays near 0.
5. **Cache:** fingerprinted assets, `Cache-Control: public, max-age=31536000, immutable`; HTML `no-store` for the review and audit (private data), short `s-maxage` is allowed for the public checker shell only.
6. **No third-party requests** on any page (Sentry's browser SDK is out of the budget and out of the checker; confirm with the Platform agent before adding it to the review page).

| Metric (mobile, throttled) | Target |
|---|---|
| Lighthouse Performance / Accessibility / Best practices | ≥ 90 / **100** / ≥ 95 (plan asks ≥ 90) |
| LCP (checker, Fast 3G) | < 2.5 s |
| CLS | < 0.05 (reserve the paper's `min-height: 15rem`; verdict is below the fold; sticky bars have reserved height) |
| INP (typing into a sentence) | < 200 ms; re-check round trip < 300 ms server-side |
| TBT | < 200 ms |
| DOM nodes | review ≤ 1,500 · audit ≤ 1,800 (500 cells + 25 table rows) · checker ≤ 600 |
| Images | none required. If an OG card is made it is a static 1200×630 PNG, never on the page itself. |

**Cold starts** (Vercel serverless) can add 1 s to a first checker request; the Platform agent should keep the checker route light (import only `engine.rules`, not the LLM stack). The shell paints before that matters, because the first interaction is typing, not loading.

## 9. Tailwind and file layout (for `web/`)

```
web/
  templates/_base.html          # head, theme snippet, skip link, sr-status, footer stamp
  components/*.html             # Jinja macros, one file per component (see components.md)
  templates/{checker,audit,review}/…
  static/src/app.css            # @tailwind + token CSS variables + the component rules from final-parts.css
  static/js/app.js              # Alpine.data components + HTMX hooks
tailwind.config.js              # colours/fonts/radii map to CSS variables (design-system.md §7)
```
`content` globs must include `web/**/*.html` and `engine/**/*.py` if any class string is built in Python. Dynamic class names (`flag-{{ sev }}`) must be listed in `safelist`, or the purge drops them: this is the usual way a purged build silently loses the severity colours. Add a test that renders every state in `states.html` and asserts the severity classes exist in the built CSS.
