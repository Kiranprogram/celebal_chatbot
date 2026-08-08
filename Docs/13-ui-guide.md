# 13 — UI Guide (Next.js Chat Dashboard)

[← API reference](12-api-reference.md) · [Back to docs hub](README.md) · [Next: Setup guide →](14-setup-guide.md)

## UI choice

**Next.js + React + Tailwind CSS** — a ChatGPT-style dashboard tailored to hybrid retrieval and memory (not a clone).

## Layout

| Region | Contents |
|--------|----------|
| **Left sidebar** | New Chat, searchable sessions by date, Memory panel link, Knowledge Base manager, Settings (OpenRouter model), account menu |
| **Main pane** | Streaming bubbles, composer (text + optional file upload for RAG), inline source citations (vector / graph / tool / memory) |
| **Right panel** (collapsible) | Reasoning trail: which LangGraph nodes ran and what they returned |
| **Top bar** | Active model, conversation title, export/share |

## Core screens

1. Register / Login  
2. Main dashboard (sidebar + chat)  
3. Memory management (list / edit / delete facts)  
4. Knowledge base / ingestion (URLs, scrape status)  
5. Settings (model, usage stats, account)

## Auth UX

- JWT access + refresh tokens via **httpOnly cookies** (preferred)
- Protected dashboard routes redirect to `/login` when unauthenticated

## Design notes

- Brand the product clearly in the header: **Memory-Augmented Chatbot**
- One primary job on the main screen: chat
- Sources under each assistant message, not floating overlays
- Reasoning trail is optional/demo-oriented

## Local URL

Through nginx: `http://localhost/` (frontend)  
Direct Next.js (dev): `http://localhost:3000`

## Related docs

- [Auth & data model](20-auth-and-data.md)  
- [API reference](12-api-reference.md)  
- [Features](05-features.md)  
