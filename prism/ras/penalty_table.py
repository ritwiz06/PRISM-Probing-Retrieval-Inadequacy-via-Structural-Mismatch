from __future__ import annotations

from prism.schemas import QueryFeatures


BACKENDS = ("bm25", "dense", "kg", "hybrid")


def compute_penalties(features: QueryFeatures) -> dict[str, float]:
    penalties = {backend: 1.0 for backend in BACKENDS}
    if features.lexical:
        penalties["bm25"] -= 0.6
        penalties["dense"] += 0.2
    if features.semantic:
        penalties["dense"] -= 0.5
    if features.deductive:
        penalties["kg"] -= 0.6
    if features.relational:
        penalties["hybrid"] -= 0.7
        penalties["kg"] -= 0.2
    return penalties
