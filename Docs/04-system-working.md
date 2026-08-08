# 04 — How the System Works

[← Architecture](03-architecture.md) · [Back to docs hub](README.md) · [Next: Features →](05-features.md)

## End-to-end flow

1. User signs in on the Next.js dashboard (JWT via auth-service).  
2. User sends a message; frontend calls nginx → orchestrator.  
3. Orchestrator validates JWT, loads memory + session history.  
4. LangGraph **router** selects RAG / KG / tools / memory paths.  
5. Context is merged; OpenRouter streams the answer.  
6. Message + sources saved (Postgres); optional memory write.  
7. UI shows streaming text, citations, and optional reasoning trail.

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant NGX as nginx
  participant Auth as auth-service
  participant Orch as orchestrator
  participant Know as knowledge
  participant Mem as memory
  participant OR as OpenRouter

  U->>FE: Login
  FE->>NGX: POST /api/auth/login
  NGX->>Auth: forward
  Auth-->>FE: JWT cookies
  U->>FE: Chat message
  FE->>NGX: POST /api/orchestrator/chat
  NGX->>Orch: forward + JWT
  Orch->>Mem: load memory
  Orch->>Know: retrieve / graph
  Orch->>OR: stream completion
  OR-->>Orch: tokens
  Orch-->>FE: SSE stream
  FE-->>U: Answer + sources
```

## Routing signals

| Signal | Prefer |
|--------|--------|
| Docs / FAQ / “according to knowledge” | RAG |
| “Related to / depends on / who reports” | Knowledge graph |
| “Today / live / current” | Tools |
| “Remember that I…” | Memory write |
| Mixed | Hybrid |

## Related docs

- [LangGraph workflow](09-langgraph-workflow.md)  
- [API reference](12-api-reference.md)  
