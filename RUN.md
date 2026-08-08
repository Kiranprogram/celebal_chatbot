# How to run — Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System

## 1) Copy env

```powershell
cd d:\ChatBot_Kiran
copy .env.example .env
```

## 2) Edit `.env` — only these matter for first run

**Required**
- `OPENROUTER_API_KEY` → from https://openrouter.ai/keys  
- `JWT_SECRET` → any long random string  

**Optional**
- `TAVILY_API_KEY` → better web search for weather/stocks (https://tavily.com)  
  - If empty → DuckDuckGo is used (no key)

**Do not manually install / host**
- PostgreSQL, MongoDB, Neo4j → Docker Compose starts them  
- FAISS/Chroma → local files inside Docker volume (no URL)  
- Weather API / stock API URLs → **not required** (web search handles live data)

## 3) Run

```powershell
docker compose up --build
```

## 4) Open

- App: http://localhost/  
- Neo4j UI (optional): http://localhost:7474  

More detail: [docs/14-setup-guide.md](docs/14-setup-guide.md)
