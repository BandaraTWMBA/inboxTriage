import { useState } from "react";
import { api } from "../api/index.js";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../components/Toast.jsx";
import { PRIORITIES, PRIORITY_ORDER } from "../components/TriageTag.jsx";
import { ErrorState } from "../components/EmptyState.jsx";
import { fmtDateTime, pct, timeAgo, timeUntil } from "../lib/format.js";

const cssVar = (p) => `var(--${p === "needs_reply" ? "reply" : p})`;

export default function Status() {
  const { data, error, loading, reload } = useAsync(() => api.getStatus(), []);
  const toast = useToast();
  const [syncing, setSyncing] = useState(false);

  async function sync() {
    setSyncing(true);
    try {
      await api.syncNow();
      await reload({ silent: true });
      toast("Synced.");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSyncing(false);
    }
  }

  if (loading && !data) return <div className="page"><p className="muted" aria-busy="true">Loading status…</p></div>;
  if (error && !data) return <div className="page"><ErrorState error={error} onRetry={reload} what="system status" /></div>;

  const counts = data.counts_24h;
  const max = Math.max(1, ...Object.values(counts));

  return (
    <div className="page">
      <div className="page__inner">
        <header className="page-head">
          <div>
            <h1>Status</h1>
            <p className="muted">How InboxTriage is doing behind the scenes.</p>
          </div>
        </header>

        <section className="block">
          <div className="block__head">
            <h2>Gmail sync</h2>
            <button className="btn btn--quiet" onClick={sync} disabled={syncing}>{syncing ? "Syncing…" : "Sync now"}</button>
          </div>
          <dl className="kv">
            <dt>Last sync</dt><dd>{timeAgo(data.sync.last_run)} ({data.sync.last_result === "ok" ? "succeeded" : "failed"})</dd>
            <dt>Last run</dt><dd>{data.sync.fetched} fetched, {data.sync.new_messages} new</dd>
            <dt>Runs every</dt><dd>{data.sync.interval_minutes} minutes</dd>
            <dt>Messages stored</dt><dd>{data.total_messages.toLocaleString()}</dd>
          </dl>
        </section>

        <section className="block">
          <h2>Last 24 hours</h2>
          <ul className="bars">
            {PRIORITY_ORDER.map((p) => (
              <li key={p}>
                <span className="bars__label">{PRIORITIES[p].label}</span>
                <span className="bars__track">
                  <span className="bars__fill" style={{ width: `${(counts[p] / max) * 100}%`, background: cssVar(p) }} />
                </span>
                <span className="bars__n">{counts[p]}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="block">
          <h2>Classifier accuracy</h2>
          <p className="muted">
            Measured on {data.eval.labeled} emails you labelled. Last run {timeAgo(data.eval.last_run)}.
          </p>
          <p className="stat">{pct(data.eval.accuracy)} overall</p>
          <ul className="bars">
            {PRIORITY_ORDER.map((p) => (
              <li key={p}>
                <span className="bars__label">{PRIORITIES[p].label}</span>
                <span className="bars__track">
                  <span className="bars__fill" style={{ width: pct(data.eval.per_class[p]), background: cssVar(p) }} />
                </span>
                <span className="bars__n">{pct(data.eval.per_class[p])}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="block">
          <h2>Google access</h2>
          <ul className="scopes">
            {data.scopes.map((s) => (
              <li key={s.scope}>
                <code>{s.scope}</code>
                <span className={`pill${s.granted ? " pill--done" : ""}`}>{s.granted ? "Granted" : "Not granted"}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="block">
          <h2>Scheduled jobs</h2>
          <table className="table">
            <thead><tr><th>Job</th><th>Schedule</th><th>Next run</th></tr></thead>
            <tbody>
              {data.jobs.map((j) => (
                <tr key={j.name}>
                  <td>{j.name}</td>
                  <td>{j.schedule}</td>
                  <td title={fmtDateTime(j.next_run)}>{timeUntil(j.next_run)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="block">
          <h2>Data retention</h2>
          <p>
            Emails are kept for {data.retention_days} days, then deleted by a weekly cleanup. The next cleanup is{" "}
            {timeUntil(data.next_cleanup)}.
          </p>
        </section>
      </div>
    </div>
  );
}
