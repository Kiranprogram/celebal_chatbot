# 01 — Introduction

[Back to docs hub](README.md) · [Next: Tech stack →](02-tech-stack.md)

## Project title

**Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System**

Prepared by: **Pritam** · B.Tech CSE, ITER, SOA University · August 2026

## Problem

1. **No long-term memory** across sessions  
2. **Limited structured reasoning** over entity relationships  
3. **Static-only knowledge** without live tool data  

## Objectives

Build an end-to-end system that ingests web data, maintains user memory, routes across RAG / graph / tools / memory, exposes an **authenticated Next.js** dashboard, evaluates quality, and is deployable via **Docker + nginx** microservices with **OpenRouter** LLMs.

## Three intelligence layers

| Layer | Role |
|-------|------|
| Static RAG | FAISS/Chroma semantic retrieval |
| Knowledge Graph | Neo4j relational queries |
| Dynamic (LangGraph) | Router + tools + memory |

## Expected outcomes

A portfolio-ready chatbot demonstrating NLP/ML, backend, frontend, and basic DevOps.

## Read next

[Tech stack](02-tech-stack.md) · [Full project plan](23-project-plan.md)
