import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/index.js";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../components/Toast.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import EmptyState, { ErrorState } from "../components/EmptyState.jsx";
import { timeAgo } from "../lib/format.js";

export default function Drafts() {
  const { id } = useParams();
  const navigate = useNavigate();
  const list = useAsync(() => api.listDrafts(), []);
  const rows = list.data ?? [];

  return (
    <div className={`split split--drafts${id ? " has-selection" : ""}`}>
      <section className="split__list" aria-label="Drafts">
        <div className="listbar"><h1 className="listbar__title">Drafts</h1></div>
        {list.error && !list.data ? (
          <ErrorState error={list.error} onRetry={list.reload} what="your drafts" />
        ) : list.loading && !list.data ? (
          <p className="muted pad" aria-busy="true">Loading drafts…</p>
        ) : rows.length === 0 ? (
          <EmptyState title="No drafts yet">
            Open an email in your inbox and choose Draft a reply. Nothing is sent until you send it.
          </EmptyState>
        ) : (
          <ul className="msglist">
            {rows.map((d) => (
              <li key={d.id}>
                <Link to={`/drafts/${d.id}`} className="msg" aria-current={String(d.id) === id ? "page" : undefined}>
                  <div className="msg__top">
                    <span className="msg__sender">{d.to}</span>
                    <span className="msg__time">{timeAgo(d.updated_at)}</span>
                  </div>
                  <div className="msg__subject">{d.subject}</div>
                  <div className="msg__foot">
                    <span className={`pill${d.status === "sent" ? " pill--done" : ""}`}>
                      {d.status === "sent" ? "Sent" : "Draft"}
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="split__detail">
        {id ? (
          <DraftEditor
            key={id}
            id={id}
            onChanged={() => list.reload({ silent: true })}
            onGone={() => { list.reload({ silent: true }); navigate("/drafts"); }}
          />
        ) : (
          <EmptyState title="Select a draft">Review the reply, edit it, and send it when you're ready.</EmptyState>
        )}
      </section>
    </div>
  );
}

function DraftEditor({ id, onChanged, onGone }) {
  const toast = useToast();
  const { data: draft, error, loading, reload, setData } = useAsync(() => api.getDraft(id), [id]);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [confirm, setConfirm] = useState(null); // "send" | "discard" | null
  const [working, setWorking] = useState(false);

  useEffect(() => {
    if (draft) setForm({ to: draft.to, subject: draft.subject, body: draft.body });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft?.id]);

  if (loading && !draft) return <div className="reader"><p className="muted" aria-busy="true">Loading draft…</p></div>;
  if (error && !draft) return <ErrorState error={error} onRetry={reload} what="this draft" />;
  if (!form) return null;

  const sent = draft.status === "sent";
  const dirty = form.to !== draft.to || form.subject !== draft.subject || form.body !== draft.body;
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function save() {
    setSaving(true);
    try {
      const updated = await api.saveDraft(draft.id, form);
      setData(updated);
      onChanged();
      toast("Draft saved.");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSaving(false);
    }
  }

  async function send() {
    setWorking(true);
    try {
      if (dirty) setData(await api.saveDraft(draft.id, form));
      setData(await api.sendDraft(draft.id));
      setConfirm(null);
      onChanged();
      toast("Reply sent.");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setWorking(false);
    }
  }

  async function discard() {
    setWorking(true);
    try {
      await api.discardDraft(draft.id);
      toast("Draft discarded.");
      onGone();
    } catch (e) {
      toast(e.message, "error");
      setWorking(false);
    }
  }

  return (
    <article className="reader">
      <Link to="/drafts" className="reader__back">Back to drafts</Link>
      <h1 className="reader__subject">{sent ? "Sent reply" : "Review your reply"}</h1>
      <p className="note">
        {sent
          ? `Sent ${timeAgo(draft.updated_at)}.`
          : "InboxTriage wrote this draft. It stays here until you choose Send reply."}
      </p>

      <div className="form">
        <label className="field">
          <span>To</span>
          <input className="input" value={form.to} onChange={set("to")} disabled={sent} />
        </label>
        <label className="field">
          <span>Subject</span>
          <input className="input" value={form.subject} onChange={set("subject")} disabled={sent} />
        </label>
        <label className="field">
          <span>Message</span>
          <textarea className="input input--area" rows={12} value={form.body} onChange={set("body")} disabled={sent} />
        </label>
      </div>

      {!sent && (
        <div className="reader__actions">
          <button className="btn btn--primary" onClick={() => setConfirm("send")}>Send reply</button>
          <button className="btn btn--quiet" onClick={save} disabled={!dirty || saving}>
            {saving ? "Saving…" : "Save draft"}
          </button>
          <button className="btn btn--danger" onClick={() => setConfirm("discard")}>Discard draft</button>
        </div>
      )}

      {draft.original && (
        <details className="original">
          <summary>Email you're replying to</summary>
          <p className="muted">{draft.original.sender}: {draft.original.subject}</p>
          <div className="reader__body reader__body--small">{draft.original.body}</div>
        </details>
      )}

      <ConfirmDialog
        open={confirm === "send"}
        title="Send this reply?"
        confirmLabel="Send reply"
        busy={working}
        onConfirm={send}
        onCancel={() => setConfirm(null)}
      >
        This sends an email to <strong>{form.to}</strong> from your Gmail account. InboxTriage never sends mail on its own.
      </ConfirmDialog>
      <ConfirmDialog
        open={confirm === "discard"}
        title="Discard this draft?"
        confirmLabel="Discard draft"
        danger
        busy={working}
        onConfirm={discard}
        onCancel={() => setConfirm(null)}
      >
        The draft will be deleted. The original email stays in your inbox.
      </ConfirmDialog>
    </article>
  );
}
