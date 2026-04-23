from __future__ import annotations

import json
import re

from prism.analysis.evaluation import BACKENDS

ROUTE_DEFINITIONS = {
    "bm25": "Lexical exact-match retrieval for identifiers, formal codes, APIs, RFCs, sections, and exact terms.",
    "dense": "Semantic retrieval for conceptual or paraphrased questions where exact wording may differ.",
    "kg": "Structured KG retrieval for membership, properties, class scope, universal/existential, and deductive questions.",
    "hybrid": "Fused retrieval for relational or multi-evidence bridge questions combining text and structure.",
}


def build_router_prompt(
    query: str,
    *,
    parsed_features: dict[str, object] | None = None,
    ras_scores: dict[str, float] | None = None,
    evidence_hints: dict[str, object] | None = None,
) -> str:
    payload = {
        "task": "Choose the best PRISM retrieval route for the query.",
        "query": query,
        "route_definitions": ROUTE_DEFINITIONS,
        "parsed_features": parsed_features or {},
        "computed_ras_scores": ras_scores or {},
        "evidence_hints": evidence_hints or {},
        "constraints": [
            "Return JSON only.",
            "Use one route from: bm25, dense, kg, hybrid.",
            "Do not answer the question.",
            "Prefer the minimum representation needed for faithful evidence.",
        ],
        "output_schema": {
            "route": "bm25|dense|kg|hybrid",
            "confidence": "number from 0 to 1",
            "rationale": "short reason",
            "alternatives": [{"route": "backend", "score": "0 to 1"}],
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parse_router_response(text: str) -> dict[str, object]:
    raw = _json_object(text)
    route = str(raw.get("route", "")).strip().lower()
    if route not in BACKENDS:
        route = _fallback_route_from_text(text)
    confidence = _coerce_confidence(raw.get("confidence", 0.0))
    alternatives = raw.get("alternatives", [])
    if not isinstance(alternatives, list):
        alternatives = []
    return {
        "route": route if route in BACKENDS else "",
        "confidence": confidence,
        "rationale": str(raw.get("rationale", "")).strip() or "Parsed from local LLM response.",
        "alternatives": _clean_alternatives(alternatives),
        "raw_text": text,
    }


def _json_object(text: str) -> dict[str, object]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


def _fallback_route_from_text(text: str) -> str:
    lowered = text.lower()
    for backend in BACKENDS:
        if backend in lowered:
            return backend
    return ""


def _coerce_confidence(value: object) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, confidence))


def _clean_alternatives(alternatives: list[object]) -> list[dict[str, object]]:
    clean: list[dict[str, object]] = []
    for item in alternatives:
        if not isinstance(item, dict):
            continue
        route = str(item.get("route", "")).lower()
        if route not in BACKENDS:
            continue
        clean.append({"route": route, "score": _coerce_confidence(item.get("score", 0.0))})
    return clean

