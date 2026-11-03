# Guardrails — Global Rules

**Status:** Non-negotiable — applies to every feature, every week. Read before starting Week 4 (feedback) and Week 5 (tool loop) especially.

## Absolute rules — never violate these

1. **No autonomous email sending, ever.** The agent itself must never call a send endpoint as part of its own reasoning loop. Sending is only ever a direct, explicit human action — viewing a draft, optionally editing it, and clicking a send button in the app is allowed (see `features/05` and `features/06`), but the agent choosing to send on its own, with or without a "confirmation" it generates itself, is not. If any code path lets the agent trigger a send without a human clicking an actual send control, that's a bug — stop and flag it, don't silently "fix" it by adding an automated confirmation step.
2. **Never hardcode credentials.** OAuth tokens, API keys — always via `.env`, never committed, never printed to logs.
3. **Never log full email bodies to any third-party/external logging service** without explicitly checking that service's data policy first. Local logs/DB are fine; anything leaving the machine needs a deliberate decision, not a default.
4. **Every LLM call producing structured data must use schema validation** (Pydantic + native structured output mode). No regex-parsing of free-text LLM responses to extract structured fields.
5. **Every tool call in the agentic loop (Week 5) must validate its arguments before executing**, and every tool call must have a bounded retry/failure path — no unhandled exceptions that crash the whole classification run for one bad email.
6. **Max step budget on the agent loop.** Hard cap (start at 4 steps) to prevent runaway loops burning API calls.
7. **No autonomous calendar writes.** The agent may only *propose* a calendar event (title, date, time) for a detected deadline — it must never call the Calendar API's create-event endpoint itself. Creating the event requires an explicit human approval action per event, surfaced as a clear yes/no in the app ("add this to your calendar?"). A rejected or ignored proposal must not silently retry or auto-create later.

## Rate limiting / cost control

- Gemini free tier is rate-limited — always implement retry-with-backoff on 429 errors, never a tight retry loop
- During development, cap batch classification runs (e.g., don't classify 500 emails in one uncapped loop while testing) — test on small batches first

## Data handling

- This project processes the user's real personal email. Treat the local database as sensitive data:
  - Don't commit any DB file, export, or dump to version control
  - `.gitignore` must cover local DB files, `token.json`/OAuth cache, `.env`
- Golden eval dataset (Week 3) will contain real email content — same rules apply, don't commit it publicly if the repo is public. Consider redacting sender names/emails if you plan to publish the repo.

## Documentation hygiene

- If implementation diverges from what's written in a `features/*.md` doc, **update the doc**, don't let it go stale — a wrong doc actively misleads the next session (yours or the agent's)
- Any new environment variable, table, or tool added must be reflected in `architecture/data-model.md` or `architecture/tech-stack-decisions.md` as appropriate

## When Copilot suggests something outside these rules

If the agent proposes something that would violate a rule above (e.g., "I'll add auto-send with a confirmation dialog" or "let's just regex-parse the JSON to save time") — reject it and ask for the compliant alternative explicitly. These rules take priority over convenience or speed of implementation.