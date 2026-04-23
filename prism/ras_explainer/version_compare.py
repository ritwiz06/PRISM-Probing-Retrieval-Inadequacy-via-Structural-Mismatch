from __future__ import annotations

from pathlib import Path
from typing import Any

from prism.ras.compute_ras import route_query
from prism.ras.route_improvement import route_query_v2
from prism.ras_explainer.math_docs import sample_computed_ras_breakdown
from prism.ras_v3.explain import explanation_payload as ras_v3_explanation_payload
from prism.ras_v3.scoring import DEFAULT_MODEL_PATH as RAS_V3_MODEL_PATH
from prism.ras_v3.scoring import route_query_v3
from prism.ras_v4.model import RASV4Model
from prism.utils import read_json


def build_version_comparison() -> dict[str, object]:
    return {
        "production_router": "computed_ras",
        "versions": [
            {
                "name": "computed_ras",
                "status": "production",
                "model_type": "heuristic penalty table",
                "selection_rule": "argmin penalty",
                "uses_evidence": False,
                "learned": False,
                "interpretability": "direct feature penalties",
                "strength": "stable on curated/external/generalization/public benchmarks",
                "weakness": "route-boundary hard cases and top-k evidence rescue failures",
            },
            {
                "name": "computed_ras_v2",
                "status": "analysis-only",
                "model_type": "rule overlay on computed_ras",
                "selection_rule": "computed_ras plus narrow overrides",
                "uses_evidence": False,
                "learned": False,
                "interpretability": "explicit correction rules",
                "strength": "surfaces hard-case route heuristics",
                "weakness": "not strong enough to replace production computed_ras",
            },
            {
                "name": "ras_v3",
                "status": "analysis-only",
                "model_type": "multiclass sparse linear route model",
                "selection_rule": "argmax linear route adequacy score",
                "uses_evidence": False,
                "learned": True,
                "interpretability": "per-feature per-route contributions",
                "strength": "formalizes route adequacy",
                "weakness": "route-only improvements do not close answer-accuracy gap on adversarial hard cases",
            },
            {
                "name": "ras_v4",
                "status": "analysis-only",
                "model_type": "binary linear joint route/evidence adequacy model",
                "selection_rule": "argmax combined route + evidence adequacy score",
                "uses_evidence": True,
                "learned": True,
                "interpretability": "route contribution plus evidence contribution",
                "strength": "makes evidence adequacy explicit and publication-friendly",
                "weakness": "recorded results still keep it analysis-only; rescue overlay remains complementary",
            },
            {
                "name": "calibrated_rescue",
                "status": "research overlay",
                "model_type": "calibrated hard-case router plus top-k rescue",
                "selection_rule": "optional overlay, not a core RAS version",
                "uses_evidence": True,
                "learned": False,
                "interpretability": "failure-bucket and rescue metadata",
                "strength": "stronger adversarial answer accuracy in recorded artifacts",
                "weakness": "overlay behavior, not the production route selection mechanism",
            },
        ],
        "empirical_snapshot": _empirical_snapshot(),
        "promotion_decision": "computed_ras remains production; RAS_V3/RAS_V4/rescue remain research overlays.",
    }


def explain_query(query: str, *, source_type: str = "ui") -> dict[str, object]:
    computed = sample_computed_ras_breakdown(query)
    v2 = route_query_v2(query, source_type_hint=source_type)
    payload: dict[str, object] = {
        "query": query,
        "computed_ras": computed,
        "computed_ras_v2": {
            "selected_backend": v2.selected_backend,
            "original_backend": v2.original_backend,
            "margin": v2.margin,
            "signals": v2.signals,
            "rationale": v2.rationale,
            "ras_scores": v2.ras_scores,
        },
        "ras_v3": _safe_ras_v3(query, source_type),
        "ras_v4": _safe_ras_v4_summary(),
    }
    routes = _route_votes(payload)
    payload["route_votes"] = routes
    payload["ambiguity_flag"] = ambiguity_flag(payload)
    return payload


def ambiguity_flag(explanation: dict[str, object]) -> dict[str, object]:
    votes = explanation.get("route_votes", {})
    routes = [str(value) for value in votes.values() if value]
    disagreement = len(set(routes)) > 1
    computed = explanation.get("computed_ras", {})
    margin = float(computed.get("margin", 0.0)) if isinstance(computed, dict) else 0.0
    low_margin = margin < 0.25
    return {
        "status": "advisory_only",
        "is_ambiguous": disagreement or low_margin,
        "low_margin": low_margin,
        "version_disagreement": disagreement,
        "computed_ras_margin": margin,
        "message": _ambiguity_message(low_margin, disagreement),
    }


def _safe_ras_v3(query: str, source_type: str) -> dict[str, object]:
    if not Path(RAS_V3_MODEL_PATH).exists():
        return {"status": "unavailable", "reason": f"Missing model file: {RAS_V3_MODEL_PATH}"}
    try:
        return ras_v3_explanation_payload(route_query_v3(query, source_type=source_type))
    except Exception as exc:  # pragma: no cover - defensive UI/report guard
        return {"status": "unavailable", "reason": str(exc)}


def _safe_ras_v4_summary() -> dict[str, object]:
    model_path = Path("data/eval/ras_v4_model.json")
    if not model_path.exists():
        return {"status": "unavailable", "reason": f"Missing model file: {model_path}"}
    try:
        model = RASV4Model.load(model_path)
    except Exception as exc:  # pragma: no cover - defensive UI/report guard
        return {"status": "unavailable", "reason": str(exc)}
    return {
        "status": "available_for_evidence_aware_evaluation",
        "model_version": model.model_version,
        "route_weight_sum": model.route_weight_sum,
        "evidence_weight_sum": model.evidence_weight_sum,
        "note": "Per-query RAS_V4 requires candidate evidence for each backend; see RAS_V4 verifier artifacts.",
    }


def _route_votes(payload: dict[str, object]) -> dict[str, str]:
    votes: dict[str, str] = {}
    computed = payload.get("computed_ras", {})
    if isinstance(computed, dict):
        votes["computed_ras"] = str(computed.get("selected_backend", ""))
    v2 = payload.get("computed_ras_v2", {})
    if isinstance(v2, dict):
        votes["computed_ras_v2"] = str(v2.get("selected_backend", ""))
    v3 = payload.get("ras_v3", {})
    if isinstance(v3, dict) and "selected_backend" in v3:
        votes["ras_v3"] = str(v3.get("selected_backend", ""))
    return votes


def _ambiguity_message(low_margin: bool, disagreement: bool) -> str:
    if low_margin and disagreement:
        return "Low computed-RAS margin and RAS-version disagreement: treat route as ambiguous."
    if low_margin:
        return "Low computed-RAS margin: selected route is close to an alternative."
    if disagreement:
        return "RAS variants disagree: useful for research comparison, not production override."
    return "No ambiguity warning from margin or version disagreement."


def _empirical_snapshot() -> dict[str, object]:
    snapshot: dict[str, object] = {}
    for name, path in {
        "ras_v3": "data/eval/ras_v3_eval.json",
        "ras_v4": "data/eval/ras_v4_eval.json",
        "calibrated": "data/eval/calibrated_router.json",
    }.items():
        file_path = Path(path)
        if not file_path.exists():
            snapshot[name] = {"status": "missing", "path": path}
            continue
        try:
            data = read_json(file_path)
        except Exception:  # pragma: no cover - report guard
            snapshot[name] = {"status": "unreadable", "path": path}
            continue
        snapshot[name] = _extract_snapshot_metrics(data, name, path)
    return snapshot


def _extract_snapshot_metrics(data: dict[str, Any], name: str, path: str) -> dict[str, object]:
    output: dict[str, object] = {"path": path}
    if name in {"ras_v3", "ras_v4"}:
        output["status"] = data.get(f"{name}_status")
        systems = data.get("systems", {})
        adv = systems.get("adversarial_test", {}) if isinstance(systems, dict) else {}
        for system_name in ("computed_ras", name, "calibrated_rescue", "ras_v4_rescue"):
            if isinstance(adv, dict) and system_name in adv:
                output[system_name] = {
                    "route_accuracy": adv[system_name].get("route_accuracy"),
                    "answer_accuracy": adv[system_name].get("answer_accuracy"),
                }
    else:
        systems = data.get("systems", {})
        adv = systems.get("adversarial_test", {}) if isinstance(systems, dict) else {}
        for system_name in ("computed_ras_normal", "computed_ras_calibrated_topk_rescue"):
            if isinstance(adv, dict) and system_name in adv:
                output[system_name] = {
                    "route_accuracy": adv[system_name].get("route_accuracy"),
                    "answer_accuracy": adv[system_name].get("answer_accuracy"),
                }
    return output
