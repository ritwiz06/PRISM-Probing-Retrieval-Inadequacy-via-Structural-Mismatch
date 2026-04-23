from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from prism.analysis.evaluation import BACKENDS
from prism.ras_v3.features import RASV3FeatureVector, extract_features
from prism.ras_v3.model import RASV3Model

DEFAULT_MODEL_PATH = Path("data/eval/ras_v3_model.json")


@dataclass(frozen=True, slots=True)
class RASV3Decision:
    selected_backend: str
    route_scores: dict[str, float]
    margin: float
    features: RASV3FeatureVector
    contributions: dict[str, dict[str, float]]
    rationale: str
    model_version: str


def route_query_v3(
    query: str,
    *,
    model: RASV3Model | None = None,
    source_type: str = "",
    query_local_graph_available: bool = False,
    topk_rescue_opportunity: bool = False,
) -> RASV3Decision:
    active_model = model or RASV3Model.load(DEFAULT_MODEL_PATH)
    features = extract_features(
        query,
        source_type=source_type,
        query_local_graph_available=query_local_graph_available,
        topk_rescue_opportunity=topk_rescue_opportunity,
    )
    scores = active_model.predict_scores(features)
    selected = max(BACKENDS, key=lambda backend: (scores[backend], -BACKENDS.index(backend)))
    margin = _margin(scores)
    contributions = active_model.contributions(features)
    rationale = _rationale(selected, scores, contributions)
    return RASV3Decision(
        selected_backend=selected,
        route_scores=scores,
        margin=margin,
        features=features,
        contributions=contributions,
        rationale=rationale,
        model_version=active_model.model_version,
    )


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted((float(value) for value in scores.values()), reverse=True)
    if len(ordered) < 2:
        return 0.0
    return ordered[0] - ordered[1]


def _rationale(selected: str, scores: dict[str, float], contributions: dict[str, dict[str, float]]) -> str:
    top_features = sorted(
        ((feature, value) for feature, value in contributions[selected].items() if feature != "intercept"),
        key=lambda row: abs(row[1]),
        reverse=True,
    )[:4]
    parts = [f"RAS_V3 selected {selected} with highest linear adequacy score {scores[selected]:.3f}."]
    if top_features:
        parts.append(
            "Largest active contributions: "
            + ", ".join(f"{feature}={value:+.3f}" for feature, value in top_features)
            + "."
        )
    runner_up = sorted(scores, key=scores.get, reverse=True)[1]
    parts.append(f"Runner-up was {runner_up} at {scores[runner_up]:.3f}.")
    return " ".join(parts)
