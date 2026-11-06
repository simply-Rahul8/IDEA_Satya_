# Satya consultant review pack: English rules (DRAFT)

- **Rule set:** satya-en v0.1.1-draft
- **Status:** DRAFT: not reviewed, not signed off
- **Content fingerprint:** 2aa67fe75bb2
- **Last updated:** 2026-11-05
- **Rules:** 24 rules, 3 safe-phrase entries, 4 product-type signals
- **Prepared for:** Cosmetics regulatory consultant (week-2 review, plan P20)

This pack is not legal advice. It is a draft for expert review.


## 1. Scope note

- What this pack covers: English claim rules for beauty product listings (title, bullets, description) and the product-type gate. It is the draft rule set the Satya engine will run.
- What it does not cover: Hindi rules (a later pack), Legal Metrology label-field checks, claims printed on packs or shown in images, marketplace-specific policies, and any product that is not a cosmetic.
- How rules match: a rule fires on a verb plus a condition in the same sentence (for example 'cures' near 'eczema'), or on a fixed phrase. A bare condition word does not fire. 'For acne-prone skin' is safe.
- Safe phrases: an allowlist stops named rules firing inside named phrases, such as a standard disclaimer.
- Severity: RED blocks approval. ORANGE needs a written reason. Non-overridable rules are always RED and cannot be overridden by anyone.
- Wording: Satya never says a listing is 'compliant'. It says 'no flagged risks under rule set vX'. This is not legal advice.
- Status: everything here is DRAFT. Nothing is shown to a brand until you sign off and the sign-off is logged in engine/rules/README.md.


## 2. What we ask of you

1. For each rule, mark Approve, Change or Remove in the decision box, and write the change.
2. Check every citation and mark it verified, or correct it.
3. Answer the open questions under each rule and the general questions at the end.
4. Sign the sign-off sheet, or say what must change before you can sign.


## 3. Rule table

| ID | Rule | Severity | Overridable | Sources |
|---|---|---|---|---|
| EN-CLAIM-001 | Absolute safety or 'no side effects' | RED | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA); Consumer Protection Act, 2019 |
| EN-CLAIM-002 | Guaranteed or permanent results | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-003 | Absolute removal or reversal of skin signs | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-004 | Tested, proven or recommended: evidence required | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA); Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020) |
| EN-CLAIM-005 | Regulator approval claims | RED | Yes | Drugs and Cosmetics Act, 1940; Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020); Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-006 | Statistics or survey results: evidence required | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-007 | Natural, organic or chemical-free absolutes | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA); Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020) |
| EN-CLAIM-008 | Safety for pregnancy, babies or all skin types | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-009 | Sun protection overstatement | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA); Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020) |
| EN-CLAIM-010 | Hair growth or hair-fall claims | ORANGE | Yes | Drugs and Cosmetics Act, 1940; ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-011 | Acne, dandruff or germ-killing efficacy claims | ORANGE | Yes | Drugs and Cosmetics Act, 1940; ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-CLAIM-012 | Superlative or 'number one' claims | ORANGE | Yes | ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA); Consumer Protection Act, 2019 |
| EN-CLAIM-013 | Fat loss or body slimming claims | ORANGE | Yes | Drugs and Cosmetics Act, 1940; ASCI Code for Self-Regulation of Advertising Content in India; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-DMR-001 | Cure, treatment or prevention of a disease listed in the DMR Act | RED | No (locked) | Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 |
| EN-DMR-002 | Miscarriage, conception, sexual pleasure or menstrual disorder claims | RED | No (locked) | Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 |
| EN-DMR-003 | Premature greying of hair | RED | No (locked) | Drugs and Cosmetics Act, 1940; Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020) |
| EN-DRUG-001 | Treatment or cure of a skin disease or medical condition | RED | No (locked) | Drugs and Cosmetics Act, 1940; Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020); Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-DRUG-002 | Prevention of disease or infection | RED | No (locked) | Drugs and Cosmetics Act, 1940; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-DRUG-003 | Claim to change a body function (hormones, immunity, circulation, metabolism) | RED | No (locked) | Drugs and Cosmetics Act, 1940 |
| EN-DRUG-004 | Prescription or medicinal product language | RED | No (locked) | Drugs and Cosmetics Act, 1940; Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020) |
| EN-DRUG-005 | Hair regrowth or reversal of hair loss | RED | No (locked) | Drugs and Cosmetics Act, 1940; Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA) |
| EN-FAIR-001 | Claim to lighten, whiten or make skin fairer | RED | No (locked) | ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products; ASCI Code for Self-Regulation of Advertising Content in India; Consumer Protection Act, 2019 |
| EN-FAIR-002 | Darker skin presented as a problem to remove or fix | RED | No (locked) | ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products; ASCI Code for Self-Regulation of Advertising Content in India |
| EN-FAIR-003 | Fair or light skin linked to success, marriage, jobs or confidence | RED | No (locked) | ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products; ASCI Code for Self-Regulation of Advertising Content in India |


## 4. Rules in detail


### Drug and treatment claims (non-overridable)

#### EN-DRUG-001: Treatment or cure of a skin disease or medical condition [RED, NON-OVERRIDABLE]

**Why it is flagged:** A cosmetic cannot claim to treat, cure or heal a disease or medical condition. Such a claim makes the product a drug.

**Rewrite direction:** Describe the cosmetic effect instead, for example 'cleanses oily skin' or 'for acne-prone skin'.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(b) definition of 'drug' (diagnosis, treatment, mitigation or prevention of disease; affecting structure or function of the body) versus s.3(aaa) definition of 'cosmetic'
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.34 (labelling) and r.36 (false or misleading claims); pin-points from the agent pre-review, to be confirmed by the consultant
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation

**Patterns:**
- Verbs: treat*, cure*, heal, heals, healed, healing, relieve*, alleviate*, remedy, remedies, mitigate*
- Conditions: acne, pimple, pimples, eczema, psoriasis, dermatitis, rosacea, infection, infections, fungal, ringworm, scabies, warts, wound, wounds, burns, rash, rashes, allergy, allergies, boils, hives, alopecia, skin disease*, skin disorder*, skin condition*, medical condition*
- Match when the two are in the same sentence, verb first, with at most 4 words between.

**Must flag (positive examples):**
- Cures eczema in just 7 days.
- This cream treats acne and pimples fast.
- Heals fungal infections of the skin.

**Must not flag (negative examples):**
- Gentle face wash for acne-prone skin.
- Cleanses oily skin without drying it out.

**Open questions:**
- Is 'soothes' or 'relieves' acceptable for visible irritation (redness, dryness) without naming a disease? The draft flags 'relieve*' only next to a named condition.
- 'Treatment' is flagged next to a condition, so 'spot treatment for acne' is red. Confirm this is the right line for 'spot treatment' products.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-DRUG-002: Prevention of disease or infection [RED, NON-OVERRIDABLE]

**Why it is flagged:** A cosmetic cannot claim to prevent disease or infection, or to protect against it. Such a claim makes the product a drug.

**Rewrite direction:** Describe what the product does to the skin's look or feel. Do not mention disease.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(b) definition of 'drug' (diagnosis, treatment, mitigation or prevention of disease; affecting structure or function of the body) versus s.3(aaa) definition of 'cosmetic'
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation

**Patterns:**
- Verbs: prevent*, protect, protects, protecting, fight, fights, fighting, combat*, kill, kills, killing
- Conditions: disease, diseases, infection, infections, illness, illnesses, virus, viruses, viral, covid, covid-19, coronavirus
- Match when the two are in the same sentence, verb first, with at most 4 words between.

**Must flag (positive examples):**
- Prevents skin infections naturally.
- Protects your family against viral infections.
- Helps prevent disease.

**Must not flag (negative examples):**
- Protects skin from dryness.
- Prevents moisture loss for 24 hours.

**Open questions:**
- Standard disclaimers such as 'not intended to diagnose, treat, cure or prevent any disease' are allowlisted (AL-001). Confirm that wording is acceptable on a listing.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-DRUG-003: Claim to change a body function (hormones, immunity, circulation, metabolism) [RED, NON-OVERRIDABLE]

**Why it is flagged:** A cosmetic cannot claim to affect how the body works internally. That is a drug claim under the 'structure or function' limb of the drug definition.

**Rewrite direction:** Limit the claim to the skin or hair surface: how it looks, feels or is cleansed.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(b) definition of 'drug' (diagnosis, treatment, mitigation or prevention of disease; affecting structure or function of the body) versus s.3(aaa) definition of 'cosmetic'

**Patterns:**
- Verbs: regulate*, balance, balances, balancing, boost, boosts, boosting, stimulate*, improve, improves, improving, increase*, lower, lowers, lowering, reduce, reduces, reducing, restore, restores, detoxify, detoxifies
- Conditions: hormone, hormones, hormonal, metabolism, immunity, immune system, blood circulation, blood flow, blood sugar, cholesterol, insulin, thyroid, bloodstream, internal organs, liver, kidney, kidneys
- Match when the two are in the same sentence, verb first, with at most 3 words between.

**Must flag (positive examples):**
- Balances hormones naturally.
- Boosts your immunity from the first use.
- Improves blood circulation in the scalp.

**Must not flag (negative examples):**
- Boosts skin radiance.
- Improves the look of skin texture.

**Open questions:**
- Scalp or body massage oils often say 'improves blood circulation'. Is that a drug claim, or accepted as a massage effect? The draft treats it as a drug claim.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-DRUG-004: Prescription or medicinal product language [RED, NON-OVERRIDABLE]

**Why it is flagged:** Words like 'medicated' or 'prescription strength' present the product as a medicine, not a cosmetic.

**Rewrite direction:** Remove the medicinal wording. Describe the formula by its ingredients and cosmetic purpose.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(b) definition of 'drug' (diagnosis, treatment, mitigation or prevention of disease; affecting structure or function of the body) versus s.3(aaa) definition of 'cosmetic'
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.34 (labelling) and r.36 (false or misleading claims); pin-points from the agent pre-review, to be confirmed by the consultant

**Patterns:**
- Phrases: prescription strength, prescription-strength, prescribed by doctors, prescribed by dermatologists, doctor prescribed, doctor-prescribed, dermatologist prescribed, dermatologist-prescribed, medicated, is a medicine, acts as a medicine, works like a medicine, pharmaceutical grade, pharmaceutical-grade

**Must flag (positive examples):**
- Doctor-prescribed strength anti-acne gel.
- Medicated shampoo for the scalp.
- Prescription strength formula.

**Must not flag (negative examples):**
- Gentle daily moisturiser for dry skin.
- Contains herbal extracts.

**Open questions:**
- Should 'medicinal herbs' or 'dermatologist-formulated' be allowlisted? The draft flags neither.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-DRUG-005: Hair regrowth or reversal of hair loss [RED, NON-OVERRIDABLE]

**Why it is flagged:** Claiming to regrow hair or reverse hair loss is a treatment claim (the reference product for this effect is a drug).

**Rewrite direction:** Talk about the look and feel of existing hair, for example 'nourishes hair' or 'helps hair feel fuller'.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(b) definition of 'drug' (diagnosis, treatment, mitigation or prevention of disease; affecting structure or function of the body) versus s.3(aaa) definition of 'cosmetic'
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation

**Patterns:**
- Verbs: regrow*, re-grow*, regenerate*, revive*, reactivate*
- Conditions: hair, hairs, follicle, follicles, hair follicles
- Match when the two are in the same sentence, verb first, with at most 3 words between.
- Phrases: hair regrowth, hair re-growth, new hair growth, reverse hair loss, reverses hair loss, reverse baldness, reverses baldness

**Must flag (positive examples):**
- Regrow hair in 30 days.
- Clinically visible hair regrowth.
- Reactivates dormant hair follicles.

**Must not flag (negative examples):**
- Nourishes hair from root to tip.
- Leaves hair feeling fuller and softer.

**Open questions:**
- 'Promotes hair growth' and 'reduces hair fall' are handled as overridable orange claims (EN-CLAIM-010). Confirm they belong there and not here.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______


### Drugs and Magic Remedies Act diseases and conditions (non-overridable)

#### EN-DMR-001: Cure, treatment or prevention of a disease listed in the DMR Act [RED, NON-OVERRIDABLE]

**Why it is flagged:** Advertising a product as treating, curing or preventing a disease named in the Drugs and Magic Remedies Act is prohibited.

**Rewrite direction:** Remove the disease. A cosmetic listing cannot refer to these conditions.

**Sources (UNVERIFIED unless marked):**
- Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954, s.3(d) and the Schedule (diseases, disorders and conditions)

**Patterns:**
- Verbs: cure*, treat*, heal, heals, healed, healing, prevent*, reverse*, reversing, relieve*, alleviate*, mitigate*, eliminate*, fight, fights, fighting, combat*, remedy, remedies, diagnos*, manage, manages, managing, control, controls, controlling, help, helps, helping
- Conditions: diabet*, cancer, cancers, cancerous, cataract*, glaucoma, epilepsy, epileptic, paralysis, leprosy, leucoderma, vitiligo, tuberculosis, tb, asthma, asthmatic, bronchial, hypertension, hypotension, blood pressure, bp, heart disease*, heart attack*, cardiac, arteriosclerosis, jaundice, goitre, goiter, hernia, rheumatism, rheumatic, arthritis, deafness, blindness, hysteria, insanity, appendicitis, lupus, impotence, impotency, sterility, infertility, varicose, gallstones, gall bladder stones, kidney stones, bladder stones, venereal, syphilis, gonorrhoea, sexually transmitted, stds, hiv, fever, fevers, malaria, dengue, typhoid, hepatitis, cirrhosis, piles, hemorrhoids, ulcer, ulcers, blood poisoning, baldness, obesity
- Match when the two are in the same sentence, verb first, with at most 4 words between.
- Verbs: for
- Conditions: diabet*, cancer, cancers, cancerous, cataract*, glaucoma, epilepsy, epileptic, paralysis, leprosy, leucoderma, vitiligo, tuberculosis, tb, asthma, asthmatic, bronchial, hypertension, hypotension, blood pressure, bp, heart disease*, heart attack*, cardiac, arteriosclerosis, jaundice, goitre, goiter, hernia, rheumatism, rheumatic, arthritis, deafness, blindness, hysteria, insanity, appendicitis, lupus, impotence, impotency, sterility, infertility, varicose, gallstones, gall bladder stones, kidney stones, bladder stones, venereal, syphilis, gonorrhoea, sexually transmitted, stds, hiv, fever, fevers, malaria, dengue, typhoid, hepatitis, cirrhosis, piles, hemorrhoids, ulcer, ulcers, blood poisoning, baldness, obesity
- Match when the two are in the same sentence, verb first, with at most 2 words between.

**Must flag (positive examples):**
- Cures diabetes naturally.
- Helps in controlling high blood pressure.
- Our oil is good for cancer patients.
- Treatment for leucoderma at home.

**Must not flag (negative examples):**
- Rich moisturiser for dry skin.
- A daily cream that helps skin feel soft.

**Open questions:**
- Verify the condition list against the current Schedule text and any amendment since 2020. Add or remove items.
- Items such as 'baldness' and 'obesity' are included from memory and are NOT confirmed to be in the Schedule. Confirm or drop them.
- Is 'for <disease>' (e.g. 'for diabetic feet') always a violation, or only when it suggests treatment?

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-DMR-002: Miscarriage, conception, sexual pleasure or menstrual disorder claims [RED, NON-OVERRIDABLE]

**Why it is flagged:** Advertising a product for miscarriage, conception, sexual pleasure or correcting menstrual disorder is prohibited under the DMR Act.

**Rewrite direction:** Remove the claim. If the product is intimate hygiene, describe cleansing only.

**Sources (UNVERIFIED unless marked):**
- Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954, s.3(a), (b), (c): miscarriage and conception, sexual pleasure, menstrual disorder

**Patterns:**
- Verbs: improve*, enhance*, boost*, increase*, restore*, correct*, regulate*, induce*, prevent*, cure*, treat*, help, helps, helping, for
- Conditions: sexual pleasure, sexual performance, sexual stamina, sexual desire, libido, virility, erectile, menstrual disorder*, menstrual problems, irregular periods, miscarriage, conception, contraception, foetus, fetus
- Match when the two are in the same sentence, verb first, with at most 3 words between.

**Must flag (positive examples):**
- Boosts sexual stamina and performance.
- Corrects menstrual disorders naturally.
- Helps prevent conception.

**Must not flag (negative examples):**
- Gentle intimate wash for daily external use.
- Soothing body oil for a relaxing massage.

**Open questions:**
- Are intimate-wash listings that mention 'feminine freshness' acceptable? The draft does not flag them.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-DMR-003: Premature greying of hair [RED, NON-OVERRIDABLE]

**Why it is flagged:** Claims to treat or reverse premature greying of hair are drug claims. Premature greying is not listed in the DMR Act Schedule; the basis is the Drugs and Cosmetics Act s.3(b)(i) and rule 36 of the Cosmetics Rules, 2020.

**Rewrite direction:** Remove the claim. A hair colour product may describe covering grey hair as a colouring effect.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(b)(i) definition of 'drug' (treatment, mitigation or prevention of disease). Cited for EN-DMR-003 because premature greying is not in the DMR Schedule
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.36 (false or misleading claims). Cited for EN-DMR-003 with D&C Act s.3(b)(i)

**Patterns:**
- Verbs: cure*, treat*, prevent*, reverse*, stop*, reduce*, delay*, restore*, fix*
- Conditions: premature greying, premature graying, premature grey, premature gray, greying, graying, grey hair, gray hair, white hair
- Match when the two are in the same sentence, verb first, with at most 3 words between.

**Must flag (positive examples):**
- Prevents premature greying of hair.
- Reverses grey hair naturally.

**Must not flag (negative examples):**
- Hair colour that covers grey hair in 10 minutes.
- Shampoo for coloured hair.

**Open questions:**
- Premature greying is not in the DMR Act Schedule (agent pre-review 2.2). The draft keeps this rule red and non-overridable on the basis of D&C Act s.3(b)(i) and r.36 Cosmetics Rules 2020. Should it stay locked, or move to an overridable claim? (pre-review section 4, Q2 and Q3). This is a consultant decision.
- Does 'covers grey hair' for a colour product need an allowlist entry? The draft does not flag 'covers'.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______


### Fairness and skin colour (non-overridable)

#### EN-FAIR-001: Claim to lighten, whiten or make skin fairer [RED, NON-OVERRIDABLE]

**Why it is flagged:** Claims that a product makes skin fairer, lighter or whiter are blocked. They imply lighter skin is better and are not allowed in listings.

**Rewrite direction:** Describe the care benefit instead, for example 'helps skin look even and radiant' or 'visibly fades the look of dark spots'.

**Sources (UNVERIFIED unless marked):**
- ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products, advertisements must not depict darker skin as inferior or link skin colour to success; edition in force to be confirmed
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter III (advertisements must not offend against public decency or portray groups adversely); clause numbers to be confirmed
- Consumer Protection Act, 2019, s.2(28) misleading advertisement; s.21 powers of the Central Consumer Protection Authority

**Patterns:**
- Verbs: whiten*, lighten*
- Conditions: skin, complexion, tone, skintone, colour, color, face, body, underarm, underarms, neck
- Match when the two are in the same sentence, verb first, with at most 2 words between.
- Verbs: make, makes, making, get, gets, getting, become, becomes, turn, turns, achieve, achieving
- Conditions: fair, fairer, fairest, whiter
- Match when the two are in the same sentence, verb first, with at most 5 words between.
- Phrases: fairness, fairer skin, whiter skin, skin whitening, skin lightening, skin-whitening, skin-lightening, whitening cream, whitening serum, whitening lotion, whitening soap, whitening face wash, whitening mask

**Must flag (positive examples):**
- Whitens your skin in 7 days.
- Get fairer skin with saffron.
- A fairness cream for glowing faces.
- Skin whitening serum with vitamin C.
- Lightens skin tone visibly.

**Must not flag (negative examples):**
- Foundation in 24 shades from fair to deep.
- Fades the look of dark spots for a more even finish.
- Brightening vitamin C serum for dull skin.

**Open questions:**
- Is 'brightening' acceptable when it does not mention skin colour? The draft allows it. Please confirm, and say whether 'glow' and 'radiance' are also fine.
- Is 'lightens dark spots / pigmentation' acceptable? The draft allows it because it does not name skin colour.
- Face bleach and underarm lightening products: flag, allow, or flag only with colour claims? The draft flags 'lighten* underarm'.
- Foundation shade names and ranges ('fair', 'fairest', 'fair to deep') are treated as shade description and allowed (AL-003). Confirm.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-FAIR-002: Darker skin presented as a problem to remove or fix [RED, NON-OVERRIDABLE]

**Why it is flagged:** Presenting dark or dusky skin as a problem to fix or remove is blocked. It portrays darker skin as inferior.

**Rewrite direction:** Describe the care benefit without referring to skin colour as a flaw.

**Sources (UNVERIFIED unless marked):**
- ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products, advertisements must not depict darker skin as inferior or link skin colour to success; edition in force to be confirmed
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter III (advertisements must not offend against public decency or portray groups adversely); clause numbers to be confirmed

**Patterns:**
- Verbs: remove*, eliminate*, get rid of, fix, fixes, fixing, correct*, cure*, treat*, say goodbye to, bye bye, hide*, end, ends
- Conditions: dark skin, dusky skin, dark complexion, dusky complexion, dark skin tone, dusky, dark-skinned
- Match when the two are in the same sentence, verb first, with at most 2 words between.

**Must flag (positive examples):**
- Say goodbye to dark skin.
- Fixes dusky skin tone.
- Get rid of dark complexion.

**Must not flag (negative examples):**
- Foundation shades for dark skin tones.
- Removes dark circles under the eyes.

**Open questions:**
- Is 'dark circles' and 'dark spots' always out of this rule? The draft does not treat them as skin colour.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-FAIR-003: Fair or light skin linked to success, marriage, jobs or confidence [RED, NON-OVERRIDABLE]

**Why it is flagged:** Linking fair or light skin to marriage, a job, success or confidence is blocked. It implies skin colour decides life outcomes.

**Rewrite direction:** Remove the link between skin colour and the life outcome.

**Sources (UNVERIFIED unless marked):**
- ASCI Guidelines for Advertisements for Skin Lightening or Fairness Products, advertisements must not depict darker skin as inferior or link skin colour to success; edition in force to be confirmed
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter III (advertisements must not offend against public decency or portray groups adversely); clause numbers to be confirmed

**Patterns:**
- Verbs: fair skin, fairer skin, fairness, whiter skin, lighter skin, light skin, fair complexion, fair face
- Conditions: marriage, wedding, groom, bride, husband, boyfriend, job, career, success, successful, confidence, confident, popular, popularity, get married, interview, rishta
- Match when the two are in the same sentence, in either order, with at most 5 words between.

**Must flag (positive examples):**
- Fair skin for a perfect wedding day.
- Fairness that wins you a better job.
- Be more confident with lighter skin.

**Must not flag (negative examples):**
- Wedding day radiance kit for all skin tones.
- Confidence in every shade.

**Open questions:**
- Should 'fair skin tones' in a make-up shade context near 'wedding' ever be flagged? The draft flags only close pairs (up to 5 words apart).

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______


### Cosmetic claims (overridable)

#### EN-CLAIM-001: Absolute safety or 'no side effects' [RED, overridable]

**Why it is flagged:** Absolute safety claims cannot be backed up for a cosmetic. They are misleading unless you hold evidence.

**Rewrite direction:** Say what is in or out of the formula, for example 'free from parabens', and avoid promising safety.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements
- Consumer Protection Act, 2019, s.2(28) misleading advertisement

**Patterns:**
- Phrases: 100 safe, 100 percent safe, completely safe, totally safe, absolutely safe, guaranteed safe, zero side effects, no side effects, no side-effects, side effect free, side-effect free, side-effects free, without side effects, without any side effects, risk free, risk-free, harmless, safe for everyone

**Must flag (positive examples):**
- 100% safe for all.
- Absolutely safe with zero side effects.

**Must not flag (negative examples):**
- Free from parabens and sulphates.
- Dermatologist-formulated gentle cleanser.

**Open questions:**
- Should 'no side effects' be non-overridable? The draft keeps it overridable with evidence.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-002: Guaranteed or permanent results [ORANGE, overridable]

**Why it is flagged:** Guaranteed or permanent results cannot be promised for a cosmetic. Results vary and fade.

**Rewrite direction:** Say what users may notice and over what period, for example 'visible results with regular use'.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Verbs: guarantee, guarantees, guaranteed, guaranteeing
- Conditions: result, results, effect, effects, outcome, outcomes, improvement, growth, glow, removal, reduction
- Match when the two are in the same sentence, verb first, with at most 2 words between.
- Verbs: permanent, permanently, forever, for life, lifelong, lifetime
- Conditions: result, results, removal, remove, removes, reduction, fix, cure, wrinkle, wrinkles, scars, dark circles, pigmentation, spots, marks, glow
- Match when the two are in the same sentence, in either order, with at most 3 words between.

**Must flag (positive examples):**
- Guaranteed results in 7 days.
- Permanent hair removal at home.
- Removes wrinkles permanently.

**Must not flag (negative examples):**
- Visible results with regular use.
- A long-lasting matte finish.

**Open questions:**
- Is 'long-lasting' alone acceptable for make-up wear time? The draft allows it.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-003: Absolute removal or reversal of skin signs [ORANGE, overridable]

**Why it is flagged:** Claims to remove or erase wrinkles, spots, scars or fat are overstated for a cosmetic. Use 'reduces the look of'.

**Rewrite direction:** Use 'visibly reduces the appearance of ...' and keep it to what a cosmetic can show.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Verbs: remove, removes, removing, erase*, eliminate*, banish*, get rid of, gets rid of, vanish*, reverse*, wipe out, wipes out
- Conditions: wrinkle, wrinkles, fine lines, dark circles, dark spots, pigmentation, scar, scars, scarring, stretch marks, age spots, pores, blemish, blemishes, cellulite, ageing, aging, signs of ageing, signs of aging
- Match when the two are in the same sentence, verb first, with at most 3 words between.

**Must flag (positive examples):**
- Erases wrinkles overnight.
- Removes dark spots and pigmentation.
- Reverse ageing with this cream.

**Must not flag (negative examples):**
- Visibly reduces the appearance of fine lines.
- Removes makeup and impurities gently.

**Open questions:**
- Is 'reduces the appearance of ...' always safe? The draft allows it as the preferred rewrite.
- 'Anti-ageing' as a product type is not flagged. Confirm.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-004: Tested, proven or recommended: evidence required [ORANGE, overridable]

**Why it is flagged:** Claims like 'clinically proven' or 'dermatologically tested' need evidence you can show. A test report must have a reference (file or document ID).

**Rewrite direction:** Keep the claim only if you hold the test report, and cite what was tested. Otherwise drop it.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.34 (labelling) and r.36 (false or misleading claims); pin-points from the agent pre-review, to be confirmed by the consultant

**Patterns:**
- Phrases: clinically proven, clinically tested, clinically approved, clinically shown, clinically effective, clinically verified, dermatologically tested, dermatologically proven, dermatologically approved, dermatologist tested, dermatologist approved, dermatologist recommended, dermatologist-recommended, recommended by dermatologists, approved by dermatologists, doctor recommended, doctor approved, recommended by doctors, scientifically proven, scientifically tested, lab tested, lab-tested, laboratory tested, patch tested, allergy tested, hypoallergenic, non-comedogenic, noncomedogenic, non comedogenic

**Must flag (positive examples):**
- Clinically proven to hydrate.
- Dermatologically tested and hypoallergenic.
- Recommended by dermatologists.

**Must not flag (negative examples):**
- Developed for everyday hydration.
- Made with hyaluronic acid.

**Open questions:**
- Which of these terms need a test report, and which need only a statement of how the test was done?
- Is 'dermatologist-formulated' (not tested) treated as a claim? The draft does not flag it.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-005: Regulator approval claims [RED, overridable]

**Why it is flagged:** Cosmetics are registered, not approved, by the regulator. 'FDA approved' or 'CDSCO approved' is misleading.

**Rewrite direction:** If you hold a registration, state the registration number, not 'approved'.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(aaa) definition of 'cosmetic'; s.3(b) definition of 'drug'
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.34 (labelling) and r.36 (false or misleading claims); pin-points from the agent pre-review, to be confirmed by the consultant
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Phrases: fda approved, fda-approved, cdsco approved, cdsco-approved, approved by fda, approved by cdsco, government approved, govt approved, approved by the government

**Must flag (positive examples):**
- FDA approved formula.
- CDSCO-approved sunscreen.

**Must not flag (negative examples):**
- Registered with CDSCO, registration number on pack.
- Made in a GMP-certified facility.

**Open questions:**
- Is 'CDSCO registered' acceptable on a listing? The draft allows it.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-006: Statistics or survey results: evidence required [ORANGE, overridable]

**Why it is flagged:** Percentages of users or '9 out of 10' claims need a study you can show, with the sample and method.

**Rewrite direction:** Cite the study (sample size, method, date) or remove the number.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Regular expression: \b\d{1,3}(?:\.\d+)?\s?%\s+(?:of\s+)?(?:\w+\s+){0,2}?(?:users|women|men|people|customers|participants|respondents|volunteers|consumers)\b
- Regular expression: \b\d{1,3}\s+(?:out\s+of|in)\s+\d{1,3}\s+(?:users|women|men|people|customers|consumers|dermatologists|doctors)\b
- Regular expression: \b\d{1,3}(?:\.\d+)?\s?%\s+(?:saw|reported|noticed|agreed|felt|showed|experienced|reduction|improvement|increase)\b

**Must flag (positive examples):**
- 93% of women saw smoother skin.
- 9 out of 10 users agree.
- 87% reduction in wrinkles.

**Must not flag (negative examples):**
- Contains 2% niacinamide.
- Available in 3 sizes.

**Open questions:**
- Do ingredient percentages ('10% vitamin C') need their own rule? The draft does not flag them.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-007: Natural, organic or chemical-free absolutes [ORANGE, overridable]

**Why it is flagged:** '100% natural' and 'chemical-free' are not accurate for a formulated product and need a basis. 'Certified organic' needs a certificate.

**Rewrite direction:** Name the natural ingredients, or say 'made with plant-derived ingredients'.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.34 (labelling) and r.36 (false or misleading claims); pin-points from the agent pre-review, to be confirmed by the consultant

**Patterns:**
- Phrases: 100 natural, 100 percent natural, 100 organic, 100 pure, chemical free, chemical-free, free from chemicals, free of chemicals, free from all chemicals, toxin free, toxin-free, non toxic, non-toxic, nontoxic, certified organic, organic certified

**Must flag (positive examples):**
- 100% natural face oil.
- A chemical-free sunscreen.
- Certified organic extracts.

**Must not flag (negative examples):**
- Made with plant-derived ingredients.
- Free from parabens and sulphates.

**Open questions:**
- Is a bare 'natural' or 'organic' (without 100% or 'certified') a claim that needs evidence? The draft does not flag it.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-008: Safety for pregnancy, babies or all skin types [ORANGE, overridable]

**Why it is flagged:** Claims that a product is safe for pregnancy, babies or all skin types need testing evidence. Do not state them without it.

**Rewrite direction:** Say 'ask your doctor if pregnant' or describe the testing done.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Phrases: safe for pregnancy, safe during pregnancy, safe in pregnancy, pregnancy safe, pregnancy-safe, safe for pregnant women, safe for breastfeeding, safe for babies, baby safe, baby-safe, safe for infants, safe for newborns, safe for children, safe for kids, safe for all skin types, safe for all ages, safe for sensitive skin

**Must flag (positive examples):**
- Pregnancy-safe body butter.
- Safe for babies and kids.
- Safe for all skin types.

**Must not flag (negative examples):**
- Suitable for daily use.
- Gentle on the skin.

**Open questions:**
- Is 'suitable for all skin types' (without 'safe') acceptable? The draft allows it.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-009: Sun protection overstatement [ORANGE, overridable]

**Why it is flagged:** 'Total' or 'complete' sun protection, SPF above 100, or 'sweatproof' sunscreen overstates what a sunscreen can do.

**Rewrite direction:** State the tested SPF and PA rating, and say 'water resistant' only if tested.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements
- Cosmetics Rules, 2020 (G.S.R. 763(E), 15 Dec 2020), r.36 (false or misleading claims). The Rules have no SPF or sunscreen provision; r.36 applies only generically

**Patterns:**
- Phrases: total sun protection, complete sun protection, full sun protection, blocks all uv, blocks 100 uv, 100 uv protection, sunproof, sweatproof sunscreen, waterproof sunscreen
- Regular expression: \bspf[\s-]*[1-9]\d{2,}\b

**Must flag (positive examples):**
- Total sun protection all day.
- SPF 200 sunscreen.
- Waterproof sunscreen for the beach.

**Must not flag (negative examples):**
- SPF 50 PA++++ sunscreen.
- Water resistant for up to 40 minutes.

**Open questions:**
- What are the SPF and PA labelling and testing requirements for India, and do they cap the SPF that may be stated?

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-010: Hair growth or hair-fall claims [ORANGE, overridable]

**Why it is flagged:** Hair growth and hair-fall claims sit close to drug claims. They need evidence and careful wording.

**Rewrite direction:** Say 'nourishes hair' or 'reduces breakage' and keep to what the product can show.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(aaa) definition of 'cosmetic'; s.3(b) definition of 'drug'
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Verbs: promote*, boost*, stimulate*, accelerate*, speed up, increase*, enhance*
- Conditions: hair growth, hair thickness, hair density, new hair
- Match when the two are in the same sentence, verb first, with at most 3 words between.
- Phrases: stops hair fall, stop hair fall, stops hair loss, stop hair loss, prevents hair fall, prevent hair fall, prevents hair loss, prevent hair loss, reduces hair fall, reduce hair fall, reduces hair loss, hair fall control, hair fall treatment, hair loss treatment, anti hair fall, anti-hair fall

**Must flag (positive examples):**
- Promotes hair growth.
- Stops hair fall in 2 weeks.
- An anti hair fall oil.

**Must not flag (negative examples):**
- Nourishes hair from root to tip.
- Helps reduce breakage.

**Open questions:**
- Where is the line between a cosmetic hair-fall claim and a drug claim? Which of these should be red or non-overridable?

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-011: Acne, dandruff or germ-killing efficacy claims [ORANGE, overridable]

**Why it is flagged:** Claims to clear acne or dandruff, or to kill germs, are efficacy claims that need evidence and sit close to drug claims.

**Rewrite direction:** Say 'cleanses excess oil' or 'for acne-prone skin' and avoid efficacy words.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(aaa) definition of 'cosmetic'; s.3(b) definition of 'drug'
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Verbs: clear, clears, clearing, eliminate*, get rid of, gets rid of, kill, kills, killing, fight, fights, fighting, control, controls, reduce, reduces, reducing, remove, removes, removing
- Conditions: acne, pimple, pimples, dandruff, breakouts, blackheads, whiteheads, bacteria, germs, fungus
- Match when the two are in the same sentence, verb first, with at most 3 words between.

**Must flag (positive examples):**
- Clears pimples overnight.
- Kills 99.9% germs.
- Fights acne-causing bacteria.
- Removes dandruff from the first wash.

**Must not flag (negative examples):**
- Gentle cleanser for acne-prone skin.
- Cleanses excess oil that can clog pores.

**Open questions:**
- Anti-dandruff shampoos are common cosmetic listings. Is 'removes dandruff' acceptable on a shampoo? Do 'antibacterial' soaps need their own treatment?

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-012: Superlative or 'number one' claims [ORANGE, overridable]

**Why it is flagged:** 'Number one' and 'best in India' claims need proof, such as a named survey or ranking.

**Rewrite direction:** Cite the ranking (source, period) or use a factual description.

**Sources (UNVERIFIED unless marked):**
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements
- Consumer Protection Act, 2019, s.2(28) misleading advertisement

**Patterns:**
- Phrases: number 1, number one, no 1, world's best, worlds best, india's best, best in india, best in the world, best in class, unbeatable, unmatched, better than all, better than any, nothing works better, no other product

**Must flag (positive examples):**
- India's No. 1 face wash.
- The world's best sunscreen.
- Better than any other cream.

**Must not flag (negative examples):**
- A gentle everyday face wash.
- Loved by customers across India.

**Open questions:**
- Is 'bestselling' acceptable without proof? The draft does not flag it.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______

#### EN-CLAIM-013: Fat loss or body slimming claims [ORANGE, overridable]

**Why it is flagged:** Claims to burn fat or reduce weight or inches are not cosmetic effects. They need evidence and sit close to drug claims.

**Rewrite direction:** Describe skin feel, such as 'firming body lotion'. Do not mention fat or weight.

**Sources (UNVERIFIED unless marked):**
- Drugs and Cosmetics Act, 1940, s.3(aaa) definition of 'cosmetic'; s.3(b) definition of 'drug'
- ASCI Code for Self-Regulation of Advertising Content in India, Chapter I (truthful and honest representation, claim substantiation); clause numbers to be confirmed
- Guidelines for Prevention of Misleading Advertisements and Endorsements for Misleading Advertisements, 2022 (CCPA), misleading advertisement; claim substantiation; endorsements

**Patterns:**
- Verbs: burn, burns, burning, melt, melts, melting, dissolve*, reduce, reduces, reducing, lose, shrink*, slim, slims
- Conditions: fat, belly fat, belly, cellulite, inches, weight, tummy, thighs
- Match when the two are in the same sentence, verb first, with at most 3 words between.

**Must flag (positive examples):**
- Burns belly fat while you sleep.
- Melts cellulite and reduces inches.

**Must not flag (negative examples):**
- Firming body lotion with caffeine.
- Lightweight lotion that absorbs quickly.

**Open questions:**
- Are 'slimming' and 'firming' body products acceptable? The draft flags only fat, weight and inch claims.

**Reviewer decision:** [ ] Approve  [ ] Change  [ ] Remove. Notes: ______


## 5. Safe-phrase allowlist

Inside these phrases the named rules do not fire. Entries that touch a non-overridable rule are marked LOCKED RULE: please look at these closely.

| ID | Phrases | Applies to | Why |
|---|---|---|---|
| AL-001 | not intended to diagnose treat cure or prevent any disease; not intended to diagnose treat or cure any disease; not meant to diagnose treat cure or prevent any disease; does not claim to treat cure or prevent any disease; does not treat cure or prevent any disease; this product does not treat or cure any disease | EN-DRUG-001, EN-DRUG-002, EN-DMR-001  (LOCKED RULE) | Standard negative disclaimer. It denies the drug claim, so it must not be flagged as one. |
| AL-002 | whiter teeth; whiter smile | EN-FAIR-001  (LOCKED RULE) | Teeth whitening is not skin lightening. |
| AL-003 | fairest shade; fairest shades | EN-FAIR-001  (LOCKED RULE) | Foundation shade range description, not a skin-colour change. |


## 6. Product-type gate

Satya v1 handles cosmetics only. Ayurvedic, AYUSH, OTC-drug and supplement products are refused with an explanation. The gate reads the listing text and the brand's declared type. It cannot verify a licence. Hard signals refuse the product. Weak signals ask for a review, or pass when the brand declares the product a cosmetic.


### OTC or prescription drug (otc_drug)

- **Hard signals (refuse):** otc, over the counter, over-the-counter, prescription only, rx only, schedule h, schedule g, drug licence, drug license, minoxidil, ketoconazole, clotrimazole, miconazole, terbinafine, fluconazole, hydrocortisone, clobetasol, betamethasone, mometasone, tretinoin, adapalene, isotretinoin, clindamycin, mupirocin, benzoyl peroxide, hydroquinone, povidone iodine, povidone-iodine, permethrin, ivermectin, lidocaine, benzocaine, paracetamol, ibuprofen, diclofenac, antiseptic, antibiotic, antifungal, analgesic, pain relief, pain relieving, pain reliever
- **Weak signals (review):** ointment, medicinal, herbal remedy, remedy
- **Explanation shown:** This looks like a drug (for example it names a drug ingredient or says OTC, antiseptic or pain relief). Drugs are regulated differently from cosmetics, so Satya v1 does not review or write listings for them.

**Refused:**
- Minoxidil 5% solution for the scalp.
- OTC antifungal cream.
**Passes:**
- Vitamin C face serum.
- Moisturising cream with shea butter.


### AYUSH product (ayush)

- **Hard signals (refuse):** ayush, siddha, unani, homeopathic, homoeopathic, homeopathy, homoeopathy, asu drug
- **Weak signals (review):** none
- **Explanation shown:** This looks like an AYUSH product (Ayurveda, Yoga, Unani, Siddha, Homeopathy). Those products have their own regulator and rules, so Satya v1 does not review or write listings for them.

**Refused:**
- AYUSH licensed herbal oil.
- Unani hair tonic.
**Passes:**
- Gentle face wash with aloe.
- Hair oil with coconut and curry leaf.


### Ayurvedic product (ayurvedic)

- **Hard signals (refuse):** ayurved*
- **Weak signals (review):** ayurveda-inspired, ayurvedic-inspired, ayurveda inspired, inspired by ayurveda, inspired by ayurvedic, rooted in ayurveda, ayurvedic principles, ayurvedic wisdom, ayurveda principles, ancient ayurvedic
- **Explanation shown:** This product is described as Ayurvedic. Ayurvedic products are regulated as AYUSH drugs, not cosmetics, so Satya v1 does not review or write listings for them. If the product is a cosmetic that is only inspired by Ayurveda, declare it as a cosmetic and remove the Ayurvedic wording.

**Refused:**
- Kumkumadi Ayurvedic face oil.
- Classical Ayurveda formulation.
**Passes:**
- Face oil with saffron and sesame.
- Nourishing hair mask.


### Supplement, food or other non-cosmetic product (other_non_cosmetic)

- **Hard signals (refuse):** dietary supplement, health supplement, food supplement, nutraceutical, nutraceuticals, fssai, multivitamin, protein powder, collagen powder, gummy, gummies, capsule, capsules, tablet, tablets, softgel, softgels, syrup, medical device
- **Weak signals (review):** none
- **Explanation shown:** This looks like a supplement, food or other non-cosmetic product. Satya v1 reviews cosmetics only.

**Refused:**
- Biotin hair gummies.
- Collagen powder with vitamin C.
**Passes:**
- Lip balm with beeswax.
- Body lotion with vitamin E.


## 7. Open questions

General questions:

1. Citations: every citation below is marked UNVERIFIED. It was drafted without access to the primary texts. Please check each Act, Rule, Schedule and guideline reference, and give the correct section or rule number where it is wrong.
2. Severity and overridability: is the split right between what can never be overridden (drug and treatment, DMR Act diseases, fairness) and what a brand may override with a reason or evidence? Should any overridable rule be locked, or any locked rule be opened?
3. Coverage: which common claims in Indian beauty listings are missing from this rule set?
4. False positives: which examples that we treat as safe would you flag, and which flagged examples would you accept?
5. Ayurveda-inspired cosmetics: the gate refuses any product described as Ayurvedic and asks for review when the wording is only 'inspired by Ayurveda'. Is that the right line? What evidence separates an Ayurvedic drug from a cosmetic with herbal ingredients?
6. Report wording: is 'No flagged risks under rule set vX. Not legal advice.' acceptable on a brand-facing report, and is there any wording that must be added?
7. Out-of-scope product types: confirm that supplements, foods, OTC drugs and AYUSH products must all be refused in v1.

Rule-specific questions (33), repeated here as a checklist:

| Rule | Question | Your answer |
|---|---|---|
| EN-CLAIM-001 | Should 'no side effects' be non-overridable? The draft keeps it overridable with evidence. |  |
| EN-CLAIM-002 | Is 'long-lasting' alone acceptable for make-up wear time? The draft allows it. |  |
| EN-CLAIM-003 | Is 'reduces the appearance of ...' always safe? The draft allows it as the preferred rewrite. |  |
| EN-CLAIM-003 | 'Anti-ageing' as a product type is not flagged. Confirm. |  |
| EN-CLAIM-004 | Which of these terms need a test report, and which need only a statement of how the test was done? |  |
| EN-CLAIM-004 | Is 'dermatologist-formulated' (not tested) treated as a claim? The draft does not flag it. |  |
| EN-CLAIM-005 | Is 'CDSCO registered' acceptable on a listing? The draft allows it. |  |
| EN-CLAIM-006 | Do ingredient percentages ('10% vitamin C') need their own rule? The draft does not flag them. |  |
| EN-CLAIM-007 | Is a bare 'natural' or 'organic' (without 100% or 'certified') a claim that needs evidence? The draft does not flag it. |  |
| EN-CLAIM-008 | Is 'suitable for all skin types' (without 'safe') acceptable? The draft allows it. |  |
| EN-CLAIM-009 | What are the SPF and PA labelling and testing requirements for India, and do they cap the SPF that may be stated? |  |
| EN-CLAIM-010 | Where is the line between a cosmetic hair-fall claim and a drug claim? Which of these should be red or non-overridable? |  |
| EN-CLAIM-011 | Anti-dandruff shampoos are common cosmetic listings. Is 'removes dandruff' acceptable on a shampoo? Do 'antibacterial' soaps need their own treatment? |  |
| EN-CLAIM-012 | Is 'bestselling' acceptable without proof? The draft does not flag it. |  |
| EN-CLAIM-013 | Are 'slimming' and 'firming' body products acceptable? The draft flags only fat, weight and inch claims. |  |
| EN-DMR-001 | Verify the condition list against the current Schedule text and any amendment since 2020. Add or remove items. |  |
| EN-DMR-001 | Items such as 'baldness' and 'obesity' are included from memory and are NOT confirmed to be in the Schedule. Confirm or drop them. |  |
| EN-DMR-001 | Is 'for <disease>' (e.g. 'for diabetic feet') always a violation, or only when it suggests treatment? |  |
| EN-DMR-002 | Are intimate-wash listings that mention 'feminine freshness' acceptable? The draft does not flag them. |  |
| EN-DMR-003 | Premature greying is not in the DMR Act Schedule (agent pre-review 2.2). The draft keeps this rule red and non-overridable on the basis of D&C Act s.3(b)(i) and r.36 Cosmetics Rules 2020. Should it stay locked, or move to an overridable claim? (pre-review section 4, Q2 and Q3). This is a consultant decision. |  |
| EN-DMR-003 | Does 'covers grey hair' for a colour product need an allowlist entry? The draft does not flag 'covers'. |  |
| EN-DRUG-001 | Is 'soothes' or 'relieves' acceptable for visible irritation (redness, dryness) without naming a disease? The draft flags 'relieve*' only next to a named condition. |  |
| EN-DRUG-001 | 'Treatment' is flagged next to a condition, so 'spot treatment for acne' is red. Confirm this is the right line for 'spot treatment' products. |  |
| EN-DRUG-002 | Standard disclaimers such as 'not intended to diagnose, treat, cure or prevent any disease' are allowlisted (AL-001). Confirm that wording is acceptable on a listing. |  |
| EN-DRUG-003 | Scalp or body massage oils often say 'improves blood circulation'. Is that a drug claim, or accepted as a massage effect? The draft treats it as a drug claim. |  |
| EN-DRUG-004 | Should 'medicinal herbs' or 'dermatologist-formulated' be allowlisted? The draft flags neither. |  |
| EN-DRUG-005 | 'Promotes hair growth' and 'reduces hair fall' are handled as overridable orange claims (EN-CLAIM-010). Confirm they belong there and not here. |  |
| EN-FAIR-001 | Is 'brightening' acceptable when it does not mention skin colour? The draft allows it. Please confirm, and say whether 'glow' and 'radiance' are also fine. |  |
| EN-FAIR-001 | Is 'lightens dark spots / pigmentation' acceptable? The draft allows it because it does not name skin colour. |  |
| EN-FAIR-001 | Face bleach and underarm lightening products: flag, allow, or flag only with colour claims? The draft flags 'lighten* underarm'. |  |
| EN-FAIR-001 | Foundation shade names and ranges ('fair', 'fairest', 'fair to deep') are treated as shade description and allowed (AL-003). Confirm. |  |
| EN-FAIR-002 | Is 'dark circles' and 'dark spots' always out of this rule? The draft does not treat them as skin colour. |  |
| EN-FAIR-003 | Should 'fair skin tones' in a make-up shade context near 'wedding' ever be flagged? The draft flags only close pairs (up to 5 words apart). |  |


## 8. Sign-off sheet

- **Rule set reviewed:** satya-en v0.1.1-draft, fingerprint 2aa67fe75bb2
- **Decision:** [ ] Approved   [ ] Approved with the changes listed   [ ] Not approved
- **Reviewer name and qualification:** 
- **Date:** 
- **Signature:** 
- **Changes required:** 

The board user records the outcome in the sign-off log in engine/rules/README.md. Until then the rule set stays DRAFT.
