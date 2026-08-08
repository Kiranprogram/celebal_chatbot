# 23 — Full Project Plan

[← DevOps](22-devops.md) · [Back to docs hub](README.md)

**Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System**  
An End-to-End AI System Design & Development Roadmap  

Prepared by: **Pritam** · B.Tech CSE, ITER, SOA University · August 2026

This document consolidates the academic project plan with the implementation docs in this folder.

---

## 1. Problem statement

Modern chatbots lack long-term memory, structured relational reasoning, and reliable fusion of static + live data. This project builds one system combining **RAG**, a **Knowledge Graph**, **long-term memory**, and **tool-based retrieval** via **LangGraph**.

## 2. Objectives

- Ingest web data into a searchable knowledge base  
- Persist user-specific memory across sessions  
- Route queries across static knowledge, graph, tools, and memory  
- Expose a **secure, authenticated, ChatGPT-style** web UI  
- Evaluate quality (relevance, correctness, faithfulness)  
- Remain deployable and maintainable (Docker, nginx, CI basics)

## 3. Architecture summary

Next.js → nginx → {auth, orchestrator, knowledge, memory} → Postgres / Mongo / Neo4j / FAISS|Chroma → OpenRouter.

See [Architecture](03-architecture.md) and [Microservices](21-microservices-nginx.md).

## 4. Key features

| Feature | Implementation |
|---------|----------------|
| Long-term memory | Postgres `user_memory` + Mongo snippets + Memory node |
| Hybrid retrieval | FAISS/Chroma + Neo4j, fused/re-ranked |
| Dynamic tools | LangGraph Tool node + REST/scrape |
| Context-aware answers | Prompt composer merges all contexts |
| Evaluation | Automated + LLM-as-judge → `eval_logs` |

## 5. Methodology

Steps 1–7: data pipeline → embeddings → KG → RAG → LangGraph → tools → evaluation.  
Mapped to weeks in [Development roadmap](18-development-roadmap.md).

## 6. Tech stack

OpenRouter, LangGraph, FastAPI microservices, Next.js, JWT auth, Postgres, MongoDB, FAISS/Chroma, Neo4j, BeautifulSoup, Docker, nginx, GitHub Actions. Full table: [Tech stack](02-tech-stack.md).

## 7. Auth & databases

See [Auth & data model](20-auth-and-data.md).

## 8. UI

See [UI guide](13-ui-guide.md).

## 9–10. Roadmap & DevOps

See [Roadmap](18-development-roadmap.md) and [DevOps](22-devops.md).

## 11. Evaluation

See [Evaluation](16-evaluation.md). Target: 20–50 labeled Q&A pairs across static, graph, and tool queries.

## 12. Expected outcomes

Memory-aware chat, graph reasoning, live tools, full-stack + DevOps demonstration suitable for ML Engineering / AI Systems portfolios.

## 13. Conclusion

RAG + KG + memory + tools, orchestrated by LangGraph, delivered as an authenticated microservice web application behind nginx with OpenRouter-backed models.
