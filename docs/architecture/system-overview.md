# System Overview

**Status:** Reference doc — read first, update if architecture changes

## What InboxTriage is

An agent that reads a Gmail inbox, classifies each message by urgency, extracts action items and deadlines, checks them against a calendar, drafts replies for routine cases, and delivers a daily digest. It learns from user corrections over time via a retrieval-based feedback loop.

## End-to-end data flow

```
Gmail API ──▶ Ingestion ──▶ messages (DB)
                                  │
                                  ▼
                     Classification Agent (Gemini)
                                  │
                                  ▼
                          classifications (DB)
                                  │
                    ┌─────────────┼──────────────┐
                    ▼             ▼              ▼
              Digest Gen    Agent Tool Loop   Eval Harness
             (daily email)  (calendar, draft,  (golden set,
                              snooze)           scikit-learn,
                    │             │             LLM-judge)
                    ▼             ▼
              User reads    User approves
              digest        drafts / corrects
                    │             │
                    └──────┬──────┘
                           ▼
                    user_feedback (DB)
                           │
                           ▼
                  Qdrant (embedded corrections)
                           │
                           ▼
              Retrieved as few-shot examples
              for future classification calls
```

## Core components

| Component | Responsibility | Built in |
|---|---|---|
| Ingestion service | Pull emails from Gmail API, normalize, store | Week 1 |
| Classification agent | Single-shot structured classification per email | Week 2 |
| Eval harness | Measure classification accuracy against golden set | Week 3 |
| Digest generator | Daily summary, correction UI, feedback storage | Week 4 |
| Personalization/RAG layer | Retrieve past corrections, inject as few-shot context | Week 4 |
| Agentic tool loop | Multi-step reasoning: calendar check, draft, snooze | Week 5 |
| Observability layer | Trace agent steps, FastAPI endpoints, scheduling | Week 6 |

## Non-negotiable system boundaries

- The system **never sends email automatically**. All replies are drafts requiring explicit human approval.
- The system **only reads/acts on the authenticated user's own inbox** — no multi-tenant behavior, no processing other people's data.
- All LLM calls must use **structured output** (schema-validated), never free-text parsing with regex.

See `guardrails.md` for the full list of cross-cutting rules.