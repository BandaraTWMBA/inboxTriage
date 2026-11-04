export default function EmptyState({ title, children, action }) {
  return (
    <div className="empty">
      <h2 className="empty__title">{title}</h2>
      {children && <p className="empty__text">{children}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry, what = "this page" }) {
  return (
    <div className="empty">
      <h2 className="empty__title">Couldn't load {what}</h2>
      <p className="empty__text">{error?.message || "Something went wrong."}</p>
      {onRetry && <button className="btn btn--quiet" onClick={() => onRetry()}>Try again</button>}
    </div>
  );
}
