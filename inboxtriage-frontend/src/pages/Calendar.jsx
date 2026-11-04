import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/index.js";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../components/Toast.jsx";
import EmptyState, { ErrorState } from "../components/EmptyState.jsx";
import { fmtRange } from "../lib/format.js";

const notify = () => window.dispatchEvent(new Event("it:proposals-changed"));

export default function Calendar() {
  const { data, error, loading, reload, setData } = useAsync(() => api.listProposals(), []);
  const toast = useToast();
  const [busyId, setBusyId] = useState(null);

  async function decide(p, action) {
    setBusyId(p.id);
    try {
      const updated = action === "add" ? await api.approveProposal(p.id) : await api.rejectProposal(p.id);
      setData((rows) => rows.map((x) => (x.id === p.id ? updated : x)));
      toast(action === "add" ? `Added "${p.title}" to your calendar.` : `Dismissed "${p.title}".`);
      notify();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusyId(null);
    }
  }

  if (loading && !data) return <div className="page"><p className="muted" aria-busy="true">Loading events…</p></div>;
  if (error && !data) return <div className="page"><ErrorState error={error} onRetry={reload} what="calendar suggestions" /></div>;

  const pending = data.filter((p) => p.status === "pending");
  const decided = data.filter((p) => p.status !== "pending");

  return (
    <div className="page">
      <div className="page__inner">
        <header className="page-head">
          <div>
            <h1>Calendar</h1>
            <p className="muted">Events found in your email. Nothing is added until you say so.</p>
          </div>
        </header>

        <h2 className="section-title">Waiting for your decision</h2>
        {pending.length === 0 ? (
          <EmptyState title="Nothing to decide">When an email mentions a meeting or deadline, a suggested event shows up here.</EmptyState>
        ) : (
          pending.map((p) => (
            <article key={p.id} className="proposal">
              <h3 className="proposal__title">{p.title}</h3>
              <p className="proposal__when">{fmtRange(p.start, p.end)}</p>
              {p.location && <p className="muted">{p.location}</p>}
              <p className="proposal__why">
                {p.rationale} <Link to={`/inbox/${p.message_id}`}>View email</Link>
              </p>
              <div className="proposal__actions">
                <button className="btn btn--primary" disabled={busyId === p.id} onClick={() => decide(p, "add")}>
                  {busyId === p.id ? "Working…" : "Add to calendar"}
                </button>
                <button className="btn btn--quiet" disabled={busyId === p.id} onClick={() => decide(p, "dismiss")}>
                  Dismiss
                </button>
              </div>
            </article>
          ))
        )}

        {decided.length > 0 && (
          <>
            <h2 className="section-title section-title--spaced">Already decided</h2>
            <ul className="decided">
              {decided.map((p) => (
                <li key={p.id}>
                  <div>
                    <strong>{p.title}</strong>
                    <span className="muted"> {fmtRange(p.start, p.end)}</span>
                  </div>
                  <span className={`pill${p.status === "approved" ? " pill--done" : ""}`}>
                    {p.status === "approved" ? "Added" : "Dismissed"}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
