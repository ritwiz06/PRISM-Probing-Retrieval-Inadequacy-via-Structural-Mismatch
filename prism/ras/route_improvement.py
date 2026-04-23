from __future__ import annotations

from dataclasses import dataclass
import re

from prism.ras.compute_ras import route_query
from prism.router_baselines.rule_router import IDENTIFIER_PATTERN
from prism.schemas import RouteDecision

SEMANTIC_AMBIGUITY_TERMS = (
    "feels like",
    "concept",
    "meaning",
    "describes",
    "not",
    "rather than",
    "metaphor",
    "idea",
)
RELATIONAL_TERMS = ("bridge", "connect", "connects", "between", "path", "relation")
DEDUCTIVE_TERMS = ("can a", "can an", "are all", "is a", "is an", "what property", "able to")
STRONG_IDENTIFIER_TERMS = ("rfc", "icd", "hipaa", "torch.nn", "§", "jsonb", "u.s.c")


@dataclass(frozen=True, slots=True)
class RASV2Decision:
    selected_backend: str
    original_backend: str
    ras_scores: dict[str, float]
    margin: float
    rationale: str
    signals: dict[str, object]


def route_query_v2(query: str, *, source_type_hint: str = "") -> RASV2Decision:
    """Interpretable analysis-only route variant.

    RAS v2 starts from computed RAS and adds narrow hard-case corrections. It
    is not the production router unless explicitly adopted after guardrails.
    """

    decision: RouteDecision = route_query(query)
    lowered = query.lower()
    margin = _margin(decision.ras_scores)
    signals = {
        "identifier_heavy": bool(IDENTIFIER_PATTERN.search(query)),
        "semantic_ambiguity": _contains_any(lowered, SEMANTIC_AMBIGUITY_TERMS),
        "relational": _contains_any(lowered, RELATIONAL_TERMS),
        "deductive": _contains_any(lowered, DEDUCTIVE_TERMS),
        "strong_identifier": _contains_any(lowered, STRONG_IDENTIFIER_TERMS) or bool(re.search(r"\b[a-z]+-\d+\b|§\d+", lowered)),
        "source_type_hint": source_type_hint,
        "ras_margin": margin,
    }
    selected = decision.selected_backend
    reasons = [f"started from computed RAS={selected}"]

    if signals["relational"]:
        selected = "hybrid"
        reasons.append("relational bridge/path marker forces Hybrid")
    elif signals["deductive"] and not signals["strong_identifier"]:
        selected = "kg"
        reasons.append("deductive membership/property marker favors KG")
    elif signals["identifier_heavy"] and signals["semantic_ambiguity"] and not signals["strong_identifier"]:
        selected = "dense"
        reasons.append("identifier-like term appears inside semantic ambiguity; avoid lexical over-trigger")
    elif signals["identifier_heavy"] and signals["strong_identifier"]:
        selected = "bm25"
        reasons.append("strong formal identifier keeps BM25")
    elif source_type_hint in {"source_pack:rfc_specs", "source_pack:medical_codes", "source_pack:cs_api_docs"} and signals["identifier_heavy"]:
        selected = "bm25"
        reasons.append("source-pack prior favors exact lexical lookup")
    elif margin < 0.15 and decision.features.semantic and not decision.features.lexical:
        selected = "dense"
        reasons.append("low-margin semantic-only query prefers Dense")

    return RASV2Decision(
        selected_backend=selected,
        original_backend=decision.selected_backend,
        ras_scores=decision.ras_scores,
        margin=margin,
        rationale="; ".join(reasons),
        signals=signals,
    )


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted(scores.values())
    if len(ordered) < 2:
        return 0.0
    return float(ordered[1] - ordered[0])


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)

