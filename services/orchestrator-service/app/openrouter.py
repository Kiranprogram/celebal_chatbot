from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import get_settings

# Free-tier models often hit 429; try these in order when the primary fails.
_FALLBACK_MODELS = [
    "openai/gpt-4o-mini",
    "openrouter/auto",
    "google/gemma-4-31b-it:free",
]


def _model_chain(preferred: str | None) -> list[str]:
    settings = get_settings()
    primary = preferred or settings.openrouter_default_model
    chain: list[str] = []
    for m in [primary, *settings.fallback_models(), *_FALLBACK_MODELS]:
        if m and m not in chain:
            chain.append(m)
    return chain


async def chat_completion(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """Call OpenRouter. Never raises for HTTP/API errors — returns a clear message instead."""
    settings = get_settings()
    if not settings.openrouter_api_key:
        return (
            "OpenRouter API key is not configured. "
            "Set OPENROUTER_API_KEY in .env to enable live LLM responses."
        )

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Memory-Augmented Chatbot",
    }

    last_error = "Unknown OpenRouter error"
    async with httpx.AsyncClient(timeout=90.0) as client:
        for candidate in _model_chain(model):
            payload: dict[str, Any] = {
                "model": candidate,
                "messages": messages,
                "temperature": temperature,
                # Required: without this, OpenRouter may reserve 16k–65k tokens and 402 on low balance
                "max_tokens": max_tokens,
            }
            for attempt in range(3):
                try:
                    resp = await client.post(
                        f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                except httpx.RequestError as exc:
                    last_error = f"Network error talking to OpenRouter: {exc}"
                    break

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait_s = float(retry_after) if retry_after and retry_after.isdigit() else (1.5 * (attempt + 1))
                    last_error = (
                        f"OpenRouter rate limit (429) on model `{candidate}`. "
                        "Free models are shared and often busy."
                    )
                    await asyncio.sleep(min(wait_s, 8.0))
                    continue

                if resp.status_code >= 400:
                    detail = resp.text[:400]
                    try:
                        detail = resp.json().get("error", {}).get("message") or detail
                    except Exception:  # noqa: BLE001
                        pass
                    last_error = f"OpenRouter {resp.status_code} ({candidate}): {detail}"
                    # Model unavailable / not found / insufficient credits for this model → next
                    if resp.status_code in (400, 402, 404):
                        break
                    await asyncio.sleep(1.0)
                    continue

                data = resp.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    last_error = f"Unexpected OpenRouter response for `{candidate}`"
                    break
                if not content:
                    last_error = f"Empty response from `{candidate}`"
                    break
                return content

    return (
        f"{last_error}\n\n"
        "Tips: wait ~20–60 seconds and try again, or pick another model in the dropdown "
        "(paid models like openai/gpt-4o-mini are less rate-limited if your OpenRouter key has credits)."
    )
