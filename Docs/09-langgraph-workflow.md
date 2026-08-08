# 09 — LangGraph Workflow

[← Knowledge graph](08-knowledge-graph.md) · [Back to docs hub](README.md) · [Next: Memory →](10-memory-system.md)

## Role

The **orchestrator-service** runs a LangGraph workflow that routes each user message across memory, RAG, knowledge graph, and tools, then calls **OpenRouter** to compose the answer.

## Nodes (v1)

| Node | Role |
|------|------|
| `memory_load` | Load user facts from memory-service |
| `router` | Heuristic / LLM intent routing |
| `rag` | Call knowledge-service retrieve |
| `kg` | Neo4j relational facts (Phase 3) |
| `tools` | Live APIs / scrape (Phase 6) |
| `generate` | OpenRouter chat completion |

Linear pipeline with route-gated no-ops keeps the graph reliable while hybrid fusion matures.

## Related

- [System working](04-system-working.md)  
- [Microservices](21-microservices-nginx.md)  
