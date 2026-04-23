from __future__ import annotations

from prism.ras_v4.scoring import RASV4Decision


def explanation_payload(decision: RASV4Decision) -> dict[str, object]:
    candidates = {}
    for backend, row in decision.candidate_scores.items():
        top = sorted(row.contributions.items(), key=lambda item: abs(float(item[1])), reverse=True)[:8]
        candidates[backend] = {
            "combined_score": row.combined_score,
            "route_contribution": row.route_contribution,
            "evidence_contribution": row.evidence_contribution,
            "margin_from_best": row.margin_from_best,
            "evidence_ids": row.evidence_ids,
            "top_contributions": [{"feature": name, "contribution": float(value)} for name, value in top],
            "evidence_diagnostics": row.features.metadata["evidence_metadata"],
        }
    return {
        "selected_backend": decision.selected_backend,
        "margin": decision.margin,
        "rationale": decision.rationale,
        "candidate_scores": candidates,
        "model_version": decision.model_version,
    }


def feature_weight_summary(weights: dict[str, float], top_n: int = 12) -> dict[str, list[dict[str, object]]]:
    route = sorted(
        ((name, value) for name, value in weights.items() if name.startswith("route__")),
        key=lambda item: abs(float(item[1])),
        reverse=True,
    )[:top_n]
    evidence = sorted(
        ((name, value) for name, value in weights.items() if name.startswith("evidence__")),
        key=lambda item: abs(float(item[1])),
        reverse=True,
    )[:top_n]
    return {
        "route_weights": [{"feature": name, "weight": float(value)} for name, value in route],
        "evidence_weights": [{"feature": name, "weight": float(value)} for name, value in evidence],
    }
