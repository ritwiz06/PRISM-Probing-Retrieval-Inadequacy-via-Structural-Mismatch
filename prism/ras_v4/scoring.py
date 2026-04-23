from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from prism.analysis.evaluation import BACKENDS
from prism.ras_v4.features import RASV4FeatureVector, extract_joint_features
from prism.ras_v4.model import RASV4Model
from prism.schemas import RetrievedItem

DEFAULT_MODEL_PATH = Path("data/eval/ras_v4_model.json")


@dataclass(frozen=True, slots=True)
class CandidateAdequacy:
    backend: str
    combined_score: float
    route_contribution: float
    evidence_contribution: float
    margin_from_best: float
    features: RASV4FeatureVector
    contributions: dict[str, float]
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class RASV4Decision:
    selected_backend: str
    candidate_scores: dict[str, CandidateAdequacy]
    margin: float
    rationale: str
    model_version: str


def route_query_v4(
    query: str,
    evidence_by_backend: dict[str, list[RetrievedItem]],
    *,
    model: RASV4Model | None = None,
    source_type: str = "",
    topk_rescue_opportunity: bool = False,
) -> RASV4Decision:
    active_model = model or RASV4Model.load(DEFAULT_MODEL_PATH)
    raw_candidates: dict[str, CandidateAdequacy] = {}
    scores: dict[str, float] = {}
    for backend in BACKENDS:
        features = extract_joint_features(
            query,
            backend,
            evidence_by_backend.get(backend, []),
            source_type=source_type,
            topk_rescue_opportunity=topk_rescue_opportunity,
        )
        score = active_model.score(features)
        groups = active_model.contribution_groups(features)
        contributions = active_model.contributions(features)
        scores[backend] = score
        raw_candidates[backend] = CandidateAdequacy(
            backend=backend,
            combined_score=score,
            route_contribution=groups["route_contribution"],
            evidence_contribution=groups["evidence_contribution"],
            margin_from_best=0.0,
            features=features,
            contributions=contributions,
            evidence_ids=[item.item_id for item in evidence_by_backend.get(backend, [])],
        )
    selected = max(BACKENDS, key=lambda backend: (scores[backend], -BACKENDS.index(backend)))
    best_score = scores[selected]
    candidates = {
        backend: CandidateAdequacy(
            backend=row.backend,
            combined_score=row.combined_score,
            route_contribution=row.route_contribution,
            evidence_contribution=row.evidence_contribution,
            margin_from_best=best_score - row.combined_score,
            features=row.features,
            contributions=row.contributions,
            evidence_ids=row.evidence_ids,
        )
        for backend, row in raw_candidates.items()
    }
    margin = _margin(scores)
    return RASV4Decision(
        selected_backend=selected,
        candidate_scores=candidates,
        margin=margin,
        rationale=_rationale(selected, candidates, margin),
        model_version=active_model.model_version,
    )


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted(scores.values(), reverse=True)
    if len(ordered) < 2:
        return 0.0
    return ordered[0] - ordered[1]


def _rationale(selected: str, candidates: dict[str, CandidateAdequacy], margin: float) -> str:
    row = candidates[selected]
    top_contrib = sorted(row.contributions.items(), key=lambda item: abs(float(item[1])), reverse=True)[:5]
    return (
        f"RAS_V4 selected {selected} with combined adequacy score {row.combined_score:.3f} "
        f"(route={row.route_contribution:+.3f}, evidence={row.evidence_contribution:+.3f}, margin={margin:.3f}). "
        "Top contributions: "
        + ", ".join(f"{name}={value:+.3f}" for name, value in top_contrib)
        + "."
    )
