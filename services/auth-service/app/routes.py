from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models import LoginRequest, RefreshRequest, RefreshToken, RegisterRequest, TokenResponse, User, UserOut
from shared_py.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)
settings = get_settings()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _user_dict(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access = create_access_token(
        subject=user.id,
        secret=settings.jwt_secret,
        expires_minutes=settings.jwt_access_ttl_minutes,
        extra={"email": user.email, "name": user.name},
    )
    refresh = create_refresh_token(
        subject=user.id,
        secret=settings.jwt_secret,
        expires_days=settings.jwt_refresh_ttl_days,
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.jwt_refresh_ttl_days),
        )
    )
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh, user=_user_dict(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await db.scalar(select(User).where(User.email == body.email.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        name=body.name.strip(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return await _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token, settings.jwt_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    token_hash = _hash_token(body.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    stored.revoked = True
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    await db.commit()
    return await _issue_tokens(db, user)


@router.post("/logout")
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> Response:
    token_hash = _hash_token(body.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored:
        stored.revoked = True
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials, settings.jwt_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name)
