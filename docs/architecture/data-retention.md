# Data Retention Policy

**Status:** Locked in — do not change retention windows without updating this doc first

This project processes real personal email. Retention is a deliberate tradeoff between two competing needs: (1) minimizing how much sensitive personal data sits in local storage indefinitely, and (2) preserving enough history for the eval harness (Feature 03) and personalization loop (Feature 04) to actually work. See `guardrails.md` for the related data-handling rules this policy sits alongside.

## Retention windows by table

| Table | Retention | Deletion behavior | Why |
|---|---|---|---|
| `messages` | 90 days rolling | Hard delete once older than window, **unless** excluded below | Enough history for eval/personalization use cases; beyond that, if it hasn't been acted on, it's stale |
| `classifications` | Same lifecycle as parent `messages` | Cascade delete when the parent `messages` row is purged | No reason to keep classifications for emails that no longer exist |
| `user_feedback` | Indefinite | Never auto-deleted | This is the personalization signal (Feature 04) — low volume, high value, must not expire |
| Qdrant embeddings (mirrors `user_feedback`) | Indefinite | Never auto-deleted; deleted only if the source `user_feedback` row is manually deleted | Same reasoning as above — retrieval index over a permanent table |
| `agent_steps` | 30 days | Hard delete once older than window | Debugging/trace value drops sharply after the first few weeks; this is not meant to be a permanent audit log |
| `calendar_proposals` | 90 days for `resolved_at IS NOT NULL` (approved/rejected); **never auto-deleted while `status='pending'`** | Hard delete resolved rows past window; pending rows are excluded from any cleanup job entirely | A pending proposal must stay visible until the user explicitly acts on it — silently deleting it would be equivalent to a forced rejection, which violates the consent principle in `guardrails.md` rule 7 |
| `golden_set.jsonl` (Feature 03) | Indefinite | Never auto-deleted | Curated reference data, not raw inbox state — treat it like versioned code, not like transient application data |

## Exclusion rule — messages tied to unresolved state

A `messages` row must **not** be purged by the 90-day cleanup job if any of the following are true, even if it's past the window:
- It has a `calendar_proposals` row with `status='pending'`
- It has an active `snoozed_until` date in the future (Feature 05)
- It has a draft in Gmail Drafts that has not been sent or discarded (best-effort check — if the Gmail API call to verify draft status fails, err on the side of not deleting rather than silently purging)

The cleanup job must check these conditions before deleting, not just filter on `received_at` age alone.

## Implementation

- A single scheduled cleanup job, run weekly via the same APScheduler instance introduced in Feature 06 — no separate scheduling infrastructure needed
- Cleanup order: `agent_steps` (30-day rule) → resolved `calendar_proposals` (90-day rule) → `messages` past 90 days that pass the exclusion check (cascades to `classifications`)
- Log every cleanup run: timestamp, row counts deleted per table — append to a simple log file or table, so deletion activity is auditable if something looks wrong later
- Never delete `user_feedback`, its Qdrant mirror, or `golden_set.jsonl` from this job — these are explicitly out of scope for automated cleanup

## What NOT to do

- Do not extend retention windows "just in case" without updating this doc — the whole point is a deliberate, documented tradeoff, not silent data accumulation
- Do not let the cleanup job delete anything tied to unresolved consent state (pending calendar proposals, unsent drafts, active snoozes)
- Do not apply the same short retention window to `user_feedback`/Qdrant — deleting personalization data on a timer would quietly degrade Feature 04's whole purpose
- Do not skip logging cleanup runs — silent deletion with no record makes debugging "where did my email go" impossible

## Relationship to the free-tier LLM privacy tradeoff

Keeping the raw `messages` archive to a 90-day rolling window (rather than accumulating indefinitely) directly reduces exposure from the free-tier Gemini data-usage tradeoff discussed for Feature 02 — a smaller local archive of real personal email is less at risk if the local machine or database were ever compromised. This is a secondary benefit of the retention policy, not its primary justification, but worth keeping in mind when deciding whether to shorten the window further.