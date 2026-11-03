# Data Model

**Status:** Reference doc — update immediately if schema changes during implementation

See `architecture/data-retention.md` for how long each table's data is kept and the cleanup job that enforces it.

All tables live in PostgreSQL (or SQLite for local dev), accessed via SQLAlchemy. Vector embeddings live separately in Qdrant (see `features/04-digest-and-feedback-loop.md`).

## `messages`

Raw ingested emails, one row per Gmail message.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID / int PK | Internal ID |
| `gmail_id` | string, unique | Gmail's message ID — used for dedup on sync |
| `thread_id` | string | Gmail thread ID |
| `sender` | string | Email address (and display name if available) |
| `subject` | string | |
| `body` | text | Plain text, HTML stripped |
| `received_at` | timestamp | |
| `raw_labels` | string/array | Gmail labels at ingestion time |
| `created_at` | timestamp | Internal record creation time |

**Constraints:** `gmail_id` must be unique — sync jobs upsert, never insert duplicates.

## `classifications`

One row per message, produced by the classification agent.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID / int PK | |
| `message_id` | FK → `messages.id` | |
| `category` | enum: `urgent_action`, `fyi`, `can_wait`, `low_priority` | Matches `EmailClassification.category` |
| `confidence` | float | 0.0–1.0 |
| `extracted_deadline` | date, nullable | ISO format only — normalize before storing |
| `extracted_actions` | array/text | List of action item strings |
| `reasoning` | text | Short model-generated explanation, used for debugging + eval |
| `prompt_version` | string | Tag identifying which prompt version produced this — required for Week 3 eval tracking |
| `created_at` | timestamp | |

## `user_feedback`

Corrections the user makes to classifications — this is what powers personalization.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID / int PK | |
| `message_id` | FK → `messages.id` | |
| `predicted_category` | enum (same as above) | What the agent originally said |
| `corrected_category` | enum (same as above) | What the user says it should be |
| `corrected_at` | timestamp | |

**Note:** Every row here should also be embedded and stored in Qdrant (see Week 4 doc) — this table is the source of truth, Qdrant is the retrieval index over it.

## `calendar_proposals` (added in Week 5/6)

Every deadline the agent detects that could become a calendar event is proposed here first — an event is only actually created in the user's calendar after explicit approval (see `guardrails.md` rule 7).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID / int PK | |
| `message_id` | FK → `messages.id` | |
| `proposed_title` | string | e.g. "Reply deadline: Q3 budget sign-off" |
| `proposed_date` | date | |
| `proposed_time` | time, nullable | Null if only a date, no specific time |
| `status` | enum: `pending`, `approved`, `rejected` | Defaults to `pending` on creation |
| `calendar_event_id` | string, nullable | Populated only after approval + successful Calendar API creation |
| `created_at` | timestamp | |
| `resolved_at` | timestamp, nullable | When approved/rejected |

**Rule:** a `rejected` or unresolved `pending` proposal must never be silently re-proposed or auto-created later — if the situation changes (e.g., the deadline itself changes), create a new proposal row rather than mutating a resolved one.

## `agent_steps` (added in Week 5/6)

Log of every step the agent takes during the multi-step tool-calling loop — powers the Week 6 observability/tracing view.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID / int PK | |
| `message_id` | FK → `messages.id` | |
| `step_number` | int | Order within the loop for this message |
| `tool_called` | string, nullable | e.g. `check_calendar`, `draft_reply`, `snooze`, or null if the step was pure reasoning with no tool call |
| `tool_input` | JSON | Arguments passed to the tool |
| `tool_output` | JSON | Result returned |
| `latency_ms` | int | |
| `tokens_used` | int, nullable | |
| `created_at` | timestamp | |

## Relationships summary

```
messages 1───N classifications
messages 1───N user_feedback
messages 1───N agent_steps
```

One message can have multiple classification rows over time (e.g., if re-classified after a prompt change) — always query the most recent by `created_at` unless explicitly comparing history.