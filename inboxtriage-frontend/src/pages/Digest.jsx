import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/index.js";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../components/Toast.jsx";
import TriageTag, { PRIORITY_ORDER } from "../components/TriageTag.jsx";
import EmptyState, { ErrorState } from "../components/EmptyState.jsx";
import { timeAgo } from "../lib/format.js";

export default function Digest() {
  const { data, error, loading, reload, setData } = useAsync(() => api.getDigest(), []);
  const toast = useToast();
  const [refreshing, setRefreshing] = useState(false);

  async function regenerate() {
    setRefreshing(true);
    try {
      setData(await api.regenerateDigest());
      toast("Digest refreshed.");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setRefreshing(false);
    }
  }

  async function rate(item, useful) {
    const next = useful ? "useful" : "not_useful";
    if (item.feedback === next) return;
    const previous = item.feedback;
    setData((d) => ({ ...d, items: d.items.map((x) => (x.id === item.id ? { ...x, feedback: next } : x)) }));
    try {
      await api.digestFeedback(item.id, useful);
    } catch (e) {
      setData((d) => ({ ...d, items: d.items.map((x) => (x.id === item.id ? { ...x, feedback: previous } : x)) }));
      toast(e.message, "error");
    }
  }

  if (loading && !data) return <div className="page"><p className="muted" aria-busy="true">Loading digest…</p></div>;
  if (error && !data) return <div className="page"><ErrorState error={error} onRetry={reload} what="the digest" /></div>;

  const groups = PRIORITY_ORDER
    .map((p) => ({ priority: p, items: data.items.filter((i) => i.priority === p) }))
    .filter((g) => g.items.length > 0);

  return (
    <div className="page">
      <div className="page__inner">
        <header className="page-head">
          <div>
            <h1>Digest</h1>
            <p className="muted">Generated {timeAgo(data.generated_at)}</p>
          </div>
          <button className="btn btn--quiet" onClick={regenerate} disabled={refreshing}>
            {refreshing ? "Refreshing…" : "Refresh digest"}
          </button>
        </header>

        <p className="digest-summary">{data.summary}</p>

        {groups.length === 0 ? (
          <EmptyState title="Nothing to report">New mail will show up here after the next sync.</EmptyState>
        ) : (
          groups.map((g) => (
            <section key={g.priority} className="digest-group">
              <h2 className="digest-group__head"><TriageTag priority={g.priority} /></h2>
              <ul>
                {g.items.map((item) => (
                  <li key={item.id} className="digest-item">
                    <div>
                      <Link to={`/inbox/${item.message_id}`} className="digest-item__title">{item.headline}</Link>
                      <p className="digest-item__why">{item.why}</p>
                    </div>
                    <div className="rate" role="group" aria-label={`Was "${item.headline}" useful?`}>
                      <button className="chip" aria-pressed={item.feedback === "useful"} onClick={() => rate(item, true)}>
                        Useful
                      </button>
                      <button className="chip" aria-pressed={item.feedback === "not_useful"} onClick={() => rate(item, false)}>
                        Not useful
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
