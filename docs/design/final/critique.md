# Design self-critique (SAT-13)

**Method note.** The task asks for a `/design-critique` self-check. That skill is not installed for this agent (the same was true of `/design-consultation` and `/design-shotgun` in SAT-7; it is not in this session's skill list). I ran the critique by hand against the usual axes: hierarchy and mood against the plan §4 bar, consistency, states and edge cases, accessibility (WCAG 2.2 AA), mobile at 360px, performance, copy and regulatory wording. I rendered every state at 360px and 1280px, light and dark ([`states.html`](states.html), screenshots in [`../screenshots/`](../screenshots/) as `final-states-*`), and ran the contrast script on the new colour pairs. **Not done:** a real-device pass, a Lighthouse run, and a screen-reader pass. Those need the built pages and belong to the Frontend and QA tasks (acceptance checklist in README §5).

## Findings, and what the specs now do about each

| # | Axis | Finding in the picked prototypes | Severity | Resolution |
|---|---|---|---|---|
| 1 | **Correctness vs engine** | Prototype treats red as "never overridable" and uses `amber`, `DRG-01` ids. The real rules have `severity: red` **with** `overridable: true` (e.g. EN-CLAIM-001), `orange`, and ids like `EN-DRUG-001`. A build to the prototype would hide a legitimate path or, worse, offer an override on a hard block. | High | foundations §1 mapping table; R1 vs R2 states; no override control rendered for non-overridable; server re-check by `policy.check_override`. Open question to CTO on "0 🔴 in exports" (`allow_red_override`). |
| 2 | **Honesty of status** | "Kept with reason" was green with a check, i.e. it read as "Clear". Green means "no flagged risks under rule set vX". | High | New `kept` state in ink with dotted edge; reason always visible; never green. |
| 3 | **Mobile tracing** (board note) | Anchor chip showed only `C5`; tapping it switched tabs and lost the reader's place. | High | `anchor_chip` shows the claim text full-width at 360px, expands an inline peek, switches tabs only on the explicit "Open in Product Truth"; "Back to sentence" and reverse-trace "Used in" chips. Verified in render R1/R3/R9. |
| 4 | **A11y: touch targets** | Chips were 28px and small buttons 36px, under the design system's own 44px rule. | Medium | 44px on `pointer: coarse` (final-parts.css). 24px floor everywhere. |
| 5 | **A11y: heat-strip cells** | About 21px at 360px (12 fixed columns), under SC 2.5.8; 120–500 tab stops; floating tooltip fails SC 1.4.13 and is absent on touch; clear cells' border ~1.9:1. | High | Auto-fill columns with a 26px floor (10 cols at 360px); roving tabindex; always-visible inspector line; `green-fg` outline. Verified in render A2–A4. |
| 6 | **A11y: focus after HTMX swap** | "Use rewrite" removes the focused button, dropping focus to `body`. | High | Foundations §6 focus rule 1 plus a named test. |
| 7 | **A11y: sticky bars** | Sticky gate and fixed dock can cover the focused control (new in WCAG 2.2, SC 2.4.11). Gate offset was a magic `9.5rem`. | Medium | `--gate-h`/`--dock-h` runtime tokens; `scroll-padding`; row `scroll-margin-top`. |
| 8 | **A11y: editing control** | `contenteditable` with `role="textbox"`: caret jumps when marks re-render, weaker IME and screen-reader behaviour. | Medium | Native `textarea` over a mirrored backdrop (same technique the board already picked for the checker); never swapped by HTMX. Trade-off accepted: no inline icon in the text (list and gutter carry it). |
| 9 | **A11y: ARIA patterns** | `role="tab"` without arrow-key handling; custom focus trap; `aria-live` on "Re-checked in N ms" would spam; "Wrong flag?" flipped label and `aria-pressed`. | Medium | Full tabs pattern; native `<dialog>`; ms text is `aria-hidden` and replaced by "Checked"; the report control is replaced by a status sentence + Undo. |
| 10 | **Mobile layout** | Review gate non-sticky on phones so the approval state scrolled away; 2rem gutter column wasted 13% of 328px; tall gate on tablets. | Medium | Bottom dock on phones; gutter only ≥ 48rem; gate condenses on scroll. The dock needed a second pass: three-line note beside two buttons in the first render, fixed with an icon-only Next (render R10). |
| 11 | **Correctness: offsets** | Highlights computed in the browser from engine offsets: Python code-point offsets differ from UTF-16 for emoji and some Indic text. | Medium | Server renders the backdrop; client never computes offsets. |
| 12 | **Perf on 3G** | "As you type" re-check on a 562ms RTT: marks vanish while typing. Debounce 120ms is for local code. | Medium | Debounce 250ms (checker) / 150ms (review), `hx-sync` replace, stale-response guard, plain-mirror while busy; known limit documented. |
| 13 | **Layout bug found in my own gallery** | Auto-track CSS grids let an input's intrinsic width overflow cards at 360px (visible in the first 360px render; same pattern exists in the SAT-7 prototypes' `main { display: grid }`). | Medium | Rule added to components.md; fixed in `states.html`. |
| 14 | **Completeness: states** | Prototypes covered only the happy and flagged paths. No empty, loading, error, rate-limit, over-cap, gate, offline, partial-failure states. | High | State tables for each screen; C1–C8, R1–R10, A1–A4 rendered. |
| 15 | **Regulatory copy** | "Nothing stored" is a factual claim the design cannot verify. "Approve pack" could read as legal approval. | Medium | Flagged as copy-risk to confirm (checker §5); approval confirm line "not a legal sign-off". Wording audit: no "compliant", "safe", "approved by" anywhere in the specs or gallery. |
| 16 | **Hierarchy and mood (plan §4 bar)** | Checker A is calm and editorial (pass). Review B is dense by nature; risk is a "form-like" feel on phones. | Low | Rows separated by space and a status edge rather than boxes; display serif for sentence text; a single accent. The result is intentionally quieter than variant C. |

## Remaining risks (not fixed by design alone)

1. **Fraunces/Inter are not in the repo.** The renders use fallback fonts; final feel and the 110 KB font budget are unverified until the fonts are subsetted. (Human step: none; licence is OFL. Frontend does the subsetting.)
2. **Native `<dialog>` animation** (`@starting-style`) is not on older Android WebViews; the spec degrades to no animation, which is acceptable.
3. **Fast-3G LCP** is argued from the critical path (HTML ≤ 14 KB, one CSS, preload one font), not measured. Confirm on the bom1 preview.
4. **Rule text and sources** in the screens are illustrative and unverified (P16/P20). Citation sheet shows "Not yet verified".
5. **No Hindi view yet** (journey step 8): layouts are built not to break, but it needs its own pass.
6. **Missing Legal Metrology fields** severity is an assumption (amber). Rules agent to confirm.
7. **Product Truth editor** (claim confirmation) is not designed; the ledger links to it.

## Checks run
- `python -I docs/design/final/contrast_final.py`: 0 failing required pairs, light and dark ([`contrast_final.txt`](contrast_final.txt)). The SAT-7 report remains 0 failing.
- Rendered `states.html` at 360px and 1280px, light and dark, headless Chrome (`tools/shots.sh`).
- `git diff` of `assets/tokens.css` is additive only (new custom properties).
