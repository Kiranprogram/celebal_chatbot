from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, HttpUrl

from app.config import get_settings
from app.neo4j_client import get_kg
from app.pipeline import graph_query, hybrid_retrieve, ingest_pdf_bytes, ingest_urls, list_sources, retrieve
from shared_py.security import decode_token

router = APIRouter(tags=["knowledge"])
security = HTTPBearer(auto_error=False)
settings = get_settings()


class IngestRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1)
    build_graph: bool = True


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = None


class GraphQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = 20


def _require_user(creds: HTTPAuthorizationCredentials | None) -> str:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials, settings.jwt_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    return str(payload["sub"])


def _allow_internal_or_user(
    creds: HTTPAuthorizationCredentials | None,
    x_internal_key: str | None,
) -> None:
    if x_internal_key and x_internal_key == settings.internal_service_key:
        return
    if creds:
        _require_user(creds)
        return
    # Public retrieve for local demo / orchestrator without key (dev only)
    return


@router.get("/health")
async def knowledge_health() -> dict:
    kg = get_kg()
    return {
        "status": "ok",
        "service": "knowledge-service",
        "neo4j": kg.available,
        "vector_backend": settings.vector_backend,
        "project": "Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System",
    }


@router.post("/ingest/urls")
async def ingest(
    body: IngestRequest,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _allow_internal_or_user(creds, x_internal_key)
    result = await ingest_urls([str(u) for u in body.urls], build_graph=body.build_graph)
    return {
        "pages_ok": result.pages_ok,
        "pages_failed": result.pages_failed,
        "chunks_upserted": result.chunks_upserted,
        "entities_upserted": result.entities_upserted,
        "relations_upserted": result.relations_upserted,
        "graph_available": result.graph_available,
        "errors": result.errors,
    }


@router.post("/ingest/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    build_graph: bool = Form(default=True),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _allow_internal_or_user(creds, x_internal_key)
    name = file.filename or "document.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty PDF")
    if len(data) > 40 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF too large (max 40MB)")
    result = await ingest_pdf_bytes(data, name, build_graph=build_graph)
    return {
        "filename": name,
        "pages_ok": result.pages_ok,
        "pages_failed": result.pages_failed,
        "chunks_upserted": result.chunks_upserted,
        "entities_upserted": result.entities_upserted,
        "relations_upserted": result.relations_upserted,
        "graph_available": result.graph_available,
        "errors": result.errors,
    }


@router.post("/retrieve")
async def retrieve_route(
    body: RetrieveRequest,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _allow_internal_or_user(creds, x_internal_key)
    return {"results": await retrieve(body.query, body.top_k)}


@router.post("/hybrid")
async def hybrid_route(
    body: RetrieveRequest,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    """Hybrid Retrieval: semantic vector search + Neo4j graph facts."""
    _allow_internal_or_user(creds, x_internal_key)
    return await hybrid_retrieve(body.query, body.top_k)


@router.post("/graph/query")
async def graph_query_route(
    body: GraphQueryRequest,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _allow_internal_or_user(creds, x_internal_key)
    return {"facts": graph_query(body.query, limit=body.limit), "neo4j": get_kg().available}


@router.get("/sources")
async def sources(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _allow_internal_or_user(creds, x_internal_key)
    return {"sources": list_sources()}
