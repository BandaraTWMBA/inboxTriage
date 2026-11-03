# Tech Stack Decisions

**Status:** Locked in — do not change without explicitly updating this doc first

These are deliberate choices. If Copilot (or you, mid-session) suggests a different tool, check against this table before accepting — swapping silently causes drift between docs and code.

| Layer | Choice | Why | Do NOT substitute with |
|---|---|---|---|
| Email source | Gmail API (OAuth 2.0) | Gives labels, threads, push notifications for free later | IMAP (unless Gmail API is genuinely blocked) |
| LLM | Gemini 2.5 Flash (Google AI Studio, free tier) | Free, no card required, native structured output + function calling | Don't switch to a paid model without discussing cost implications first |
| Backend | FastAPI | Matches existing stack/skills | Flask, Django — no reason to introduce a new framework |
| Structured output | Pydantic models + Gemini's native `response_schema` | Reliable, type-safe, matches Python ecosystem | Regex/manual JSON parsing — never acceptable |
| Vector DB | Qdrant | Already known from prior RAG project | Pinecone, Weaviate, Chroma — no need to relearn a new DB |
| Relational DB | PostgreSQL (SQLite acceptable for local dev only) | Structured state: messages, classifications, feedback | MongoDB/NoSQL — data is inherently relational here |
| Scheduling | APScheduler (in-process) | Keep infra light for a personal project | Celery + Redis — only if APScheduler genuinely becomes a bottleneck |
| Calendar | Google Calendar API | Same OAuth project as Gmail, minimal extra setup | N/A |
| Eval tooling | scikit-learn (`classification_report`) + custom LLM-judge script | Standard, well-documented, sufficient at this scale | Don't introduce MLflow/W&B unless doing the optional Week 6 CI/CD stretch goal |

## Environment & secrets

- OAuth credentials and API keys live in `.env`, never hardcoded, never committed
- `.env.example` should list required variable names with no real values
- `.gitignore` must include `.env`, `token.json` (or wherever OAuth tokens cache), and any local DB files

## When it's okay to deviate

Only if a Week's implementation doc explicitly says "stretch goal" or "optional" — otherwise treat this table as fixed for the duration of the 6-week build. Revisit after v1 ships.

## OAuth scope progression

Scopes are added incrementally, one feature at a time, never requested speculatively ahead of the feature that needs them:

| Scope | Added in | Used for |
|---|---|---|
| `gmail.readonly` | Feature 01 | Ingesting messages |
| `gmail.modify` | Feature 02 | Applying `InboxTriage/*` labels |
| `gmail.compose` | Feature 05 | Creating (not sending) reply drafts |
| Calendar read-only | Feature 05 | `check_calendar` conflict checks |
| `gmail.send` | Feature 06 | Sending a draft — only ever from an explicit in-app user click |
| Calendar write | Feature 06 | Creating an approved calendar event — only ever from an explicit in-app approval click |

See `guardrails.md` rules 1 and 7 for the human-approval requirements attached to the last two scopes.