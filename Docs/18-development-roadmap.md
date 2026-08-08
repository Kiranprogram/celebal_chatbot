# 18 — Development Roadmap

[← Project structure](17-project-structure.md) · [Back to docs hub](README.md) · [Next: FAQ →](19-faq-glossary.md)

## 12-week plan (academic)

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **0** | Week 1 | Repo, Docker Compose, nginx, OpenRouter hello via orchestrator |
| **1** | Weeks 2–3 | Auth (JWT) + Postgres schema + Next.js shell (sidebar/chat) |
| **2** | Weeks 4–5 | Scrape/clean/chunk; FAISS/Chroma; basic RAG endpoint |
| **3** | Weeks 6–7 | NER/relations; Neo4j; hybrid fusion |
| **4** | Week 8 | Full LangGraph router (RAG, KG, Tool, Memory) + streaming UI |
| **5** | Week 9 | Long-term memory + memory management screen |
| **6** | Week 10 | Dynamic tools + graceful fallback |
| **7** | Week 11 | Evaluation metrics + `eval_logs` |
| **8** | Week 12 | CI/CD, monitoring, deploy, demo polish |

## Current implementation focus

Scaffold + Phase 0/1 foundations:

- Microservices + nginx + Compose
- Auth service + Postgres models
- Orchestrator OpenRouter path
- Next.js login/register/dashboard shell
- Knowledge & memory service skeletons

## Demo script (final)

1. Register/login  
2. Ingest curated URLs  
3. RAG factual question  
4. Graph relationship question  
5. Save preference → personalized style  
6. Live tool question  
7. Show evaluation scores  

## Related docs

- [Full project plan](23-project-plan.md)  
- [DevOps](22-devops.md)  
