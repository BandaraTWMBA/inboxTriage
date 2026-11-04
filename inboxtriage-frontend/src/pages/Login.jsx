import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import { USE_MOCK } from "../api/index.js";
import TriageTag from "../components/TriageTag.jsx";

const SAMPLE = [
  { priority: "urgent", text: "API review before 3 pm" },
  { priority: "needs_reply", text: "Confirm your demo slot" },
  { priority: "fyi", text: "CI passed on feature branch" },
  { priority: "noise", text: "48-hour flash sale" },
];

export default function Login() {
  const { user, loading, login } = useAuth();
  const [busy, setBusy] = useState(false);

  if (!loading && user) return <Navigate to="/inbox" replace />;

  async function go() {
    setBusy(true);
    try { await login(); } finally { setBusy(false); }
  }

  return (
    <div className="login">
      <section className="login__story" aria-hidden="true">
        <p className="login__quote">Your inbox, sorted by what needs you.</p>
        <ul className="login__sample">
          {SAMPLE.map((s) => (
            <li key={s.text}>
              <TriageTag priority={s.priority} />
              <span>{s.text}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="login__panel">
        <div className="login__box">
          <img src="/favicon.svg" alt="" width="40" height="40" />
          <h1>Sign in to InboxTriage</h1>
          <p className="muted">
            Connect your Google account. InboxTriage reads your mail to rank it, and never sends an email or
            creates an event without your approval.
          </p>
          <button className="btn btn--primary btn--wide" onClick={go} disabled={busy || loading}>
            {busy ? "Connecting…" : "Continue with Google"}
          </button>
          {USE_MOCK && <p className="note">Running on sample data. No Google account is needed.</p>}
        </div>
      </section>
    </div>
  );
}
