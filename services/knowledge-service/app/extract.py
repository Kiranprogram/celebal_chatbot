from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import get_settings

STOP = {
    "The", "This", "That", "With", "From", "And", "For", "Are", "Was", "Were",
    "Have", "Has", "Not", "But", "You", "Your", "Our", "Their", "About",
}


def heuristic_extract(text: str, max_entities: int = 25) -> tuple[list[str], list[tuple[str, str, str]]]:
    candidates = re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b", text)
    entities: list[str] = []
    for c in candidates:
        if c in STOP or len(c) < 3:
            continue
        if c not in entities:
            entities.append(c)
        if len(entities) >= max_entities:
            break

    relations: list[tuple[str, str, str]] = []
    for m in re.finditer(
        r"([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,2})\s+"
        r"(depends on|part of|used by|uses|owns|created|founded|works at|reports to|related to|based on)\s+"
        r"([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,2})",
        text,
        flags=re.IGNORECASE,
    ):
        src, rel, dst = m.group(1), m.group(2).lower().replace(" ", "_"), m.group(3)
        relations.append((src, rel, dst))

    if len(relations) < 3 and len(entities) >= 2:
        for i in range(min(len(entities) - 1, 12)):
            relations.append((entities[i], "RELATED_TO", entities[i + 1]))
    return entities, relations


async def llm_extract(text: str) -> tuple[list[str], list[tuple[str, str, str]]] | None:
    settings = get_settings()
    if not settings.openrouter_api_key:
        return None
    prompt = (
        "Extract entities and relationships from the text. "
        'Return ONLY JSON: {"entities": ["..."], "relations": [{"source":"...","relation":"...","target":"..."}]}.\n\n'
        f"TEXT:\n{text[:6000]}"
    )
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System",
    }
    payload: dict[str, Any] = {
        "model": settings.openrouter_default_model,
        "messages": [
            {"role": "system", "content": "You extract knowledge graph triples. Output JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 1024,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code >= 400:
                return None
            content = resp.json()["choices"][0]["message"]["content"]
            start = content.find("{")
            end = content.rfind("}")
            if start < 0 or end < 0:
                return None
            data = json.loads(content[start : end + 1])
            entities = [str(e).strip() for e in data.get("entities") or [] if str(e).strip()]
            relations: list[tuple[str, str, str]] = []
            for r in data.get("relations") or []:
                src = str(r.get("source", "")).strip()
                rel = str(r.get("relation", "RELATED_TO")).strip() or "RELATED_TO"
                dst = str(r.get("target", "")).strip()
                if src and dst:
                    relations.append((src, rel, dst))
            return entities, relations
    except Exception:  # noqa: BLE001
        return None


async def extract_graph(text: str) -> tuple[list[str], list[tuple[str, str, str]]]:
    llm = await llm_extract(text)
    if llm and (llm[0] or llm[1]):
        return llm
    return heuristic_extract(text)
