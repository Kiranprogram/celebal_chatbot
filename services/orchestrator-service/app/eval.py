from __future__ import annotations

import re
from typing import Any

import httpx

from app.config import get_settings
from app.openrouter import chat_completion


async def score_response(
    *,
    question: str,
    answer: str,
    context: str,
) -> dict[str, Any]:
    """
    Evaluation Framework metrics:
    - context relevance
    - answer correctness
    - faithfulness
    """
    settings = get_settings()
    heuristic = _heuristic_scores(question, answer, context)

    if not settings.openrouter_api_key:
        return {**heuristic, "method": "heuristic"}

    prompt = (
        "Score the QA for a RAG system from 1-5 integers.\n"
        "Return ONLY JSON: "
        '{"context_relevance":1-5,"answer_correctness":1-5,"faithfulness":1-5,"rationale":"..."}\n\n'
        f"QUESTION:\n{question}\n\nCONTEXT:\n{context[:4000]}\n\nANSWER:\n{answer}\n"
    )
    try:
        raw = await chat_completion(
            messages=[
                {"role": "system", "content": "You are an impartial RAG evaluator. JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        start, end = raw.find("{"), raw.rfind("}")
        data = {}
        if start >= 0 and end >= 0:
            import json

            data = json.loads(raw[start : end + 1])
        return {
            "context_relevance": int(data.get("context_relevance", heuristic["context_relevance"])),
            "answer_correctness": int(data.get("answer_correctness", heuristic["answer_correctness"])),
            "faithfulness": int(data.get("faithfulness", heuristic["faithfulness"])),
            "rationale": data.get("rationale", ""),
            "method": "llm_judge",
        }
    except Exception:  # noqa: BLE001
        return {**heuristic, "method": "heuristic_fallback"}


def _heuristic_scores(question: str, answer: str, context: str) -> dict[str, int]:
    q_tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
    c_tokens = set(re.findall(r"[a-z0-9]+", context.lower()))
    a_tokens = set(re.findall(r"[a-z0-9]+", answer.lower()))
    overlap_qc = len(q_tokens & c_tokens) / max(1, len(q_tokens))
    overlap_ac = len(a_tokens & c_tokens) / max(1, len(a_tokens))
    overlap_qa = len(q_tokens & a_tokens) / max(1, len(q_tokens))

    def to_score(x: float) -> int:
        return max(1, min(5, int(round(1 + 4 * x))))

    faithfulness = to_score(overlap_ac if context.strip() else 0.4)
    relevance = to_score(overlap_qc if context.strip() else 0.3)
    correctness = to_score(0.5 * overlap_qa + 0.5 * overlap_ac)
    return {
        "context_relevance": relevance,
        "answer_correctness": correctness,
        "faithfulness": faithfulness,
    }


async def persist_eval_optional(payload: dict[str, Any]) -> None:
    """Best-effort log hook (orchestrator DB wiring can store later)."""
    _ = payload
    return None
