# 19 — FAQ & Glossary

[← Development roadmap](18-development-roadmap.md) · [Back to docs hub](README.md)

## FAQ (zero-knowledge)

### What is this project in one sentence?
A chatbot that answers using **documents (RAG)**, **relationships (knowledge graph)**, **what it remembers about you (memory)**, and **live tools**, coordinated by **LangGraph**.

### Do I need to know machine learning deeply to understand the docs?
No. Read in the order listed in [docs/README.md](README.md). Terms are defined in the glossary below.

### Is the application code ready?
Not yet. This repository currently ships the documentation set. Build order is in [Development roadmap](18-development-roadmap.md).

### What is the difference between RAG and a knowledge graph?
- **RAG** finds text chunks that are *semantically similar* to your question.
- A **knowledge graph** stores *explicit links* between entities (A depends on B).

### Why LangGraph?
So the system can **route** each question to the right tools/nodes instead of always doing the same single pipeline.

### Why MongoDB and Neo4j and Chroma?
They store different shapes of data:

- Chroma → vectors / chunks  
- Neo4j → graph relations  
- MongoDB → chat + memory documents  

### Which UI will users use?
**Next.js + Tailwind** ChatGPT-style dashboard behind **nginx**, calling FastAPI microservices. See [UI guide](13-ui-guide.md).

### How do LLMs get called?
Through **OpenRouter** (OpenAI-compatible API). Set `OPENROUTER_API_KEY` and pick a model in the UI.

### Can it browse the entire internet?
No. It scrapes **configured / requested URLs** and calls **configured tools**. It is not a general search engine.

### How do we know answers are good?
Use the evaluation metrics: context relevance, answer correctness, faithfulness. See [Evaluation](16-evaluation.md).

### Where do I start if I want to implement code next?
Start Phase 1 in the [Development roadmap](18-development-roadmap.md), using the layout in [Project structure](17-project-structure.md).

---

## Glossary

| Term | Meaning |
|------|---------|
| **API** | Application Programming Interface — how programs talk over HTTP |
| **Chunk** | A small piece of a document used for embedding and retrieval |
| **Chroma** | Vector database used to store embeddings |
| **Cypher** | Query language for Neo4j |
| **Embedding** | Numeric vector representation of text meaning |
| **Entity** | A thing in the knowledge graph (person, service, concept, …) |
| **Faithfulness** | Whether the answer sticks to provided context |
| **FastAPI** | Python web framework for the backend API |
| **Hallucination** | Model invents facts not supported by context |
| **Hybrid retrieval** | Combining vector search and graph queries |
| **Knowledge graph (KG)** | Network of entities connected by relationships |
| **LangGraph** | Framework for building stateful multi-step LLM workflows |
| **LLM** | Large Language Model — the model that writes answers |
| **Long-term memory** | Stored user preferences/facts across sessions |
| **MongoDB** | Document database for chat history and memory |
| **Neo4j** | Graph database |
| **Node (LangGraph)** | A step in the orchestration graph |
| **Orchestrator** | Component that decides order of operations (LangGraph) |
| **RAG** | Retrieval-Augmented Generation |
| **Router** | Node that chooses RAG / KG / tools / memory paths |
| **Semantic search** | Search by meaning via embeddings, not only keywords |
| **Streamlit** | Python framework for the chat UI |
| **Tool** | Function the agent can call for live or external data |
| **Top-k** | Number of nearest chunks returned from the vector store |
| **Vector store** | Database specialized for similarity search over embeddings |

## Related docs

- [Introduction](01-introduction.md)  
- [Architecture](03-architecture.md)  
- [Tech stack](02-tech-stack.md)  
