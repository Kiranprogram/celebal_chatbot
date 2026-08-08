from __future__ import annotations

from typing import Any

import httpx
import numpy as np

from app.config import get_settings


def _hash_embed(texts: list[str], dim: int = 384) -> np.ndarray:
    """Offline fallback embedding so FAISS works without an API key."""
    out = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        for token in text.lower().split():
            h = hash(token) % dim
            out[i, h] += 1.0
        norm = np.linalg.norm(out[i])
        if norm > 0:
            out[i] /= norm
    return out


async def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)

    settings = get_settings()
    if not settings.openrouter_api_key:
        return _hash_embed(texts)

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Memory-Augmented Chatbot",
    }
    payload: dict[str, Any] = {
        "model": settings.openrouter_embedding_model,
        "input": texts,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/embeddings",
            headers=headers,
            json=payload,
        )
        if resp.status_code >= 400:
            # Fall back so ingest still succeeds
            return _hash_embed(texts)
        data = resp.json()
        vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        arr = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms
