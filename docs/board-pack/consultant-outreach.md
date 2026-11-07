# Consultant outreach (DRAFT, not sent)

**For:** SAT-3 (book the consultant, week 0). **Sender:** you, from your own address. **Gate:** any external email is a board action (plan section 8). I have contacted no one.
**Attach:** (1) the one-pager at the bottom of this file, as a PDF; (2) `docs/consultant-pack/consultant-pack.html` printed to PDF (A4); (3) `consultant-signoff-template.md` (can go now or with the pack).
**Before sending:** regenerate the pack if the rules changed (`uv run python -m engine.rules.pack`) and update the version and fingerprint in the one-pager. At drafting time: rule set `satya-en v0.1.1-draft`, fingerprint `2aa67fe75bb2`, 24 rules.
**Timing (plan section 9):** book in week 0, review done by end of week 2, sign-off in week 3. Consultant sign-off gates the public checker and any audit report a brand sees (P20).

Who to look for: an advocate or regulatory consultant with hands-on cosmetics experience under the Drugs and Cosmetics Act and Cosmetics Rules 2020 (CDSCO), the Drugs and Magic Remedies Act, ASCI codes (including the fairness-product guidelines), and Legal Metrology packaged-commodity rules. Nothing here assumes a particular person or firm.

---

## Variant A: cold

**To:** `{{CONSULTANT_EMAIL}}`
**Subject options:** (1) Paid review of a draft claims rule set for beauty listings (about {{HOURS}} hours) · (2) Cosmetics regulatory review: 24 draft rules, fixed scope

Dear {{TITLE}} {{LAST_NAME}},

I'm {{SENDER_NAME}}. I'm building Satya, a tool that helps Indian beauty brands spot risky wording in product listings (drug-like claims, DMR Act disease claims, fairness claims) and suggests safer wording. I found your work through {{HOW_FOUND, e.g. a published article or your firm's cosmetics practice page}}.

I'd like to hire you for a bounded review. We have a draft rule set (24 rules, English only) with citations, positive and negative examples, and open questions. Before any brand sees output from it, I need an expert to:

1. mark each rule Approve, Change or Remove;
2. verify or correct every citation (we drafted without the primary texts, so all are marked unverified);
3. spot-check a sample of our labelled test listings; and
4. confirm the disclaimer wording and the limits of the review.

Estimated effort is {{HOURS, suggest 8 to 12}} hours over about two weeks, starting {{START_DATE}}. I'd propose {{FEE, e.g. "a fixed fee of ₹{{AMOUNT}}", or "I'm happy to hear your rate"}}. A one-page summary is attached. The full review pack follows if you'd like to go ahead. It is a self-contained PDF with a decision box for every rule.

This is not a request for a legal opinion on any brand or listing, and the tool never calls anything "compliant". It says "no flagged risks under rule set vX" and is not legal advice. Your sign-off would apply only to the rule set version you review, within the limits you set.

Could we have a 20-minute call this week to confirm fit, scope and fee? If this isn't your area, a pointer to someone who covers it would be welcome.

Thank you,
{{SENDER_NAME}}
{{SENDER_ROLE}}, Satya · {{PHONE}} · {{EMAIL}}

---

## Variant B: warm intro

Use when someone has agreed to introduce you. Ask the introducer to forward the email or copy you in. Send nothing until they say yes.

**To:** `{{CONSULTANT_EMAIL}}` · **Cc:** `{{INTRODUCER_EMAIL}}`
**Subject:** Intro from {{INTRODUCER_NAME}}: paid cosmetics claims-rule review

Dear {{TITLE}} {{LAST_NAME}},

{{INTRODUCER_NAME}} suggested I write to you ({{ONE_LINE_CONTEXT, e.g. "after we spoke about listing claims on Nykaa"}}). Thank you, {{INTRODUCER_FIRST_NAME}}, for the intro.

I'm building Satya, a claims checker for Indian beauty product listings. We have a draft English rule set of 24 rules covering drug and treatment claims, DMR Act diseases, fairness claims and common overridable claims (evidence, absolutes, superlatives). I'd like to engage you for a bounded review, about {{HOURS}} hours over two weeks from {{START_DATE}}:

- decide Approve / Change / Remove for each rule;
- verify or correct the citations;
- spot-check a sample of labelled listings; and
- sign a sheet that states what you reviewed and where the review stops.

A one-page summary is attached. The full pack is ready to send once you confirm interest and we agree scope and fee ({{FEE_LINE}}).

Would a short call on {{TWO_SLOTS}} work?

Thank you,
{{SENDER_NAME}}
{{SENDER_ROLE}}, Satya · {{PHONE}} · {{EMAIL}}

---

## Reply helpers (paste as needed)

- **"What do you want me to sign?"** A sheet that names the rule-set version and fingerprint, says what you reviewed, and lists changes you require. You can approve, approve with changes, or decline. Template attached.
- **"Is this a legal opinion?"** No. It is a review of draft rules and wording. The tool never says "compliant". Reports read "no flagged risks under rule set vX. Not legal advice."
- **"Does it cover Legal Metrology or label claims?"** Not yet. The pack covers listing text only. Label-field checks are out of scope for the v1 rules, and I'd welcome your view on whether and how to add them.
- **"Do you cover Ayurvedic products?"** v1 refuses Ayurvedic, AYUSH, supplement and OTC-drug products. The pack asks you to confirm that line.

---

## One-pager to attach (print this section as a PDF)

# Satya: summary of the review pack

**What it is.** Satya checks product-listing text for Indian beauty brands against a written rule set and says which phrases are risky and why. It reports "no flagged risks under rule set vX". It never says "compliant" and is not legal advice.

**What we ask you to review.** Rule set `satya-en`, version `{{RULE_SET_VERSION}}` (v0.1.1-draft at drafting), fingerprint `{{FINGERPRINT}}`. English only. Draft: not yet reviewed by anyone qualified.

| Group | Rules | Can a brand override? |
|---|---|---|
| Drug and treatment claims (`EN-DRUG-*`) | 5 | No: always blocked |
| Drugs and Magic Remedies Act diseases (`EN-DMR-*`) | 3 | No: always blocked |
| Fairness and skin colour (`EN-FAIR-*`) | 3 | No: always blocked |
| Overridable claims (`EN-CLAIM-*`: evidence, absolutes, superlatives, sun protection, hair, slimming) | 13 | Yes, with a written reason or evidence |
| Safe-phrase allowlist, each entry tied to named rules | 3 entries | n/a |
| Product-type gate: refuses AYUSH, Ayurvedic and supplement or OTC-drug products | 4 signals | n/a |

**Regulatory areas touched.** Drugs and Cosmetics Act 1940 and Cosmetics Rules 2020 (CDSCO); Drugs and Magic Remedies (Objectionable Advertisements) Act 1954; ASCI Code and ASCI fairness-product guidelines; CCPA misleading-advertisement guidelines 2022; Consumer Protection Act 2019. Legal Metrology label-field checks are out of scope for this pack.

**Known gaps (stated up front).**
- Every citation is unverified: drafted without the primary texts.
- The DMR Act condition list was written from memory and needs checking against the current Schedule.
- Premature greying (`EN-DMR-003`) is kept locked on a Drugs and Cosmetics Act basis and needs your decision.
- 33 rule-specific questions and 7 general ones are listed in the pack.

**What we need from you.**
1. Approve, Change or Remove for each of the 24 rules.
2. Verify or correct every citation.
3. Spot-check a sample of our labelled test listings (50 synthetic listings, labels in draft).
4. Confirm the disclaimer wording and the report wording.
5. Complete the sign-off sheet (template attached): rule-set version, each rule reviewed, spot-check, disclaimer language, limits of review.

**Effort and timing.** About {{HOURS}} hours over two weeks, starting {{START_DATE}}. Fee: {{FEE_LINE}}.

**What happens to your sign-off.** It is recorded against the exact rule-set version. Brand-facing output stays switched off until it is recorded. Any later rule change needs a new review of that change.

**Contact.** {{SENDER_NAME}}, {{EMAIL}}, {{PHONE}}.
