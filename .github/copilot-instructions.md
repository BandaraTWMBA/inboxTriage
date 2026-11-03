# Copilot Instructions — InboxTriage

This file is read automatically by the Copilot agent every session. Keep it current as the project evolves.

## What this project is

InboxTriage is an agentic email/notification prioritizer. It reads a Gmail inbox, classifies messages by urgency, extracts action items/deadlines, checks them against a calendar, drafts (never sends) replies, and delivers a daily digest. It personalizes over time via a retrieval-based feedback loop.

## Tech stack — fixed, see `docs/architecture/tech-stack-decisions.md` for full rationale

- Backend: FastAPI
- LLM: Gemini 2.5 Flash (Google AI Studio, free tier)
- Structured output: Pydantic + Gemini's native `response_schema` — never regex-parse LLM output
- Vector DB: Qdrant
- Relational DB: PostgreSQL (SQLite acceptable for local dev)
- Email: Gmail API (`google-api-python-client`)
- Calendar: Google Calendar API
- Scheduling: APScheduler
- Eval: scikit-learn + custom LLM-as-judge script

Do not introduce a different tool for any of the above without flagging it explicitly — check `docs/architecture/tech-stack-decisions.md` first.

## Documentation to reference

Before implementing any feature, read the relevant file in `docs/features/`:
- `01-gmail-ingestion.md` — Week 1
- `02-classification-agent.md` — Week 2
- `03-evaluation-harness.md` — Week 3
- `04-digest-and-feedback-loop.md` — Week 4
- `05-agentic-tool-loop.md` — Week 5
- `06-observability-deployment.md` — Week 6

Full DB schema: `docs/architecture/data-model.md` — keep this file in sync with actual models.
Data retention windows and cleanup rules: `docs/architecture/data-retention.md` — the Feature 06 cleanup job must follow this exactly.

## Absolute rules (see `docs/guardrails.md` for full list)

1. **No autonomous email sending.** The agent's own reasoning loop must never call a send endpoint. Sending only happens via an explicit user click on a send control in the app (built in Feature 06) — never from the agent loop, a scheduled job, or a batch process.
2. **Never hardcode credentials.** Use `.env`, never commit secrets or OAuth tokens.
3. **Always use schema-validated structured output** for LLM calls that produce structured data (Pydantic + native structured output mode).
4. **Agent tool-calling loop has a hard max step budget (4 steps).** Enforce in code.
5. **Validate every tool call's arguments before executing.** One retry on tool failure, then log and degrade gracefully — never crash the whole batch on one failure.
6. **No autonomous calendar writes.** The agent may only propose an event (`calendar_proposals`, status `pending`). Actual event creation requires an explicit per-event user approval click in the app — never automatic, never re-triggered after rejection.

## Coding conventions

- All DB access through SQLAlchemy models, no raw SQL in application/route code
- All Pydantic schemas centralized (e.g., `schemas.py`), referenced consistently across modules — don't redefine similar models ad hoc
- Every feature should include tests alongside implementation (unit tests for logic, integration tests for API-touching code where feasible)
- When something in a feature doc turns out to be wrong or incomplete during implementation, update the doc — don't let it drift out of sync with the code

## How to work with me on this project

- Prefer scoped tasks over "build the whole feature" — I'll usually point you at one `docs/features/NN-*.md` file at a time
- For anything involving the agentic loop (Feature 05) or the feedback loop (Feature 04), explain your planned approach before writing code
- If you're unsure whether something violates a guardrail, ask rather than assuming it's fine