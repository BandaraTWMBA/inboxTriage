# Feature 05 — Agentic Tool-Use Loop

**Status:** Not started
**Week:** 5
**Depends on:** `features/02-classification-agent.md`, `features/04-digest-and-feedback-loop.md`, `guardrails.md` (read fully before starting)

## Goal

Move from single-shot classification to a genuine multi-step agent loop that reasons about which tools to call — calendar checks, reply drafting, snoozing — for `urgent_action` emails specifically.

## Context / why this matters

This is the core "agentic orchestration" skill the whole project is built to demonstrate. It's also the highest-risk feature from a guardrails perspective (draft generation, external API writes) — read `guardrails.md` in full before starting.

## What to build

1. Three tools as callable, schema-validated functions: `check_calendar`, `draft_reply`, `snooze`
2. A ReAct-style reasoning loop: LLM reasons → picks a tool or finishes → tool result fed back → repeat
3. Guardrails: step budget, tool failure handling, argument validation
4. Step logging into the `agent_steps` table (feeds Week 6's observability view)

## Requirements — what to follow

**Tools (exact signatures, extend the doc if you add more):**

```python
def check_calendar(date_range: tuple[str, str]) -> CalendarCheckResult:
    """Read-only. Flags if an extracted deadline conflicts with existing calendar events."""

def draft_reply(message_id: str, tone: str) -> DraftResult:
    """Generates a reply draft, saves to Gmail Drafts. Never sends — sending is a
    separate, human-triggered action in the app (see features/06)."""

def propose_calendar_event(message_id: str, title: str, date: str, time: str | None) -> ProposedEvent:
    """Writes a row to calendar_proposals with status='pending'. Does NOT call the
    Calendar API's create-event endpoint. Actual event creation only happens when
    the user explicitly approves the proposal in the app (features/06)."""

def snooze(message_id: str, until_date: str) -> SnoozeResult:
    """Marks a message to resurface later; removed from today's digest until then."""
```

- Loop only runs for `urgent_action`-classified emails — other categories don't need multi-step reasoning
- Loop structure: LLM reasons about next action → either calls a tool or declares done → tool result appended to context → LLM reasons again → repeat until done or step budget hit
- **Hard step budget: max 4 steps per email** (per `guardrails.md`) — enforce this in code, not just as a prompt instruction
- Every tool call's arguments must be validated (Pydantic) before execution
- If a tool call fails (API error, timeout): catch it, log the failure, let the agent continue reasoning without that result rather than crashing the whole loop
- `draft_reply` must use the Gmail API's draft-creation endpoint (`gmail.compose` scope) — **never** the send endpoint. Sending is implemented entirely in Feature 06, as a human-triggered in-app action, not part of this agent loop.
- `propose_calendar_event` only ever writes a `pending` row to `calendar_proposals` — it must never call the Calendar API's write/create endpoint directly. Actual event creation is implemented in Feature 06's approval endpoint, triggered by explicit user action.
- Calendar access uses the same OAuth project as Gmail; `check_calendar` needs calendar read-only scope. Calendar *write* scope is requested in Feature 06 when the approval endpoint is built, not here.
- Every step (tool called, arguments, result, latency, token usage where available) must be written to the `agent_steps` table as it happens, not batched at the end — so a mid-loop crash still leaves a usable trace

## What NOT to do

- Do not implement or expose any send-email capability anywhere in this feature — draft creation only, sending lives entirely in Feature 06 as an explicit human action
- Do not implement or call any calendar event *creation* in this feature — only propose via `calendar_proposals`, creation lives in Feature 06 gated by explicit approval
- Do not let the loop run unbounded — the step budget is not optional
- Do not let a single tool failure crash processing for that email's entire loop — degrade gracefully
- Do not skip argument validation on tool calls "because the LLM usually gets it right" — validate every time
- Do not silently retry tools indefinitely on failure — one retry per tool call max, then log and move on

## Step-by-step tasks

1. Define Pydantic result schemas for each tool (`CalendarCheckResult`, `DraftResult`, `ProposedEvent`, `SnoozeResult`)
2. Implement `check_calendar` using Google Calendar API (read-only)
3. Implement `draft_reply` using Gmail API draft creation, with a reply-generation prompt (uses the classification's extracted context)
4. Implement `propose_calendar_event`: writes a `pending` row to `calendar_proposals` (per `data-model.md`) — no Calendar API write call
5. Implement `snooze` as a DB-level flag/field update (add `snoozed_until` to `messages` or a related table if not already modeled — update `data-model.md` if you do)
6. Write the agent loop controller: manages step count, calls the LLM with available tools (function-calling mode), dispatches to the right tool implementation, logs each step
7. Wire step-budget enforcement and per-tool-call validation/error handling
8. Extend `models.py` with `agent_steps` and `calendar_proposals` tables per `data-model.md`
9. Test the full loop against real `urgent_action` emails from your inbox, manually review generated drafts and proposed events before considering this feature done

## Acceptance criteria / expected outcome

- For a set of real `urgent_action` test emails, the agent correctly decides when to check the calendar, when to draft a reply, when to propose a calendar event, and when to snooze
- No loop exceeds 4 steps
- A deliberately-induced tool failure (e.g., temporarily revoke calendar access) does not crash the batch run — it's logged and the loop continues or exits gracefully
- Every step of every loop run is present in `agent_steps`, queryable and human-readable
- You've manually reviewed a sample of generated drafts and confirmed none were sent (only saved as drafts)
- You've confirmed no calendar event exists in your real calendar for any proposal that hasn't been explicitly approved (Feature 06)

## Edge cases to handle

- `urgent_action` email with no extractable deadline — `check_calendar` shouldn't be called, or should handle a null/absent date gracefully
- Email where a reply doesn't make sense (e.g., an automated notification misclassified as urgent) — the agent should be able to reason its way to "no action needed" rather than forcing a draft
- Calendar API returns no conflicts vs. returns an error — these are different outcomes and should be logged/handled differently

## Testing

- Unit test each tool function in isolation with mocked API responses (success and failure cases)
- Unit test the step-budget enforcement with a mocked LLM that would otherwise loop indefinitely
- Integration test: run the full loop against 5-10 real emails, manually verify tool call sequences make sense
- Explicit test verifying no code path in `draft_reply` calls a send endpoint