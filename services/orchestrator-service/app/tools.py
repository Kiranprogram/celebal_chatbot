from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings


async def tool_web_search(query: str, max_results: int = 5) -> str:
    """
    Live web search for weather, stocks, news, and other real-time facts.
    Prefer Tavily when TAVILY_API_KEY is set; otherwise DuckDuckGo (no key).
    """
    settings = get_settings()
    query = query.strip()
    if not query:
        return "Empty search query."

    if settings.tavily_api_key:
        return await _search_tavily(query, max_results=max_results)

    # Free fallback — no API key required
    try:
        return await _search_duckduckgo(query, max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        return f"Web search failed: {exc}"


async def _search_tavily(query: str, max_results: int = 5) -> str:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=settings.tool_http_timeout_seconds) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": True,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    lines: list[str] = []
    if data.get("answer"):
        lines.append(f"Summary: {data['answer']}")
    for i, item in enumerate(data.get("results") or [], start=1):
        title = item.get("title") or "Result"
        url = item.get("url") or ""
        snippet = (item.get("content") or "")[:400]
        lines.append(f"{i}. {title}\n   {url}\n   {snippet}")
    return "Web search (Tavily):\n" + ("\n".join(lines) if lines else "No results.")


async def _search_duckduckgo(query: str, max_results: int = 5) -> str:
    """HTML search fallback (no API key)."""
    settings = get_settings()
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; MemoryAugmentedChatbot/1.0; "
            "+https://localhost research-project)"
        )
    }
    async with httpx.AsyncClient(
        timeout=settings.tool_http_timeout_seconds,
        follow_redirects=True,
        headers=headers,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

    results: list[str] = []
    for i, node in enumerate(soup.select(".result")[:max_results], start=1):
        title_el = node.select_one(".result__a")
        snippet_el = node.select_one(".result__snippet")
        title = title_el.get_text(" ", strip=True) if title_el else "Result"
        href = title_el.get("href") if title_el else ""
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        results.append(f"{i}. {title}\n   {href}\n   {snippet[:400]}")

    if not results:
        # Instant Answer API (limited, but key-free)
        async with httpx.AsyncClient(timeout=settings.tool_http_timeout_seconds) as client:
            ia = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            ia.raise_for_status()
            data = ia.json()
        abstract = data.get("AbstractText") or data.get("Answer") or ""
        related = data.get("RelatedTopics") or []
        lines = []
        if abstract:
            lines.append(f"Summary: {abstract}")
        for i, topic in enumerate(related[:max_results], start=1):
            if isinstance(topic, dict) and topic.get("Text"):
                lines.append(f"{i}. {topic.get('Text')} ({topic.get('FirstURL', '')})")
        return "Web search (DuckDuckGo):\n" + ("\n".join(lines) if lines else f"No results for: {query}")

    return "Web search (DuckDuckGo):\n" + "\n".join(results)


async def tool_scrape(url: str) -> str:
    settings = get_settings()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Invalid URL for scrape tool."
    async with httpx.AsyncClient(
        timeout=settings.tool_http_timeout_seconds,
        follow_redirects=True,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        return f"Scraped '{title}': {text[:1200]}"


LIVE_KEYWORDS = (
    "weather",
    "temperature",
    "forecast",
    "stock",
    "share price",
    "nasdaq",
    "nifty",
    "sensex",
    "crypto",
    "bitcoin",
    "gold price",
    "news",
    "today",
    "live",
    "current",
    "real-time",
    "realtime",
    "latest",
    "who won",
    "score",
)


def detect_tool_calls(message: str) -> list[dict[str, Any]]:
    lower = message.lower()
    calls: list[dict[str, Any]] = []

    # Explicit URL → scrape that page
    urls = re.findall(r"https?://[^\s)]+", message)
    for u in urls[:2]:
        calls.append({"tool": "scrape", "url": u.rstrip(".,")})

    # Live / factual questions → web search (weather, stocks, news, etc.)
    if any(k in lower for k in LIVE_KEYWORDS) or lower.strip().endswith("?"):
        # Prefer search for live intents; skip if message is clearly about ingested docs only
        doc_hints = ("according to our", "from the knowledge", "in the ingested", "from neo4j")
        if not any(h in lower for h in doc_hints):
            if any(k in lower for k in LIVE_KEYWORDS):
                calls.append({"tool": "web_search", "query": message.strip()})

    # Deduplicate by tool+payload
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in calls:
        key = str(c)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


async def run_tools(message: str) -> tuple[str, list[dict[str, Any]]]:
    calls = detect_tool_calls(message)
    if not calls and any(k in message.lower() for k in LIVE_KEYWORDS):
        calls = [{"tool": "web_search", "query": message.strip()}]

    outputs: list[str] = []
    sources: list[dict[str, Any]] = []
    for call in calls:
        try:
            if call["tool"] == "web_search":
                text = await tool_web_search(call.get("query") or message)
            elif call["tool"] == "scrape":
                text = await tool_scrape(call["url"])
            else:
                text = f"Unknown tool: {call.get('tool')}"
            outputs.append(text)
            sources.append(
                {
                    "type": "tool",
                    "tool": call["tool"],
                    "detail": call,
                    "snippet": text[:400],
                }
            )
        except Exception as exc:  # noqa: BLE001
            outputs.append(f"Tool {call['tool']} failed: {exc}")
            sources.append({"type": "tool", "tool": call["tool"], "error": str(exc)})
    return "\n\n".join(outputs), sources
