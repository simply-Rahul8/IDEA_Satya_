# Consultant sign-off template (DRAFT)

**Purpose:** the exact fields a consultant must complete before the rule set can move from DRAFT to SIGNED_OFF (plan P20).
**Use:** (1) send the "Sign-off sheet" below to the consultant with the pack; (2) when the signed sheet comes back, you paste the "Drop-in log entry" into `engine/rules/README.md` under "Sign-off log" and, only if the decision says Approved, ask the CTO to set `status: SIGNED_OFF` in `engine/rules/meta.yaml`.
**Rule:** the status changes only after a log entry says "Approved". "Approved with changes" keeps the set DRAFT until the changes are made and the consultant confirms them in writing. Nothing here claims compliance. The only permitted wording is "no flagged risks under rule set vX. Not legal advice."

---

## Sign-off sheet (give this to the consultant)

### 1. Identity and scope
| Field | Entry |
|---|---|
| Reviewer name | |
| Qualification and registration (for example Bar Council enrolment, years in cosmetics regulatory work) | |
| Firm or independent | |
| Engagement date range | |
| Conflicts of interest (any relationship with a brand or competitor that uses Satya) | |

### 2. Rule set reviewed
| Field | Entry |
|---|---|
| Rule set name | `satya-en` |
| Rule set version (vX) | `{{RULE_SET_VERSION}}` |
| Content fingerprint (shown on the pack cover) | `{{FINGERPRINT}}` |
| Files reviewed | `consultant-pack.html` or `.pdf`, generated from `engine/rules/*.yaml` |
| Number of rules in scope | `{{RULE_COUNT}}` |

The sign-off applies only to this exact version and fingerprint. A later change to any rule needs a new review of that change.

### 3. Each rule reviewed
One row per rule. The pack has the same decision box. Copy the decisions here or attach the marked-up pack.

| Rule ID | Approve / Change / Remove | Change required (exact wording) | Citation verified? (Y / corrected / could not verify) |
|---|---|---|---|
| EN-CLAIM-001 to EN-CLAIM-013 | | | |
| EN-DMR-001 to EN-DMR-003 | | | |
| EN-DRUG-001 to EN-DRUG-005 | | | |
| EN-FAIR-001 to EN-FAIR-003 | | | |

Also confirm:
- [ ] Non-overridable group (drug and treatment, DMR Act diseases, fairness) is correct as locked, or list moves: ______
- [ ] Any overridable rule that should be locked: ______
- [ ] Safe-phrase allowlist entries (AL-001 to AL-003) reviewed: ______
- [ ] Product-type gate (refuse AYUSH, Ayurvedic, supplement and OTC-drug products) reviewed: ______
- [ ] General questions 1 to 7 and the rule-specific questions in pack section 7 answered, or listed as unanswered: ______
- [ ] Decision on `EN-DMR-003` (premature greying: keep locked or move to overridable): ______

### 4. Corpus spot-check
| Field | Entry |
|---|---|
| Corpus reviewed | 50 labelled listings, `data/corpus/` (synthetic; labels are draft) |
| Sample size and how chosen | |
| Sentences checked | |
| Labels you disagree with (listing id, sentence, your label, rule id) | |
| Overall view: are the labels fit to measure the rules against? | Yes / Yes after changes / No |

### 5. Disclaimer and report language
| Item | Wording as drafted | Decision (Accept / Change to) |
|---|---|---|
| Report line | "No flagged risks under rule set vX. Not legal advice." | |
| Standard disclaimer allowlisted as AL-001 ("not intended to diagnose, treat, cure or prevent any disease") | as in pack | |
| Wording that must be added or removed before a brand sees a report | | |
| Confirm Satya must never describe a listing as "compliant" or "approved" | Yes / No | |

### 6. Limits of review (the reviewer completes this; it is recorded with the sign-off)
The reviewer confirms that the review is limited as follows, or states otherwise:
- English rules for listing text only. Not Hindi, not images, not label or pack claims, not Legal Metrology label fields, not marketplace policies.
- Cosmetics only. No view on AYUSH, drug, supplement or food products beyond the product-type gate.
- A review of the rules and wording as written, not a legal opinion on any brand, listing or product, and not a guarantee that a listing is acceptable to a regulator, ASCI or a marketplace.
- Law as at the review date: ______. Amendments after that date are not covered.
- Other limits stated by the reviewer: ______

### 7. Decision and signature
- **Decision:** [ ] Approved  [ ] Approved with the changes listed above  [ ] Not approved
- **Changes required before sign-off takes effect:** ______
- **Reviewer signature:**
- **Date:**

---

## Drop-in log entry (for `engine/rules/README.md`, after the sheet comes back)

The sign-off log table in `engine/rules/README.md` has these columns: Date, Rule set version, Reviewer (name, qualification), Scope reviewed, Decision, Changes required, Recorded by. Replace the "(none yet)" row with a row like this, filled from the signed sheet:

```
| {{YYYY-MM-DD}} | {{RULE_SET_VERSION}} (fingerprint {{FINGERPRINT}}) | {{REVIEWER_NAME}}, {{QUALIFICATION}} | All {{RULE_COUNT}} rules (each Approve/Change/Remove recorded), citations, allowlist, product-type gate, corpus spot-check of {{N}} sentences, disclaimer and report wording; limits as in sheet section 6 | {{Approved / Approved with changes / Not approved}} | {{summary or "none"}} | {{BOARD_USER_NAME}} |
```

If you want the fuller record to live in the repo, also file the signed PDF at `docs/consultant-pack/signoff/{{RULE_SET_VERSION}}.pdf` and link it from the row. Do not commit anything containing the consultant's personal phone or address.

Citation verification (P16) goes in the second table in the same file, one row per citation:

```
| {{YYYY-MM-DD}} | {{citation as written in the pack}} | {{primary text or source the consultant checked}} | {{Verified / Corrected to ... / Could not verify}} | {{BOARD_USER_NAME}} |
```

After the entry is in, ask the CTO to merge it. The checker and any brand-facing report go live only when the row says Approved and `meta.yaml` says `SIGNED_OFF`.
