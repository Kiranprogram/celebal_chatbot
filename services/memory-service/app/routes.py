from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models import UserMemory
from shared_py.security import decode_token

router = APIRouter(tags=["memory"])
security = HTTPBearer(auto_error=False)
settings = get_settings()


class MemoryItem(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1)
    source_session_id: str | None = None


def _auth_user(creds: HTTPAuthorizationCredentials | None) -> str | None:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials, settings.jwt_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    return str(payload["sub"])


def _authorize(
    path_user_id: str,
    creds: HTTPAuthorizationCredentials | None,
    x_internal_key: str | None,
) -> None:
    if x_internal_key and x_internal_key == settings.internal_service_key:
        return
    token_user = _auth_user(creds)
    if not token_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if path_user_id != token_user:
        raise HTTPException(status_code=403, detail="Cannot access another user's memory")


@router.get("/health")
async def memory_health() -> dict:
    return {
        "status": "ok",
        "service": "memory-service",
        "project": "Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System",
    }


@router.get("/{user_id}")
async def list_memory(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _authorize(user_id, creds, x_internal_key)
    rows = (await db.scalars(select(UserMemory).where(UserMemory.user_id == user_id))).all()
    return {
        "user_id": user_id,
        "facts": [
            {
                "id": r.id,
                "key": r.key,
                "value": r.value,
                "source_session_id": r.source_session_id,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
    }


@router.post("/{user_id}")
async def upsert_memory(
    user_id: str,
    body: MemoryItem,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _authorize(user_id, creds, x_internal_key)
    existing = await db.scalar(
        select(UserMemory).where(UserMemory.user_id == user_id, UserMemory.key == body.key)
    )
    if existing:
        existing.value = body.value
        existing.source_session_id = body.source_session_id
        item = existing
    else:
        item = UserMemory(
            user_id=user_id,
            key=body.key,
            value=body.value,
            source_session_id=body.source_session_id,
        )
        db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "key": item.key, "value": item.value}


@router.delete("/{user_id}/{key}", status_code=204)
async def delete_memory(
    user_id: str,
    key: str,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_key: str | None = Header(default=None),
):
    _authorize(user_id, creds, x_internal_key)
    existing = await db.scalar(
        select(UserMemory).where(UserMemory.user_id == user_id, UserMemory.key == key)
    )
    if existing:
        await db.delete(existing)
        await db.commit()
