# SAT-41 live-mode checklist (board user)

Built and tested with `SATYA_LLM=mock`. Draft content: nothing here is a legal sign-off.

1. Set `SATYA_LLM=live` plus `SARVAM_API_KEY` and/or `ANTHROPIC_API_KEY` in the Vercel preview environment (never in git).
2. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (the same pair also enables evidence uploads) and run `supabase/schema.sql` (creates the private `evidence` bucket).
3. Paste one cosmetic listing at `/fix/new`: expect a Product Truth draft with every claim "Not confirmed". Check that a treatment claim shows "Cannot confirm" with its citation.
4. Confirm a claim with "Test report" and no reference: expect a refusal. Upload a small PDF instead: expect the claim confirmed, and the object present in Storage under `<workspace id>/`.
5. Generate: expect "Writing the copy · step 1 of 2" then "Checking every sentence..." then the review page. Cancel mid-way once: expect "Nothing was changed".
6. Check Supabase `llm_calls` has `extract`, `generate` and `verify` rows, and that live replies parse (a garbled reply shows "We couldn't write the pack", not a broken pack).
7. Not built (cut list / raise with CTO): per-section retry on a failed section (generation is two whole-pack steps), editing Product Truth fields by hand, writing to the relational `claims` / `evidence` tables (the pack row holds the truth JSON, as in SAT-38).
