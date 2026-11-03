# Feature 01 — Gmail Ingestion & Data Foundation

**Status:** Done
**Week:** 1
**Depends on:** `architecture/tech-stack-decisions.md`, `architecture/data-model.md`

## Goal

Pull real emails from Gmail into a local database. No AI/classification yet — this is pure ingestion and data modeling. Success = you can run a script and see your own inbox reflected in a `messages` table.

## Context / why this matters

Every later feature (classification, digest, agent loop) depends on clean, reliable ingestion. Bugs here compound downstream, so this should be boring and solid before moving on.

## What to build

1. Google Cloud project + OAuth 2.0 credentials (Desktop app type)
2. A Python ingestion module that authenticates and pulls recent messages
3. Parsing logic: strip HTML to plain text, extract sender/subject/timestamp/thread ID/labels
4. The `messages` table (see `architecture/data-model.md` for exact schema) via SQLAlchemy
5. A sync job that upserts messages, deduped by `gmail_id`
6. A sanity-check script/CLI command that prints the last 20 synced emails

## Requirements — what to follow

- OAuth scope: start with `gmail.readonly` only. Do not request `gmail.compose`, `gmail.send`, or `gmail.modify` yet — those are added deliberately in later features (`gmail.modify` in Feature 02 for label sync, `gmail.compose` in Feature 05 for draft replies). Each scope addition should be a conscious, documented decision, not requested speculatively up front.
- Use `google-api-python-client` + `google-auth-oauthlib` for auth and API calls
- Use `users.messages.list` + `users.messages.get` with `format=full`
- Strip HTML bodies to plain text using `beautifulsoup4`
- All DB access via SQLAlchemy — no raw SQL in application code
- `gmail_id` must be unique in the `messages` table; sync must upsert (never create duplicate rows for the same email)
- Store OAuth token cache (`token.json` or equivalent) outside version control

## What NOT to do

- Do not implement any classification, summarization, or LLM calls in this feature — ingestion only
- Do not request write/send scopes yet
- Do not skip HTML stripping — raw HTML bodies will pollute later LLM prompts and eval data
- Do not hardcode the OAuth client secret or any credential directly in source files

## Step-by-step tasks

1. Create Google Cloud project, enable Gmail API, generate OAuth credentials, download `credentials.json`
2. Write `auth.py`: handles the OAuth flow, caches the resulting token
3. Write `gmail_client.py`: wraps `list` and `get` calls, returns parsed message dicts
4. Write `models.py` (or extend it): SQLAlchemy model for `messages` matching the data model doc
5. Write `sync.py`: orchestrates fetch → parse → upsert, callable as a script or function
6. Write a small CLI entry point (`python -m inboxtriage sync` or similar) that runs the sync and prints a summary table

## Acceptance criteria / expected outcome

- Running the sync command against your real Gmail account populates the `messages` table with the last 24h of emails
- Re-running the sync does not create duplicate rows
- Printed sanity-check table shows sender, subject, and timestamp for at least the last 20 emails, matching what you see in your actual inbox

## Edge cases to handle

- Email with no body / attachment-only email
- Email with malformed or missing sender header
- Very long email threads — make sure `thread_id` grouping doesn't break parsing
- API rate limit / transient network failure during sync — should retry, not crash

## Testing

- Unit test for the HTML-stripping function with a few sample HTML bodies
- Unit test for upsert logic: simulate syncing the same `gmail_id` twice, assert only one row exists
- Integration test (can be manual for this feature): run against a real test inbox and visually confirm output