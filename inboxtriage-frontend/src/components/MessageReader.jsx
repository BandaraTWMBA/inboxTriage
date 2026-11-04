import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/index.js";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "./Toast.jsx";
import TriageTag, { PRIORITIES, PRIORITY_ORDER } from "./TriageTag.jsx";
import { ErrorState } from "./EmptyState.jsx";
import { fmtDateTime, pct } from "../lib/format.js";

export default function MessageReader({ id, onChanged }) {
  const navigate = useNavigate();
  const toast = useToast();
  const { data: m, error, loading, reload, setData } = useAsync(() => api.getMessage(id), [id]);
  const [busy, setBusy] = useState("");

  // Opening a message marks it read.
  useEffect(() => {
    if (m && !m.is_read) {
      setData((x) => ({ ...x, is_read: true }));
      api.markRead(m.id).finally(() => onChanged?.());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [m?.id]);

  async function relabel(priority) {
    setBusy("label");
    try {
      const updated = await api.relabelMessage(m.id, priority);
      setData((x) => ({ ...x, ...updated }));
      toast(`Moved to ${PRIORITIES[priority].label}. Saved as feedback.`);
      onChanged?.();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy("");
    }
  }

  async function draftReply() {
    setBusy("draft");
    try {
      const d = await api.createDraft(m.id);
      onChanged?.();
      navigate(`/drafts/${d.id}`);
    } catch (e) {
      toast(e.message, "error");
      setBusy("");
    }
  }

  if (loading && !m) return <div className="reader" aria-busy="true"><p className="muted">Loading message…</p></div>;
  if (error && !m) return <ErrorState error={error} onRetry={reload} what="this message" />;

  return (
    <article className="reader">
      <Link to="/inbox" className="reader__back">Back to inbox</Link>

      <h1 className="reader__subject">{m.subject}</h1>
      <p className="reader__from">
        {m.sender} &lt;{m.sender_email}&gt; on {fmtDateTime(m.received_at)}
      </p>

      <div className="verdict" style={{ "--c": `var(--${m.priority === "needs_reply" ? "reply" : m.priority})` }}>
        <div className="verdict__top">
          <TriageTag priority={m.priority} />
          <span className="muted">{pct(m.confidence)} confident</span>
        </div>
        <p className="verdict__reason">{m.reason}</p>
        <div className="verdict__fix">
          <span className="muted">Not right? Move it to</span>
          {PRIORITY_ORDER.filter((p) => p !== m.priority).map((p) => (
            <button key={p} className="chip" disabled={busy === "label"} onClick={() => relabel(p)}>
              {PRIORITIES[p].label}
            </button>
          ))}
        </div>
      </div>

      <div className="reader__actions">
        <button className="btn btn--primary" onClick={draftReply} disabled={busy === "draft"}>
          {busy === "draft" ? "Writing draft…" : m.has_draft ? "Open draft" : "Draft a reply"}
        </button>
      </div>

      <div className="reader__body">{m.body || "This email has no text content."}</div>

      {m.labels?.length > 0 && (
        <ul className="labels" aria-label="Gmail labels">
          {m.labels.map((l) => <li key={l}>{l.replace("CATEGORY_", "").toLowerCase()}</li>)}
        </ul>
      )}
    </article>
  );
}
