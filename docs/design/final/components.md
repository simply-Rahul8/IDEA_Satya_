# Component specs for `web/components/`

One Jinja file per component, each exporting one macro (`{% macro name(...) %}`), imported with `{% from "components/flag_badge.html" import flag_badge %}`. Parameters are keyword-only in practice. Every macro **escapes its text parameters** (Jinja autoescape on; never `|safe` on listing text, rule text or reasons; AGENTS.md: listing text is data). The only `|safe` allowed is the output of `highlight_field`'s own builder, which escapes each segment itself.

Reference CSS for every class named here is in [`final-parts.css`](final-parts.css), [`../assets/tokens.css`](../assets/tokens.css) and [`../assets/review-parts.css`](../assets/review-parts.css). Visual states: [`states.html`](states.html). Screen composition: [checker](screen-checker.md), [review](screen-review.md), [audit](screen-audit.md).

**Layout rule (found in the 360px render):** any CSS grid or flex parent of these components must use `grid-template-columns: minmax(0, 1fr)` (or `min-width: 0` on flex children). With an `auto` track, an input's intrinsic width pushes cards past the right edge at 360px.

State words used below: **default · hover · focus · active · disabled · busy · error**. Hover and active are never the only indicator of anything. Focus is always the global ring.

## A. Primitives

### `icon(name, label=None)`  · `icon.html`
Inline `<svg class="ic"><use href="#i-{name}"/></svg>` against one sprite included once in `_base.html`. Decorative by default (`aria-hidden="true" focusable="false"`); if `label` is given: `role="img" aria-label`. **Icon set:** `block warn ok info close moon sun thumbdown anchor book arrow pencil check menu` (from SAT-7) plus `refresh upload down copy spin error unchecked` (paths in `states.html`). Rule: an icon that carries meaning is always adjacent to a word.

### `button(label, kind="primary|secondary|ghost", size="md|sm", icon=None, href=None, disabled_reason=None, attrs={})`
Pill, 44px (`sm` 36px, 44px on `pointer: coarse`). Renders `<a>` when `href`, else `<button type="button">` (forms pass `type="submit"`).
- **`disabled_reason` set** → `aria-disabled="true"` (stays focusable), `aria-describedby` points at the reason text rendered next to it, click handler is a no-op that moves focus to the first blocker. Native `disabled` is used only when no explanation is needed (never for Approve).
- States: hover (bg step), active (1px down), focus ring, busy (`aria-busy="true"`, label unchanged, spinner icon replaces the leading icon, width does not change).

### `flag_badge(sev, label=None, rule_id=None)`
`sev ∈ red|amber|green|ink`. Icon + word (+ mono rule id). Default words: Blocked / Review / Clear; `label` overrides (e.g. "Needs a reason", "Kept with reason", "Confirmed", "Needs reference", "Cannot confirm", "Not confirmed", "Couldn't check"). Icon map: red `block`, amber `warn`, green `ok`, ink `info` (or `check` for kept). Not interactive. Text is exactly what a screen reader needs; the rule id is read as letters ("E N dash D R U G…") so wrap it in `<span class="id" aria-label="rule EN-DRUG-001">`.

### `chip(label, kind="filter|type|anchor", pressed=None, attrs={})`
- `filter`: `<button aria-pressed>`; selected = filled accent.
- `type`: not interactive, dashed border, `<span>`.
- Sizes: 28px, **44px on `pointer: coarse`**.
- `anchor` has its own macro below.

### `notice(kind="info|error", title, body, actions=[])`
System message. `role="alert"` for `error` and for rate-limit; `role="status"` for `info`. Ink border, `info`/`error` icon, title in bold, one calm sentence, optional buttons. **Never uses red/amber/green** (those are severity). Copy rule: say what happened, what is safe ("your text is still here"), and what to do.

### `draft_banner(ruleset)`
Dashed `surface-2` box with `info` icon. Text when `not ruleset.is_signed_off`: "**Draft rule set {label}.** Not yet reviewed by a regulatory consultant. Not legal advice." When signed off: "Rule set {label}. Not legal advice." (the draft sentence disappears only because `meta.yaml` status is `SIGNED_OFF`, nothing else flips it). Appears in the checker (above the paper on pre-launch, plus the footer), citation sheet footer, the review gate area, the audit footer and the print stamp.

### `field(id, label, value="", error=None, hint=None, required=False, multiline=False)`
Visible `<label class="lbl">`, 1.5px `line-strong` border, `aria-describedby` = hint + error ids, `aria-invalid` when error. "(required)" in words. Error `<p role="alert">` always present in the DOM (empty) so the first error is announced.

### `toast(message)`
Single `role="status"` instance. 2.6s, but **never the only place an outcome appears**: every toast is mirrored in `#sr-status` and in the changed UI. Hover/focus on the toast pauses its timer (SC 2.2.1 spirit). Reduced motion: appears, no slide.

### `topbar()` and `theme_toggle()`
Brand (`स` mark + "Satya", links to `/`), page nav slot, theme toggle (`button`, `aria-pressed`, 44px). No hamburger in v1 (three screens, one level).

## B. Shared by checker and review

### `highlight_field(name, text, spans, label, max_chars=None, rev, busy=False)` · **the signature component**
A native `<textarea>` over a mirrored `.backdrop` (same font metrics, `aria-hidden`, `pointer-events: none`) in which the server wrapped flagged ranges in `<mark class="hl hl-red|hl-amber">`. Used by the checker paper and by every review sentence (replaces the prototype's `contenteditable`, which has weaker screen-reader and IME support and fights the caret).
- `spans` are **server-rendered** into the backdrop; segments escaped one by one. The partial includes `data-rev` (hash of the text it checked).
- Fluid height: `field-sizing: content` where supported, else a 6-line Alpine `input` handler sets `style.height` (`satyaAutogrow`). Min height 15rem (checker) / 2 lines (sentence).
- States: default; **busy** (backdrop = plain text, `aria-busy="true"` on the wrapper, "Checking…" indicator with reserved space so nothing shifts); **new highlight** (`.is-new`, the only moment that animates; added by an `htmx:afterSwap` hook to marks whose `rule_id+text` key was not present before); **over limit** (counter turns red-fg bold with the word "over", see checker); **error** (see `notice`; the textarea keeps its value).
- Accessibility: the textarea is the one real control and carries the visible or `sr-only` label. The marks are *not* announced inline (they live in `aria-hidden` backdrop); the flag list/panel is where icon + word + rule live. Spellcheck off, `autocomplete="off"`, `autocapitalize="off"`. Marks use pattern + colour; inline icons are not possible in a textarea, so the list/gutter provide them (the checker A trade-off the board accepted).
- Optional (not required for v1): caret-aware hint line (`hint-bar`) that names the flag under the caret with a "View rule" button.

### `severity_meter(level, label)`
Five segments, `role="img"`, `aria-label="Severity: {label}, level {n} of 5"`. Segments 1–5 fill left to right, colour from level (0 green-line, 2–3 amber, 4–5 red). Level is derived server-side by the same rule as the prototype (`red ≥ 2 → 5; red = 1 → 4; orange ≥ 3 → 3; orange ≥ 1 → 2; else 0`); the **text label always sits beside it** (High risk / Elevated / Moderate / No flagged risks). Level wording avoids "safe", "compliant", "approved".

### `citation_sheet()` · one instance per page, content by HTMX
A native `<dialog id="sheet">` styled as bottom sheet (< 48rem, `max-height: 82dvh`) or right panel (≥ 48rem, `--sheet-w`). Content (`GET /rules/{rule_id}/sheet?v={ruleset}`), in order:
1. `flag_badge` + rule id; 2. `h2` rule title; 3. quote of the matched text (set from the trigger's `data-quote` by Alpine, so the cacheable partial holds no user text); 4. **Why it is flagged** (`explanation`); 5. **Source**: each `ref` + `provision`, with a "Not yet verified" tag when `verified: false` (all today); 6. **What to do** (`rewrite_hint`); 7. **Can it be overridden?**: "No. This rule cannot be overridden." / "Yes, with an evidence reference." / "Yes, with a written reason."; 8. `draft_banner`.
- Behaviour: open = `showModal()` then add `.is-open` next frame (transition); close = remove class, `close()` on `transitionend` (with a 500ms timeout fallback so reduced motion never leaves it open). Esc and scrim click close. Focus → close button, returns to opener.
- Loading: skeleton of 4 lines; error: `notice` + "Try again"; the quote remains visible.

### `flag_list_item(flag)` (checker verdict list) and `flag_panel(sentence)` (review)
- `flag_list_item`: full-width 44px+ `<button>` (opens the sheet): badge, `<q>` phrase in display type, rule title in small text, arrow icon. 3-column ≥ 30rem, badge-above on 360px.
- `flag_panel`: for each flag: `fp-item` (red: solid 5px start edge, amber: dashed) with head (badge + title), why-sentence with the quoted phrase, "Citation" ghost button. Then, in this order and only when applicable: **policy line** (red non-overridable: "Cannot be overridden. Rewrite or remove it."; red overridable and `allow_red_override`: evidence form; amber: reason form) → `rewrite_card` → "Wrong flag?" footer.
- Clear sentences render the single line "No flagged risks under rule set {label}." with a green badge (hidden in the visual layout once the row is clear and has no flags, but kept in the DOM for AT: see `review` spec).

### `rewrite_card(text)` 
"Suggested rewrite" eyebrow, the text in display type, primary small "Use rewrite" button. Shown only when the engine supplied a rewrite **and** the sentence has a red or amber flag. After Use rewrite: server swaps in the new text, re-checks it, adds `.resolve` to the row once, focus → the textarea, live message "Bullet 4 rewritten. Re-checked: …". If the re-check of the rewrite is itself flagged, the card says so plainly ("This rewrite still has 1 flagged phrase") rather than pretending to resolve.

### `reason_form(sentence, kind="reason|evidence")`
`field` + "Keep with reason" / "Keep with evidence" secondary small button. Empty submit → inline error "Add a reason to keep this wording." (evidence: "Add an evidence reference: a document ID or an uploaded file."), `aria-invalid`, focus stays in the field. Success → the `kept` state (below). Evidence accepts a document ID text or a file (reuses the P25 evidence widget; file upload is Platform's). Reasons are stored with the audit record ("it travels with the export"). Reason text is plain text, max 500 chars, with a counter.

### `kept_panel(reason)` 
Dotted box, eyebrow "Your reason", the reason in display type as a quote, "Edit reason" ghost button (opens the form pre-filled). This is how the flag stays visible after being kept.

### `report_wrong_flag(flag)` 
Ghost small button "Wrong flag?" (`thumbdown`). One tap sends to the tuning queue; the button is replaced by the sentence "Reported as a wrong flag. Thanks." with an "Undo" ghost button (undo within the page session). The label is static ("Wrong flag?") and state is conveyed by replacing the control, not by flipping `aria-pressed`.

## C. Review screen (variant B)

### `approval_gate(summary, rule_set)` + `approval_dock(summary)`
- **Gate** (≥ 48rem, `position: sticky; top: 0`): eyebrow "Step 7 · Review · {product}", `h1` "Does every sentence trace to a confirmed claim?", note line, **Next issue** secondary button, **Approve pack** primary button, `progress_strip`, `draft_banner` (compact). After the user scrolls past 120px it **condenses** (`data-condensed="true"`: title hides, note + buttons + strip stay) to keep the tablet gate short. Height changes are published to `--gate-h` by a `ResizeObserver`.
- **Dock** (< 48rem, fixed bottom, `padding-bottom: env(safe-area-inset-bottom)`): strip, one note line ("2 blocked · 2 to review", may wrap to two lines), an **icon-only Next issue button** (`aria-label="Next issue"`, 44px square on touch) and Approve. Icon-only is allowed here only because the label is announced and the strip above it already explains the context; the full-width gate keeps the word. The top of the page keeps the same `h1` and a non-sticky copy of the note.
- **Approve behaviour:** `aria-disabled="true"` while any sentence is red/amber/unchecked or any re-check is pending or failed. The note beside it says exactly why. Activating it while disabled moves focus to the first blocking sentence and announces the reason; it does not just toast. Ready state: green `ok` icon + "Ready to approve. No flagged risks under rule set {label}." (never "compliant"). Approved state: gate replaced by a `notice` "Approved. The audit record is attached to your export." + link to Export.
- **Next issue**: focuses the next sentence textarea whose status is red, then amber, then unchecked, in document order, wrapping; disabled with reason "No open issues" when none.

### `progress_strip(statuses)`
One `<i data-s>` per sentence: `red` solid, `amber` hatched, `kept` solid ink-2, `ok` green, `pending` outline. **Non-interactive** (`role="img"`, label like "Sentences: 2 blocked, 2 to review, 1 kept with reason, 2 clear"). Navigation is the Next issue button, so segments need no 24px targets even with 20+ sentences. Colour is not the only signal: the label, the counts line and each row's own badge repeat it.

### `sentence_row(sentence, flags, anchors, status)`
`<article class="row" id="s-{id}" data-status="red|amber|kept|ok" aria-labelledby="h-{id}">` with `sr-only` heading "Bullet 2" for the section label. Anatomy, top to bottom:
1. (≥ 48rem) **gutter icon** for status; (< 48rem) hidden, as the badge below carries it;
2. `highlight_field` (textarea labelled "Bullet 2 text, editable");
3. meta row: `type` chip + status `flag_badge` (Blocked / Needs a reason / Kept with reason / Clear);
4. **anchors**: `anchor_chip` per source claim, or the `No source claim` chip (amber, dashed, not interactive) + one sentence "Nothing in Product Truth backs this sentence. Rewrite it, or keep it with a reason.";
5. `flag_panel` / `kept_panel` / clear line.
- Status derivation (server): `red` if any red flag (or anchored claim state `blocked`); else `amber` if any orange flag, or no anchor on a Claim/Ingredient sentence, or anchored claim `needs_reference`/`unconfirmed`, and not kept; `kept` if amber and a reason is stored; else `ok`. An anchor problem shows a flag-panel item "Source claim is not confirmed" with a button "Open in Product Truth" instead of a rule citation.
- Row `scroll-margin-top: var(--gate-h)+1rem`. `.is-linked` (accent-soft background + start edge) when its anchor is selected elsewhere.
- Busy: `aria-busy="true"`, "Checking…". Re-check failed: `notice` error "Couldn't re-check Bullet 2. Your edit is kept. Approval stays off until it is checked." + Retry (status becomes `unchecked`, counted as blocking).

### `anchor_chip(claim, pressed, expanded)` · **the board's mobile requirement**
Shows the **claim text in the sentence card on 360px**, so tracing never needs the other tab.
- **< 60rem:** full-width (`chip-claim`), 44px min, wraps to as many lines as needed: `[link icon] C5  Hydrating, dewy finish  [state icon]`. Tapping toggles an inline **claim peek** directly under the chip (`aria-expanded`, `aria-controls`): state badge, evidence line, and a ghost button **"Open in Product Truth"** (explicit; this is the only thing that switches tabs). Tapping never switches tabs by itself (the prototype did; that lost the reader's place).
- **≥ 60rem:** compact pill (id + state icon); the text is visually hidden but remains in the accessible name; the ledger is beside the copy, so toggling it highlights the claim there (`.is-source`: 3px accent outline + soft fill + one pulse) and marks every sentence that shares it (`.is-linked`).
- Accessible name (both): "Anchor C5: Hydrating, dewy finish, confirmed. Show source claim." `aria-pressed` reflects selection on desktop; `aria-expanded` on mobile.
- One claim selected at a time. Esc clears the selection.

### `ledger(claims)` and `claim_item(claim)` (the "Product Truth" pane)
- `claim_item` anatomy: type chip (`C4 · Claim`), claim text (strong), state `flag_badge`, evidence line, **"Used in" chips** (reverse trace; each a button that returns to Copy and focuses that sentence), optional "Confirm…" link for unconfirmed claims (goes to the Product Truth editor, not built here).
- **Claim states** (plan P25 and "every claim starts unconfirmed"): `confirmed` (green "Confirmed"), `unconfirmed` (ink "Not confirmed"), `needs_reference` (amber "Needs reference": a test-report claim without a reference), `blocked` (red "Cannot confirm": hard-blocked, can never be confirmed). Start edge: blocked solid red, amber dashed, others none.
- Ledger heading `h2` "Product Truth ledger" with count; sticky ≥ 60rem with `top: var(--gate-h)+1rem; max-height: calc(100dvh - var(--gate-h) - 2rem); overflow: auto`.

### `tabs(items)` (< 60rem only)
Proper tabs pattern: `tablist` / `tab` / `tabpanel`; roving `tabindex` (selected = 0); **Left/Right/Home/End** move and activate; inactive panels use the `hidden` attribute; panels `tabindex="0"`. Labels: "Copy · 7 sentences" and "Product Truth · 7 claims". Arrival from "Open in Product Truth": the ledger shows a sticky ghost button **"Back to Bullet 4"** (returns to the Copy tab, scrolls to and focuses that sentence's textarea) and focus lands on the highlighted claim (`tabindex="-1"`). Hidden at ≥ 60rem (both panes visible, no tabs in the DOM tab order).

## D. Checker

### `verdict_card(result, ruleset)`
`<article class="card verdict" aria-labelledby>`: eyebrow "Verdict · rule set {label}", `h2` ("{Risk label} risk" or "No flagged risks"), sub ("3 phrases flagged" / "under rule set {label}"), `severity_meter`, tally badges ("3 blocked", "2 to review", or "Nothing flagged"), then `flag_list_item`s (sorted: red first, then in text order), then a footer: sentence "This is a text check against {a draft / the} rule set. It does not mean the listing is approved by a marketplace or a regulator. Not legal advice.", and two quiet actions: **Copy summary** (`copy` icon; copies "Checked with Satya under rule set v0.1.0-draft: 3 blocked, 2 to review. Not legal advice." to the clipboard; no text content is included) and a link "Audit your whole catalogue" (sign-in, draft copy, board sends nothing). Entrance animation `rise` runs only the first time a verdict appears on the page.
- Variants: `flagged`, `clear`, `out_of_scope` (product-type gate `needs_review` / `refused`: heading "This may not be a cosmetic" / "Satya v1 reviews cosmetics only", the gate's `explanation` text verbatim, ink "Not reviewed" badge, no meter, no flag list).

## E. Audit

### `stat_counter(sev, value, total, state)`
Card with `flag_badge`, a big display number (`font-variant-numeric: tabular-nums`), "of {total} products". The animating number is `aria-hidden`; a sibling `sr-only` span holds the final value. `state="loading"` shows `—` in ink-3 and the badge; `state="error"` shows "—" and "Couldn't check". Counters animate once on first paint (`satyaCounter`, 700ms), never again on filter/sort.

### `heat_strip(items, filter, sort)` and `heat_cell(item)`
`<div role="group" aria-label="One square per product. Use arrow keys to move." class="strip">` of `<button class="cell" data-s="red|amber|green|pending|skipped|error" aria-label="SKU-1004, Rosewater Dew Serum: Blocked. EN-DRUG-001 treatment claim">`. **Roving tabindex** (one tab stop; arrows move, Home/End ± PageUp/PageDown by row; Enter/Space opens the product peek). Cell size `minmax(var(--cell), 1fr)` ⇒ ≥ 26px at 360px and ~39 columns at 1152px. Six states, each with its own pattern (solid / diagonal hatch / pale + outline / dashed outline / dotted / vertical stripes); a legend lists only the states present, each with swatch + icon + word. Dimmed (`.dim`, opacity .18) when filtered out, but a focused or current cell is always full opacity.

### `inspector(item)`
Always-visible line under the strip (`role="status"`; not a floating tooltip, so SC 1.4.13 and touch both work): badge, product name, SKU (mono), the top flag as "EN-DRUG-001 treatment claim", "+2 more", and link "Open report". Updates on hover, focus and tap of a cell. Empty state: "Select a square to see why." Opening the full peek for a product (flags list, "Fix with Satya") reuses `citation_sheet`'s shell with a different body.

### `filter_chips(options)` and `sort_toggle()`
Chips "All / Blocked / Review / Clear" (+ "Not checked" when present), single-select (`aria-pressed`), counts inside each label ("Blocked 21"). Sort: a button toggling "Sorted by risk" / "Catalogue order" (`aria-pressed`). Both update via Alpine instantly (data is already on the page) and mirror to the URL (`?f=red&sort=risk`) with `history.replaceState`; the table below follows. A polite live message: "Showing 21 blocked products."

### `data_table(rows)`
Real `<table>` with `<th scope="col">`, `<caption class="sr-only">`, columns SKU (mono) · Product · Status (badge) · Flags (≥ 40rem; on 360px the flags text folds under the product name). First 25 rows by risk; "Show more" loads the next 25 via `hx-get` with `hx-swap="beforeend"` and moves focus to the first new row. Wrapped in `overflow-x: auto` with `tabindex="0"` and a label only when it can actually scroll.

### `dropzone()` and `job_progress(done, total)`
- `dropzone`: dashed box containing a real `<input type="file" accept=".csv,.xlsx">` styled as the "Choose a file" button (the drag-and-drop is an enhancement; the button always works), a "Paste text instead" ghost button, and the limits line ("CSV or XLSX, up to 500 products."). On drag-over: accent border + soft fill + text "Drop to upload".
- `job_progress`: `role="progressbar"` with `aria-valuenow/max`, a status line "Checking 38 of 120 products" (`role="status"`, throttled to every 25%), Cancel ghost button. The job is stepwise and **client-driven** (ADR-8/P11): the client polls or posts the next step; if the tab sleeps, "Resume" appears.
