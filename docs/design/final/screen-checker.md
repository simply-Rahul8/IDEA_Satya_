# Screen spec: public checker "Is my claim safe?" (variant A, Editorial Paper)

Board pick: SAT-12, Variant A. Plan: §3 step 10, §4 signature moment 1, P18 (deterministic only, with caps), P20 (not public before consultant sign-off). Prototype: [`../checker-a.html`](../checker-a.html). States: [`states.html`](states.html) C1–C8. Components: [`components.md`](components.md).

**Job:** a stranger pastes listing copy and, within a second or two, sees which phrases are risky and why, with a citation for each. It is the outreach hook: it must feel calm and expert, and a screenshot of it must look good.

## 1. Route and data

| | |
|---|---|
| Page | `GET /check` (public, no login) |
| Check | `POST /check` (form) → full page without JS; HTMX partial with JS (`HX-Request`) |
| Partial returns | `#backdrop` (highlighted mirror), `#verdict` (card or empty), `#count`, `#sr-status` (all OOB) |
| Rule sheet | `GET /rules/{rule_id}/sheet?v={rule_set_label}` (cacheable, contains no user text) |
| Limits | `CHECKER_MAX_CHARS = 5000` (placeholder from the prototype; **Engine/Platform to confirm the real cap, P18**). Rate limit from `engine/ratelimit.py`. |
| Engine | `engine.rules.evaluate(text, ruleset)` only (deterministic). No LLM on this page. |

## 2. Layout

**360px (single column, nothing else exists at this size):**
1. `topbar` (brand, theme toggle).
2. Hero (centred): eyebrow "Is my claim safe?", `h1` display type `--t-3xl` "Check your listing copy *before* a marketplace does." (the italic *before* in `accent-ink`), one sentence of support at `--t-md`.
3. **Draft banner** (visible above the paper while `not is_signed_off`; see §6 pre-launch).
4. **Paper**: `highlight_field`, `min-height: 15rem`, serif `--t-lg` (20px) text, 24px padding; foot: char counter (left), "Clear" ghost + "Try a sample" secondary (right).
5. Verdict card (appears below the paper once there is text).
6. Footer fine print (stamp, "Not legal advice", how it works).

**≥ 48rem:** same single column, `max-width: 44rem`, centred; hero text scales with the fluid type. The sheet becomes a right-hand panel. **No second column at any width** (that was the point of variant A).

Vertical rhythm: hero → paper `--s-7`; paper → verdict `--s-6`; verdict internal `--s-4`/`--s-5`.

## 3. Behaviour

1. **On load:** paper is empty with placeholder "Paste or type your product copy here…". Verdict region is empty and takes no space. Textarea is **not** auto-focused (it would open the keyboard and scroll the hero away on mobile).
2. **Typing/paste:** `hx-trigger="input changed delay:250ms"`. The backdrop immediately mirrors the plain text; "Checking…" appears in the foot (reserved space). On response: marks draw in (only new ones animate), the verdict updates (rise only the first time), counter updates.
3. **Verdict list item** → opens the citation sheet; focus returns to the item on close.
4. **Try a sample** fills the sample text and checks. **Clear** empties text, hides the verdict, clears the live region, returns focus to the textarea.
5. **Long text:** the counter shows `5,412 / 5,000` in red-fg bold with the word "over" (e.g. "412 over") and a `notice` "Only the first 5,000 characters were checked. Remove 412 characters to check the whole text." Marks beyond the cap do not exist. Nothing is truncated or deleted silently.
6. **Pasted HTML/rich text:** paste as plain text (`paste` handler uses `text/plain`). The text is data; it is never interpreted (P19).
7. **Share moment:** "Copy summary" in the verdict card (no user text in the copied string).
8. **Optional (not v1):** caret-aware hint under the paper naming the flag at the caret with a "View rule" button.

## 4. States

| State | Trigger | What shows | Notes |
|---|---|---|---|
| **C1 Empty** | no text | placeholder, counter `0 / 5,000`, Try a sample, no verdict | live region silent |
| **C2 Checking** | request in flight | plain mirrored text, "Checking…" + spinner, `aria-busy` | the verdict from the last check stays visible but gets `aria-busy`; no layout shift |
| **C3 Flagged** | ≥ 1 flag | marks in the paper, verdict (High/Severe risk etc.), tally, list | live: "3 blocked, 2 to review under rule set v0.1.0-draft." |
| **C4 Clear** | 0 flags | "No flagged risks" · "under rule set v0.1.0-draft", empty meter, green "Nothing flagged", honest caveat sentence | never "safe", "compliant", "approved", "passed" |
| **C5 Error** | 5xx / network | `notice` (error) with "Try again", text kept | `role="alert"` |
| **C6 Rate limited** | 429 | `notice` "You've reached the check limit. Try again in about {n} minutes. Nothing you typed is lost." (uses `Retry-After`) | no red |
| **C7 Over cap** | > 5,000 chars | red counter + notice (above) | check runs on first 5,000 |
| **C8 Out of scope** | product-type gate `needs_review` / `refused` (**if the Engine runs the gate on the public page; Rules agent to confirm**) | `verdict_card` variant `out_of_scope` with the gate's own explanation | no meter, no list |
| **Pre-launch** | `not is_signed_off` | prominent draft banner above the paper; "rule set v0.1.0-draft" everywhere | the page is not public until sign-off (P20); this state is also what the board sees on the preview |
| **No JS** | JS blocked | plain form + "Check" button, full-page result, marks in a read-only copy under the verdict | the paper's marks need the backdrop; the no-JS result renders the text with marks in a `<p>` |

## 5. Verdict content rules

- Heading: "{Moderate|Elevated|High|Severe} risk" for flags; "No flagged risks" for none. Sub: "{n} phrase(s) flagged" / "under rule set {label}".
- List order: red before amber; within a severity, text order. Each item: badge + rule id, the phrase in `<q>`, the rule's `title`.
- Every sentence on the page that describes the result ends in "under rule set {label}". The footer carries "Not legal advice."
- Copy is plain English for a content owner, not legalese: say "cures acne scars" is a treatment claim; leave citations to the sheet.
- **Copy-risk to confirm before launch:** the hero says "No login, nothing stored." This is a factual claim. The Platform/Engine agents must confirm that the text is neither persisted nor logged (including Sentry breadcrumbs and `llm_calls`, though none is used here). If not true, change the copy to what is true. Until confirmed it stays in the spec as draft copy.

## 6. Accessibility

**Focus order:** skip link → brand → theme toggle → textarea → Clear → Try a sample → (verdict) Copy summary → flag list items (in order) → "Audit your whole catalogue" → footer links.
- The paper's focus indicator is the `:focus-within` ring on the whole paper (3px `--focus`, 2px offset) and the textarea's own outline is suppressed **only** because the wrapper shows it. Verified ≥ 3:1 vs bg in both themes.
- Textarea `aria-describedby="live count"`; label "Product listing copy to check" (visually hidden, because the hero explains it; the label exists for AT).
- The verdict is a labelled `article`; its heading is `h2`. Flag items are buttons named like "cures acne scars: Blocked, Treatment or cure claim. Open citation".
- Live region: one polite message per completed check, and only when the result's signature (level + rule ids + phrases) changed.
- Marks differ by pattern (solid vs dashed underline) and the list adds icon + word; colour alone is never the signal.
- Contrast: all text ≥ 4.5:1, marks' text stays `--ink` on the soft backgrounds (verified in `contrast_report.txt`).
- Reflow at 320px and 200% zoom: the paper and verdict are fluid; no horizontal scroll.
- Reduced motion: no underline draw, no rise, no meter grow, static spinner; every state still arrives with the same words.

## 7. Motion

Underline draw 700ms on new marks only · verdict rise 420ms once · meter grow 420ms + 70ms stagger · sheet 420ms. Debounce 250ms (the prototype's 120ms is for local JS; a network round trip makes 250ms the right quiet period). See foundations §5 for reduced-motion.

## 8. Performance (this is the LCP page)

- LCP element: the `h1`. All hero, paper and footer markup is in the first HTML (≤ 14 KB compressed). The verdict, sheet and partials are never in the initial payload.
- Fonts: preload Fraunces 500 only; the `h1` paints with the metric-matched fallback and swaps without shift.
- JS+CSS: ≈ 48 KB compressed (see foundations §8).
- Paper reserves its height, so typing does not push the hero; the verdict is below the fold on mobile.
- Do not defer the stylesheet; do not use `x-cloak` on anything but the `<dialog>`.

## 9. Out of scope here
Sign-up flow, OG share image, analytics, Hindi checker UI, history of past checks (the page stores nothing).
