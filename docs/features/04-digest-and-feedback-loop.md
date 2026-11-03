# Feature 04 — Digest Generation & Feedback Loop

**Status:** Not started
**Week:** 4
**Depends on:** `features/02-classification-agent.md`, `features/03-evaluation-harness.md`

## Goal

Produce a daily digest you actually read, plus a correction mechanism that feeds back into future classifications (personalization via RAG). This is where the project becomes something used daily rather than just tested.

## Context / why this matters

This feature covers two of the harder, more current problems in agent design: generating genuinely useful summaries (not just data dumps) and building a memory/personalization loop without a full fine-tuning setup. It's also your first "write" scope on the Gmail API if you choose the email-delivery option.

## What to build

1. Digest generator: groups classified messages, produces natural-language summary
2. Delivery mechanism (file, email, or Slack webhook)
3. Correction interface (CLI or minimal FastAPI + HTML page)
4. `user_feedback` table population
5. Qdrant embedding + storage of corrections
6. Retrieval step injected into the Week 2 classification prompt as few-shot context

## Requirements — what to follow

- Digest scope: last 24h of classified messages, grouped by category
- Generate a short natural-language summary per group, not a raw list — e.g., "3 emails need action today: [X], [Y], [Z]" rather than a bare enumeration
- Output format: Markdown (if writing to file) or simple HTML (if emailing)
- Correction interface must write to the `user_feedback` table exactly as specified in `data-model.md` (`message_id`, `predicted_category`, `corrected_category`, `corrected_at`)
- Personalization/RAG mechanism:
  - Every row written to `user_feedback` must also be embedded (embed the original email content, not just the category) and upserted into a Qdrant collection
  - At classification time, before calling the LLM, run a similarity search against this Qdrant collection for the 3-5 most similar past corrections
  - Inject retrieved corrections into the prompt as explicit few-shot context, e.g.: "Note: a similar past email from this sender was corrected to `can_wait`"
  - This retrieval step is additive to the Week 2 prompt — do not replace or restructure the core classification prompt, extend it
- If using email delivery: this is the first feature requiring `gmail.compose` (or `gmail.send` if sending the digest itself) scope — update the OAuth consent screen/scopes deliberately, don't silently request broader scopes than needed
- After building the feedback loop, **re-run the Week 3 eval** and specifically check accuracy on emails from senders present in `user_feedback` — this is the concrete evidence that personalization works

## What NOT to do

- Do not auto-send anything from this feature beyond the digest itself (if you choose email delivery for the digest) — reply drafting/sending is Week 5, and even then, drafts only, never auto-sent (see `guardrails.md`)
- Do not skip storing feedback in Qdrant — a correction that isn't retrievable doesn't personalize anything, it's just a log
- Do not let the retrieval step silently override the classification — it's context for the LLM to weigh, not a hard rule that skips the LLM call entirely
- Do not build a full user-facing web app here — the correction interface should be minimal (CLI is fine, a single HTML page is the upper bound of scope)

## Step-by-step tasks

1. Write `digest.py`: query last 24h classifications, group by category, generate summary text (can use a lightweight LLM call for the natural-language framing, or template-based — either is fine)
2. Choose and implement delivery: file write, email send, or Slack webhook
3. Write the correction interface (CLI command or minimal FastAPI route + HTML page)
4. Extend `models.py` with `user_feedback` table if not already present
5. Write the Qdrant embedding/upsert function, triggered whenever a correction is saved
6. Write the retrieval function: given a new email, query Qdrant for similar past corrections
7. Modify the Week 2 classification call to accept and inject retrieved context into the prompt
8. Re-run `eval.py` from Week 3, compare accuracy before/after on emails from previously-corrected senders, log the result

## Acceptance criteria / expected outcome

- A digest is generated and delivered automatically (or via a manual trigger command) covering the last 24h
- Corrections made via the interface are persisted to `user_feedback` and embedded into Qdrant
- A documented eval comparison showing the effect (positive, neutral, or even negative — document what you actually observe) of the feedback loop on classification accuracy

## Edge cases to handle

- No corrections exist yet for a given sender — retrieval should return nothing and the prompt should proceed without few-shot context, not error
- Digest run when there are zero classified messages in the last 24h — should produce a sensible "nothing to report" output, not crash
- Conflicting corrections (user corrects the same sender's emails differently on different occasions) — retrieval should surface the most relevant/recent ones, not average them into nonsense

## Testing

- Unit test digest grouping logic with a mocked set of classifications
- Unit test the Qdrant upsert/retrieval round-trip with a small fixed example
- Manual test: correct a classification, submit a new similar email, confirm the retrieved context appears in the prompt sent to the LLM (log/print the final prompt during testing to verify)