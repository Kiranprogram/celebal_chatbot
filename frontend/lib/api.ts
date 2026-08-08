export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export type AuthUser = {
  id: string;
  email: string;
  name: string;
};

export type TokenBundle = {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
};

const ACCESS_KEY = "mac_access";
const REFRESH_KEY = "mac_refresh";
const USER_KEY = "mac_user";

export function saveAuth(bundle: TokenBundle) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, bundle.access_token);
  localStorage.setItem(REFRESH_KEY, bundle.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(bundle.user));
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers || {});
  const isForm = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (!headers.has("Content-Type") && init.body && !isForm) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new Error("Cannot reach API gateway. Wait a few seconds and retry.");
  }

  if (!res.ok) {
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new Error("Service starting up (Bad Gateway). Wait ~10s and try again.");
    }
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function register(email: string, password: string, name: string) {
  const data = (await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  })) as TokenBundle;
  saveAuth(data);
  return data;
}

export async function login(email: string, password: string) {
  const data = (await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })) as TokenBundle;
  saveAuth(data);
  return data;
}

export async function logout() {
  const refresh = typeof window !== "undefined" ? localStorage.getItem(REFRESH_KEY) : null;
  try {
    if (refresh) {
      await apiFetch("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refresh }),
      });
    }
  } finally {
    clearAuth();
  }
}

export async function sendChat(message: string, sessionId?: string | null, model?: string) {
  return apiFetch("/orchestrator/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId || null,
      model: model || null,
    }),
  }) as Promise<{
    answer: string;
    session_id: string;
    route: string[];
    sources: Array<Record<string, unknown>>;
  }>;
}

export async function listSessions() {
  return apiFetch("/orchestrator/sessions") as Promise<Array<{ id: string; title: string }>>;
}

export async function createSession() {
  return apiFetch("/orchestrator/sessions", { method: "POST" }) as Promise<{
    id: string;
    title: string;
  }>;
}

export async function renameSession(sessionId: string, title: string) {
  return apiFetch(`/orchestrator/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  }) as Promise<{ id: string; title: string }>;
}

export async function deleteSession(sessionId: string) {
  return apiFetch(`/orchestrator/sessions/${sessionId}`, { method: "DELETE" });
}

export async function getSessionMessages(sessionId: string) {
  return apiFetch(`/orchestrator/sessions/${sessionId}/messages`) as Promise<{
    session_id: string;
    messages: Array<{
      id: string;
      role: "user" | "assistant" | string;
      content: string;
      sources?: Array<Record<string, unknown>>;
      route?: string[];
    }>;
  }>;
}

export async function ingestUrls(urls: string[], buildGraph = true) {
  return apiFetch("/knowledge/ingest/urls", {
    method: "POST",
    body: JSON.stringify({ urls, build_graph: buildGraph }),
  });
}

export async function ingestPdf(file: File, buildGraph = true) {
  const form = new FormData();
  form.append("file", file);
  form.append("build_graph", String(buildGraph));
  return apiFetch("/knowledge/ingest/pdf", {
    method: "POST",
    body: form,
  }) as Promise<{
    filename: string;
    chunks_upserted: number;
    entities_upserted: number;
    relations_upserted: number;
    errors: string[];
  }>;
}

export async function listSources() {
  return apiFetch("/knowledge/sources") as Promise<{
    sources: Array<{ id: string; url: string; title: string }>;
  }>;
}

export async function listMemory(userId: string) {
  return apiFetch(`/memory/${userId}`) as Promise<{
    facts: Array<{ key: string; value: string }>;
  }>;
}
