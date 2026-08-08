# 22 — DevOps

[← Microservices](21-microservices-nginx.md) · [Back to docs hub](README.md) · [Next: Project plan →](23-project-plan.md)

## Containerization

- Dockerfile per service: `auth`, `orchestrator`, `knowledge`, `memory`, `frontend`
- `docker-compose.yml` starts api services + postgres + mongo + neo4j + nginx
- Volumes for Postgres, Neo4j, Chroma/FAISS data

## CI/CD (GitHub Actions — Phase 8)

- On PR: lint (ruff / eslint), unit tests, Docker build
- On main: build/push images, deploy
- Secrets in GitHub Actions (OpenRouter, DB, JWT)

## Monitoring & logging

- Structured JSON logs per LangGraph node (latency, route, success)
- `/health` and `/ready` on services
- Optional Prometheus + Grafana for latency and token usage

## Security checklist

- bcrypt + short JWTs + httpOnly cookies
- Rate limit auth and chat
- Sanitize scrape/tool inputs
- No secrets in git

## Suggested hosting (low cost)

- Backend/API containers: Render / Railway / VPS  
- Frontend: Vercel (or same VPS behind nginx)  
- DBs: Compose on VPS or managed free tiers  

## Related docs

- [Setup guide](14-setup-guide.md)  
- [Configuration](15-configuration.md)  
- [Development roadmap](18-development-roadmap.md)  
