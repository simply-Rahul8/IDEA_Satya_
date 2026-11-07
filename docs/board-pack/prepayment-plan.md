# Prepayment plan: manual UPI / bank transfer + invoice (DRAFT)

**For:** SAT-24 (collect payments, plan P30). **Status: DRAFT. No money has been requested or taken, no invoice has been issued, nothing has been sent.**
Plan refs: P7 (3-month prepaid commitment, ₹2,997 per brand, target 3 or more brands), P27, P30, section 7, section 9 (week 7 prepaid ask, go/no-go).

## BLOCKER: do not take any money until this is approved (P27)

Vercel Hobby is non-commercial and free Supabase projects pause when idle. Plan P27 requires **Vercel Pro (about $20 a month) and Supabase Pro (about $25 a month) before taking any prepayment.**

- This is a **spend change**, so it is a board approval (plan section 8) before anyone upgrades.
- The company budget is $100 a month. The upgrade is about $45 a month, leaving about $55 for LLM calls and everything else. Confirm that split when you approve.
- Production also needs its own Supabase project, Sentry environment and keys (`docs/deploy.md` section 5), and a production deploy is itself a board approval.
- The upgrade is a human step. The agents do not hold payment details and do not upgrade accounts.

**Checklist (all must be ticked before the first payment is requested):**
- [ ] Board approves the Vercel Pro + Supabase Pro spend in a task comment, with the monthly cap.
- [ ] You upgrade both accounts yourself and note the date here: ______
- [ ] Production deploy approved and live (`docs/deploy.md` section 5).
- [ ] The product the brand pays for exists and works (a pilot is under way, not a promise).
- [ ] The tax and accounting points below are confirmed with an accountant.

## 1. The offer (as in the plan)

3-month prepaid commitment, **₹2,997 total per brand** (P7), for the pilot service. Spell out in writing what the brand gets, the three months it covers, and the refund position. Suggested refund line, for you to decide: "Refundable in full within 14 days, or pro rata if we stop providing the service." Use the same wording in the invoice and the confirmation email.

## 2. Flow

1. **Brand agrees** by reply email (keep it). You send the payment request. This is an outward message, so it is yours to send.
2. **You send the payment details:** UPI ID and/or bank account, and the invoice (PDF) with a unique invoice number. Put the invoice number in the payment note or reference so you can match it.
3. **Brand pays** by UPI or bank transfer (NEFT / IMPS).
4. **You capture the UTR** (UPI reference or bank UTR number) from your bank or UPI app statement. Never take a screenshot alone as proof of receipt. Check that the amount landed in the account.
5. **You confirm receipt** to the brand with the UTR in the message and start the 3-month period. If the invoice has "Paid" fields, mark them now.
6. **Log it** in a private sheet outside git: invoice number, brand, amount, date received, UTR, period, notes. Do not commit payment data, bank details or UTRs to the repo.
7. **Refunds or cancellations:** refund to the same account, record the refund UTR against the invoice, and issue a credit note or a cancelled-invoice note with a new number. Do not reuse numbers.

Your choice, a business decision for you: receive money into a business account in the company's name if you have one, rather than a personal account. If you use a personal account, check with an accountant first.

## 3. Below the GST threshold

P30 assumes turnover stays below the GST registration threshold, so no GST is charged. **Check this with an accountant before the first invoice. I have not verified the current thresholds, and the position depends on your state, whether you supply across state lines, and your other income.**

If you are not registered under GST:
- You must not charge GST on the invoice.
- The document should say it is an invoice by a supplier not registered under GST, with **GSTIN: Not applicable**. Avoid the words "tax invoice".
- Watch cumulative turnover from all sources against the threshold. Registration becomes mandatory once you cross it, and the plan moves to Razorpay with GST in v1.1.
- Income tax and any TDS the brand may deduct are separate. Ask the accountant.

## 4. Invoice template (copy into a document, fill the fields)

> **INVOICE**  (supplier not registered under GST: no GST charged)
>
> **Invoice number:** `SAT-{{YYYY}}-{{NNN}}`  (sequential, never reused)
> **Invoice date:** `{{DD-MMM-YYYY}}`
> **Due date:** `{{DD-MMM-YYYY}}`
>
> **Supplier (who is paid):**
> `{{SUPPLIER_LEGAL_NAME}}`, trading as Satya
> `{{ADDRESS}}`
> PAN: `{{PAN, optional, ask the accountant}}`
> **GSTIN: Not applicable (not registered under GST)**
> Email: `{{EMAIL}}`
>
> **Receiver (who pays):**
> `{{BRAND_LEGAL_NAME}}`
> `{{BRAND_ADDRESS}}`
> GSTIN: `{{BRAND_GSTIN or "Not provided"}}`
> Contact: `{{BRAND_CONTACT_NAME}}, {{BRAND_EMAIL}}`
>
> | # | Description | Period | Amount (₹) |
> |---|---|---|---|
> | 1 | Satya pilot: listing claims review and claim-safe copy service, 3-month prepaid commitment | `{{START_DATE}}` to `{{END_DATE}}` | 2,997.00 |
> | | **Total payable** | | **2,997.00** |
>
> Amount in words: Rupees Two Thousand Nine Hundred and Ninety-Seven only.
> GST: Not charged (supplier not registered).
>
> **Pay by UPI or bank transfer:**
> UPI ID: `{{UPI_ID}}`
> Account name: `{{ACCOUNT_NAME}}` · Account number: `{{ACCOUNT_NUMBER}}` · IFSC: `{{IFSC}}` · Bank/branch: `{{BANK}}`
> **Please quote invoice number `SAT-{{YYYY}}-{{NNN}}` in the payment reference.** Please email the UTR number to `{{EMAIL}}` after paying.
>
> **Payment received (supplier fills on receipt):**
> Date received: `__________`  Amount: `₹__________`  **UTR / reference: `__________`**  Mode: UPI / NEFT / IMPS
>
> **Terms:** Refundable `{{REFUND_TERMS}}`. The service gives claims-risk review under a draft rule set. It reports "no flagged risks under rule set vX", which is not legal advice and not a statement that any listing is compliant or approved by any regulator or marketplace. Cancellation: reply to `{{EMAIL}}`.

Do not put the rule-set status, the consultant's name or any compliance wording in the invoice beyond the terms line above.

## 5. Open items for you

| Decision | Who | When |
|---|---|---|
| Approve Vercel Pro + Supabase Pro spend (blocker) | Board | Week 5 per plan, before any payment request |
| Which account receives money (business or personal) | Board, with an accountant | Week 0 per P30 |
| Refund terms | Board | Before the first invoice |
| GST position confirmed | Board, with an accountant | Before the first invoice |
| Pilot brands to ask (week 7) | Board | After the pilot read-out |
