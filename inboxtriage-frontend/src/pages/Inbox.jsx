import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/index.js";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../components/Toast.jsx";
import TriageTag, { PRIORITIES, PRIORITY_ORDER } from "../components/TriageTag.jsx";
import MessageReader from "../components/MessageReader.jsx";
import EmptyState, { ErrorState } from "../components/EmptyState.jsx";
import { timeAgo } from "../lib/format.js";

export default function Inbox() {
  const { id } = useParams();
  const toast = useToast();
  const [priority, setPriority] = useState("");
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 250);
    return () => clearTimeout(t);
  }, [query]);

  const list = useAsync(() => api.listMessages({ priority, q: debounced }), [priority, debounced]);

  async function sync() {
    setSyncing(true);
    try {
      const r = await api.syncNow();
      toast(r.new_messages ? `Synced. ${r.new_messages} new messages.` : "Synced. Nothing new.");
      list.reload({ silent: true });
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSyncing(false);
    }
  }

  const rows = list.data ?? [];

  return (
    <div className={`split${id ? " has-selection" : ""}`}>
      <section className="split__list" aria-label="Messages">
        <div className="listbar">
          <div className="listbar__row">
            <input
              className="input"
              type="search"
              placeholder="Search mail"
              aria-label="Search mail"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button className="btn btn--quiet" onClick={sync} disabled={syncing}>
              {syncing ? "Syncing…" : "Sync now"}
            </button>
          </div>
          <div className="filters" role="group" aria-label="Filter by priority">
            <button className="chip" aria-pressed={priority === ""} onClick={() => setPriority("")}>All</button>
            {PRIORITY_ORDER.map((p) => (
              <button key={p} className="chip" aria-pressed={priority === p} onClick={() => setPriority(p)}>
                {PRIORITIES[p].label}
              </button>
            ))}
          </div>
        </div>

        {list.error && !list.data ? (
          <ErrorState error={list.error} onRetry={list.reload} what="your inbox" />
        ) : list.loading && !list.data ? (
          <p className="muted pad" aria-busy="true">Loading messages…</p>
        ) : rows.length === 0 ? (
          <EmptyState title="No messages here">
            {debounced || priority ? "Try a different filter or search." : "Sync to pull in your latest mail."}
          </EmptyState>
        ) : (
          <ul className="msglist">
            {rows.map((m) => (
              <li key={m.id}>
                <Link
                  to={`/inbox/${m.id}`}
                  className={`msg${m.is_read ? "" : " msg--unread"}`}
                  aria-current={String(m.id) === id ? "page" : undefined}
                >
                  <div className="msg__top">
                    <span className="msg__sender">{m.sender}</span>
                    <span className="msg__time">{timeAgo(m.received_at)}</span>
                  </div>
                  <div className="msg__subject">{m.subject}</div>
                  <div className="msg__snippet">{m.snippet}</div>
                  <div className="msg__foot">
                    <TriageTag priority={m.priority} />
                    {m.has_draft && <span className="pill">Draft ready</span>}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="split__detail">
        {id ? (
          <MessageReader key={id} id={id} onChanged={() => list.reload({ silent: true })} />
        ) : (
          <EmptyState title="Select a message">
            Pick an email on the left to read it, see why it was ranked this way, and draft a reply.
          </EmptyState>
        )}
      </section>
    </div>
  );
}
