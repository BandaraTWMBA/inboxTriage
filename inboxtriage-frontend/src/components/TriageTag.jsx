// The four priority levels the classifier assigns, in display order.
export const PRIORITY_ORDER = ["urgent", "needs_reply", "fyi", "noise"];

export const PRIORITIES = {
  urgent: { label: "Urgent", hint: "Needs you today" },
  needs_reply: { label: "Reply needed", hint: "Someone is waiting on you" },
  fyi: { label: "FYI", hint: "Worth knowing, no action" },
  noise: { label: "Noise", hint: "Promotions and automated mail" },
};

export default function TriageTag({ priority }) {
  const p = PRIORITIES[priority] ?? { label: priority };
  return <span className={`tag tag--${priority}`}>{p.label}</span>;
}
