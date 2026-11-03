# Feature 06 — Observability, API, Scheduling & Ship

**Status:** Not started
**Week:** 6
**Depends on:** All prior features (01-05), `architecture/data-retention.md`

## Goal

Make the system demoable, debuggable, and something you'd actually keep running day to day. Wrap everything behind FastAPI, add scheduling, build a tracing view, and finish with proper documentation for job applications.

## Context / why this matters

This is where the project goes from "a collection of scripts" to "a system." The tracing view specifically is what makes an agentic system trustworthy enough to actually rely on daily — without visibility into *why* the agent did something, you won't trust it, and neither will an interviewer evaluating your judgment about agent safety.

## What to build

1. A minimal tracing/timeline view over `agent_steps`
2. FastAPI endpoints wrapping the core operations
3. In-app draft view/edit/send flow, gated entirely on explicit user action
4. In-app calendar-proposal consent flow (approve/reject), gated entirely on explicit user action
5. APScheduler job for daily automated sync + classify + digest
6. Weekly APScheduler cleanup job implementing `architecture/data-retention.md`
7. Final README with architecture diagram, eval results, and lessons learned
8. (Optional stretch) GitHub Actions CI eval-on-commit workflow

## Requirements — what to follow

**FastAPI endpoints (exact set, extend only if genuinely needed):**

| Endpoint | Method | Purpose |
|---|---|---|
| `/sync` | POST | Trigger inbox sync (Feature 01) |
| `/digest/today` | GET | Return today's digest |
| `/messages?category={cat}&from={date}&to={date}` | GET | List messages in a category (or all), for the inbox browse view |
| `/messages/{message_id}` | GET | Return full email content (sender, subject, body, classification, extracted fields) for reading in-app |
| `/feedback` | POST | Submit a correction (Feature 04) |
| `/trace/{message_id}` | GET | Return agent reasoning steps for a specific email (from `agent_steps`) |
| `/drafts/{message_id}` | GET | Return the current draft content (fetched from Gmail Drafts via API) for viewing/editing in-app |
| `/drafts/{message_id}` | PUT | Update draft content — writes the edited text back to the same Gmail draft via the API, does not create a new draft |
| `/drafts/{message_id}/send` | POST | Sends the draft **only** in direct response to this explicit call, which must originate from a user clicking a send control in the app — never called by the agent loop itself |
| `/calendar-proposals?status=pending` | GET | List calendar event proposals awaiting user decision |
| `/calendar-proposals/{id}/approve` | POST | Creates the actual calendar event via Calendar API, only on this explicit call; updates `calendar_proposals.status` to `approved` and stores the resulting `calendar_event_id` |
| `/calendar-proposals/{id}/reject` | POST | Marks the proposal `rejected`; must not create anything |

**Draft view/edit/send flow (new requirement):** the dashboard's email detail view (from the browse feature) must, for any `urgent_action` email with a generated draft, show the draft content in an editable text area, let the user modify it freely, save edits via `PUT /drafts/{message_id}`, and send via a clearly-labeled send button calling `POST /drafts/{message_id}/send`. This requires the `gmail.send` OAuth scope — add it deliberately alongside `gmail.compose`, both requested at this point in the build (Week 6), not earlier. Treat every scope addition as a conscious decision per `guardrails.md` and `features/01`.

**Calendar consent flow (new requirement):** whenever a `calendar_proposals` row exists with `status='pending'`, the dashboard must surface it clearly — e.g. "Add 'Reply deadline: Q3 budget sign-off' to your calendar for tomorrow, 5:00 PM?" with explicit approve/reject controls. No proposal is ever auto-approved, auto-expired into approval, or re-surfaced silently after rejection (per `guardrails.md` rule 7). This requires Calendar *write* scope, requested here alongside the send-scope addition above.

**Dashboard inbox/browse view:** the dashboard must let the user go beyond digest counts — clicking a category opens the full list of emails in that category (sender, subject, one-line preview), and clicking an individual email opens its full body to read in-app, using the `body` already stored in `messages` from Feature 01 (no extra Gmail API call needed at read-time). Each opened email should also show its classification (category, extracted deadline, action items) and include a link to open the same email directly in Gmail (`https://mail.google.com/mail/u/0/#inbox/{gmail_id}`) for forwarding or viewing attachments — reply-and-send now happens in-app via the draft flow above, so this Gmail link is a fallback for anything the in-app view doesn't cover.

- Tracing view: a simple table/timeline per `message_id` showing step number, tool called, arguments, result, latency — reuses `agent_steps` data, no new data collection needed, just presentation
- Scheduling: one APScheduler job running sync → classify → digest generation in sequence, on a daily schedule, configurable time
- **Retention cleanup job:** a second APScheduler job, run weekly, implementing the windows and exclusion rules in `architecture/data-retention.md` exactly — 30 days for `agent_steps`, 90 days for `messages`/`classifications` (subject to the pending-proposal/unsent-draft/active-snooze exclusion check), 90 days for resolved `calendar_proposals` only. `user_feedback`, its Qdrant mirror, and `golden_set.jsonl` are never touched by this job. Every run must log timestamp + row counts deleted per table.
- README must include: architecture diagram (can reuse the one from `architecture/system-overview.md`), eval results with before/after numbers from Week 3's prompt iterations, and an explicit "what I'd do differently at scale" section

## What NOT to do

- Do not build a full frontend/UI beyond what's needed for browse/read, trace view, draft edit/send, calendar consent, and the correction interface (already scoped in Feature 04) — this is a backend/API project with a functional-but-minimal dashboard, not a polished consumer product
- Do not add scheduling infrastructure beyond APScheduler unless you've actually hit a concrete limitation — no Celery/Redis speculatively
- Do not let `/drafts/{message_id}/send` be callable from anywhere except a genuine user-initiated click in the app — no scheduled job, no batch process, no agent-loop code path may call it
- Do not let `/calendar-proposals/{id}/approve` be called automatically by any scheduled or batch process — approval is per-event, per-click, by the user
- Do not let the retention cleanup job delete `user_feedback`, its Qdrant mirror, `golden_set.jsonl`, or any `messages`/`calendar_proposals` row excluded per `architecture/data-retention.md`
- Do not skip the "what I'd do differently at scale" section in the README — this is a strong interview signal and takes 10 minutes to write

## Step-by-step tasks

1. Write the `/trace/{message_id}` endpoint and a simple rendering (JSON is fine; HTML table is a nice-to-have)
2. Wrap sync, digest, and feedback logic behind the remaining FastAPI endpoints
3. Write `/messages` (list, filterable by category and date range) and `/messages/{message_id}` (full detail) endpoints
4. Build the dashboard's category browse view: clicking a category count opens a scrollable list (sender, subject, preview) for that category
5. Build the email detail view: clicking a list item shows full body, classification, extracted deadline/action items, and an "open in Gmail" link
6. Re-authenticate with `gmail.send` and Calendar write scope added
7. Write `/drafts/{message_id}` GET/PUT and `/drafts/{message_id}/send` — wire the detail view's editable draft text area to these
8. Write `/calendar-proposals` list + approve/reject endpoints — wire a pending-proposal banner/card into the dashboard with explicit approve/reject buttons
9. Manually test: edit a real draft, send it, confirm it actually arrives in the recipient's inbox as edited; approve a real proposal, confirm the event appears in your actual calendar; reject one, confirm nothing is created
10. Write the APScheduler job wiring sync → classify → digest in sequence
11. Write the weekly retention cleanup job per `architecture/data-retention.md`, including the exclusion checks and per-run logging
12. Run the full scheduled pipeline (including one cleanup cycle) for at least one real week before considering the project "done" — daily use surfaces bugs no test set catches
13. Write the final README: architecture diagram, tech stack, setup instructions, eval results table, lessons learned
14. (Optional) Set up a GitHub Actions workflow that runs `eval.py` on every push to `main` and fails the build if accuracy drops below a set threshold — this closes the CI/CD-for-ML gap and is worth mentioning explicitly in interviews since it's rare among junior candidates
15. Prepare your interview narrative: one classification failure you found and fixed, one guardrail you added after something went wrong, one concrete eval number

## Acceptance criteria / expected outcome

- All endpoints work against real data, including `/messages`, `/messages/{message_id}`, `/drafts/*`, and `/calendar-proposals/*`
- From the dashboard, you can click into any category, read the full list, open any individual email's full content in-app, edit and send a draft reply, and approve or reject a proposed calendar event — all without leaving the app
- A deliberate test confirms `/drafts/{message_id}/send` and `/calendar-proposals/{id}/approve` only ever fire from a real button click — no scheduled job or batch process can reach them
- The scheduled sync/digest job runs unattended for at least a week without manual intervention
- The retention cleanup job runs at least once for real, and its log confirms it deleted only what the retention doc permits — verify by hand that `user_feedback`, Qdrant, and any pending `calendar_proposals` were untouched
- README is complete enough that someone unfamiliar with the project could set it up and understand the architecture and results
- You can articulate, out loud, the concrete accuracy improvement from Week 3 and one specific bug/guardrail story from Week 5

## Edge cases to handle

- Scheduled job runs while a manual `/sync` call is also in progress — decide and document the behavior (skip, queue, or allow concurrent — pick one deliberately)
- `/trace/{message_id}` called for a message that never went through the agent loop (e.g., it was `fyi`, not `urgent_action`) — should return an empty/appropriate response, not an error
- User edits a draft, then the underlying Gmail draft is independently modified/deleted outside the app (e.g., directly in Gmail) before they hit send — `PUT`/`send` should handle a stale or missing draft gracefully, not silently overwrite or crash
- User clicks approve on a calendar proposal twice in quick succession (double-click) — must not create two calendar events; check `status` before creating and treat a second approval on an already-`approved` proposal as a no-op
- Calendar or Gmail API call fails during an approve/send action — surface a clear error to the user in the app, do not mark the proposal `approved` or claim the email was sent if the underlying API call actually failed
- A `messages` row is past the 90-day window but has a pending `calendar_proposals` row, an unsent draft, or a future `snoozed_until` — cleanup job must skip it, not delete it

## Testing

- Endpoint tests for all routes (happy path + at least one failure case each), including `/drafts/*` and `/calendar-proposals/*`
- Explicit test verifying `/drafts/{message_id}/send` and `/calendar-proposals/{id}/approve` are not reachable from the scheduler or any batch/background code path — only from the user-facing route
- Test the double-approval-is-a-no-op case for calendar proposals
- Test that the scheduled job's sequential steps handle a failure in an earlier step (e.g., sync fails) by not proceeding to classify/digest on stale data
- Test the retention cleanup job's exclusion logic directly: seed a message past the 90-day window with a pending proposal, confirm it survives a cleanup run; seed one without any exclusion condition, confirm it's deleted
- Manual end-to-end test: let the full scheduled pipeline run for real over several days, review the digest and traces each morning, and at least once, actually edit and send a real draft and approve a real calendar proposal to confirm the full loop works end to end