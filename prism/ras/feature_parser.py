from __future__ import annotations

import re

from prism.schemas import QueryFeatures


LEXICAL_MARKERS = ("section", "identifier", "code", "exact", "bm25", "rfc", "jsonb", "torch.nn", "sklearn.")
DEDUCTIVE_MARKERS = ("can", "are all", "every", "property", "membership", "class", "able to", "produce", "two-hop", "eats")
RELATIONAL_MARKERS = ("relation", "path", "between", "multi-hop", "chain", "connect", "connects", "bridge")
SEMANTIC_MARKERS = ("similar", "feels like", "concept", "meaning", "about")
IDENTIFIER_PATTERN = re.compile(
    r"(?:§\s*\d+|\b\d+\.\d+\b|\brfc[- ]?\d+\b|\bjsonb_[a-z0-9_]+\b|\b[a-z]+-\d+\b|\b[a-z]+(?:\.[a-z0-9_]+){2,}\b)",
    re.IGNORECASE,
)
MEMBERSHIP_PATTERN = re.compile(r"^(?:is|are)\s+(?:a|an)?\s*\w+\s+(?:a|an)\s+\w+", re.IGNORECASE)


def parse_query_features(query: str) -> QueryFeatures:
    lowered = query.lower()
    features = QueryFeatures(query=query)
    features.lexical = _has_marker(lowered, LEXICAL_MARKERS) or bool(IDENTIFIER_PATTERN.search(query))
    features.deductive = _has_marker(lowered, DEDUCTIVE_MARKERS) or bool(MEMBERSHIP_PATTERN.search(query))
    features.relational = _has_marker(lowered, RELATIONAL_MARKERS)
    features.semantic = _has_marker(lowered, SEMANTIC_MARKERS)

    if not any((features.lexical, features.deductive, features.relational, features.semantic)):
        features.semantic = True
    return features


def _has_marker(lowered_query: str, markers: tuple[str, ...]) -> bool:
    for marker in markers:
        if re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", lowered_query):
            return True
    return False
