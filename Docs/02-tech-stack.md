# 02 — Tech Stack

[← Introduction](01-introduction.md) · [Back to docs hub](README.md) · [Next: Architecture →](03-architecture.md)

## Overview

Python microservices (FastAPI) handle auth, orchestration, knowledge, and memory. A **Next.js** dashboard is the client. **nginx** is the API gateway. LLMs and embeddings go through **OpenRouter**. Data is split across PostgreSQL, MongoDB, Neo4j, and a vector store (FAISS locally / Chroma for persistence).

## Stack at a glance

| Layer | Technology | Notes |
|-------|------------|-------|
| LLM access | **OpenRouter** | One API key; swap models (GPT, Claude, Llama, DeepSeek, …) |
| Orchestration | LangGraph + LangChain | Stateful routing: RAG / KG / tools / memory |
| Backend | FastAPI microservices | auth, orchestrator, knowledge, memory |
| Gateway | **nginx** | Reverse proxy, path routing, future TLS/rate limits |
| Frontend | **Next.js + React + Tailwind** | ChatGPT-style authenticated dashboard |
| Auth | JWT (access + refresh) + bcrypt | Optional Google OAuth as stretch goal |
| Relational DB | **PostgreSQL** | Users, sessions, messages, eval logs, structured memory |
| Document DB | **MongoDB** | Transcripts, flexible memory summaries |
| Vector DB | **FAISS** (dev) / **Chroma** (persistent) | Semantic chunk search |
| Graph DB | **Neo4j** | Entities + relationships (Cypher) |
| Scraping | BeautifulSoup / Scrapy | Knowledge ingestion |
| Containers | Docker + Docker Compose | One container per service |
| CI/CD | GitHub Actions | Lint, test, build, deploy |
| Observability | Structured logs → Prometheus/Grafana later | Latency, tokens, tool failures |

## Why these choices

### OpenRouter
Single key and OpenAI-compatible API; easy model switching for demos and cost control.

### Microservices + nginx
Separates auth, chat orchestration, knowledge ingest/retrieval, and memory so each can scale and fail independently. nginx is the single entry point for the browser.

### Next.js dashboard
Supports login, streaming chat, sidebar sessions, memory/KB management, and settings—closer to a real product than Streamlit.

### PostgreSQL + MongoDB
Postgres holds relational auth/chat/eval data. Mongo holds flexible transcripts and summarized memory snippets during iteration.

### FAISS + Chroma
FAISS for fast local/dev retrieval; Chroma when you need durable collections in Docker/prod.

## Related docs

- [Architecture](03-architecture.md)  
- [Microservices & nginx](21-microservices-nginx.md)  
- [Auth & data model](20-auth-and-data.md)  
- [Configuration](15-configuration.md)  
