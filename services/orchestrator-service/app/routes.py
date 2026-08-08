from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.eval import score_response
from app.graph.workflow import workflow
from app.models import ChatSession, Message
from shared_py.security import decode_token

router = APIRouter(tags=["orchestrator"])
security = HTTPBearer(auto_error=False)
settings = get_settings()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    model: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    route: list[str]
    sources: list[dict]
    eval: dict | None = None


class SessionOut(BaseModel):
    id: str
    title: str


class EvaluateRequest(BaseModel):
    question: str
    answer: str
    context: str = ""


def _user_id_from_auth(creds: HTTPAuthorizationCredentials | None) -> str:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials, settings.jwt_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return str(payload["sub"])


@router.get("/health")
async def orch_health() -> dict:
    return {
        "status": "ok",
        "service": "orchestrator-service",
        "project": "Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System",
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> ChatResponse:
    user_id = _user_id_from_auth(creds)
    token = creds.credentials if creds else None

    session: ChatSession | None = None
    if body.session_id:
        session = await db.get(ChatSession, body.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        title = body.message[:60]
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    db.add(Message(session_id=session.id, role="user", content=body.message))
    await db.commit()

    try:
        result = await workflow.ainvoke(
            {
                "user_id": user_id,
                "message": body.message,
                "model": body.model,
                "access_token": token,
                "route": [],
                "sources": [],
            }
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=f"Chat pipeline failed: {exc}",
        ) from exc

    answer = result.get("answer") or ""
    route = result.get("route") or []
    sources = result.get("sources") or []
    eval_scores = result.get("eval_scores") or None

    db.add(
        Message(
            session_id=session.id,
            role="assistant",
            content=answer,
            sources_json={"items": sources, "eval": eval_scores},
            route_json=route,
        )
    )
    await db.commit()

    return ChatResponse(
        answer=answer,
        session_id=session.id,
        route=route,
        sources=sources,
        eval=eval_scores,
    )


@router.post("/evaluate")
async def evaluate(
    body: EvaluateRequest,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    _user_id_from_auth(creds)
    return await score_response(question=body.question, answer=body.answer, context=body.context)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> list[SessionOut]:
    user_id = _user_id_from_auth(creds)
    rows = (
        await db.scalars(
            select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
        )
    ).all()
    return [SessionOut(id=r.id, title=r.title) for r in rows]


@router.post("/sessions", response_model=SessionOut)
async def create_session(
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> SessionOut:
    user_id = _user_id_from_auth(creds)
    session = ChatSession(user_id=user_id, title="New chat")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionOut(id=session.id, title=session.title)


class RenameSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@router.patch("/sessions/{session_id}", response_model=SessionOut)
async def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> SessionOut:
    user_id = _user_id_from_auth(creds)
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = body.title.strip()[:200]
    await db.commit()
    await db.refresh(session)
    return SessionOut(id=session.id, title=session.title)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> Response:
    user_id = _user_id_from_auth(creds)
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    msgs = (
        await db.scalars(select(Message).where(Message.session_id == session_id))
    ).all()
    for m in msgs:
        await db.delete(m)
    await db.delete(session)
    await db.commit()
    return Response(status_code=204)


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    user_id = _user_id_from_auth(creds)
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    rows = (
        await db.scalars(
            select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        )
    ).all()
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": r.id,
                "role": r.role,
                "content": r.content,
                "sources": (r.sources_json or {}).get("items") if r.sources_json else [],
                "route": r.route_json or [],
            }
            for r in rows
        ],
    }
