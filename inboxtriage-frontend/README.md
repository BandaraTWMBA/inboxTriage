# InboxTriage frontend

React + Vite (plain JavaScript) UI for InboxTriage. It runs on built-in sample data by default, so you can use every screen before the FastAPI backend exists.

## Run it

```bash
npm install
cp .env.example .env     # VITE_USE_MOCK=true by default
npm run dev              # http://localhost:5173
npm run build            # production bundle in dist/
```

To use the real backend, set `VITE_USE_MOCK=false` in `.env`. In dev, Vite proxies `/api/*` to `http://localhost:8000` (override with `VITE_BACKEND_URL`), which keeps the session cookie same-origin and avoids CORS setup.

## Screens

| Route | What it does | Backend feature |
|---|---|---|
| `/login` | Google sign-in | Google OAuth login |
| `/inbox`, `/inbox/:id` | Two-panel browse and read view with priority filters, search, sync, and relabel (feedback) | 01 ingestion, 02 classification + label sync |
| `/digest` | Prioritised summary, with Useful / Not useful feedback per item | Digest and feedback loop |
| `/drafts`, `/drafts/:id` | Edit an agent-written reply. Sending always needs a confirmation click | Agentic tool loop (`gmail.compose`) |
| `/calendar` | Suggested events. Each needs Add to calendar or Dismiss | Agentic tool loop (Calendar API) |
| `/status` | Sync health, 24h counts, classifier accuracy, Google scopes, scheduled jobs, retention | Evaluation harness, observability, 90-day retention |

Guardrails are built into the UI: there is no code path that sends an email or creates an event without an explicit user click, and sending is behind a confirm dialog.

## Project layout

```
src/
  api/
    client.js      real fetch client (credentials: "include")
    mock.js        sample-data backend with the same method names
    index.js       picks one based on VITE_USE_MOCK
  auth/            AuthContext: session, login, logout, 401 handling
  components/      Layout, TriageTag, MessageReader, ConfirmDialog, Toast, EmptyState
  hooks/useAsync.js
  lib/format.js    relative times and date ranges
  pages/           Login, Inbox, Digest, Drafts, Calendar, Status
  styles.css       design tokens and all styles
```

## Backend contract

All requests send the session cookie. Errors should return `{"detail": "message"}` with a proper status; a `401` signs the user out in the UI. Priorities are `urgent | needs_reply | fyi | noise`.

```
GET  /auth/google/login          redirect into Google OAuth, then back to the app with a session cookie
GET  /auth/me                    -> { name, email, picture }
POST /auth/logout

GET  /messages?priority=&q=      -> [{ id, sender, sender_email, subject, snippet, received_at,
                                       priority, confidence, reason, is_read, has_draft, labels }]
GET  /messages/{id}              -> same fields plus body (plain text)
POST /messages/{id}/feedback     { priority }  -> updated message (stores the correction for evals, syncs Gmail label)
POST /messages/{id}/read
POST /sync                       -> { last_run, last_result, fetched, new_messages, interval_minutes }

GET  /digest                     -> { generated_at, summary, items: [{ id, message_id, priority, headline, why, feedback }] }
POST /digest/regenerate          -> digest
POST /digest/items/{id}/feedback { useful: bool }

GET    /drafts                   -> [{ id, message_id, to, subject, body, status: "draft"|"sent", updated_at }]
GET    /drafts/{id}              -> draft plus original: { sender, subject, body }
POST   /drafts                   { message_id } -> draft (idempotent: returns the open draft if one exists)
PUT    /drafts/{id}              { to, subject, body } -> draft
POST   /drafts/{id}/send         human-triggered only -> draft with status "sent"
DELETE /drafts/{id}

GET  /calendar/proposals         -> [{ id, message_id, title, start, end, location, rationale,
                                       status: "pending"|"approved"|"rejected" }]
POST /calendar/proposals/{id}/approve   creates the Google Calendar event
POST /calendar/proposals/{id}/reject

GET  /status                     -> { sync, counts_24h, total_messages, retention_days, next_cleanup,
                                      scopes: [{ scope, granted }], jobs: [{ name, schedule, next_run }],
                                      eval: { accuracy, labeled, last_run, per_class } }
```

`src/api/mock.js` is the reference for exact response shapes.

## Notes for production

- Set the OAuth redirect URI in Google Cloud to the backend callback, and have the backend redirect to the frontend origin after login.
- Use `SameSite=Lax` and `HttpOnly` on the session cookie. Serving the built frontend and the API from the same origin (or behind one reverse proxy at `/api`) keeps it simple.
- Message bodies are rendered as plain text, never as HTML, so email content can't inject markup.
