"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AuthUser,
  createSession,
  deleteSession,
  getAccessToken,
  getSessionMessages,
  getStoredUser,
  ingestPdf,
  ingestUrls,
  listMemory,
  listSessions,
  listSources,
  logout,
  renameSession,
  sendChat,
} from "@/lib/api";

type ChatMsg = {
  role: "user" | "assistant";
  content: string;
  route?: string[];
  sources?: Array<Record<string, unknown>>;
};

const DEFAULT_MODEL = "openai/gpt-4o-mini";

export default function ChatPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [sessions, setSessions] = useState<Array<{ id: string; title: string }>>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [ingestUrl, setIngestUrl] = useState("");
  const [facts, setFacts] = useState<Array<{ key: string; value: string }>>([]);
  const [sources, setSources] = useState<Array<{ id: string; url: string; title: string }>>([]);
  const [trailOpen, setTrailOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const lastTrail = useMemo(() => {
    const last = [...messages].reverse().find((m) => m.role === "assistant");
    return last;
  }, [messages]);

  async function refreshSidebar(u?: AuthUser | null) {
    const s = await listSessions();
    setSessions(s);
    try {
      const src = await listSources();
      setSources(src.sources || []);
    } catch {
      /* optional */
    }
    const who = u ?? user;
    if (who) {
      try {
        const mem = await listMemory(who.id);
        setFacts(mem.facts || []);
      } catch {
        /* memory may lag after restart */
      }
    }
  }

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    const u = getStoredUser();
    setUser(u);
    (async () => {
      try {
        await refreshSidebar(u);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chats");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function openSession(id: string) {
    setSessionId(id);
    setBusy(true);
    setError(null);
    try {
      const data = await getSessionMessages(id);
      setMessages(
        (data.messages || []).map((m) => ({
          role: m.role === "assistant" ? "assistant" : "user",
          content: m.content,
          route: m.route,
          sources: m.sources,
        })),
      );
    } catch (err) {
      setMessages([]);
      setError(err instanceof Error ? err.message : "Could not load messages");
    } finally {
      setBusy(false);
    }
  }

  async function onNewChat() {
    setBusy(true);
    setError(null);
    try {
      const s = await createSession();
      setSessions((prev) => [s, ...prev]);
      setSessionId(s.id);
      setMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create chat");
    } finally {
      setBusy(false);
    }
  }

  async function onRename(id: string) {
    const title = editTitle.trim();
    if (!title) return;
    setBusy(true);
    try {
      const updated = await renameSession(id, title);
      setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)));
      setEditingId(null);
      setStatus("Chat renamed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Delete this chat?")) return;
    setBusy(true);
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (sessionId === id) {
        setSessionId(null);
        setMessages([]);
      }
      setStatus("Chat deleted");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const res = await sendChat(text, sessionId, model);
      setSessionId(res.session_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, route: res.route, sources: res.sources },
      ]);
      await refreshSidebar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  }

  async function onIngestUrl() {
    if (!ingestUrl.trim()) return;
    setBusy(true);
    setError(null);
    setStatus("Ingesting URL into knowledge base…");
    try {
      await ingestUrls([ingestUrl.trim()], true);
      setIngestUrl("");
      setStatus("URL ingested — ask questions about it");
      await refreshSidebar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed");
      setStatus(null);
    } finally {
      setBusy(false);
    }
  }

  async function onPdfSelected(file: File | null) {
    if (!file) return;
    setBusy(true);
    setError(null);
    setStatus(`Uploading ${file.name}…`);
    try {
      const res = await ingestPdf(file, true);
      setStatus(
        `PDF ready: ${res.chunks_upserted} chunks` +
          (res.entities_upserted ? `, ${res.entities_upserted} entities` : "") +
          " — ask anything about it",
      );
      await refreshSidebar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF upload failed");
      setStatus(null);
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-80 flex-col border-r border-[var(--line)] bg-black/25 p-4">
        <p className="font-display text-xl leading-tight">Kiran Chatbot</p>
        <p className="mt-1 text-xs text-[var(--muted)]">PDF Q&amp;A · Hybrid RAG · Memory</p>

        <button
          onClick={onNewChat}
          disabled={busy}
          className="mt-5 rounded-lg bg-[var(--accent)] px-3 py-2 text-sm font-medium text-[#04140f] disabled:opacity-60"
        >
          New chat
        </button>

        <div className="mt-4 flex-1 space-y-1 overflow-y-auto">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`group rounded-md px-2 py-1.5 ${
                sessionId === s.id ? "bg-white/10" : "hover:bg-white/5"
              }`}
            >
              {editingId === s.id ? (
                <form
                  className="flex gap-1"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void onRename(s.id);
                  }}
                >
                  <input
                    className="w-full rounded border border-[var(--line)] bg-transparent px-1 text-xs"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    autoFocus
                  />
                  <button type="submit" className="text-xs text-[var(--accent)]">
                    Save
                  </button>
                </form>
              ) : (
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => void openSession(s.id)}
                    className="min-w-0 flex-1 truncate text-left text-sm"
                  >
                    {s.title}
                  </button>
                  <button
                    title="Rename"
                    className="hidden text-[10px] text-[var(--muted)] group-hover:inline"
                    onClick={() => {
                      setEditingId(s.id);
                      setEditTitle(s.title);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    title="Delete"
                    className="hidden text-[10px] text-red-300 group-hover:inline"
                    onClick={() => void onDelete(s.id)}
                  >
                    Del
                  </button>
                </div>
              )}
            </div>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-[var(--muted)]">No chats yet — start one or upload a PDF.</p>
          )}
        </div>

        <div className="mt-4 space-y-3 border-t border-[var(--line)] pt-4 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Upload PDF</p>
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf,.pdf"
              className="mt-2 block w-full text-xs text-[var(--muted)] file:mr-2 file:rounded-md file:border-0 file:bg-[var(--warm)] file:px-2 file:py-1 file:text-xs file:font-medium file:text-[#1a0f08]"
              onChange={(e) => void onPdfSelected(e.target.files?.[0] || null)}
              disabled={busy}
            />
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Or ingest URL</p>
            <div className="mt-2 flex gap-2">
              <input
                className="w-full rounded-md border border-[var(--line)] bg-transparent px-2 py-1 text-xs"
                placeholder="https://…"
                value={ingestUrl}
                onChange={(e) => setIngestUrl(e.target.value)}
              />
              <button
                onClick={() => void onIngestUrl()}
                disabled={busy}
                className="rounded-md border border-[var(--line)] px-2 text-xs disabled:opacity-60"
              >
                Add
              </button>
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Documents</p>
            <ul className="mt-1 max-h-24 space-y-1 overflow-y-auto text-xs text-[var(--muted)]">
              {sources.length === 0 && <li>None yet — upload a PDF.</li>}
              {sources.map((s) => (
                <li key={s.id} className="truncate" title={s.url}>
                  {s.title || s.url}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Memory</p>
            <ul className="mt-1 max-h-20 space-y-1 overflow-y-auto text-xs text-[var(--muted)]">
              {facts.length === 0 && <li>No saved facts yet.</li>}
              {facts.map((f) => (
                <li key={f.key}>
                  <span className="text-[var(--warm)]">{f.key}</span>: {f.value}
                </li>
              ))}
            </ul>
          </div>

          <button onClick={() => void onLogout()} className="text-left text-xs text-red-300">
            Log out {user ? `(${user.name})` : ""}
          </button>
        </div>
      </aside>

      <section className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[var(--line)] px-6 py-3">
          <div>
            <p className="text-sm text-[var(--muted)]">Model (OpenRouter)</p>
            <select
              className="mt-1 rounded-md border border-[var(--line)] bg-transparent px-2 py-1 text-sm"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="openai/gpt-4o-mini">openai/gpt-4o-mini</option>
              <option value="openrouter/auto">openrouter/auto</option>
              <option value="google/gemma-4-31b-it:free">google/gemma-4-31b-it:free</option>
              <option value="anthropic/claude-3.5-sonnet">anthropic/claude-3.5-sonnet</option>
              <option value="meta-llama/llama-3.1-8b-instruct">meta-llama/llama-3.1-8b-instruct</option>
              <option value="deepseek/deepseek-chat">deepseek/deepseek-chat</option>
            </select>
          </div>
          <button
            onClick={() => setTrailOpen((v) => !v)}
            className="rounded-md border border-[var(--line)] px-3 py-1.5 text-xs"
          >
            {trailOpen ? "Hide" : "Show"} reasoning
          </button>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <div className="flex flex-1 flex-col">
            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
              {messages.length === 0 && (
                <div className="mx-auto max-w-xl rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6">
                  <p className="font-display text-2xl">Upload a PDF or ask anything</p>
                  <p className="mt-2 text-sm text-[var(--muted)]">
                    After login you can upload PDFs, rename or delete chats, and get answers from your
                    documents plus live web search when needed.
                  </p>
                </div>
              )}
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`mx-auto max-w-3xl rounded-2xl px-4 py-3 ${
                    m.role === "user" ? "bg-[var(--accent)]/15" : "border border-[var(--line)] bg-black/20"
                  }`}
                >
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{m.role}</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>
                  {m.sources && m.sources.length > 0 && (
                    <details className="mt-2 text-xs text-[var(--muted)]">
                      <summary>Sources</summary>
                      <pre className="mt-1 overflow-x-auto">{JSON.stringify(m.sources, null, 2)}</pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
            <form onSubmit={onSend} className="border-t border-[var(--line)] px-6 py-4">
              {status && <p className="mb-2 text-sm text-[var(--accent)]">{status}</p>}
              {error && <p className="mb-2 text-sm text-red-300">{error}</p>}
              <div className="mx-auto flex max-w-3xl gap-2">
                <input
                  className="flex-1 rounded-xl border border-[var(--line)] bg-black/20 px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
                  placeholder="Ask about your PDF or anything else…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={busy}
                />
                <button
                  disabled={busy}
                  className="rounded-xl bg-[var(--warm)] px-5 py-3 text-sm font-medium text-[#1a0f08] disabled:opacity-60"
                >
                  {busy ? "…" : "Send"}
                </button>
              </div>
            </form>
          </div>

          {trailOpen && (
            <aside className="hidden w-72 border-l border-[var(--line)] bg-black/10 p-4 lg:block">
              <p className="text-sm font-medium">Reasoning trail</p>
              <ul className="mt-4 space-y-2 text-sm">
                {(lastTrail?.route || []).map((n) => (
                  <li key={n} className="rounded-md border border-[var(--line)] px-2 py-1">
                    {n}
                  </li>
                ))}
                {!lastTrail?.route?.length && (
                  <li className="text-xs text-[var(--muted)]">Send a message to see routing.</li>
                )}
              </ul>
            </aside>
          )}
        </div>
      </section>
    </div>
  );
}
