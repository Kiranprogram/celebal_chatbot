"""Shared utilities for ChatBot_Kiran services."""

from shared_py.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "verify_password",
]


def __getattr__(name: str):
    if name in {"hash_password", "verify_password"}:
        from shared_py.security import hash_password, verify_password

        return hash_password if name == "hash_password" else verify_password
    raise AttributeError(name)
