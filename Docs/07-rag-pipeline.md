# 07 — RAG Pipeline

[← Data pipeline](06-data-pipeline.md) · [Back to docs hub](README.md) · [Next: Knowledge graph →](08-knowledge-graph.md)

## Project: Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System

## Libraries

- Embeddings: OpenRouter `/embeddings` (`embeddings.py`), hash fallback offline  
- Vector store: **FAISS** (`faiss-cpu`) or **Chroma** (`vector_store.py`)  
- Hybrid fusion: `pipeline.hybrid_retrieve` → docs + Neo4j facts  

## Query flow

1. Embed question  
2. FAISS/Chroma top-k  
3. Neo4j structured facts  
4. Fuse → LangGraph generate node → OpenRouter  

## Endpoints

- `POST /retrieve` — vector only  
- `POST /hybrid` — vector + graph  

## Related

- [Knowledge graph](08-knowledge-graph.md)  
- [Evaluation](16-evaluation.md)  
