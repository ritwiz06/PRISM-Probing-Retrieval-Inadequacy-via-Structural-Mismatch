from __future__ import annotations

from dataclasses import asdict

from prism.schemas import QueryFeatures, RetrievedItem


def build_reasoning_trace(
    query: str,
    features: QueryFeatures,
    ras_scores: dict[str, float],
    selected_backend: str,
    evidence: list[RetrievedItem],
    synthesis_note: str,
) -> list[dict[str, object]]:
    sorted_scores = sorted(ras_scores.items(), key=lambda item: item[1])
    feature_signals = [name for name, enabled in asdict(features).items() if isinstance(enabled, bool) and enabled]
    return [
        {
            "step": "parse_query_features",
            "query_family_signals": feature_signals or ["semantic"],
            "features": asdict(features),
        },
        {
            "step": "score_ras",
            "ras_scores": ras_scores,
            "best_backend": sorted_scores[0][0],
            "runner_up_backend": sorted_scores[1][0] if len(sorted_scores) > 1 else None,
        },
        {
            "step": "select_backend",
            "selected_backend": selected_backend,
            "route_rationale": route_rationale(selected_backend, features, ras_scores),
            "why_others_not_preferred": [
                f"{backend} RAS={score:.3f} vs selected {selected_backend} RAS={ras_scores[selected_backend]:.3f}"
                for backend, score in sorted_scores
                if backend != selected_backend
            ],
        },
        {
            "step": "retrieve_evidence",
            "evidence_ids": [item.item_id for item in evidence],
            "evidence_modes": [item.metadata.get("query_mode") or item.metadata.get("fusion_method") for item in evidence],
        },
        {
            "step": "synthesize_answer",
            "used_evidence_ids": [item.item_id for item in evidence],
            "synthesis_note": synthesis_note,
        },
    ]


def route_rationale(selected_backend: str, features: QueryFeatures, ras_scores: dict[str, float]) -> str:
    family = {
        "bm25": "lexical/exact-match",
        "dense": "semantic/paraphrase",
        "kg": "deductive/structured",
        "hybrid": "relational/fused-evidence",
    }.get(selected_backend, selected_backend)
    return f"Selected {selected_backend} for {family} signals with minimum RAS={ras_scores[selected_backend]:.3f}."
