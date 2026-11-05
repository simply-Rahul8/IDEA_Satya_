# Consultant review pack (DRAFT)

Plan: P10, P16, P17, P20, P23, P24. Owner: Rules & Compliance agent. Status: **DRAFT**. Nothing here has been sent to anyone.

## Files

| File | What it is |
|---|---|
| `consultant-pack.html` | The pack to review. Self-contained, no scripts. Open it in a browser and use Print, then Save as PDF (A4). |
| `consultant-pack.md` | The same content as Markdown, for review in the repo. |

Both files are **generated** from `engine/rules/*.yaml`. Do not edit them by hand. After any rule change:

```
uv run python -m engine.rules.pack
```

`tests/test_consultant_pack.py` fails if the committed pack is out of date with the rules.

## Contents

1. Scope note: what the rule set covers, what it does not, how matching works, wording.
2. What we ask of the consultant.
3. Rule table, then each rule in detail: severity, whether it can be overridden, why it is flagged, rewrite direction, citations, patterns, positive and negative examples, open questions, a decision box.
4. Safe-phrase allowlist. Entries that touch a locked rule are marked.
5. Product-type gate: what is refused and why.
6. Open questions: general ones, plus a checklist of every rule-specific one.
7. Sign-off sheet.

## Known gaps the consultant should know about

- Every citation is **unverified**. The pack was drafted without access to the primary texts (plan P16 week-0 verification has not been recorded). Section and rule numbers need checking.
- The DMR Act condition list (`engine/rules/dmr_diseases.yaml`) was written from memory, not copied from the current Schedule. Items such as baldness and obesity are unconfirmed.
- Hindi rules are not in this pack. The Indic agent's rules will get their own pack.

## Human steps (board user only)

The agent does not contact the consultant. The board user:

1. Decides when the pack goes out and sends `consultant-pack.html` (or a PDF printed from it) to the consultant. Week-2 review per plan section 9.
2. Collects the consultant's decisions and answers, and passes them to the Rules agent as a task.
3. After sign-off, records it in the sign-off log in `engine/rules/README.md`. The rule set status changes from DRAFT to SIGNED_OFF only then.
