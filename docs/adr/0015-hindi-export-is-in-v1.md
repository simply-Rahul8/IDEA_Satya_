# ADR-15: Hindi export is in the first paid test; it leaves through its own route, with the same gate plus the English-approval check

Status: accepted (CTO, SAT-57). Answers the question raised in SAT-45 (`docs/qa/sat-35-journey/REPORT.md`, Should-fix 1). Numbered 15 because SAT-50 takes ADR-14.

## Context
The Hindi tab said the pack "passes the export gate" but no route exported it. PLAN section 1 promises "English and Hindi output", the job statement says "fix them with claim-safe English and Hindi copy", step 9 exports it, and "Hindi UI" and "second Indic language" are the only Hindi items on the not-in-v1 list. So Hindi *copy* is v1 and its export is not scope creep.

## Decision
1. Hindi export is **Must-fix for the first paid test**, not a rewording of the page.
2. `GET/POST /packs/{id}/export/hindi` reuse the English export handlers with `lang="hi"`. Same generic CSV, same column-mapping screen, same audit record, UTF-8 with BOM so Excel reads Devanagari.
3. The gate fails closed and is stricter than English: `hindi_export_blockers` (English approved, Hindi made from that exact English text, Hindi verified with no open flag), checked on every request, and `export_csv` re-checks the pack itself.
4. The file is named `satya-export-<layout>-hi.csv` and the audit record carries `language: "hi"`. Listing fields come from the Hindi pack; product facts (name, brand, ingredients) stay as entered.
5. Hindi stays DRAFT until the native reviewer (SAT-5) signs off. The page says "No flagged risks under lexicon X", never "compliant". The print report stays English-only; Hindi has the audit record.
6. Out of scope: Hindi into Nykaa XLSX (waits for SAT-29 and SAT-4), a Hindi print report, any Hindi UI.
