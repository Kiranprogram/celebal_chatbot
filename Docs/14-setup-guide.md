# 14 — Setup Guide (Env + Databases + How to Run)

[← UI guide](13-ui-guide.md) · [Back to docs hub](README.md) · [Next: Configuration →](15-configuration.md)

Project: **Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System**

## What you must configure vs what Docker handles

### You MUST set (in `.env`)

| Variable | Why | Where to get it |
|----------|-----|-----------------|
| `OPENROUTER_API_KEY` | LLM chat + embeddings | https://openrouter.ai/keys |
| `JWT_SECRET` | Signs login tokens | Any long random string you invent |

### Optional (recommended)

| Variable | Why | Where |
|----------|-----|-------|
| `TAVILY_API_KEY` | Better web search for weather/stocks/news | https://tavily.com |
| `OPENROUTER_DEFAULT_MODEL` | Which chat model to use | OpenRouter model list |
| `NEO4J_PASSWORD` | Change default Neo4j password | Your choice (must match Compose) |

### You do NOT need to create these yourself (Docker Compose starts them)

| Database / store | Purpose | Default URL inside Docker |
|------------------|---------|---------------------------|
| **PostgreSQL** | Users, sessions, messages, structured memory | `postgresql+asyncpg://chatbot:chatbot@postgres:5432/chatbot` |
| **MongoDB** | Flexible transcripts / memory snippets | `mongodb://mongo:27017` |
| **Neo4j** | Knowledge graph | `bolt://neo4j:7687` (browser UI: http://localhost:7474) |
| **FAISS / Chroma** | Vector RAG index | Local volume `/data/faiss` or `/data/chroma` — **no cloud URL** |

### URLs you do NOT need to buy/configure

- No separate OpenAI URL if you use OpenRouter (`OPENROUTER_BASE_URL` already set)
- No weather API URL / stock API URL — live facts use **web search**
- No MongoDB Atlas / Neo4j Aura required for local demo
- Internal service URLs (`AUTH_SERVICE_URL`, etc.) stay as Docker hostnames when using Compose

---

## How to run (recommended: Docker)

### 1. Prerequisites
- Docker Desktop installed and running
- A free/paid **OpenRouter** API key

### 2. Create `.env`

```powershell
cd d:\ChatBot_Kiran
copy .env.example .env
```

Edit `.env` and set at least:

```env
OPENROUTER_API_KEY=sk-or-v1-YOUR_REAL_KEY
JWT_SECRET=some-long-random-secret
```

Optional:

```env
TAVILY_API_KEY=tvly-YOUR_KEY
```

### 3. Start everything

```powershell
docker compose up --build
```

First run downloads images and builds services (can take several minutes).

### 4. Open the app

| What | URL |
|------|-----|
| Chat UI (main) | http://localhost/ |
| Register / Login | http://localhost/register · http://localhost/login |
| Neo4j Browser (optional) | http://localhost:7474 (user `neo4j`, password from `.env`) |
| Auth API docs | http://localhost/api/auth/docs |
| Orchestrator health | http://localhost/api/orchestrator/health |
| Knowledge health | http://localhost/api/knowledge/health |

### 5. Demo flow

1. Register a user  
2. In the sidebar, paste a docs URL → **Ingest** (builds RAG + Neo4j graph)  
3. Ask a question about that content (static RAG / graph)  
4. Ask “What’s the weather in Mumbai today?” or “AAPL stock price” (web search tool)  
5. Say “Remember that I prefer short answers” (long-term memory)

### 6. Stop

```powershell
docker compose down
```

Keep data volumes:

```powershell
docker compose down   # data kept in named volumes
```

Wipe data:

```powershell
docker compose down -v
```

---

## Dynamic live data (web search plan)

Live questions (weather, stocks, news) go through LangGraph **tools node** → **web search**:

1. If `TAVILY_API_KEY` is set → Tavily Search API  
2. Else → DuckDuckGo (no key)  

You do **not** need separate weather/stock API keys.

---

## Local run without full Docker (advanced)

```powershell
docker compose up -d postgres mongo neo4j
# then run each FastAPI service + frontend separately
```

Only needed if you are developing a single service.

---

## Related docs

- [Configuration reference](15-configuration.md)  
- [Dynamic tools / web search](11-dynamic-tools.md)  
- [Databases & auth model](20-auth-and-data.md)  
