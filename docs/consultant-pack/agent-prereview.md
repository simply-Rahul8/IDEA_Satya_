# Agent pre-review of the draft rules and citations

**Agent pre-review, not legal advice, not a consultant sign-off.**

- Rule set reviewed: satya-en v0.1.0-draft (fingerprint 5bdfe1b61c05). Status stays DRAFT.
- Author: Regulatory Research Analyst agent. Task: SAT-31. Date checked: **2026-11-06** (all rows below).
- Nothing in `engine/rules/` was edited. No severity or overridable flag was touched. Every change below is a **suggestion** for the consultant (SAT-3/SAT-24/SAT-14, which stay with the board user).
- Nobody outside the repo was contacted.

## 0. How the check was done, and its limits

- Status words: **verified** = provision text read and matches what the rule says. **partly** = source exists but the pack's pin-point, number or description is wrong or too loose. **could-not-verify** = no readable primary text. **wrong** = the pack's statement is contradicted by the text.
- Official hosts `indiacode.nic.in`, `consumeraffairs.nic.in`, `meity.gov.in`, `pib.gov.in`, `egazette.gov.in` and `legalmetrology.gov.in` refused or failed to load. Where a mirror was used, the row says "mirror". The consultant must still check mirrored text against the Gazette.
- Read as primary: the Cosmetics Rules 2020 PDF on cdsco.gov.in, and the ASCI site (code, guidelines).
- Mirrors: Indian Kanoon (Consumer Protection Act), advocatekhoj (D&C Act s.3), bnblegal (DMR Act), taxguru (CCPA 2022 guidelines).
- Secondary only (news or law-firm notes): DPDP Rules 2025, Legal Metrology, E-Commerce Rules, Supreme Court 2024 order, Rule 170, BIS sunscreen standard.

## 1. Citation table

### 1a. By source and provision

| Rules citing it | Citation in the pack | Status | Primary-source URL used | Note |
|---|---|---|---|---|
| CLAIM-005, 010, 011, 013; DRUG-001..005 | D&C Act 1940 s.3(aaa) "cosmetic" | verified (mirror) | https://www.advocatekhoj.com/library/bareacts/drugsandcosmetics/3.php | "cleansing, beautifying, promoting attractiveness, or altering the appearance". A search snippet says a 2026 amendment may have changed words in s.3; not confirmed. |
| DRUG-001..005; CLAIM-005, 010, 011, 013 | D&C Act s.3(b) "drug" | partly | same | (i) treatment/prevention of disease: matches. But the "structure or function" limb is s.3(b)(ii) and covers only substances "specified... by the Central Government by notification" and excludes food. The pack presents it as a general limb. s.3(b)(i) also expressly makes body-applied insect repellents drugs. |
| CLAIM-004, 005, 007, 009; DRUG-001, 004 | Cosmetics Rules, 2020 "(G.S.R. 426(E))" | **wrong** | https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/cos_rules/Cosmetics%20Rules%202020.pdf ; https://www.cdsco.gov.in/opencms/opencms/en/Acts-and-rules/Cosmetics-Rules/ | The number is **G.S.R. 763(E), 15 Dec 2020** (Gazette Extra. Pt II Sec 3(i) No. 632). 426(E) does not appear. |
| same | Cosmetics Rules "labelling and claims provisions; rule numbers to be confirmed" | partly | same PDF | Labelling is **r.34**. False or misleading claims is **r.36**: "No cosmetic may purport or claim to purport or convey any idea which is false or misleading to the intending user." Also r.12-14 (import registration), r.37 (hair dye caution), r.39 (Ninth Schedule standards; r.39(7) bans animal testing). The Rules contain **no** rule on "tested/proven" evidence, "natural", SPF/sunscreen claims, or "medicated" wording. Only r.36 applies to those, generically. |
| CLAIM-005 | "Cosmetics are registered, not approved" | partly | same PDF (r.12-14, r.34(2)(b), r.34(5)) | Only **imported** cosmetics are "registered" (Import Registration Certificate, label "RC No"). Domestic products are made under a State licence ("M. L. No" on label). "CDSCO registered" is accurate only for imports. |
| DMR-001, 003 | DMR Act 1954 s.3(d) and the Schedule | verified (mirror) | https://bnblegal.com/bareact/the-drugs-and-magic-remedies-objectionable-advertisements-act-1954/ | s.3(d) and the 54-item Schedule exist as described. Many of the rule's conditions are **not** in the Schedule (see 2.2). s.16(2)(a) lets the Centre add conditions by rule; any such rules were not checked. |
| DMR-002 | DMR Act s.3(a), (b), (c) | verified (mirror) | same | (a) miscarriage / prevention of conception in women; (b) capacity for sexual pleasure; (c) correction of menstrual disorder in women. Applies to ads "referring to any drug". |
| DMR-003 | DMR Act "premature greying (listed in the Schedule, to be confirmed)" | **wrong** | same | Premature greying is **not** in the Schedule. Neither is baldness. |
| DMR-001 | (open question) "baldness", "obesity" in Schedule | partly | same | Obesity **is** item 38, printed "Obsesity". Baldness is not. |
| FAIR-001..003 | ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products | verified | https://www.ascionline.in/the-asci-code-guidelines | Real title on ASCI: "Guidelines for advertising of skin lightening or fairness improvement products", signed 14 Aug 2014. Four points: no discrimination or negative stereotyping by skin colour; pre-use depiction must not look unhappy/unattractive; no link of darker or lighter skin to socio-economic strata, caste, community, religion, profession, ethnicity; no gender discrimination by skin colour. It governs **depiction**. It does not itself ban lightening claims. |
| FAIR-001..003 | ASCI Code "Chapter III (public decency or portray groups adversely)" | partly | https://www.ascionline.in/the-asci-code/ | The colour/race/caste clause is **Ch. III cl.1(b)** ("Derides any individual or groups on the basis of race, caste, colour, religion, gender, ..."). Ch. III is "Against harmful products/services/situations". "Public decency" is **Ch. II**. |
| CLAIM-001..004, 006..013 | ASCI Code "Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed" | verified | https://www.ascionline.in/the-asci-code/ | I.1 substantiation; I.2 source and date of research; I.4 no distortion or misleading by implication or omission; I.5 no grave or widespread disappointment (its example covers claims on obesity, illness, impotence, infertility, baldness). Ch. I is dated 10 Jul 2025 on the page. |
| CLAIM-012 | ASCI Code (superlatives) | partly | same; https://www.ascionline.in/the-asci-code-guidelines | No superlative-specific clause. Nearest: I.1, I.4, IV.1(c) (comparisons factual and substantiable) and the ASCI awards/rankings guideline (21 Apr 2022). |
| CLAIM-001..013 (most), DRUG-001, 002, 005 | CCPA Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 | verified (mirror) | https://taxguru.in/?p=828129 | Title and date match: 9 Jun 2022, F. No. J-25/4/2020-CCPA (Reg), issued under **CPA s.18**. The pack's pin-point is generic. Use cl.4(1)(a),(b) (truthful; no exaggeration of performance); cl.11 (disclaimers); cl.12(a) (substantiation on demand), 12(b) (source and date); cl.13 (endorser due diligence); cl.14 (material connection disclosure); cl.8 (ads targeting children, 8(1)(o) health claims). The guidelines do not define "misleading advertisement"; they defer to the Act. |
| CLAIM-001, 012; FAIR-001 | Consumer Protection Act 2019 s.2(28) | verified (mirror) | https://indiankanoon.org/doc/48103131/ | Four limbs: falsely describes; false guarantee or likely to mislead on nature, substance, quantity, quality; implied representation that would be an unfair trade practice; deliberately conceals important information. |
| FAIR-001 | CPA s.21 "powers of the CCPA" | verified (mirror) | https://indiankanoon.org/doc/160830141/ | s.21(1) directions; (2) penalty up to ₹10 lakh, ₹50 lakh repeat; (3) endorser ban 1 yr, 3 yrs repeat; (4) up to ₹10 lakh on any person who "publish[es], or is a party to the publication of" a misleading ad; (5) endorser due-diligence defence. |
| (not cited in pack; relevant) | CPA s.18(2)(l); s.89 | verified (mirror) | https://indiankanoon.org/doc/146190727/ ; https://indiankanoon.org/doc/112210594/ | s.18(2)(l) guideline power. s.89: manufacturer or service provider causing a false or misleading ad: up to 2 yrs and ₹10 lakh, repeat up to 5 yrs and ₹50 lakh. |

### 1b. Per rule roll-up (after the corrections above)

| Rule | Status | One-line note |
|---|---|---|
| EN-CLAIM-001 | verified | ASCI I.1/I.4, CCPA cl.4, CPA 2(28) all fit. |
| EN-CLAIM-002 | verified | CCPA 4(1)(b) exaggeration of performance. |
| EN-CLAIM-003 | verified | Same. |
| EN-CLAIM-004 | partly | ASCI I.1/I.2 and CCPA 12(a)/(b) fit. Cosmetics Rules cite is wrong number; r.36 is generic only. |
| EN-CLAIM-005 | partly | Wrong GSR number. "Registered, not approved" holds for imports only. |
| EN-CLAIM-006 | verified | ASCI I.2 and CCPA 12(b) require source and date of research. |
| EN-CLAIM-007 | partly | Cosmetics Rules give only r.36. Stronger basis exists: ASCI green-claims guideline (see 2.5). |
| EN-CLAIM-008 | verified | Generic substantiation. CCPA cl.8 covers ads *targeting* children, not products *for* babies. |
| EN-CLAIM-009 | partly | The Cosmetics Rules have no SPF/sunscreen rule. Drop or replace that cite. |
| EN-CLAIM-010 | partly | D&C cites fine. Also relevant: the Rules' Fourth Schedule lists "Anti hair loss products" as a cosmetic category. |
| EN-CLAIM-011 | partly | Fourth Schedule lists "Antidandruff products" as a cosmetic category. |
| EN-CLAIM-012 | partly | No superlative clause. Use ASCI IV.1(c) and awards/rankings guideline. |
| EN-CLAIM-013 | partly | Fits r.36. CDSCO posted a 28 Oct 2026 notice on "Misleading or false claims of the product FatX solution registered under COS-2" (title only, PDF unread). |
| EN-DMR-001 | partly | Provision verified. About 16 listed conditions are not in the Schedule. Over 20 Schedule items are missing from the rule. |
| EN-DMR-002 | verified | s.3(a)-(c) wording matches. |
| EN-DMR-003 | **wrong** | Premature greying is not in the Schedule, so the DMR basis for a locked red rule does not exist. |
| EN-DRUG-001 | partly | s.3(b)(i) fits. Wrong GSR number. |
| EN-DRUG-002 | verified | s.3(b)(i) "prevention of any disease". |
| EN-DRUG-003 | partly | s.3(b)(ii) is limited to Central-Government-notified substances. The broader hook is DMR s.2(b)(iii) (see 2.3). |
| EN-DRUG-004 | partly | Nothing in the Cosmetics Rules on "medicated" wording. Rests on D&C s.3(b)(i) plus r.36. |
| EN-DRUG-005 | partly | Regrowth is not within s.3(aaa)'s purposes, which supports the drug reading. But "anti hair loss" is a recognised cosmetic category. |
| EN-FAIR-001 | partly | Guideline is real. The ASCI Code chapter reference is imprecise. Guideline concerns depiction, not a flat ban on lightening claims. |
| EN-FAIR-002 | partly | Guideline point 1 fits directly. Same chapter-reference issue. |
| EN-FAIR-003 | partly | Guideline points 1 and 3 fit directly. Same chapter-reference issue. |

### 1c. Other regimes named in the plan or task (not cited by any rule today)

| Regime | Status | URL used | Note |
|---|---|---|---|
| Legal Metrology (Packaged Commodities) Rules 2011, "r.10 fields" (PLAN §3) | could-not-verify | https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/662702/e-commerce-entities-legal-metrology-packaged-commodities-amendment-rules-2017 (secondary) | Secondary sources say declarations are in **Rule 6(1)** and the 2017 amendment (in force 1 Jan 2018) added **Rule 6(10)**, making e-commerce entities display them. Khaitan calls it "rule 10 of the Amendment Rules". "r.10" in the plan is probably a mix-up. Check against the Gazette. |
| Consumer Protection (E-Commerce) Rules 2020, G.S.R. 462(E), 23 Jul 2020 | could-not-verify | https://taxguru.in/wp-content/uploads/2020/07/Consumer-Protection-E-Commerce-Rules-2020.pdf (not read) | Secondary: r.4(4) grievance officer; r.5 marketplace duties; r.6 seller duties incl. country of origin. Section numbers are inconsistent across sources. |
| DPDP Act 2023 and DPDP Rules 2025 | could-not-verify (primary) | https://www.mondaq.com/india/data-protection/1708164/digital-personal-data-protection-rules-2025-notified (secondary) | Rules notified 13/14 Nov 2025. Rules 1, 2, 17-21 in force at once. Main obligations (notice, consent, safeguards, breach notification) about 18 months later, about **13 May 2027** (sources differ by a day). Act sections were not read. |
| Supreme Court self-declaration order, IMA v Union of India, 7 May 2024 | partly | https://www.ascionline.in/advisories/ (titles); https://www.mondaq.com/india/broadcasting-film-tv-radio/1500870/supreme-court-mandates-self-declaration-by-advertisers (secondary) | ASCI lists the advisory (3 Jun 2024, 3 Jul 2024). Secondary: for ads from 18 Jun 2024; TV/radio via Broadcast Seva portal, print/digital via Press Council of India portal. The order and advisory PDFs were unreadable. |
| D&C Rules 1945 r.170 (Ayurvedic/Siddha/Unani ad pre-approval) | could-not-verify | https://www.barandbench.com/story/news/misleading-medical-ads-case-supreme-court-closes-case-allows-ayush-ads-without-state-approval (secondary) | Secondary: Ayush ministry omitted r.170 (1 Jul 2024); SC stayed the omission 27 Aug 2024 and vacated the stay 11 Aug 2025. Current status needs a primary check. |
| BIS sunscreen standard | could-not-verify | https://services.bis.gov.in/tmp/PPCD5515096_09122022_2.pdf (draft, not read) | Search snippets: draft PCD 15096 (Dec 2022); SPF test IS 17494 (= ISO 24444); water resistance IS 17660 (= ISO 16217). Final status and any mandatory certification unknown. No cosmetics Quality Control Order found. |
| CDSCO notices | partly | https://www.cdsco.gov.in/opencms/opencms/en/Cosmetics/cosmetics/ | Page cites r.12(1), r.36, r.39. Notice titles only (PDFs unreadable): "Misleading or false claims of the product FatX solution..." (28 Oct 2026); "Use of Cosmetics" (19 May 2026); animal-testing notices G.S.R. 346(E) (2014) and 718(E) (2014). No CDSCO text on sunscreen or cosmetic-vs-drug classification was found. |
| ASCI influencer guidelines | verified | https://www.ascionline.in/the-asci-code-guidelines | 6 Mar 2025 edition; Addendum 1 (15 Jul 2021), Addendum II (6 Mar 2025). |
| ASCI green-claims guidelines | verified | same | Effective 15 Feb 2024. |

## 2. Suggested rule changes (suggestions only)

### 2.1 Citation fixes (no behaviour change)

1. Replace "G.S.R. 426(E)" with **G.S.R. 763(E), 15 Dec 2020** wherever it appears.
2. Replace "labelling and claims provisions" with r.34 (labelling) and r.36 (false or misleading claims). Add r.12-14 for CLAIM-005.
3. Fairness rules: cite **ASCI Code Ch. III cl.1(b)** and the guideline's four points. Fix the guideline title. Drop "public decency", which is Ch. II.
4. Pin the ASCI Chapter I cites to I.1, I.2, I.4, I.5. Pin CCPA cites to cl.4, 11, 12, 13, 14, and cl.8 for children.
5. Pin CPA cites to s.2(28), s.18(2)(l), s.21(1)-(5), s.89.
6. Remove the Cosmetics Rules cite from CLAIM-009 (no SPF provision) and replace it with r.36.
7. Add DMR s.2(b)(iii) and s.7 (penalty: up to 6 months and/or fine; repeat up to 1 year) as sources to DMR rules. Add s.9 (offences by companies) as context.

### 2.2 EN-DMR-001 and EN-DMR-003 (DMR Schedule)

Evidence: Schedule of 54 items, read from the bnblegal mirror. The consultant should confirm it is unchanged since 1963 and that no s.16(2)(a) rules have added conditions.

- **EN-DMR-003 (wrong basis).** Premature greying is not listed. Options for the consultant: keep it as a drug-claim red rule citing D&C s.3(b) instead of the DMR Act, or move it to an overridable claim. I made no change.
- **Conditions in the rule but not in the Schedule:** asthma, asthmatic, bronchial, jaundice, hernia, arthritis, cardiac, varicose, hiv, malaria, dengue, hepatitis, cirrhosis, piles, hemorrhoids, baldness, and likely infertility and hypertension as worded (Schedule has "sterility in women" and "high or low blood pressure"). Most remain disease claims under EN-DRUG-001, so moving them to a D&C-cited rule loses no coverage. Re-citing is a suggestion; the wording of the rule is the consultant's call.
- **Schedule items missing from the rule:** Bright's disease, dropsy, fits, gangrene, hydrocele, infantile paralysis, lockjaw, locomotor ataxia, nervous debility, plague, pleurisy, pneumonia, smallpox, trachoma, tumours, ruptures, "typhoid fever", diseases and disorders of the brain / optical system / uterus / nervous system / prostatic gland, "female diseases (in general)", "disorders of menstrual flow".
- **Two Schedule items matter for cosmetics:** "Forms and structure of the female bust" (item 21) and "Stature of persons" (item 47). Bust-firming or enlarging creams and height-gain claims are common. Suggest a rule for these, subject to the consultant's answer on question 4 in section 4.
- **Typo to keep in mind:** the Schedule prints "Obsesity".

### 2.3 EN-DRUG-003 (structure or function)

D&C s.3(b)(ii) reaches only substances notified by the Centre. DMR s.2(b)(iii) is wider: "any article, other than food, intended to affect or influence in any way the structure or any organic function of the body". Suggest citing DMR s.2(b)(iii) for the rationale and asking the consultant whether the locked-red status rests on it.

### 2.4 EN-CLAIM-005 (regulator approval)

- Suggested rewrite hint: imports: "Import Reg. Cert. No. RC/..."; domestic: "Manufactured under licence no. M...". The current hint ("state the registration number") fits imports only.
- Possible widening (agent judgement, no statute behind it): "cdsco certified", "cdsco licensed", "dcgi approved", "fda cleared", "fda registered", "ministry of health approved", "state fda approved".

### 2.5 EN-CLAIM-007 (natural, organic, chemical-free)

ASCI green-claims guidelines (effective 15 Feb 2024): absolute claims such as "environment friendly", "eco-friendly", "sustainable" need robust data or credible accreditation and cannot be diluted by a disclaimer; "non-toxic", "biodegradable" and similar claims need "competent and reliable scientific evidence"; "free-of" claims must not mislead. Suggest adding phrases: eco-friendly, environment friendly, planet friendly, sustainable, biodegradable, and keeping "non-toxic". Suggest the rewrite hint say that a disclaimer will not cure an absolute claim.

### 2.6 EN-CLAIM-004 (tested or proven)

ASCI I.2 and CCPA 12(b) require the source and date of research to appear in the ad. Suggest the rewrite hint say so. Possible additional phrases: "tested by dermatologists", "dermatologist-tested", "paediatrician approved", "paediatrician recommended", "ophthalmologist tested". The consultant answers the existing open question on which terms need a report.

### 2.7 EN-CLAIM-012 (superlatives)

Add: "award-winning", "no. 1 selling", "top-rated" (ASCI awards/rankings guideline: rankings are not a substitute for research). Separately consider a comparative rule for named competitors (ASCI IV.1(a),(c),(e) denigration).

### 2.8 Fairness rules

ASCI point 1 lists things a darker-skinned person must not be shown as (unattractive, unhappy, depressed, concerned, inferior, unsuccessful, unattractive to the opposite sex, in matrimony, job placement, promotions). Point 3 bans linking skin colour to socio-economic strata, caste, community, religion, profession, ethnicity. Suggest widening EN-FAIR-003 conditions with "promotion", "attractive to men", "opposite sex", "caste", "community", "religion", "profession", and adding "unattractive", "unhappy", "depressed" near dark-skin terms (EN-FAIR-002).

### 2.9 Allowlist

- **AL-001** (disclaimers). CCPA cl.11(1)(c) and the ASCI disclaimers guideline (13 Jul 2023) say a disclaimer cannot correct a misleading claim. Suggest a test that a claim sentence next to the disclaimer still flags. The allowlist is phrase-scoped, so this likely already holds.
- **AL-002** ("whiter teeth"). Supported: "Tooth whiteners" is a separate cosmetic category (Fourth Schedule item 79).

### 2.10 Product-type gate

- D&C s.3(b)(i) puts body-applied insect repellents in the drug definition. Suggest adding hard signals: "mosquito repellent", "insect repellent", "repels mosquitoes".
- The Fourth Schedule (categories of cosmetics for import) includes skin lightening, anti hair loss, antidandruff, sun protection, hair bleaching, tooth whitening, and body-hair bleach. These are cosmetic categories, so the product types are in scope. Only the claim wording is at issue.

## 3. Gaps: claim types and regimes the draft misses

| Gap | Evidence | Suggestion |
|---|---|---|
| **Influencer / endorsement disclosure** | CCPA cl.13 (genuine opinion, adequate experience), cl.14 (material connection); ASCI influencer guidelines (disclosure labels; Addendum II: health claims need qualified influencer). | Out of v1 scope per PLAN §3, but listing copy can carry testimonials and "as recommended by". Add an orange testimonial/endorsement rule, and a note in the report. |
| **Ayurvedic / AYUSH positioning** | Gate refuses `ayurved*`. Cosmetics Rules and DMR s.14 give no Ayurvedic carve-out. Rule 170 status unclear (section 1c). | Many D&C brands use "Ayurvedic" wording. Consultant to say where the line is (question 6). |
| **Hair loss** | Fourth Schedule item 48 "Anti hair loss products"; ASCI I.5 example on baldness. DRUG-005 (red) and CLAIM-010 (orange) split the claim. | Consultant to confirm the split. Add "hair growth serum", "hair regrowth oil" product-name forms. |
| **Sunscreen** | Fourth Schedule items 42, 59. No SPF rule in the Cosmetics Rules. BIS standard in draft. | Not flagged today: "prevents sunburn", "protects from skin damage", "broad spectrum" without a stated test, "SPF" with no PA/UVA statement. Add after consultant guidance. |
| **Baby and children's products** | Ninth Schedule includes IS 5339 (infant skin powder) and IS 10523 (baby toilet soap); r.34(8) requires BIS labelling where an IS applies. CCPA cl.8 covers ads aimed at children. | CLAIM-008 covers "safe for babies" only. Add "tear-free", "no tears", "gentle for newborns", "paediatrician tested" (orange, evidence). |
| **Free claims, bait, scarcity** | CCPA cl.5 (bait; limited stock), cl.7 (free claims). | Listings use "Buy 1 Get 1 Free", "limited stock". No rule exists. |
| **Cruelty-free / animal testing** | Cosmetics Rules r.39(7) bans animal testing; r.18(4) bars import of products tested on animals after 12 Nov 2014. | "Cruelty free" claims need a basis. Orange rule suggested. |
| **Environmental claims** | ASCI green-claims guidelines (see 2.5). | Covered by the CLAIM-007 widening. |
| **Comparative advertising** | ASCI Ch. IV.1. | See 2.7. |
| **Awards and rankings** | ASCI guideline, 21 Apr 2022. | See 2.7. |
| **Mosquito repellent / drug-by-definition** | D&C s.3(b)(i). | See 2.10. |
| **Synthetically generated content labelling** | ASCI guidelines page lists "Guidelines for Responsible Labelling of Synthetically Generated Content in Advertising" (signed 17 Sep 2026; effective 3 months after publication). Only the heading and date were read. | Satya generates ad copy with an LLM. Consultant or board to say whether text copy is in scope. |
| **Legal Metrology and E-Commerce Rules declarations** | See 1c. | Audit feature "missing Legal Metrology fields" needs the correct rule number from the Gazette before it ships. |

## 4. For the consultant

1. **MIB / Supreme Court self-declaration.** Does the 7 May 2024 order (and the June 2024 portal arrangements) reach cosmetics listing copy on a brand site or marketplace? Is a cosmetic advertisement "health" for that purpose? Does Satya's brand user need a certificate before publishing?
2. **DMR Act and cosmetics.** DMR s.3 bites on ads "referring to any drug". Given s.2(b)(iii), do ordinary cosmetics count? Is the locked-red status of the DMR rules justified?
3. **DMR Schedule.** Is the 54-item Schedule current, and have any rules under s.16(2)(a) added conditions? Which of the non-Schedule conditions in EN-DMR-001 should stay red under the drug rules?
4. **Bust and height claims.** Do "bust firming/enlarging" and "height increase" cosmetic claims fall under Schedule items 21 and 47?
5. **Structure-or-function claims.** With s.3(b)(ii) limited to notified substances, which body-function claims make a cosmetic a drug in practice? Is EN-DRUG-003 correctly locked?
6. **Ayurvedic cosmetics.** What licence path lets a brand lawfully use the word "Ayurvedic" on a cosmetic? Does the gate over-refuse?
7. **Wording for imports and domestic products.** Is "CDSCO registered" acceptable for imports? What is the correct claim for a licensed domestic product?
8. **Recognised-category claims.** Anti-hair-loss, antidandruff, skin lightening and sun protection are import categories. What claim wording is acceptable for each? Is there an SPF cap? What is the status of the BIS sunscreen standard?
9. **Fairness basis.** The ASCI guideline governs depiction. Is a ban on "lightening" or "brightening" claims in a listing required by any binding rule, or is it ASCI/marketplace policy only?
10. **Marketplace banned terms.** Nykaa, Amazon, Flipkart and others keep their own prohibited-claim lists. The agent cannot contact anyone. A human needs to obtain the current policy text.
11. **Satya's own exposure.** CPA s.21(4) penalises any person who "publish[es], or is a party to the publication of" a misleading advertisement. DMR s.3 uses "take any part in the publication". Does generating or approving copy make Satya a party? What does the brand terms of service need to say?
12. **DPDP.** Is Satya a data fiduciary for brand-user account data? What must be in place before the 18-month commencement (about May 2027)? The Act and Rules text was not read.
13. **Report wording.** Is "No flagged risks under rule set vX. Not legal advice." sufficient on a brand-facing report?
14. **Overridable reds.** Should EN-CLAIM-001 (no side effects) or EN-CLAIM-005 (approval claims) be locked?
15. **AI-content labelling.** Is text copy in scope of the ASCI synthetically-generated-content guidelines?
