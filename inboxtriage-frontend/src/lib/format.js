export function timeAgo(iso) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} h ago`;
  const d = Math.floor(h / 24);
  return `${d} d ago`;
}

export function timeUntil(iso) {
  const s = (new Date(iso).getTime() - Date.now()) / 1000;
  if (s < 60) return "any moment";
  const m = Math.floor(s / 60);
  if (m < 60) return `in ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `in ${h} h`;
  return `in ${Math.floor(h / 24)} d`;
}

const dateOpts = { weekday: "short", month: "short", day: "numeric" };
const timeOpts = { hour: "numeric", minute: "2-digit" };

export function fmtDateTime(iso) {
  return new Date(iso).toLocaleString(undefined, { ...dateOpts, ...timeOpts });
}

export function fmtRange(startIso, endIso) {
  const s = new Date(startIso);
  const e = new Date(endIso);
  const day = s.toLocaleDateString(undefined, dateOpts);
  const t1 = s.toLocaleTimeString(undefined, timeOpts);
  const t2 = e.toLocaleTimeString(undefined, timeOpts);
  return `${day}, ${t1} to ${t2}`;
}

export const pct = (x) => `${Math.round(x * 100)}%`;
