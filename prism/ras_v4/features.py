from __future__ import annotations

from dataclasses import dataclass
import math
import re

from prism.analysis.evaluation import BACKENDS
from prism.ras_v3.features import FEATURE_NAMES as RAS_V3_FEATURE_NAMES
from prism.ras_v3.features import extract_features as extract_route_features
from prism.schemas import RetrievedItem

ROUTE_FEATURE_PREFIX = "route__"
EVIDENCE_FEATURE_PREFIX = "evidence__"

EVIDENCE_FEATURE_NAMES: tuple[str, ...] = (
    "candidate_bm25",
    "candidate_dense",
    "candidate_kg",
    "candidate_hybrid",
    "candidate_matches_computed_ras",
    "candidate_matches_keyword",
    "top1_score",
    "topk_score_mean",
    "top1_top2_gap",
    "evidence_count_log",
    "query_overlap_top1",
    "query_overlap_topk",
    "identifier_exact_match",
    "title_or_id_match",
    "source_diversity",
    "redundancy",
    "kg_fact_or_path_present",
    "kg_path_completeness",
    "hybrid_component_agreement",
    "semantic_snippet_consistency",
    "negation_or_distractor_contamination",
    "public_noise_indicator",
    "answerability_marker",
)

FEATURE_NAMES: tuple[str, ...] = tuple(f"{ROUTE_FEATURE_PREFIX}{name}" for name in RAS_V3_FEATURE_NAMES) + tuple(
    f"{EVIDENCE_FEATURE_PREFIX}{name}" for name in EVIDENCE_FEATURE_NAMES
)


@dataclass(frozen=True, slots=True)
class EvidenceDiagnostics:
    backend: str
    values: dict[str, float]
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class RASV4FeatureVector:
    query: str
    backend: str
    source_type: str
    values: dict[str, float]
    route_feature_values: dict[str, float]
    evidence_feature_values: dict[str, float]
    metadata: dict[str, object]

    def ordered_values(self) -> list[float]:
        return [float(self.values.get(name, 0.0)) for name in FEATURE_NAMES]


def extract_joint_features(
    query: str,
    backend: str,
    evidence: list[RetrievedItem],
    *,
    source_type: str = "",
    query_local_graph_available: bool = False,
    topk_rescue_opportunity: bool = False,
) -> RASV4FeatureVector:
    route_features = extract_route_features(
        query,
        source_type=source_type,
        query_local_graph_available=query_local_graph_available,
        topk_rescue_opportunity=topk_rescue_opportunity,
    )
    evidence_diagnostics = extract_evidence_diagnostics(query, backend, evidence, route_features.metadata, source_type=source_type)
    values: dict[str, float] = {}
    for name, value in route_features.values.items():
        values[f"{ROUTE_FEATURE_PREFIX}{name}"] = float(value)
    for name, value in evidence_diagnostics.values.items():
        values[f"{EVIDENCE_FEATURE_PREFIX}{name}"] = float(value)
    for name in FEATURE_NAMES:
        values.setdefault(name, 0.0)
    metadata = {
        "route_metadata": route_features.metadata,
        "evidence_metadata": evidence_diagnostics.metadata,
        "active_features": {key: value for key, value in values.items() if abs(float(value)) > 1e-9},
    }
    return RASV4FeatureVector(
        query=query,
        backend=backend,
        source_type=source_type,
        values=values,
        route_feature_values=route_features.values,
        evidence_feature_values=evidence_diagnostics.values,
        metadata=metadata,
    )


def extract_evidence_diagnostics(
    query: str,
    backend: str,
    evidence: list[RetrievedItem],
    route_metadata: dict[str, object] | None = None,
    *,
    source_type: str = "",
) -> EvidenceDiagnostics:
    route_metadata = route_metadata or {}
    query_tokens = _tokens(query)
    evidence_texts = [item.content for item in evidence]
    top1 = evidence[0] if evidence else None
    scores = [float(item.score) for item in evidence]
    normalized_scores = [_squash_score(score) for score in scores]
    values = {name: 0.0 for name in EVIDENCE_FEATURE_NAMES}
    values[f"candidate_{backend}"] = 1.0
    values["candidate_matches_computed_ras"] = float(route_metadata.get("computed_route") == backend)
    values["candidate_matches_keyword"] = float(route_metadata.get("keyword_route") == backend)
    values["top1_score"] = normalized_scores[0] if normalized_scores else 0.0
    values["topk_score_mean"] = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.0
    values["top1_top2_gap"] = max(0.0, normalized_scores[0] - normalized_scores[1]) if len(normalized_scores) > 1 else values["top1_score"]
    values["evidence_count_log"] = math.log1p(len(evidence)) / 2.0
    values["query_overlap_top1"] = _overlap(query_tokens, _tokens(top1.content if top1 else ""))
    values["query_overlap_topk"] = _overlap(query_tokens, _tokens(" ".join(evidence_texts)))
    values["identifier_exact_match"] = _identifier_match(query, evidence_texts)
    values["title_or_id_match"] = _title_or_id_match(query, evidence)
    values["source_diversity"] = _source_diversity(evidence)
    values["redundancy"] = _redundancy(evidence_texts)
    values["kg_fact_or_path_present"] = float(any(_is_structural_item(item) for item in evidence))
    values["kg_path_completeness"] = _kg_path_completeness(evidence)
    values["hybrid_component_agreement"] = _hybrid_component_agreement(evidence)
    values["semantic_snippet_consistency"] = _semantic_consistency(query, evidence_texts)
    values["negation_or_distractor_contamination"] = _contamination(query, evidence_texts)
    values["public_noise_indicator"] = float("public" in source_type.lower() or _contains_any(" ".join(evidence_texts).lower(), ("boilerplate", "navigation", "snapshot", "fallback")))
    values["answerability_marker"] = _answerability_marker(evidence_texts)
    metadata = {
        "backend": backend,
        "evidence_count": len(evidence),
        "top_evidence_ids": [item.item_id for item in evidence[:5]],
        "top1_source_type": top1.source_type if top1 else "",
        "top1_metadata": top1.metadata if top1 else {},
        "diagnostic_summary": _diagnostic_summary(values),
    }
    return EvidenceDiagnostics(backend=backend, values=values, metadata=metadata)


def _tokens(text: str) -> set[str]:
    stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "what", "which", "can", "does"}
    return {token for token in re.findall(r"[a-z0-9._:/§-]+", text.lower()) if token not in stopwords and len(token) > 1}


def _overlap(query_tokens: set[str], text_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)


def _squash_score(score: float) -> float:
    if score <= 0:
        return 0.0
    return float(score / (1.0 + abs(score)))


def _identifier_match(query: str, evidence_texts: list[str]) -> float:
    identifiers = re.findall(r"\b(?:rfc-?\d+|icd-10\s+[a-z]\d{2}\.\d|hipaa\s+\d{3}\.\d{3}|[a-z_]+\.[\w.]+|jsonb_[a-z0-9_]+)\b|§\s*\d+", query.lower())
    if not identifiers:
        return 0.0
    haystack = " ".join(evidence_texts).lower().replace(" ", "")
    hits = sum(1 for identifier in identifiers if identifier.replace(" ", "") in haystack)
    return hits / len(identifiers)


def _title_or_id_match(query: str, evidence: list[RetrievedItem]) -> float:
    query_tokens = _tokens(query)
    if not query_tokens or not evidence:
        return 0.0
    best = 0.0
    for item in evidence:
        meta_text = " ".join(str(item.metadata.get(key, "")) for key in ("title", "doc_id", "source_doc_id", "parent_doc_id", "chunk_id", "triple_id", "path_id"))
        best = max(best, _overlap(query_tokens, _tokens(meta_text + " " + item.item_id)))
    return best


def _source_diversity(evidence: list[RetrievedItem]) -> float:
    if not evidence:
        return 0.0
    sources = {item.metadata.get("parent_doc_id") or item.metadata.get("source_doc_id") or item.metadata.get("kg_source_doc_id") or item.item_id for item in evidence}
    return min(1.0, len(sources) / len(evidence))


def _redundancy(evidence_texts: list[str]) -> float:
    if len(evidence_texts) < 2:
        return 0.0
    token_sets = [_tokens(text) for text in evidence_texts if text]
    if len(token_sets) < 2:
        return 0.0
    overlaps = []
    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            union = left | right
            overlaps.append(len(left & right) / len(union) if union else 0.0)
    return sum(overlaps) / len(overlaps) if overlaps else 0.0


def _is_structural_item(item: RetrievedItem) -> bool:
    return item.source_type in {"kg", "triple", "path"} or any(key in item.metadata for key in ("triple_id", "path_id", "kg_mode"))


def _kg_path_completeness(evidence: list[RetrievedItem]) -> float:
    if not evidence:
        return 0.0
    path_like = sum(1 for item in evidence if "path" in item.item_id or "path_id" in item.metadata or str(item.metadata.get("mode", "")).startswith("two_hop"))
    triple_like = sum(1 for item in evidence if _is_structural_item(item))
    if path_like:
        return 1.0
    return min(1.0, triple_like / 2.0)


def _hybrid_component_agreement(evidence: list[RetrievedItem]) -> float:
    backends: set[str] = set()
    for item in evidence:
        for key in ("component_backends", "component_sources", "fused_backends", "backend"):
            value = str(item.metadata.get(key, ""))
            for backend in BACKENDS:
                if backend in value:
                    backends.add(backend)
        if item.source_type in BACKENDS:
            backends.add(item.source_type)
    return min(1.0, len(backends) / 3.0)


def _semantic_consistency(query: str, evidence_texts: list[str]) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    overlaps = [_overlap(query_tokens, _tokens(text)) for text in evidence_texts[:5]]
    return sum(overlaps) / len(overlaps) if overlaps else 0.0


def _contamination(query: str, evidence_texts: list[str]) -> float:
    text = (query + " " + " ".join(evidence_texts[:3])).lower()
    markers = ("not ", "do not", "rather than", "instead of", "despite", "distractor", "nearby", "wrong", "fallback")
    return min(1.0, sum(1 for marker in markers if marker in text) / 3.0)


def _answerability_marker(evidence_texts: list[str]) -> float:
    text = " ".join(evidence_texts[:5]).lower()
    markers = ("defines", "is a", "are", "connects", "because", "property", "means", "describes", "uses", "causes")
    return min(1.0, sum(1 for marker in markers if marker in text) / 3.0)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _diagnostic_summary(values: dict[str, float]) -> str:
    positives = sorted(values.items(), key=lambda item: abs(float(item[1])), reverse=True)[:5]
    return ", ".join(f"{name}={value:.2f}" for name, value in positives)
