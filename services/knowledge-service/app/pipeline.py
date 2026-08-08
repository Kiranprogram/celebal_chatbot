from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.embeddings import embed_texts
from app.extract import extract_graph
from app.neo4j_client import get_kg
from app.vector_store import get_vector_store

_DOC_STORE: dict[str, dict[str, Any]] = {}


@dataclass
class IngestResult:
    pages_ok: int = 0
    pages_failed: int = 0
    chunks_upserted: int = 0
    entities_upserted: int = 0
    relations_upserted: int = 0
    errors: list[str] = field(default_factory=list)
    graph_available: bool = False


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


async def scrape_url(url: str) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        return title, _clean_text(resp.text)


async def ingest_text(
    *,
    text: str,
    title: str,
    source_url: str,
    build_graph: bool = True,
) -> IngestResult:
    """Chunk, embed, and optionally graph-extract arbitrary document text."""
    settings = get_settings()
    result = IngestResult()
    Path(settings.faiss_index_dir).mkdir(parents=True, exist_ok=True)
    store = get_vector_store()
    kg = get_kg()
    result.graph_available = kg.available

    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if not cleaned:
        result.pages_failed = 1
        result.errors.append(f"{title}: empty text")
        return result

    try:
        doc_id = hashlib.sha256(source_url.encode()).hexdigest()[:16]
        _DOC_STORE[doc_id] = {"url": source_url, "title": title, "text": cleaned}

        parts = _chunk_text(cleaned, settings.chunk_size, settings.chunk_overlap)
        metadatas = [
            {
                "id": f"{doc_id}_{i}",
                "doc_id": doc_id,
                "url": source_url,
                "title": title,
                "text": part,
            }
            for i, part in enumerate(parts)
        ]
        vectors = await embed_texts(parts)
        store.add(vectors, metadatas)
        result.pages_ok = 1
        result.chunks_upserted = len(parts)

        if build_graph:
            entities, relations = await extract_graph(cleaned[:8000])
            e_n, r_n = kg.upsert_entities_and_relations(entities, relations, source_url=source_url)
            result.entities_upserted += e_n or len(entities)
            result.relations_upserted += r_n or len(relations)
            if not kg.available:
                result.errors.append(
                    f"{title}: Neo4j unavailable — entities extracted but not persisted"
                )
    except Exception as exc:  # noqa: BLE001
        result.pages_failed = 1
        result.errors.append(f"{title}: {exc}")
    return result


async def ingest_pdf_bytes(
    data: bytes,
    filename: str,
    build_graph: bool = True,
) -> IngestResult:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001
            pages.append("")
    text = "\n".join(pages)
    title = filename.rsplit(".", 1)[0] or filename
    source = f"pdf://{filename}"
    return await ingest_text(text=text, title=title, source_url=source, build_graph=build_graph)


async def ingest_urls(urls: list[str], build_graph: bool = True) -> IngestResult:
    result = IngestResult()
    kg = get_kg()
    result.graph_available = kg.available

    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            result.pages_failed += 1
            result.errors.append(f"Invalid URL: {url}")
            continue
        try:
            title, text = await scrape_url(url)
            sub = await ingest_text(text=text, title=title, source_url=url, build_graph=build_graph)
            result.pages_ok += sub.pages_ok
            result.pages_failed += sub.pages_failed
            result.chunks_upserted += sub.chunks_upserted
            result.entities_upserted += sub.entities_upserted
            result.relations_upserted += sub.relations_upserted
            result.errors.extend(sub.errors)
            result.graph_available = result.graph_available or sub.graph_available
        except Exception as exc:  # noqa: BLE001
            result.pages_failed += 1
            result.errors.append(f"{url}: {exc}")
    return result


async def retrieve(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    k = top_k or settings.rag_top_k
    qvec = await embed_texts([query])
    return get_vector_store().search(qvec[0], top_k=k)


def graph_query(query: str, limit: int = 20) -> list[dict[str, Any]]:
    return get_kg().query_from_text(query, limit=limit)


async def hybrid_retrieve(query: str, top_k: int | None = None) -> dict[str, Any]:
    """Hybrid Retrieval System: vector search + knowledge graph facts."""
    settings = get_settings()
    k = top_k or settings.rag_top_k
    rag_hits = await retrieve(query, top_k=k)
    graph_facts = graph_query(query, limit=k * 2)

    # Simple fusion: keep both; re-rank rag by score already from FAISS
    fused_context_parts: list[str] = []
    for h in rag_hits:
        fused_context_parts.append(f"[DOC] {h.get('title')}: {h.get('snippet')}")
    for f in graph_facts:
        fused_context_parts.append(f"[GRAPH] {f.get('fact')}")

    return {
        "rag": rag_hits,
        "graph": graph_facts,
        "fused_context": "\n".join(fused_context_parts),
        "sources": rag_hits + graph_facts,
    }


def list_sources() -> list[dict[str, str]]:
    sources = get_vector_store().list_sources()
    if sources:
        return sources
    return [{"id": k, "url": v["url"], "title": v["title"]} for k, v in _DOC_STORE.items()]
