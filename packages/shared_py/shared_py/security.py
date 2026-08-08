from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

_pwd_context = None


def _get_pwd_context():
    global _pwd_context
    if _pwd_context is None:
        from passlib.context import CryptContext

        _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return _pwd_context


def _bcrypt_safe(password: str) -> str:
    # bcrypt only uses the first 72 bytes
    encoded = password.encode("utf-8")[:72]
    return encoded.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return _get_pwd_context().hash(_bcrypt_safe(password))


def verify_password(plain: str, hashed: str) -> bool:
    return _get_pwd_context().verify(_bcrypt_safe(plain), hashed)


def create_access_token(
    *,
    subject: str,
    secret: str,
    expires_minutes: int = 30,
    extra: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(
    *,
    subject: str,
    secret: str,
    expires_days: int = 7,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=expires_days),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])
