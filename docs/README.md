# InboxTriage — Documentation Index

This is the documentation set for InboxTriage, an agentic email/notification prioritizer. It's structured so that both you and the Copilot agent have a single source of truth for what to build, in what order, following what rules.

## Read order

1. **`architecture/system-overview.md`** — what the system does end to end, before touching any feature doc
2. **`architecture/tech-stack-decisions.md`** — locked-in tools and why (don't let the agent swap these without asking)
3. **`architecture/data-model.md`** — full DB schema, referenced by every feature doc
4. **`architecture/data-retention.md`** — how long data is kept and why, referenced by Feature 06
5. **`guardrails.md`** — global rules that apply across every feature, read this before Week 5 especially
6. **`features/01` through `features/06`** — one per implementation week, work through in order

## How to use these docs with Copilot agent

- Keep `.github/copilot-instructions.md` in the repo root — Copilot reads it automatically every session
- When starting a new feature/week, open the relevant `features/NN-*.md` file and reference it directly in your prompt: `"Implement what's described in #file:docs/features/01-gmail-ingestion.md"`
- Each feature doc is self-contained: goal, requirements, what to follow, what NOT to do, schemas, step-by-step tasks, and acceptance criteria — the agent shouldn't need outside context to implement it
- If you deviate from a doc during implementation (e.g., you decide SQLite instead of Postgres for local dev), update the doc afterward so it stays accurate — stale docs are worse than no docs

## Status tracking

Mark each feature doc's status at the top as you go: `Not started / In progress / Done / Needs revisit`. This lets you (or the agent) quickly see where the project stands.