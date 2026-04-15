from __future__ import annotations

from prism.ras.compute_ras import route_query
from prism.schemas import RouteDecision


def predict_route(query: str) -> RouteDecision:
    """Local placeholder baseline until Ollama wiring is added."""
    return route_query(query)
