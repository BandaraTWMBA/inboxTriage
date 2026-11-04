import { realApi } from "./client.js";
import { mockApi } from "./mock.js";

export const USE_MOCK = String(import.meta.env.VITE_USE_MOCK ?? "true") === "true";
export const api = USE_MOCK ? mockApi : realApi;
export { ApiError } from "./client.js";
