from __future__ import annotations

from prism.ras_v3.scoring import RASV3Decision


def explanation_payload(decision: RASV3Decision) -> dict[str, object]:
    selected = decision.selected_backend
    selected_contrib = decision.contributions[selected]
    sorted_contrib = sorted(
        ((feature, value) for feature, value in selected_contrib.items()),
        key=lambda row: abs(float(row[1])),
        reverse=True,
    )
    return {
        "query": decision.features.query,
        "selected_backend": selected,
        "route_scores": decision.route_scores,
        "margin": decision.margin,
        "rationale": decision.rationale,
        "active_features": decision.features.metadata["active_features"],
        "top_selected_route_contributions": [
            {"feature": feature, "contribution": float(value)} for feature, value in sorted_contrib[:8]
        ],
        "all_route_contributions": decision.contributions,
        "computed_ras_context": {
            "computed_route": decision.features.metadata["computed_route"],
            "computed_ras_scores": decision.features.metadata["computed_ras_scores"],
            "keyword_route": decision.features.metadata["keyword_route"],
        },
    }


def feature_weight_summary(weights: dict[str, dict[str, float]], top_n: int = 8) -> dict[str, list[dict[str, object]]]:
    summary: dict[str, list[dict[str, object]]] = {}
    for route, row in weights.items():
        ranked = sorted(row.items(), key=lambda item: abs(float(item[1])), reverse=True)[:top_n]
        summary[route] = [{"feature": feature, "weight": float(weight)} for feature, weight in ranked]
    return summary
