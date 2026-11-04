// Sample-data backend used when VITE_USE_MOCK=true.
// It mirrors the shape of the real API so the UI can be built and demoed without FastAPI running.
import { ApiError } from "./client.js";

const delay = (ms = 250) => new Promise((r) => setTimeout(r, ms));
const clone = (x) => JSON.parse(JSON.stringify(x));
const ago = (mins) => new Date(Date.now() - mins * 60_000).toISOString();
const inHours = (h) => new Date(Date.now() + h * 3_600_000).toISOString();

let session = (() => {
  try {
    return localStorage.getItem("it_mock_session") === "1";
  } catch {
    return false;
  }
})();

const user = { name: "Budhathri", email: "budhathri@example.com", picture: null };

let messages = [
  {
    id: 1, thread_id: "t1", sender: "Nimali Perera", sender_email: "nimali@agrithmics.example",
    subject: "Field Collection Register: API review before 3 pm",
    received_at: ago(22), priority: "urgent", confidence: 0.94, is_read: false, has_draft: false,
    reason: "Direct request from your supervisor with a same-day deadline.",
    labels: ["INBOX", "IMPORTANT"],
    body: "Hi,\n\nCould you go through the collection endpoints before the 3 pm review? Two things I want checked: the pagination on /collections and the error shape when a farmer ID is missing.\n\nIf anything blocks you, message me directly and I'll free up ten minutes.\n\nThanks,\nNimali",
  },
  {
    id: 2, thread_id: "t2", sender: "Dilan Fernando", sender_email: "dilan@agrithmics.example",
    subject: "Sync on SmartAuction payload mapping",
    received_at: ago(75), priority: "needs_reply", confidence: 0.88, is_read: false, has_draft: false,
    reason: "Asks you a direct question and proposes a meeting time.",
    labels: ["INBOX"],
    body: "Hey,\n\nI looked at the SmartAuction producer response and the lot fields don't line up with our Sales model. Do you have time tomorrow at 10:30 to go over the mapping together?\n\nI'll bring the sample payload.\n\nDilan",
  },
  {
    id: 3, thread_id: "t3", sender: "Google Cloud", sender_email: "noreply@google.example",
    subject: "Action required: your OAuth consent screen is in testing",
    received_at: ago(140), priority: "needs_reply", confidence: 0.71, is_read: true, has_draft: false,
    reason: "Automated notice, but it affects your Gmail sign-in and has an expiry.",
    labels: ["INBOX", "CATEGORY_UPDATES"],
    body: "Your OAuth consent screen is still in Testing status. Refresh tokens for test users expire after 7 days.\n\nTo keep tokens valid, publish the app or re-authenticate each week.",
  },
  {
    id: 4, thread_id: "t4", sender: "DeepLearning.AI", sender_email: "hello@dl.example",
    subject: "Your next lesson is ready: Agentic design patterns",
    received_at: ago(260), priority: "fyi", confidence: 0.9, is_read: true, has_draft: false,
    reason: "Course progress update. No action needed.",
    labels: ["INBOX", "CATEGORY_UPDATES"],
    body: "You're 62% through the course. The next module covers reflection, tool use and planning patterns.\n\nPick up where you left off whenever you're ready.",
  },
  {
    id: 5, thread_id: "t5", sender: "GitHub", sender_email: "notifications@github.example",
    subject: "[inboxtriage] CI passed on feature/gmail-ingestion",
    received_at: ago(310), priority: "fyi", confidence: 0.93, is_read: true, has_draft: false,
    reason: "Build notification with a passing result.",
    labels: ["INBOX"],
    body: "All checks have passed on feature/gmail-ingestion.\n\n3 jobs completed in 1m 42s.",
  },
  {
    id: 6, thread_id: "t6", sender: "Kavindi Silva", sender_email: "kavindi@uni.example",
    subject: "Project demo schedule: please confirm your slot",
    received_at: ago(480), priority: "needs_reply", confidence: 0.83, is_read: false, has_draft: false,
    reason: "Asks for confirmation of a date and time.",
    labels: ["INBOX"],
    body: "Hi,\n\nThe final-year project demos are on Thursday. Your slot is 2:00 pm to 2:20 pm in Lab B. Please confirm you can make it by tomorrow evening.\n\nKavindi",
  },
  {
    id: 7, thread_id: "t7", sender: "Daily Deals", sender_email: "promo@deals.example",
    subject: "48-hour flash sale: up to 70% off",
    received_at: ago(600), priority: "noise", confidence: 0.97, is_read: true, has_draft: false,
    reason: "Bulk promotional email.",
    labels: ["INBOX", "CATEGORY_PROMOTIONS"],
    body: "Flash sale ends Thursday at midnight. Shop now.",
  },
  {
    id: 8, thread_id: "t8", sender: "LinkedIn", sender_email: "jobs@linkedin.example",
    subject: "12 new jobs match your AI engineer search",
    received_at: ago(780), priority: "noise", confidence: 0.86, is_read: true, has_draft: false,
    reason: "Automated job alert digest.",
    labels: ["INBOX", "CATEGORY_SOCIAL"],
    body: "New jobs this week: AI engineer, ML engineer, Backend engineer (Python).",
  },
];

let drafts = [];
let draftSeq = 1;

let proposals = [
  {
    id: 1, message_id: 2, title: "SmartAuction mapping review with Dilan",
    start: inHours(23.5), end: inHours(24.5), location: "Google Meet", status: "pending",
    rationale: "Dilan asked to meet tomorrow at 10:30 to go over the payload mapping.",
  },
  {
    id: 2, message_id: 6, title: "Project demo (Lab B)",
    start: inHours(52), end: inHours(52.33), location: "Lab B", status: "pending",
    rationale: "Your demo slot is Thursday 2:00 pm to 2:20 pm.",
  },
  {
    id: 3, message_id: 1, title: "Collection API review",
    start: inHours(4), end: inHours(4.5), location: "Meeting room 2", status: "approved",
    rationale: "Review scheduled for 3 pm today.",
  },
];

let digest = {
  generated_at: ago(35),
  summary: "Two things need you today: the API review before 3 pm and a mapping meeting with Dilan. The rest can wait.",
  items: [
    { id: 11, message_id: 1, priority: "urgent", headline: "API review before 3 pm", why: "Nimali wants pagination and the missing farmer ID error checked.", feedback: null },
    { id: 12, message_id: 2, priority: "needs_reply", headline: "Confirm 10:30 mapping meeting", why: "Dilan is waiting on a yes or a new time.", feedback: null },
    { id: 13, message_id: 6, priority: "needs_reply", headline: "Confirm your demo slot", why: "Kavindi needs your answer by tomorrow evening.", feedback: null },
    { id: 14, message_id: 3, priority: "needs_reply", headline: "OAuth tokens will expire in testing mode", why: "Re-authenticate weekly or publish the consent screen.", feedback: null },
    { id: 15, message_id: 4, priority: "fyi", headline: "Next course lesson is ready", why: "Progress update only.", feedback: null },
    { id: 16, message_id: 5, priority: "fyi", headline: "CI passed on gmail-ingestion", why: "All 3 jobs green.", feedback: null },
  ],
};

const status = {
  sync: { last_run: ago(4), last_result: "ok", fetched: 14, new_messages: 3, interval_minutes: 15 },
  counts_24h: { urgent: 1, needs_reply: 3, fyi: 2, noise: 2 },
  total_messages: 412,
  retention_days: 90,
  next_cleanup: inHours(61),
  scopes: [
    { scope: "gmail.readonly", granted: true },
    { scope: "gmail.modify", granted: true },
    { scope: "gmail.compose", granted: true },
    { scope: "calendar.events", granted: true },
  ],
  jobs: [
    { name: "Gmail sync", schedule: "Every 15 minutes", next_run: inHours(0.2) },
    { name: "Daily digest", schedule: "Weekdays at 8:00", next_run: inHours(21) },
    { name: "Retention cleanup", schedule: "Sundays at 3:00", next_run: inHours(61) },
  ],
  eval: { accuracy: 0.87, labeled: 120, last_run: ago(60 * 26), per_class: { urgent: 0.92, needs_reply: 0.84, fyi: 0.89, noise: 0.95 } },
};

function replyTemplate(m) {
  const first = m.sender.split(" ")[0];
  return `Hi ${first},\n\nThanks for the note. I'll take a look and get back to you shortly.\n\nBest,\nBudhathri`;
}

function requireSession() {
  if (!session) throw new ApiError("Not signed in", 401);
}

export const mockApi = {
  loginUrl: () => "#mock-login",
  async mockLogin() {
    await delay(300);
    session = true;
    try { localStorage.setItem("it_mock_session", "1"); } catch { /* ignore */ }
  },
  async getMe() {
    await delay(150);
    requireSession();
    return clone(user);
  },
  async logout() {
    await delay(100);
    session = false;
    try { localStorage.removeItem("it_mock_session"); } catch { /* ignore */ }
    return null;
  },

  async listMessages({ priority, q } = {}) {
    await delay();
    requireSession();
    let rows = messages;
    if (priority) rows = rows.filter((m) => m.priority === priority);
    if (q) {
      const needle = q.toLowerCase();
      rows = rows.filter((m) => (m.subject + m.sender + m.body).toLowerCase().includes(needle));
    }
    return clone(rows.map(({ body, ...rest }) => ({ ...rest, snippet: body.replace(/\s+/g, " ").slice(0, 110) })));
  },
  async getMessage(id) {
    await delay(150);
    requireSession();
    const m = messages.find((x) => x.id === Number(id));
    if (!m) throw new ApiError("Message not found", 404);
    return clone(m);
  },
  async relabelMessage(id, priority) {
    await delay(150);
    const m = messages.find((x) => x.id === Number(id));
    if (!m) throw new ApiError("Message not found", 404);
    m.priority = priority;
    m.reason = "Relabelled by you. Saved as feedback for evaluation.";
    return clone(m);
  },
  async markRead(id) {
    const m = messages.find((x) => x.id === Number(id));
    if (m) m.is_read = true;
    return null;
  },
  async syncNow() {
    await delay(900);
    status.sync = { ...status.sync, last_run: new Date().toISOString(), last_result: "ok", fetched: 5, new_messages: 0 };
    return clone(status.sync);
  },

  async getDigest() {
    await delay();
    requireSession();
    return clone(digest);
  },
  async regenerateDigest() {
    await delay(1100);
    digest = { ...digest, generated_at: new Date().toISOString() };
    return clone(digest);
  },
  async digestFeedback(itemId, useful) {
    await delay(120);
    const it = digest.items.find((x) => x.id === itemId);
    if (it) it.feedback = useful ? "useful" : "not_useful";
    return null;
  },

  async listDrafts() {
    await delay();
    requireSession();
    return clone(drafts);
  },
  async getDraft(id) {
    await delay(120);
    const d = drafts.find((x) => x.id === Number(id));
    if (!d) throw new ApiError("Draft not found", 404);
    return clone(d);
  },
  async createDraft(messageId) {
    await delay(900); // the agent writes the draft
    const m = messages.find((x) => x.id === Number(messageId));
    if (!m) throw new ApiError("Message not found", 404);
    const existing = drafts.find((d) => d.message_id === m.id && d.status === "draft");
    if (existing) return clone(existing);
    const d = {
      id: draftSeq++, message_id: m.id, to: m.sender_email,
      subject: m.subject.startsWith("Re:") ? m.subject : `Re: ${m.subject}`,
      body: replyTemplate(m), status: "draft", updated_at: new Date().toISOString(),
      original: { sender: m.sender, subject: m.subject, body: m.body },
    };
    drafts.unshift(d);
    m.has_draft = true;
    return clone(d);
  },
  async saveDraft(id, fields) {
    await delay(200);
    const d = drafts.find((x) => x.id === Number(id));
    if (!d) throw new ApiError("Draft not found", 404);
    if (d.status === "sent") throw new ApiError("This draft was already sent", 409);
    Object.assign(d, fields, { updated_at: new Date().toISOString() });
    return clone(d);
  },
  async sendDraft(id) {
    await delay(700);
    const d = drafts.find((x) => x.id === Number(id));
    if (!d) throw new ApiError("Draft not found", 404);
    d.status = "sent";
    d.updated_at = new Date().toISOString();
    return clone(d);
  },
  async discardDraft(id) {
    await delay(150);
    const d = drafts.find((x) => x.id === Number(id));
    drafts = drafts.filter((x) => x.id !== Number(id));
    const m = d && messages.find((x) => x.id === d.message_id);
    if (m) m.has_draft = false;
    return null;
  },

  async listProposals() {
    await delay();
    requireSession();
    return clone(proposals);
  },
  async approveProposal(id) {
    await delay(700); // backend creates the Google Calendar event
    const p = proposals.find((x) => x.id === Number(id));
    if (!p) throw new ApiError("Proposal not found", 404);
    p.status = "approved";
    return clone(p);
  },
  async rejectProposal(id) {
    await delay(200);
    const p = proposals.find((x) => x.id === Number(id));
    if (!p) throw new ApiError("Proposal not found", 404);
    p.status = "rejected";
    return clone(p);
  },

  async getStatus() {
    await delay();
    requireSession();
    return clone(status);
  },
};
