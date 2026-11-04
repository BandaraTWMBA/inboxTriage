// Real backend client (FastAPI). All calls send the session cookie.
// Endpoint contract is documented in README.md.
const BASE = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, query } = {}) {
  const qs = query
    ? "?" +
      new URLSearchParams(
        Object.entries(query).filter(([, v]) => v !== undefined && v !== null && v !== "")
      ).toString()
    : "";
  let res;
  try {
    res = await fetch(`${BASE}${path}${qs}`, {
      method,
      credentials: "include",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Can't reach the server. Check that the backend is running.", 0);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(typeof detail === "string" ? detail : "Request failed", res.status);
  }
  return res.status === 204 ? null : res.json();
}

export const realApi = {
  loginUrl: () => `${BASE}/auth/google/login`,
  getMe: () => request("/auth/me"),
  logout: () => request("/auth/logout", { method: "POST" }),

  listMessages: (params) => request("/messages", { query: params }),
  getMessage: (id) => request(`/messages/${id}`),
  relabelMessage: (id, priority) =>
    request(`/messages/${id}/feedback`, { method: "POST", body: { priority } }),
  markRead: (id) => request(`/messages/${id}/read`, { method: "POST" }),
  syncNow: () => request("/sync", { method: "POST" }),

  getDigest: () => request("/digest"),
  regenerateDigest: () => request("/digest/regenerate", { method: "POST" }),
  digestFeedback: (itemId, useful) =>
    request(`/digest/items/${itemId}/feedback`, { method: "POST", body: { useful } }),

  listDrafts: () => request("/drafts"),
  getDraft: (id) => request(`/drafts/${id}`),
  createDraft: (messageId) => request("/drafts", { method: "POST", body: { message_id: messageId } }),
  saveDraft: (id, fields) => request(`/drafts/${id}`, { method: "PUT", body: fields }),
  sendDraft: (id) => request(`/drafts/${id}/send`, { method: "POST" }),
  discardDraft: (id) => request(`/drafts/${id}`, { method: "DELETE" }),

  listProposals: () => request("/calendar/proposals"),
  approveProposal: (id) => request(`/calendar/proposals/${id}/approve`, { method: "POST" }),
  rejectProposal: (id) => request(`/calendar/proposals/${id}/reject`, { method: "POST" }),

  getStatus: () => request("/status"),
};
