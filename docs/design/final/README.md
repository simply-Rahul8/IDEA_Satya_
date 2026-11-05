# Satya final design specs, v1.0 (SAT-13)

Build-ready specs for the Frontend agent (SAT-21). **Status: draft regulatory content, final layout and behaviour.** Rule text, disclaimers and report wording stay *draft* until consultant sign-off (P20): nothing here says "compliant"; it says "no flagged risks under rule set vX".

## 1. The board's decision (SAT-12)
- **Public checker: Variant A, Editorial Paper.** One calm column; underlines drawn in the text box itself.
- **Review screen: Variant B, Truth ↔ Copy.** Product Truth ledger beside the copy; mobile uses Copy / Product Truth tabs and the anchor chip **keeps the claim text visible** in the sentence card.
- **Audit dashboard:** the heat-strip sketch as drafted.
- Shared tokens and `design-system.md` are kept. Checker B/C and review A/C stay in `docs/design/` as reference only.

## 2. Read in this order
| File | What it is |
|---|---|
| [`foundations.md`](foundations.md) | Engine→UI vocabulary, tokens (additions), themes, motion, HTMX/Alpine conventions, accessibility baseline, **performance budget**, Tailwind and file layout |
| [`components.md`](components.md) | Spec for every Jinja component in `web/components/`: macro signature, anatomy, states, ARIA |
| [`screen-checker.md`](screen-checker.md) | Public checker: layout at 360/1280, behaviour, states, focus order, perf |
| [`screen-review.md`](screen-review.md) | Review: tracing on desktop and 360px, re-check, approval gate, states, focus order |
| [`screen-audit.md`](screen-audit.md) | Audit heat-strip: upload, loading, partial failure, keyboard model, print |
| [`states.html`](states.html) | Open in a browser. Every state at 360px (moon button for dark) |
| [`final-parts.css`](final-parts.css) | Reference CSS for new and changed components (port to Tailwind) |
| [`critique.md`](critique.md) | The self-critique log: what was wrong in the prototypes and how the specs fix it |
| [`contrast_final.py`](contrast_final.py) / [`.txt`](contrast_final.txt) | Contrast check for the added colour pairs: 0 failing |

Screenshots: [`../screenshots/final-states-360-light.png`](../screenshots/final-states-360-light.png), `…-360-dark`, `…-1280-light`, `…-1280-dark`.

## 3. What changed from the picked prototypes (short list; reasons in `critique.md`)
1. Rules model is the engine's: `red`/`orange`, overridable or not, `EN-…` ids. Three review outcomes, not two.
2. "Kept with reason" is ink, not green. It never reads as "Clear".
3. Sentence editing is a native `textarea` over a server-rendered highlight backdrop, never swapped by HTMX.
4. Mobile tracing: claim text in the chip, inline peek, reverse "Used in", explicit tab switch.
5. Mobile approval: fixed bottom dock; gate condenses on tablets; sticky offsets are runtime tokens.
6. Heat-strip: ≥ 26px cells, roving tabindex, inspector line instead of tooltip, six patterned states.
7. Focus is restored after every HTMX swap; one polite live region; native `<dialog>` for sheets.
8. Full state coverage: empty, loading, error, rate-limit, over-cap, gate, offline, partial failure.

## 4. Build order suggested for SAT-21
1. `_base.html`, tokens, Tailwind config, fonts, theme snippet, sprite, `sr-status`, footer stamp (+ budget CI check).
2. Primitives: `icon`, `button`, `flag_badge`, `chip`, `notice`, `draft_banner`, `field`, `toast`.
3. `highlight_field`, `severity_meter`, `citation_sheet`, `flag_list_item` → **checker page** (week 3 in the plan).
4. `heat_strip` family, `stat_counter`, `data_table`, `dropzone`, `job_progress` → **audit page**.
5. `sentence_row`, `flag_panel`, `reason_form`, `anchor_chip`, `ledger`, `tabs`, `approval_gate`/`dock` → **review page** (week 4).
6. Lighthouse mobile + axe on all three; keyboard and screen-reader pass.

## 5. Acceptance checklist for the built pages
- [ ] JS+CSS ≤ 150 KB compressed per page (target ~50 KB); CI fails above 100 KB.
- [ ] Lighthouse mobile: Performance ≥ 90, Accessibility 100, on checker, audit, review. Checker LCP < 2.5 s on Fast 3G (throttling in foundations §8).
- [ ] 360px: no horizontal scroll; every target ≥ 44px on touch, ≥ 24px otherwise.
- [ ] Light and dark both pass the contrast script after Tailwind purge (and severity classes survive the purge: render test).
- [ ] `prefers-reduced-motion`: no animation, every outcome still announced.
- [ ] After "Use rewrite", "Keep with reason" and "Retry", focus is on a sensible element, not `body`.
- [ ] Non-overridable flags never render an override control; the API rejects an override attempt (`check_override`).
- [ ] Nothing on any page says "compliant", "safe", "approved" about a listing; rule-set label comes from `meta.yaml`.
- [ ] Tests run with `SATYA_LLM=mock`; the public checker imports no LLM provider.

## 6. Open questions (also in the task comment)
| # | To | Question |
|---|---|---|
| 1 | CTO | Plan §10 "0 🔴 in exports" vs rules that allow evidence overrides on some reds. Specs support both via `allow_red_override`. Which? |
| 2 | Engine | Per-sentence `anchor_state`, the sentence `type` enum, and `suggested_rewrite` in the review payload. |
| 3 | Rules | Severity for missing Legal Metrology r.10 fields (assumed amber, `LM-` ids). Does the public checker also run the product-type gate? |
| 4 | Platform / Engine | Confirm "nothing stored" is true (no persistence or logging of checker text), and the real checker cap (5,000 chars placeholder) and rate limits. |
| 5 | CTO | Alpine CSP build (`@alpinejs/csp`) and HTMX `allowEval: false`, to allow a strict CSP later. |
