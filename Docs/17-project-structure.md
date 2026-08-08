# 17 — Project Structure

[← Evaluation](16-evaluation.md) · [Back to docs hub](README.md) · [Next: Development roadmap →](18-development-roadmap.md)

## Monorepo layout (implemented)

```text
ChatBot_Kiran/
  README.md
  .env.example
  .gitignore
  docker-compose.yml
  docs/
  nginx/
    nginx.conf
  packages/
    shared_py/                 # shared JWT + settings helpers
  services/
    auth-service/
    orchestrator-service/
    knowledge-service/
    memory-service/
  frontend/                    # Next.js + Tailwind
  data/                        # local volumes (gitignored)
  .github/workflows/           # CI (Phase 8)
```

## Service folders

Each Python service typically contains:

```text
services/<name>/
  Dockerfile
  requirements.txt
  app/
    main.py
    config.py
    ...
```

## Responsibility map

| Path | Responsibility |
|------|----------------|
| `services/auth-service` | Register, login, refresh, logout, JWT |
| `services/orchestrator-service` | LangGraph, OpenRouter, streaming chat |
| `services/knowledge-service` | Scrape, chunk, embed, retrieve, Neo4j |
| `services/memory-service` | Preferences/facts + Mongo transcripts |
| `frontend` | Auth pages + ChatGPT-style dashboard |
| `nginx` | Single public entry + path routing |
| `packages/shared_py` | Cross-service Python utilities |

## Related docs

- [Microservices & nginx](21-microservices-nginx.md)  
- [Development roadmap](18-development-roadmap.md)  
