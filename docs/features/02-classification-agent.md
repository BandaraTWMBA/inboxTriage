# Feature 02 — Classification Agent (Single-Shot)

**Status:** In progress
**Week:** 2
**Depends on:** `features/01-gmail-ingestion.md`, `architecture/data-model.md`

## Goal

Every synced email gets classified into a category with structured output, plus extracted deadline and action items. This is the core "intelligence" of v1 — no multi-step agent loop yet, just one reliable LLM call per email.

## Context / why this matters

This is the first LLM integration in the project and sets the pattern (structured output, schema validation, retry-on-failure) that every later LLM call in the project follows. Get this reliable before building anything on top of it.

## What to build

1. The `EmailClassification` Pydantic schema
2. A classification prompt template
3. A Gemini API wrapper function that calls the model with structured output mode
4. Retry logic for schema validation failures
5. The `classifications` table population logic
6. A manual review pass over 30-50 classifications (produces seed data for Week 3)
7. **Gmail label sync** — apply a corresponding Gmail label to each classified message, so the sorting is visible in the real Gmail inbox (app, browser, mobile) and not only in the InboxTriage dashboard

## Requirements — what to follow

**Taxonomy (do not invent different categories):**
- `urgent_action` — needs a response/decision within 24h
- `fyi` — informational, no action needed
- `can_wait` — needs action eventually, no urgency
- `low_priority` — newsletters, notifications, automated

**Schema (exact fields, do not add/remove without updating this doc and `data-model.md`):**

```python
class EmailClassification(BaseModel):
    category: Literal["urgent_action", "fyi", "can_wait", "low_priority"]
    confidence: float
    extracted_deadline: Optional[str]  # ISO 8601 date, normalize relative dates before storing
    action_items: list[str]
    reasoning: str  # short, used for debugging and eval — not shown to end user
```

- Use Gemini's native structured output (`response_schema`), not free-text + manual JSON parsing
- Prompt must include: sender, subject, cleaned body (truncate very long bodies — define a max length), and explicit rules (e.g., "emails from known priority senders or containing urgent-language cues lean toward `urgent_action`")
- Tag every classification with a `prompt_version` string in the DB row — required for Week 3's eval tracking
- On schema validation failure: retry once with a corrective message describing the validation error, then log the failure if it fails twice (don't silently drop the email)
- Normalize any relative date language ("next Friday," "tomorrow") to ISO format before storing `extracted_deadline` — do this in code, don't rely on the model always outputting ISO format correctly

## Gmail label sync — requirements

**Why this exists:** without it, classifications only live in InboxTriage's own database — opening real Gmail (phone, browser, app) shows an unsorted inbox with no visual difference between an urgent email and a newsletter. Labels close that gap non-destructively.

**Scope change required:** this needs the `gmail.modify` OAuth scope (not just `gmail.readonly` from Feature 01). Update the OAuth consent request deliberately — this is a broader scope than ingestion needed, so treat it as a conscious decision, not an incidental widening. Re-authenticate/re-consent after adding this scope.

**Label mapping (fixed, do not invent additional labels without updating this doc):**

| Category | Gmail label |
|---|---|
| `urgent_action` | `InboxTriage/Urgent` |
| `fyi` | `InboxTriage/FYI` |
| `can_wait` | `InboxTriage/Can-Wait` |
| `low_priority` | `InboxTriage/Low-Priority` |

- Labels are nested under a parent `InboxTriage/` label so they're visually grouped in Gmail's sidebar and don't clutter the top-level label list
- Create labels programmatically on first run if they don't already exist (`users.labels.create`), then cache their label IDs — don't look them up by name on every classification call
- Apply the label via `users.messages.modify` (`addLabelIds`), immediately after a classification is successfully stored in the `classifications` table — label sync is a side effect of classification, not a separate scheduled job
- If a message is re-classified later (e.g., after a prompt change in Week 3, or a user correction in Week 4), **remove the old label and apply the new one** — a message should only ever carry one `InboxTriage/*` category label at a time
- This sync is **additive only** — it applies labels, it does not archive, move, delete, mark as read, or otherwise change the message's location in the inbox. Do not implement the "auto-archive low priority" behavior here — that's a separate, opt-in decision to make later if wanted, not part of this feature's default behavior.

**What NOT to do (label sync specifically):**
- Do not use starring or Gmail's built-in "important" marker as a substitute for labels — the four-category taxonomy doesn't map cleanly onto those, use dedicated labels
- Do not apply labels before the classification is durably stored in the DB — DB write is the source of truth, the label is a reflection of it, not the other way around
- Do not silently expand the requested OAuth scope further than `gmail.modify` for this feature

## What NOT to do

- Do not build the multi-step agent/tool-calling loop here — that's Week 5. This is single-shot classification only.
- Do not regex-parse the model's response — use structured output mode
- Do not skip the retry-on-validation-failure path
- Do not silently drop emails that fail classification twice — log them for review
- Do not invent categories beyond the four listed above

## Step-by-step tasks

1. Define `EmailClassification` in a `schemas.py` module
2. Write the prompt template (as a separate, editable string/file — you'll iterate on this in Week 3)
3. Write `classify_email(message) -> EmailClassification` wrapping the Gemini call, structured output mode, retry logic
4. Write date-normalization helper for `extracted_deadline`
5. Extend `models.py` with the `classifications` table (see `data-model.md`)
6. Write a batch runner: classify all unclassified messages, store results
7. Run against your real synced inbox
8. Manually review 30-50 results, correct any wrong classifications by hand, save as a labeled set (this feeds directly into `features/03-evaluation-harness.md` — do not discard this data)
9. Re-authenticate with the added `gmail.modify` scope
10. Write `label_sync.py`: on first run, create the four `InboxTriage/*` Gmail labels if missing and cache their IDs; write `apply_label(message, category)` that removes any prior `InboxTriage/*` label and applies the correct one
11. Call `apply_label` immediately after each successful classification write in the batch runner
12. Open Gmail (browser or app) and confirm labels are visible and correctly applied against your real inbox

## Acceptance criteria / expected outcome

- Every message in `messages` has a corresponding row in `classifications` with all fields populated
- Schema validation failures are logged, not silently swallowed or crashing the batch run
- You've manually reviewed a sample and have a labeled set saved (this becomes `golden_set.jsonl` seed data)
- Opening real Gmail (app or browser) shows each classified message carrying exactly one correct `InboxTriage/*` label — the sorting is visible outside the custom dashboard, not only inside it

## Edge cases to handle

- Extremely short emails (e.g., just "Thanks!") — should still classify without error
- Emails with no clear deadline language — `extracted_deadline` should be `null`, not a hallucinated date
- Very long email bodies — define and apply a sensible truncation before sending to the model
- Model returns a category outside the allowed `Literal` values — this should fail validation and trigger the retry path, not silently coerce
- A message is re-classified and its category changes — old label must be removed, not left alongside the new one (a message should never carry two `InboxTriage/*` labels)
- Label creation API call fails on first run (e.g., transient error) — should retry/log clearly, since every subsequent label application depends on having valid label IDs cached

## Testing

- Unit test the date-normalization helper with several relative-date phrasings
- Unit test that an intentionally malformed mock LLM response triggers the retry path
- Spot-check test: run classification on a small fixed set of hand-picked example emails with known expected categories, assert reasonable output (not exact-match, since LLM output varies, but category should be sane)
- Unit test `apply_label` with a mocked Gmail client: verify old label removal + new label addition happen together, not just addition
- Manual test: reclassify a message and confirm in real Gmail that only the new label remains
