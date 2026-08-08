from __future__ import annotations

import re
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.eval import score_response
from app.openrouter import chat_completion
from app.tools import run_tools


class GraphState(TypedDict, total=False):
    user_id: str
    message: str
    model: str | None
    access_token: str | None
    memory_context: str
    rag_context: str
    graph_context: str
    tool_context: str
    route: list[str]
    answer: str
    sources: list[dict[str, Any]]
    eval_scores: dict[str, Any]


def _headers(state: GraphState) -> dict[str, str]:
    settings = get_settings()
    headers = {"X-Internal-Key": settings.internal_service_key}
    token = state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _simple_route(message: str) -> list[str]:
    lower = message.lower()
    route = ["memory_load"]
    if any(k in lower for k in ("remember", "prefer", "my name is", "call me")):
        route.append("memory_write")
    if any(k in lower for k in ("related", "depends", "who reports", "connected", "relationship")):
        route.append("kg")
    if any(
        k in lower
        for k in (
            "today",
            "live",
            "current",
            "weather",
            "price",
            "stock",
            "news",
            "http://",
            "https://",
            "latest",
        )
    ):
        route.append("tools")
    route.append("rag")  # hybrid always attempts vector side
    route.append("kg")  # hybrid also tries graph when useful; kg node no-ops lightly
    route.append("generate")
    return list(dict.fromkeys(route))


async def memory_load_node(state: GraphState) -> GraphState:
    settings = get_settings()
    memory_context = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.memory_service_url.rstrip('/')}/{state['user_id']}",
                headers=_headers(state),
            )
            if resp.status_code == 200:
                facts = resp.json().get("facts") or []
                memory_context = "\n".join(f"{f.get('key')}: {f.get('value')}" for f in facts)
    except Exception:  # noqa: BLE001
        memory_context = ""
    route = list(state.get("route") or [])
    if "memory_load" not in route:
        route.append("memory_load")
    return {
        **state,
        "memory_context": memory_context,
        "route": route,
        "sources": state.get("sources") or [],
    }


async def router_node(state: GraphState) -> GraphState:
    return {**state, "route": _simple_route(state["message"])}


async def memory_write_node(state: GraphState) -> GraphState:
    if "memory_write" not in (state.get("route") or []):
        return state
    settings = get_settings()
    msg = state["message"]
    key, value = "preference", msg
    m = re.search(r"remember that (.+)", msg, re.I)
    if m:
        value = m.group(1).strip()
        key = "note"
    m2 = re.search(r"prefer (.+)", msg, re.I)
    if m2:
        key, value = "answer_style", m2.group(1).strip()
    m3 = re.search(r"my name is ([A-Za-z][A-Za-z\s-]{1,40})", msg, re.I)
    if m3:
        key, value = "name", m3.group(1).strip()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.memory_service_url.rstrip('/')}/{state['user_id']}",
                headers=_headers(state),
                json={"key": key, "value": value},
            )
    except Exception:  # noqa: BLE001
        pass
    memory_context = (state.get("memory_context") or "") + f"\n{key}: {value}"
    return {**state, "memory_context": memory_context.strip()}


async def rag_node(state: GraphState) -> GraphState:
    """Static Knowledge Layer via hybrid retrieve (vector + graph fusion)."""
    settings = get_settings()
    sources = list(state.get("sources") or [])
    rag_context = ""
    graph_context = state.get("graph_context") or ""
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(
                f"{settings.knowledge_service_url.rstrip('/')}/hybrid",
                headers=_headers(state),
                json={"query": state["message"]},
            )
            if resp.status_code == 200:
                data = resp.json()
                rag_hits = data.get("rag") or []
                graph_facts = data.get("graph") or []
                rag_context = "\n\n".join(
                    f"[{r.get('title')}]({r.get('url')})\n{r.get('snippet')}" for r in rag_hits
                )
                graph_context = "\n".join(f.get("fact", "") for f in graph_facts)
                sources.extend(data.get("sources") or (rag_hits + graph_facts))
    except Exception:  # noqa: BLE001
        pass
    return {
        **state,
        "rag_context": rag_context,
        "graph_context": graph_context,
        "sources": sources,
    }


async def kg_node(state: GraphState) -> GraphState:
    """Knowledge Graph Layer — extra Cypher lookup when relational intent detected."""
    if "kg" not in (state.get("route") or []):
        return state
    if state.get("graph_context"):
        return state
    settings = get_settings()
    sources = list(state.get("sources") or [])
    graph_context = ""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{settings.knowledge_service_url.rstrip('/')}/graph/query",
                headers=_headers(state),
                json={"query": state["message"]},
            )
            if resp.status_code == 200:
                facts = resp.json().get("facts") or []
                graph_context = "\n".join(f.get("fact", "") for f in facts)
                sources.extend(facts)
    except Exception:  # noqa: BLE001
        pass
    return {**state, "graph_context": graph_context, "sources": sources}


async def tools_node(state: GraphState) -> GraphState:
    """Dynamic Intelligence — live APIs / scraping."""
    if "tools" not in (state.get("route") or []):
        return state
    text, tool_sources = await run_tools(state["message"])
    sources = list(state.get("sources") or [])
    sources.extend(tool_sources)
    return {**state, "tool_context": text, "sources": sources}


async def generate_node(state: GraphState) -> GraphState:
    system = (
        "You are the assistant for 'Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System'. "
        "Blend MEMORY, DOCUMENTS (RAG), GRAPH facts, and TOOL output. "
        "Cite which source type informed key claims when possible. "
        "If context is insufficient, say so clearly."
    )
    context_blocks = []
    if state.get("memory_context"):
        context_blocks.append(f"MEMORY:\n{state['memory_context']}")
    if state.get("rag_context"):
        context_blocks.append(f"DOCUMENTS:\n{state['rag_context']}")
    if state.get("graph_context"):
        context_blocks.append(f"GRAPH:\n{state['graph_context']}")
    if state.get("tool_context"):
        context_blocks.append(f"TOOLS:\n{state['tool_context']}")
    context = "\n\n".join(context_blocks) if context_blocks else "No extra context."

    try:
        answer = await chat_completion(
            model=state.get("model"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{context}\n\nUSER QUESTION:\n{state['message']}"},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        answer = f"Sorry — the model call failed: {exc}"

    # Skip LLM-as-judge when the answer is an API/rate-limit notice (saves free quota)
    looks_like_api_error = any(
        marker in (answer or "")
        for marker in ("rate limit", "OpenRouter", "API key is not configured", "model call failed")
    )
    eval_scores = None
    if not looks_like_api_error:
        try:
            eval_scores = await score_response(
                question=state["message"], answer=answer, context=context
            )
        except Exception:  # noqa: BLE001
            eval_scores = None

    return {
        **state,
        "answer": answer,
        "sources": state.get("sources") or [],
        "eval_scores": eval_scores,
    }


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("memory_load", memory_load_node)
    graph.add_node("router", router_node)
    graph.add_node("memory_write", memory_write_node)
    graph.add_node("rag", rag_node)
    graph.add_node("kg", kg_node)
    graph.add_node("tools", tools_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("memory_load")
    graph.add_edge("memory_load", "router")
    graph.add_edge("router", "memory_write")
    graph.add_edge("memory_write", "rag")
    graph.add_edge("rag", "kg")
    graph.add_edge("kg", "tools")
    graph.add_edge("tools", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


workflow = build_graph()
