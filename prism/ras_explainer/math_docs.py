from __future__ import annotations

from dataclasses import asdict

from prism.ras.feature_parser import (
    DEDUCTIVE_MARKERS,
    IDENTIFIER_PATTERN,
    LEXICAL_MARKERS,
    RELATIONAL_MARKERS,
    SEMANTIC_MARKERS,
    parse_query_features,
)
from prism.ras.penalty_table import BACKENDS, compute_penalties
from prism.ras_v3.features import FEATURE_NAMES as RAS_V3_FEATURES
from prism.ras_v4.features import EVIDENCE_FEATURE_NAMES, FEATURE_NAMES as RAS_V4_FEATURES


def ras_math_payload() -> dict[str, object]:
    """Return implementation-faithful RAS math documentation."""

    return {
        "production_router": "computed_ras",
        "research_overlays": ["computed_ras_v2", "ras_v3", "ras_v4", "calibrated_rescue"],
        "notation": {
            "R": list(BACKENDS),
            "x": "query text",
            "f(x)": "interpretable query feature vector",
            "E_r(x)": "top-k evidence retrieved by candidate route r",
            "score_r": "route score for candidate route r",
            "margin": "gap between the best route score and runner-up score; direction depends on score convention",
        },
        "computed_ras": _computed_ras_payload(),
        "computed_ras_v2": _ras_v2_payload(),
        "ras_v3": _ras_v3_payload(),
        "ras_v4": _ras_v4_payload(),
        "calibrated_rescue": _calibrated_rescue_payload(),
        "scientific_position": {
            "route_only_adequacy": "Helpful and interpretable, but insufficient on adversarial hard cases where evidence use matters.",
            "evidence_adequacy": "RAS_V4 models answerability signals from candidate evidence, but recorded results still keep it analysis-only.",
            "production_decision": "computed_ras remains production default; rescue and learned RAS variants remain overlays.",
        },
    }


def sample_computed_ras_breakdown(query: str) -> dict[str, object]:
    features = parse_query_features(query)
    penalties = compute_penalties(features)
    selected = min(penalties, key=penalties.get)
    ordered = sorted(penalties.values())
    margin = ordered[1] - ordered[0] if len(ordered) > 1 else 0.0
    return {
        "query": query,
        "features": asdict(features),
        "scores": penalties,
        "selected_backend": selected,
        "margin": margin,
        "score_convention": "lower is better",
        "feature_effects": _computed_feature_effects(features),
    }


def _computed_ras_payload() -> dict[str, object]:
    return {
        "status": "production",
        "score_convention": "lower is better",
        "inputs": ["query text"],
        "feature_parser": {
            "lexical": list(LEXICAL_MARKERS) + [f"identifier regex: {IDENTIFIER_PATTERN.pattern}"],
            "semantic": list(SEMANTIC_MARKERS),
            "deductive": list(DEDUCTIVE_MARKERS),
            "relational": list(RELATIONAL_MARKERS),
            "fallback": "If no feature fires, semantic=True.",
        },
        "formula": (
            "Initialize p_r=1.0 for r in {bm25,dense,kg,hybrid}. "
            "If lexical: p_bm25 -= 0.6 and p_dense += 0.2. "
            "If semantic: p_dense -= 0.5. "
            "If deductive: p_kg -= 0.6. "
            "If relational: p_hybrid -= 0.7 and p_kg -= 0.2. "
            "Select argmin_r p_r."
        ),
        "outputs": ["selected_backend", "ras_scores", "parsed QueryFeatures"],
        "interpretability": "Direct weighted heuristic penalty table.",
    }


def _ras_v2_payload() -> dict[str, object]:
    return {
        "status": "analysis-only",
        "score_convention": "starts from computed_ras scores; final route may be overridden by narrow rules",
        "inputs": ["query text", "optional source_type_hint", "computed_ras route and margin"],
        "signals": [
            "identifier_heavy",
            "semantic_ambiguity",
            "relational",
            "deductive",
            "strong_identifier",
            "source_type_hint",
            "ras_margin",
        ],
        "rule_recipe": [
            "Start with computed_ras selected backend.",
            "If relational marker appears, select hybrid.",
            "Else if deductive marker appears and no strong identifier appears, select kg.",
            "Else if identifier-heavy plus semantic ambiguity and no strong identifier, select dense.",
            "Else if identifier-heavy plus strong identifier, select bm25.",
            "Else if formal source-pack prior plus identifier-heavy, select bm25.",
            "Else if margin < 0.15 and semantic-only, select dense.",
        ],
        "outputs": ["selected_backend", "original_backend", "ras_scores", "margin", "signals", "rationale"],
        "interpretability": "Rule-overlay correction layer; not a learned model and not production.",
    }


def _ras_v3_payload() -> dict[str, object]:
    return {
        "status": "analysis-only",
        "score_convention": "higher linear adequacy score is better",
        "inputs": ["query text", "source_type", "query_local_graph_available", "topk_rescue_opportunity"],
        "feature_count": len(RAS_V3_FEATURES),
        "feature_names": list(RAS_V3_FEATURES),
        "formula": (
            "For each route r, compute s_r = b_r + sum_j w_{r,j} f_j(x). "
            "The implementation uses multinomial logistic regression weights but routes by max linear score. "
            "Select argmax_r s_r."
        ),
        "training_protocol": "Curated benchmark plus selected dev layers and adversarial dev; held-out tests are not used for fitting.",
        "outputs": ["selected_backend", "route_scores", "margin", "active_features", "per-route feature contributions"],
        "interpretability": "Sparse linear per-feature route contributions.",
    }


def _ras_v4_payload() -> dict[str, object]:
    return {
        "status": "analysis-only",
        "score_convention": "higher joint adequacy score is better",
        "inputs": ["query text", "candidate backend", "candidate backend top-k evidence", "source_type"],
        "route_feature_count": len([name for name in RAS_V4_FEATURES if name.startswith("route__")]),
        "evidence_feature_count": len(EVIDENCE_FEATURE_NAMES),
        "evidence_feature_names": list(EVIDENCE_FEATURE_NAMES),
        "formula": (
            "For each candidate backend r, compute z_r = b + sum_j alpha_j route_j(x) "
            "+ sum_k beta_k evidence_k(E_r(x), x). Select argmax_r z_r. "
            "The score decomposes into route contribution, evidence contribution, and intercept."
        ),
        "training_protocol": "Binary logistic adequacy model over candidate backend/query/evidence pairs; adversarial test and held-out layers are not used for fitting.",
        "outputs": [
            "selected_backend",
            "combined_score_by_backend",
            "route_contribution",
            "evidence_contribution",
            "top feature contributions",
            "evidence diagnostics",
        ],
        "interpretability": "Joint route-and-evidence linear adequacy decomposition.",
    }


def _calibrated_rescue_payload() -> dict[str, object]:
    return {
        "status": "research overlay, not a core RAS version",
        "role": "Hard-case rescue and top-k evidence-use comparison.",
        "reason_included": "Recorded adversarial answer accuracy is stronger with rescue, showing route choice alone is not the whole target.",
        "outputs": ["calibrated route", "top-k rescue metadata", "failure-delta artifacts"],
    }


def _computed_feature_effects(features: object) -> list[dict[str, object]]:
    rows = []
    if getattr(features, "lexical", False):
        rows.extend(
            [
                {"feature": "lexical", "backend": "bm25", "delta": -0.6, "meaning": "exact identifiers favor BM25"},
                {"feature": "lexical", "backend": "dense", "delta": +0.2, "meaning": "lexical exactness slightly penalizes Dense"},
            ]
        )
    if getattr(features, "semantic", False):
        rows.append({"feature": "semantic", "backend": "dense", "delta": -0.5, "meaning": "conceptual wording favors Dense"})
    if getattr(features, "deductive", False):
        rows.append({"feature": "deductive", "backend": "kg", "delta": -0.6, "meaning": "membership/property reasoning favors KG"})
    if getattr(features, "relational", False):
        rows.extend(
            [
                {"feature": "relational", "backend": "hybrid", "delta": -0.7, "meaning": "bridge/path queries favor Hybrid"},
                {"feature": "relational", "backend": "kg", "delta": -0.2, "meaning": "relational structure partially favors KG"},
            ]
        )
    return rows
