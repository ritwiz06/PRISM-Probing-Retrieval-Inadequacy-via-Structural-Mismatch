from __future__ import annotations

from dataclasses import dataclass
import math
import re

from prism.analysis.evaluation import BACKENDS
from prism.calibration.route_calibrator import detect_route_signals
from prism.public_corpus.lexical_retriever import is_identifier_heavy_query
from prism.ras.compute_ras import route_query
from prism.ras.feature_parser import parse_query_features
from prism.router_baselines.rule_router import keyword_rule_route


FEATURE_NAMES: tuple[str, ...] = (
    "bias",
    "query_length_log",
    "token_count_log",
    "identifier_heavy",
    "identifier_count_log",
    "lexical_exactness",
    "semantic_abstraction",
    "deductive_cue",
    "relational_bridge",
    "multi_hop_cue",
    "negation_or_contrast",
    "route_ambiguity",
    "low_ras_margin",
    "computed_route_bm25",
    "computed_route_dense",
    "computed_route_kg",
    "computed_route_hybrid",
    "keyword_route_bm25",
    "keyword_route_dense",
    "keyword_route_kg",
    "keyword_route_hybrid",
    "source_curated",
    "source_external",
    "source_generalization",
    "source_public_raw",
    "source_adversarial",
    "source_open_corpus",
    "source_formal_spec",
    "query_local_graph_available",
    "public_document_noise",
    "topk_rescue_opportunity",
)


@dataclass(frozen=True, slots=True)
class RASV3FeatureVector:
    query: str
    source_type: str
    values: dict[str, float]
    metadata: dict[str, object]

    def ordered_values(self) -> list[float]:
        return [float(self.values.get(name, 0.0)) for name in FEATURE_NAMES]


def extract_features(
    query: str,
    *,
    source_type: str = "",
    query_local_graph_available: bool = False,
    topk_rescue_opportunity: bool = False,
) -> RASV3FeatureVector:
    """Extract an interpretable, publication-facing route feature vector."""

    parsed = parse_query_features(query)
    decision = route_query(query)
    keyword = keyword_rule_route(query)
    signals = detect_route_signals(query)
    lowered = query.lower()
    tokens = re.findall(r"[a-z0-9._:/§-]+", lowered)
    identifier_count = len(signals.get("identifiers", [])) + len(
        re.findall(r"\b(?:rfc-?\d+|icd-10\s+[a-z]\d{2}\.\d|hipaa\s+\d{3}\.\d{3}|[a-z_]+\.[\w.]+)\b", lowered)
    )
    margin = _margin(decision.ras_scores)
    exact_terms = ("exact", "identifier", "code", "section", "rfc", "icd", "hipaa", "jsonb", "torch.nn", "sklearn.")
    semantic_terms = (
        "feels like",
        "meaning",
        "concept",
        "idea",
        "describes",
        "called",
        "why",
        "how",
        "rather than",
        "metaphor",
    )
    deductive_terms = ("can a", "can an", "are all", "is a", "is an", "every", "property", "membership", "class")
    relational_terms = ("bridge", "connect", "connects", "between", "path", "relation", "multi-hop", "chain")
    noise_terms = ("boilerplate", "fallback", "snapshot", "nearby", "distractor", "public page", "formatting")

    route_ambiguity = sum(bool(value) for value in (parsed.lexical, parsed.semantic, parsed.deductive, parsed.relational))
    values = {name: 0.0 for name in FEATURE_NAMES}
    values.update(
        {
            "bias": 1.0,
            "query_length_log": math.log1p(len(query)) / 6.0,
            "token_count_log": math.log1p(len(tokens)) / 3.0,
            "identifier_heavy": float(is_identifier_heavy_query(query)),
            "identifier_count_log": math.log1p(identifier_count),
            "lexical_exactness": float(parsed.lexical or _contains_any(lowered, exact_terms)),
            "semantic_abstraction": float(parsed.semantic or _contains_any(lowered, semantic_terms)),
            "deductive_cue": float(parsed.deductive or _contains_any(lowered, deductive_terms)),
            "relational_bridge": float(parsed.relational or _contains_any(lowered, relational_terms)),
            "multi_hop_cue": float(any(term in lowered for term in ("two-hop", "multi-hop", "bridge", "chain", "path"))),
            "negation_or_contrast": float(any(term in lowered for term in (" not ", "do not", "rather than", "instead of", "despite", "although"))),
            "route_ambiguity": max(0.0, (route_ambiguity - 1) / 3.0),
            "low_ras_margin": float(margin < 0.25),
            "query_local_graph_available": float(query_local_graph_available),
            "public_document_noise": float(_contains_any(lowered, noise_terms) or "public" in source_type),
            "topk_rescue_opportunity": float(topk_rescue_opportunity),
        }
    )
    values[f"computed_route_{decision.selected_backend}"] = 1.0
    values[f"keyword_route_{keyword.route}"] = 1.0
    for key, active in _source_features(source_type).items():
        values[key] = float(active)

    metadata = {
        "computed_route": decision.selected_backend,
        "computed_ras_scores": decision.ras_scores,
        "computed_ras_margin": margin,
        "keyword_route": keyword.route,
        "keyword_scores": keyword.scores,
        "parsed_features": {
            "lexical": parsed.lexical,
            "semantic": parsed.semantic,
            "deductive": parsed.deductive,
            "relational": parsed.relational,
        },
        "signals": signals,
        "active_features": {key: value for key, value in values.items() if abs(value) > 1e-9},
    }
    return RASV3FeatureVector(query=query, source_type=source_type, values=values, metadata=metadata)


def _source_features(source_type: str) -> dict[str, bool]:
    lowered = source_type.lower()
    return {
        "source_curated": "curated" in lowered,
        "source_external": "external" in lowered,
        "source_generalization": "generalization" in lowered,
        "source_public_raw": "public" in lowered,
        "source_adversarial": "adversarial" in lowered,
        "source_open_corpus": "open" in lowered or "source_pack" in lowered or "runtime" in lowered,
        "source_formal_spec": any(term in lowered for term in ("rfc", "spec", "medical", "policy", "api", "formal")),
    }


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted(float(value) for value in scores.values())
    if len(ordered) < 2:
        return 0.0
    return ordered[1] - ordered[0]


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
