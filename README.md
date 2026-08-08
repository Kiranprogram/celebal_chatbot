# Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System

End-to-end AI system integrating:

- **RAG** (BeautifulSoup → chunk → embeddings → FAISS/Chroma)
- **Knowledge Graph** (entity/relation extraction → **Neo4j**)
- **Long-term memory** (PostgreSQL / MongoDB)
- **LangGraph** orchestration (RAG + KG + Tools + Memory)
- **Evaluation** (context relevance, correctness, faithfulness)

LLMs/embeddings via **OpenRouter**. Served as FastAPI microservices behind **nginx**, with a Next.js dashboard.

## Quick start

```powershell
cd d:\ChatBot_Kiran
copy .env.example .env
# Set OPENROUTER_API_KEY and JWT_SECRET (optional: TAVILY_API_KEY for better web search)
docker compose up --build
```

Open **http://localhost/**

**Setup details:** [RUN.md](RUN.md) · [docs/14-setup-guide.md](docs/14-setup-guide.md)

Live weather/stocks/news use **web search** (Tavily or DuckDuckGo) — no separate weather/stock API keys.

## Core libraries (Python)

| Concern | Library |
|---------|---------|
| API | FastAPI, Uvicorn |
| Orchestration | LangGraph, LangChain Core |
| Scraping | BeautifulSoup |
| Vectors | FAISS (`faiss-cpu`), optional Chroma |
| Graph DB | Neo4j Python driver |
| Embeddings / LLM | OpenRouter (httpx) |
| Auth DB | SQLAlchemy + asyncpg (PostgreSQL) |
| Memory docs | Motor / MongoDB |

## Docs

**[docs/README.md](docs/README.md)** · **[docs/23-project-plan.md](docs/23-project-plan.md)**

## Architecture

```text
Static Knowledge (RAG)  +  Knowledge Graph (Neo4j)  +  Dynamic Tools/Memory
                         └──────── LangGraph ────────┘
```
# Celebel_ChatBot
