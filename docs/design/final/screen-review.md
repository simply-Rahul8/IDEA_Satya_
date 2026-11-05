# Screen spec: review (variant B, Truth ↔ Copy)

Board pick: SAT-12, Variant B, with the board's mobile note: *the claim ledger is a separate tab on phones, so keep tracing easy at 360px (for example by keeping the anchor chip's claim text visible in the sentence card).* Plan: §3 step 7, §4 signature moment 3, P24, P25. Prototype: [`../review-b.html`](../review-b.html). States: [`states.html`](states.html) R1–R10. Components: [`components.md`](components.md) §B and §C.

**Job:** the content owner confirms that every sentence of the generated PDP pack traces to a confirmed Product Truth claim and carries no unresolved flag, fixing what does not, then approves. The product's core promise is on this page: *every sentence is anchored.*

## 1. Route and data

| | |
|---|---|
| Page | `GET /packs/{pack_id}/review` (auth, one brand workspace) |
| Re-check | `POST /packs/{pack_id}/sentences/{id}/check` (HTMX; returns OOB parts, see foundations §6) |
| Actions | `POST …/rewrite` (Use rewrite) · `POST …/keep` (reason or evidence) · `POST …/report` (wrong flag) · `POST …/approve` |
| Rule sheet | `GET /rules/{rule_id}/sheet?v=…` |
| Server must call | `policy.check_override` before accepting a keep on a red flag; `policy.hard_blocks` for claim state (ADR-9) |

**Pack content and order** (plan §3 step 6): Title · Bullet points (5) · Description · How to use · Warnings and storage · SEO meta (title tag, meta description, with live character counters in the meta row: 60 / 160 as soft limits, stated as text). Every sentence has `type ∈ Claim|Ingredient|Usage|Warning|…` (Engine models define the enum; the chip just prints the label) and 0..n anchors.

## 2. Layout

**≥ 60rem (two columns):** left **Product Truth ledger** (22rem, sticky below the gate, own scroll), right **Copy** (fluid, measure ~44rem). Above both: the sticky **approval gate**. Tabs are not rendered.

**48–60rem:** one column (Copy), tabs visible, gate sticky and **condensed on scroll**, ledger in its tab.

**< 48rem (360px first):**
1. `topbar`
2. page header (not sticky): eyebrow "Step 7 · Review · {product}", `h1`, one note line with the open-issue count
3. **tabs**: "Copy · 7 sentences" | "Product Truth · 7 claims"
4. the active pane
5. fixed bottom **dock**: progress strip + "2 blocked · 2 to review" + Next + Approve

Section headings in Copy: display type `--t-xl`, ink-2, a hairline rule filling the line (`h3`, because `h2` is the pane title).

### Sentence row at 360px (the unit users spend the session in)
Left edge: 4px status edge (solid red / dashed amber / dotted ink / none). No gutter column (it would cost 44px of 328): the status badge in the meta row carries the icon. Order: text (textarea, 20px serif) → type chip + status badge → anchors (full-width chips showing the claim text) → [claim peek] → flag panel / kept panel / clear line. Rows are separated by space and the status edge, not by boxes, so the page reads like a document, not a form.

## 3. Behaviour

### Tracing (the signature interaction)
- **Sentence → claim (desktop ≥ 60rem):** tapping an anchor chip highlights the claim in the ledger (outline + soft fill + one pulse), scrolls it into view (`nearest`), and marks every sentence that shares that claim (`.is-linked`). Live: "Source claim highlighted: Hydrating, dewy finish." Tapping again, or Esc, clears.
- **Sentence → claim (mobile < 60rem):** the chip is already readable (`C5 · Hydrating, dewy finish`, with the claim's state icon). Tapping it expands the **claim peek** directly beneath: state, evidence, and "Open in Product Truth". It **does not switch tabs**. Choosing "Open in Product Truth" switches to the ledger tab with that claim highlighted and focused, plus a sticky "Back to Bullet 4" button at the top of the pane.
- **Claim → sentences:** every ledger claim lists "Used in: [Title] [Bullet 1]" as buttons; each returns to the Copy pane (mobile) or scrolls (desktop), focuses that sentence's textarea and flashes `.is-linked`. A claim used nowhere says "Used in: nothing yet".
- **Unanchored sentence:** a dashed amber "No source claim" chip with its one-sentence explanation. It is not a link; the fix is to rewrite or keep with reason.

### Editing and live re-check
- Every sentence is a `highlight_field`. Edits re-check on `input` with 150ms quiet (target round trip < 300ms server-side), marks redraw, status/badge/panel/strip/gate update via OOB swaps, the textarea itself never re-renders.
- **Status transitions:** any edit clears a stored reason/evidence **only if the flagged wording changed** (the server compares flag sets); otherwise the reason is retained ("redundant entry").
- **Use rewrite** → sentence text replaced and re-checked; row gets `.resolve` once (green ring pulse, 700ms); toast "Rewrite applied. Re-checked, no flagged risks." only if it really came back clear; focus → textarea.
- **Keep with reason / evidence:** validates non-empty; on success the status becomes `kept` (dotted edge, ink badge "Kept with reason", `kept_panel` showing the reason). Reason is saved to the audit record and travels with the export. Server re-validates (`check_override`).
- **Wrong flag?** → tuning queue; replaced by "Reported as a wrong flag. Thanks." + Undo. It does not change status or unblock anything.

### Approval gate
- Blocking conditions: any `red` sentence; any `amber` sentence without a reason; any sentence `unchecked` (re-check failed or pending); any claim anchor in state `blocked`. 
- Note text, always exactly what blocks: "2 blocked and 2 need a reason before you can approve." / "1 sentence hasn't been checked." / "Ready to approve. No flagged risks under rule set v0.1.0-draft."
- **Next issue** cycles through blocking sentences (red first). **Approve** while blocked focuses the first blocker and announces why.
- Approved state replaces the gate with a notice and a link to Export; sentences stay editable but any edit reopens the gate ("Edited since approval: check again").
- Wording: **never** "compliant", "approved by regulator", "safe". "Approve pack" approves *Satya's review step*, not legality: the confirm text under the button on first use says "Approving records your review and the rule set version. It is not a legal sign-off."

## 4. States

| State | Where | What shows |
|---|---|---|
| **R1 Blocked, cannot override** | row | red edge, red badge "Blocked", panel item with rule + citation, line "Cannot be overridden. Rewrite or remove it." + rewrite card. **No reason/evidence field.** |
| **R2 Blocked, evidence can override** | row | as R1 but "Evidence reference to keep this wording (required)" + "Keep with evidence"; hidden if `allow_red_override` is false (foundations §1) |
| **R3 Review** | row | dashed amber, badge "Needs a reason", panel, reason form, rewrite card |
| **R4 Kept with reason** | row | dotted ink edge, ink badge "Kept with reason", reason shown, "Edit reason" |
| **R5 Clear** | row | no edge, green badge "Clear", one quiet line "No flagged risks under rule set {label}." |
| **R6 No source claim** | row | amber dashed chip + explanation; status `amber` |
| **R7 Re-check in flight** | row | plain mirror, "Checking…", `aria-busy` |
| **R8 Re-check failed** | row | `notice` error + "Retry check"; status `unchecked` blocks approval |
| **R9 Ledger claim states** | ledger | confirmed · not confirmed · needs reference · cannot confirm, each icon + word + start edge pattern |
| **R10 Gate/dock** | page | full gate, condensed gate, dock; blocked and ready variants |
| **Empty** | page | no pack yet (`pack.sentences == []`): "Nothing to review yet." + sentence "Generate the PDP pack first." + primary button "Generate PDP pack". No gate, no tabs. |
| **Loading (generation)** | page | skeleton rows grouped by section, stepwise job status in a `role="status"` line ("Writing bullets… 3 of 6 sections"), Cancel; rows appear section by section; gate shows "Review starts when generation finishes" and Approve is disabled |
| **Loading (initial page)** | page | the page is server-rendered; there is no spinner state |
| **Error (generation failed)** | section | per-section `notice` "Couldn't write Bullets." + "Try this section again"; other sections stay usable |
| **Error (offline)** | page | `notice` at top "You're offline. Edits are kept here and checked when you reconnect."; sentences edited offline are `unchecked` |
| **Conflict** | page | another tab approved/edited: `notice` "This pack changed elsewhere. Reload to see it." (no silent overwrite) |
| **Out of scope** | not shown here | a refused product never reaches review (gate happens before extraction, plan §3 step 4) |

## 5. Accessibility

**Focus order (desktop):** skip link → brand/theme → gate: Next issue → Approve pack → [ledger: claim "Used in" buttons, in order] → Copy: for each sentence in document order: textarea → anchor chip(s) → claim peek controls → flag-panel buttons (Citation, Use rewrite, reason field, Keep) → Wrong flag? → next sentence. On desktop the ledger comes **before** Copy in the DOM (it is the left column); keyboard users can jump with the skip links "Skip to Product Truth" / "Skip to copy" placed after the gate.
**Mobile:** tabs (one tab stop; arrows switch) → the active pane → dock (reached last; it is `position: fixed` but placed at the end of `<body>` so the tab order is natural).

- Page title: "Review: {product} · Satya". `h1` once; `h2` "Product Truth ledger" and "PDP copy" (the latter `sr-only`); `h3` per section.
- Row `aria-labelledby` its `sr-only` heading ("Bullet 2, Blocked"): the status is part of what a screen-reader user hears when they land on it.
- Anchor chip names include the claim text and state (components §C). Peek disclosure uses `aria-expanded` + `aria-controls`.
- Tabs: full ARIA tab pattern, arrow keys, `hidden` for inactive.
- Dock and gate use `role="region"` with `aria-label`; the approval note is `aria-live="polite"`, updated only on count changes.
- The progress strip is `role="img"` with its counts; navigation is the Next issue button.
- Errors on the reason field: `aria-invalid`, `aria-describedby`, `role="alert"`, focus stays on the field.
- Focus is never lost after HTMX swaps (foundations §6 rule 1). **Test:** after Use rewrite, `document.activeElement` is the sentence textarea.
- Sticky/fixed UI never obscures focus: `scroll-padding` + `scroll-margin-top` on rows (SC 2.4.11).
- Targets: chips and small buttons 44px on touch; anchor chips ≥ 44px tall; textareas ≥ 44px.
- Color is never alone: edge pattern + badge icon/word + progress label + live message.
- Hindi: the row, chips and panels contain no fixed heights or truncation (Devanagari is taller); hold the same layout.

## 6. Motion
Underline draw on new marks (700ms) · resolve ring pulse (700ms) · source-claim pulse (700ms) · peek expand (220ms height/opacity) · gate condense (220ms) · sheet 420ms. All collapse under reduced motion; the resolve and trace outcomes are carried by text and focus instead.

## 7. Performance
Review is a heavy-DOM page: render all rows server-side but keep ≤ 1,500 nodes (about 25 sentences). Ledger and copy panes are both in the DOM on mobile (the inactive one `hidden`) so switching tabs is instant and needs no request. JS+CSS ≈ 53 KB compressed. Re-check partials are small (< 4 KB each) and must not repaint the textarea. Debounced input + `hx-sync` bound the request rate; the server rate-limits per user.

## 8. Open questions (raised in the task comment)
1. **Reds in exports:** plan says "0 🔴 in exports", rules allow overridable reds with evidence. Spec supports both via `allow_red_override`. CTO to decide.
2. **Unanchored and unconfirmed-anchor sentences** count as "needs a reason" here. Engine to provide `anchor_state` per sentence and the `type` enum.
3. **Claim confirmation UI** (Product Truth editor) is a different screen: not specified here; the ledger only links to it.
