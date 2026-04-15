from __future__ import annotations

from prism.ras.feature_parser import parse_query_features
from prism.ras.penalty_table import compute_penalties
from prism.schemas import RouteDecision


def route_query(query: str) -> RouteDecision:
    features = parse_query_features(query)
    scores = compute_penalties(features)
    selected_backend = min(scores, key=scores.get)
    return RouteDecision(selected_backend=selected_backend, ras_scores=scores, features=features)
