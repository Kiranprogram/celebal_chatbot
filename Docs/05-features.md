# 05 — Features

[← System working](04-system-working.md) · [Back to docs hub](README.md) · [Next: Data pipeline →](06-data-pipeline.md)

| Feature | What it does | How |
|---------|--------------|-----|
| Long-term memory | Personalized replies across sessions | Postgres + Mongo + Memory node |
| Hybrid retrieval | Semantic + relational context | FAISS/Chroma + Neo4j fusion |
| Dynamic tools | Live answers | Tool node + APIs/scrape |
| Context-aware responses | History + retrieval + memory | Prompt composer → OpenRouter |
| Evaluation | Quality tracking | Metrics + LLM judge → `eval_logs` |
| Authenticated UI | Secure ChatGPT-style app | Next.js + JWT + nginx |
| Microservices | Maintainable deployment | Docker Compose + nginx |

## Related docs

- [UI guide](13-ui-guide.md)  
- [Evaluation](16-evaluation.md)  
