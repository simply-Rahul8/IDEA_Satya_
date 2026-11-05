# Screen spec: audit dashboard (heat-strip, as drafted)

Board pick: SAT-12 said "plus the audit heat-strip sketch as drafted". This spec keeps that design and adds what a build needs: states, keyboard model, upload and progress, and fixes to two accessibility problems in the sketch. Plan: §3 step 3, §4 signature moment 2, P8, P11, P23, P29. Prototype: [`../audit-heatstrip.html`](../audit-heatstrip.html). States: [`states.html`](states.html) A1–A4. Components: [`components.md`](components.md) §E.

**Job:** "Show me which listings could get my CDSCO registration or marketplace listing pulled." A brand uploads a catalogue and within one screen sees how much of it is at risk, which products first, and why.

## 1. Route and data

| | |
|---|---|
| Page | `GET /audits/{audit_id}` (auth); `GET /audits/new` is the empty/upload state |
| Upload | `POST /audits` (multipart CSV/XLSX, or pasted text) → creates a stepwise job (ADR-8, P11) |
| Progress | client-driven: `POST /audits/{id}/step` until done; `GET /audits/{id}/cells?from=n` returns resolved cells |
| Rows | `GET /audits/{id}/rows?page=2` (HTMX, 25 per page) |
| Report | `GET /audits/{id}/report` (print-friendly page, Export agent). Stamped "not legal advice · rule set {label}". |
| Per item | `{sku, name, state, flags:[{rule_id,title,severity}], missing_fields:[…]}`, `state ∈ red|amber|green|pending|skipped|error` |

**Missing Legal Metrology r.10 fields** (plan §3 step 3) are shown as a flag type on the product with ids prefixed `LM-` and a plain list ("Missing: net quantity, MRP"). **Assumption to confirm with the Rules agent:** severity is `amber` (Review) until a rule says otherwise. Product state = the worst of its flags and missing fields.

## 2. Layout

**360px:** topbar → `h1` + support sentence → **counters** (two columns, cards stack to one row of two; "Clear" card wraps below) → **strip card** (controls, strip, inspector line, legend) → **table card** → footer stamp.
**≥ 48rem:** counters in a row of three/four, strip fills the card (~39 columns at 1152px), table shows the Flags column.

Strip geometry: `grid-template-columns: repeat(auto-fill, minmax(var(--cell), 1fr)); gap: 2px;` with `--cell: 1.625rem`. At 360px with 16px card padding that is **10 columns of ~29px**; the sketch's fixed 12 columns gave ~21px cells, below WCAG 2.2 SC 2.5.8's 24px. Card padding is `--s-4` (16px) below 48rem, `--s-5` above.

## 3. Behaviour

1. **Counters** animate once on first paint (700ms ease-out); filter/sort never re-animate them. Reduced motion: final numbers at once.
2. **Strip:** one cell per product, sorted by risk by default (red → amber → green; within a state, catalogue order). Six cell states with six patterns (components §E).
3. **Filter chips** (single-select: All · Blocked · Review · Clear, plus "Not checked" when any skipped/error cells exist) dim non-matching cells to 18%. **Sort toggle** switches between risk order and catalogue order. Both run in Alpine over data already on the page (no round trip, good on 3G) and mirror to the URL (`?f=red&sort=risk`) so the view is shareable and the back button behaves.
4. **Selecting a cell** (hover, focus, or tap) updates the **inspector line** below the strip: badge, product, SKU, top rule, "+n more", "Open report". Nothing floats. Empty text: "Select a square to see why." Enter/Space on a cell (or the "Open report" link) opens the product peek sheet.
5. **Keyboard model:** the strip is one tab stop (roving `tabindex`). Arrow keys move one cell (Up/Down move one row: column count is read from the computed grid), Home/End first/last, PageUp/PageDown ± 5 rows. A visible hint below the legend: "Tip: use the arrow keys to move between products."
6. **Table:** the same data, first 25 rows by risk, "Show more" loads 25 more (focus moves to the first new row). It is the non-visual, non-pattern-reading route to everything the strip shows.
7. **Upload flow:** Choose a file (or drop) → the page shows the **loading** state immediately (the strip is created with `pending` cells so the layout is final), cells resolve in place as steps complete, counters count up only when done. **Cancel** stops the job; partial results are kept and labelled "Stopped at 38 of 120".
8. **Product-type gate:** non-cosmetic products (P23) become `skipped` cells with the gate's explanation; they are excluded from the risk counts, counted separately ("3 not reviewed: not a cosmetic").
9. **Print:** controls and dock are hidden, the strip prints with patterns (`print-color-adjust: exact`), the table shows all rows, and the page carries the stamp "Not legal advice · rule set {label}" plus the draft banner while the rule set is `DRAFT`.

## 4. States

| State | Trigger | What shows |
|---|---|---|
| **A1 Empty** | no audit yet | dropzone card: icon, `h2` "Audit your catalogue", one sentence of supported inputs (Shopify CSV; Nykaa or Amazon catalogue download; pasted text), "Choose a file", "Paste text instead", limits line. No counters, no strip |
| **A2 Loading** | job running | "Checking 38 of 120 products" (`role="status"`, throttled announcements), `role="progressbar"`, Cancel; counters show "—"; strip with `pending` (outlined) cells that fill in |
| **A3 Partial failure** | some rows failed, some skipped | `notice` "5 products couldn't be checked and 3 aren't cosmetics." + "Retry 5"; cells `error` (vertical stripes) and `skipped` (dotted); legend lists them; counts exclude them |
| **A4 Loaded** | done | counters, strip, inspector, legend, table |
| **All clear** | 0 red, 0 amber | counters show 0/0/N; a calm `notice` "No flagged risks in {N} products under rule set {label}. Not legal advice." (never "your catalogue is compliant") |
| **Bad file** | unparseable / wrong type | `notice` error "We couldn't read that file." + reason (type, size > limit, empty) + "Choose another file" |
| **Needs column mapping** | no known template matched (P29) | the generic-CSV mapping step: a simple table "Your column → Satya field" with selects, "Product name" and "Description" required; Continue |
| **Over the limit** | > 500 products | `notice` "This file has {n} products. v1 checks up to 500 at a time. Split the file, or check the first 500." with both actions |
| **Offline / job interrupted** | tab slept, network lost | "Paused at 38 of 120" + Resume button; progress is server-side so nothing is lost |
| **Filtered to empty** | a filter has 0 matches | strip shows all cells dimmed and the inspector line says "No products match this filter."; chip counts show 0 |

## 5. Accessibility

**Focus order:** skip link → brand/theme → (upload state: Choose a file → Paste text) → filter chips → sort toggle → the strip (single stop) → inspector link "Open report" → legend (not focusable) → table (header, rows: "Open" links) → "Show more" → footer.
- `h1` "Where your listings are at risk." (display); strip card `h2` "Risk heat-strip"; table card `h2`.
- Strip cells are real `<button>`s with a full `aria-label` ("SKU-1004, Rosewater Dew Serum: Blocked. EN-DRUG-001 treatment claim"). The group has an instruction label.
- **Fixed from the sketch:** (1) the floating tooltip is gone (it was `pointer-events: none`, so it failed SC 1.4.13 "hoverable" and was invisible on touch); the inspector line replaces it. (2) 120–500 tab stops are gone (roving tabindex). (3) Cell size is ≥ 26px (SC 2.5.8). (4) Clear cells have a `green-fg` outline (≥ 3:1) instead of a `green-line` that was ~1.9:1.
- Severity never by colour alone: solid / hatch / outline / dashed / dotted / stripes **plus** legend with icon + word **plus** table with badges.
- Counters: animation `aria-hidden`; final value in an `sr-only` span.
- Progress: `progressbar` with `aria-valuenow`; textual status announced at 25% steps and on finish (foundations §6).
- Filter chips announce the result count politely: "Showing 21 blocked products."
- Table: `scope`d headers, caption, no layout tables.
- Contrast: cell edges and patterns ≥ 3:1 (`contrast_final.txt`); the inspector and legend text ≥ 4.5:1.

## 6. Motion
Counters 700ms (once) · cell resolve fade 220ms when a `pending` cell takes its state (staggered by index, max 40 per frame) · filter dim 220ms · peek sheet 420ms. Reduced motion: all instant.

## 7. Performance
All cell data is in the first HTML response (≈ 80 bytes per cell: 500 cells ≈ 40 KB uncompressed, ~6 KB brotli) so filter and sort are instant and the page works on 3G without extra requests. DOM ≤ 1,800 nodes. JS+CSS ≈ 52 KB compressed. The strip is not an image or canvas: it must stay selectable and accessible. A `pending` strip is created at its final size to keep CLS at zero.

## 8. Out of scope here
The print report itself (Export agent), the column-mapping screen's full design (it reuses `field`, `button`, `data_table`), per-product fix flow (links into the review screen).
