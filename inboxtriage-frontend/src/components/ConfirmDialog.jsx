import { useEffect, useRef } from "react";

// Native <dialog>: focus trapping, Esc to close and backdrop come for free.
export default function ConfirmDialog({
  open, title, children, confirmLabel, cancelLabel = "Cancel", danger = false, busy = false,
  onConfirm, onCancel,
}) {
  const ref = useRef(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  return (
    <dialog ref={ref} className="dialog" onCancel={(e) => { e.preventDefault(); if (!busy) onCancel(); }}>
      <h2 className="dialog__title">{title}</h2>
      <div className="dialog__body">{children}</div>
      <div className="dialog__actions">
        <button className="btn btn--quiet" onClick={onCancel} disabled={busy}>{cancelLabel}</button>
        <button className={`btn ${danger ? "btn--danger-solid" : "btn--primary"}`} onClick={onConfirm} disabled={busy}>
          {busy ? "Working…" : confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
