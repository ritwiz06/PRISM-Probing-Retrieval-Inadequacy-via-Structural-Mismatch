from __future__ import annotations

from dataclasses import dataclass
import re

from prism.analysis.evaluation import BACKENDS


@dataclass(frozen=True, slots=True)
class RouterPrediction:
    route: str
    scores: dict[str, float]
    rationale: str


IDENTIFIER_PATTERN = re.compile(
    r"(?:§\s*\d+|\b\d+\.\d+\b|\brfc[- ]?\d+\b|\bjsonb_[a-z0-9_]+\b|\b[a-z]+-\d+\b|\b[a-z]+(?:\.[a-z0-9_]+){2,}\b)",
    re.IGNORECASE,
)

LEXICAL_TERMS = (
    "rfc",
    "icd",
    "hipaa",
    "section",
    "torch.nn",
    "sklearn.",
    "numpy.",
    "postgresql",
    "jsonb",
    "u.s.c",
    "find",
)
DEDUCTIVE_TERMS = (
    "can a",
    "can an",
    "are all",
    "is a",
    "is an",
    "what property",
    "able to",
    "counterexample",
    "what eats",
)
RELATIONAL_TERMS = (
    "bridge",
    "connects",
    "connect",
    "relation connects",
    "between",
    "path",
    "multi-hop",
    "chain",
)
SEMANTIC_TERMS = (
    "feels like",
    "which idea",
    "which concept",
    "which term",
    "which condition",
    "called",
    "meaning",
    "concept",
    "describes",
)


def keyword_rule_route(query: str) -> RouterPrediction:
    lowered = query.lower()
    raw_scores = {backend: 0.0 for backend in BACKENDS}
    matched: list[str] = []

    if IDENTIFIER_PATTERN.search(query) or _contains_any(lowered, LEXICAL_TERMS):
        raw_scores["bm25"] += 3.0
        matched.append("identifier_or_formal_lookup")
    if _contains_any(lowered, RELATIONAL_TERMS):
        raw_scores["hybrid"] += 3.0
        matched.append("relational_bridge_or_connection")
    if _contains_any(lowered, DEDUCTIVE_TERMS):
        raw_scores["kg"] += 2.6
        matched.append("deductive_membership_or_property")
    if _contains_any(lowered, SEMANTIC_TERMS):
        raw_scores["dense"] += 2.4
        matched.append("semantic_paraphrase_marker")

    if not any(raw_scores.values()):
        raw_scores["dense"] = 1.0
        matched.append("default_semantic")

    # Relational questions often contain property words too; prefer Hybrid when both fire.
    if raw_scores["hybrid"] > 0:
        raw_scores["kg"] = max(0.0, raw_scores["kg"] - 0.8)
    # Exact identifiers should stay lexical unless explicitly relational.
    if raw_scores["bm25"] > 0 and raw_scores["hybrid"] == 0:
        raw_scores["dense"] = max(0.0, raw_scores["dense"] - 0.8)

    route = max(BACKENDS, key=lambda backend: (raw_scores[backend], -BACKENDS.index(backend)))
    total = sum(raw_scores.values()) or 1.0
    scores = {backend: raw_scores[backend] / total for backend in BACKENDS}
    return RouterPrediction(route=route, scores=scores, rationale=", ".join(matched))


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
