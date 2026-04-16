from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from prism.ras.compute_ras import route_query
from prism.router_baselines.rule_router import keyword_rule_route

if TYPE_CHECKING:
    from prism.router_baselines.classifier_router import ClassifierRouter


def compute_route_confidence(query: str, classifier: ClassifierRouter | None = None) -> dict[str, object]:
    decision = route_query(query)
    ranked = sorted(decision.ras_scores.items(), key=lambda item: item[1])
    selected, best_score = ranked[0]
    competitor, second_score = ranked[1]
    margin = float(second_score - best_score)
    keyword = keyword_rule_route(query)
    classifier_route = classifier.predict(query).route if classifier is not None else ""
    agreements = [keyword.route == selected]
    if classifier_route:
        agreements.append(classifier_route == selected)
    agreement_count = sum(1 for item in agreements if item)
    confidence_score = margin + 0.15 * agreement_count
    label = _confidence_label(confidence_score, margin, agreement_count)
    return {
        "selected_backend": selected,
        "confidence_score": round(confidence_score, 6),
        "confidence_label": label,
        "ras_margin": round(margin, 6),
        "top_competing_backend": competitor,
        "best_ras_score": best_score,
        "second_best_ras_score": second_score,
        "keyword_route": keyword.route,
        "classifier_route": classifier_route,
        "router_agreement_count": agreement_count,
        "route_rationale": _rationale(selected, competitor, margin, agreement_count),
        "features": asdict(decision.features),
        "ras_scores": decision.ras_scores,
    }


def _confidence_label(score: float, margin: float, agreement_count: int) -> str:
    if score >= 0.65 and margin >= 0.35:
        return "high"
    if score >= 0.35 or agreement_count >= 1:
        return "medium"
    return "low"


def _rationale(selected: str, competitor: str, margin: float, agreement_count: int) -> str:
    return (
        f"Computed RAS selected {selected}; next competitor is {competitor} "
        f"with margin {margin:.3f}. {agreement_count} auxiliary router(s) agreed."
    )
