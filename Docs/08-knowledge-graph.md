# 08 — Knowledge Graph (Neo4j)

[← RAG pipeline](07-rag-pipeline.md) · [Back to docs hub](README.md) · [Next: LangGraph →](09-langgraph-workflow.md)

## Project alignment

Part of **Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System**.

## Implementation (Python)

| Piece | Library / module |
|-------|------------------|
| Driver | `neo4j` (`services/knowledge-service/app/neo4j_client.py`) |
| Extraction | LLM via OpenRouter + heuristic fallback (`extract.py`) |
| Storage | `(:Entity)-[:REL]->(:Entity)` in Neo4j |
| Query | Cypher neighbors + shortestPath |

## Ingest path

1. Scrape/clean text (BeautifulSoup)  
2. `extract_graph(text)` → entities + relations  
3. `Neo4jKG.upsert_entities_and_relations(...)`  

## Query path

`POST /graph/query` and hybrid `POST /hybrid` fuse graph facts with FAISS/Chroma hits.

## Related

- [Hybrid RAG](07-rag-pipeline.md)  
- [API reference](12-api-reference.md)  
