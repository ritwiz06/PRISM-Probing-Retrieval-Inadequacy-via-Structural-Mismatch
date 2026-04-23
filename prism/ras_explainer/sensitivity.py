from __future__ import annotations

import csv
from dataclasses import replace
import os
from pathlib import Path
from typing import Any

Path("data/eval/.mplconfig").mkdir(parents=True, exist_ok=True)
Path("data/eval/.fontconfig").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", "data/eval/.mplconfig")
os.environ.setdefault("XDG_CACHE_HOME", "data/eval/.fontconfig")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from prism.adversarial.loaders import load_adversarial_benchmark
from prism.ras.compute_ras import route_query
from prism.ras.penalty_table import compute_penalties
from prism.ras.route_improvement import route_query_v2
from prism.ras_v3.scoring import DEFAULT_MODEL_PATH as RAS_V3_MODEL_PATH
from prism.ras_v3.scoring import route_query_v3
from prism.utils import read_json, write_json


def build_sensitivity_artifacts(output_dir: str | Path = "data/eval") -> dict[str, object]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    items = load_adversarial_benchmark()
    disagreement = _version_disagreement(items)
    ablation_rows = _computed_feature_ablation(items)
    margin_rows = _margin_rows(disagreement["items"])
    sensitivity = {
        "benchmark": "adversarial",
        "item_count": len(items),
        "production_router": "computed_ras",
        "advisory_feature": "route_ambiguity_flag",
        "route_ambiguity_definition": "low computed-RAS margin (<0.25) or disagreement among RAS variants",
        "margin_summary": _summarize_margins(margin_rows),
        "version_disagreement_summary": disagreement["summary"],
        "feature_ablation_summary": _summarize_ablation(ablation_rows),
        "artifacts": {
            "ras_sensitivity": str(target / "ras_sensitivity.json"),
            "ras_version_disagreement": str(target / "ras_version_disagreement.json"),
            "ras_feature_ablation": str(target / "ras_feature_ablation.csv"),
            "ras_margin_distribution": str(target / "ras_margin_distribution.png"),
            "ras_confusion_summary": str(target / "ras_confusion_summary.md"),
        },
    }
    write_json(target / "ras_sensitivity.json", sensitivity)
    write_json(target / "ras_version_disagreement.json", disagreement)
    _write_csv(target / "ras_feature_ablation.csv", ablation_rows)
    _plot_margins(target / "ras_margin_distribution.png", margin_rows)
    (target / "ras_confusion_summary.md").write_text(_confusion_markdown(disagreement, sensitivity), encoding="utf-8")
    return sensitivity


def _version_disagreement(items: list[object]) -> dict[str, object]:
    ras_v4_routes = _ras_v4_case_routes()
    rows: list[dict[str, object]] = []
    for item in items:
        query = str(item.query)
        computed = route_query(query)
        v2 = route_query_v2(query, source_type_hint="adversarial")
        v3_route = _safe_v3_route(query)
        v4_route = ras_v4_routes.get(query, "")
        routes = {
            "computed_ras": computed.selected_backend,
            "computed_ras_v2": v2.selected_backend,
            "ras_v3": v3_route,
            "ras_v4": v4_route,
        }
        active_routes = {name: route for name, route in routes.items() if route}
        route_values = set(active_routes.values())
        margin = _margin(computed.ras_scores)
        rows.append(
            {
                "id": item.id,
                "split": item.split,
                "query": query,
                "gold_route": item.intended_route_family,
                "ambiguity_tags": item.ambiguity_tags,
                "computed_ras_margin": margin,
                "low_margin": margin < 0.25,
                "routes": active_routes,
                "version_disagreement": len(route_values) > 1,
                "advisory_ambiguity_flag": margin < 0.25 or len(route_values) > 1,
            }
        )
    summary = {
        "total": len(rows),
        "version_disagreement_count": sum(int(row["version_disagreement"]) for row in rows),
        "low_margin_count": sum(int(row["low_margin"]) for row in rows),
        "advisory_ambiguity_count": sum(int(row["advisory_ambiguity_flag"]) for row in rows),
        "route_confusion_computed_ras": _confusion(rows, "computed_ras"),
        "route_confusion_ras_v3": _confusion(rows, "ras_v3"),
        "route_confusion_ras_v4": _confusion(rows, "ras_v4"),
    }
    return {"summary": summary, "items": rows}


def _computed_feature_ablation(items: list[object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        decision = route_query(str(item.query))
        features = decision.features
        baseline = decision.selected_backend
        for feature_name in ("lexical", "semantic", "deductive", "relational"):
            if not getattr(features, feature_name):
                continue
            ablated = replace(features, **{feature_name: False})
            scores = compute_penalties(ablated)
            selected = min(scores, key=scores.get)
            rows.append(
                {
                    "item_id": item.id,
                    "split": item.split,
                    "gold_route": item.intended_route_family,
                    "feature_removed": feature_name,
                    "baseline_route": baseline,
                    "ablated_route": selected,
                    "route_changed": selected != baseline,
                    "baseline_margin": _margin(decision.ras_scores),
                    "ablated_margin": _margin(scores),
                }
            )
    return rows


def _margin_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "id": row["id"],
            "split": row["split"],
            "computed_ras_margin": float(row["computed_ras_margin"]),
            "low_margin": bool(row["low_margin"]),
            "version_disagreement": bool(row["version_disagreement"]),
            "advisory_ambiguity_flag": bool(row["advisory_ambiguity_flag"]),
        }
        for row in items
    ]


def _safe_v3_route(query: str) -> str:
    if not Path(RAS_V3_MODEL_PATH).exists():
        return ""


def _ras_v4_case_routes() -> dict[str, str]:
    path = Path("data/eval/ras_v4_explanations.json")
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception:  # pragma: no cover - artifact guard
        return {}
    routes: dict[str, str] = {}
    for row in payload.get("cases", []) if isinstance(payload, dict) else []:
        if isinstance(row, dict) and row.get("query") and row.get("selected_backend"):
            routes[str(row["query"])] = str(row["selected_backend"])
    return routes
    try:
        return route_query_v3(query, source_type="adversarial").selected_backend
    except Exception:  # pragma: no cover - analysis artifact guard
        return ""


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted(float(value) for value in scores.values())
    if len(ordered) < 2:
        return 0.0
    return ordered[1] - ordered[0]


def _confusion(rows: list[dict[str, object]], route_key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        routes = row.get("routes", {})
        if not isinstance(routes, dict) or not routes.get(route_key):
            continue
        key = f"{row['gold_route']}->{routes[route_key]}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _summarize_margins(rows: list[dict[str, object]]) -> dict[str, object]:
    margins = [float(row["computed_ras_margin"]) for row in rows]
    if not margins:
        return {"count": 0}
    return {
        "count": len(margins),
        "min": min(margins),
        "max": max(margins),
        "mean": sum(margins) / len(margins),
        "low_margin_count": sum(int(row["low_margin"]) for row in rows),
    }


def _summarize_ablation(rows: list[dict[str, object]]) -> dict[str, object]:
    by_feature: dict[str, dict[str, int]] = {}
    for row in rows:
        feature = str(row["feature_removed"])
        bucket = by_feature.setdefault(feature, {"tested": 0, "route_changed": 0})
        bucket["tested"] += 1
        bucket["route_changed"] += int(bool(row["route_changed"]))
    return by_feature


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _plot_margins(path: Path, rows: list[dict[str, object]]) -> None:
    margins = [float(row["computed_ras_margin"]) for row in rows]
    plt.figure(figsize=(7.5, 4.2))
    plt.hist(margins, bins=8, color="#0F766E", edgecolor="white")
    plt.axvline(0.25, color="#BE123C", linestyle="--", label="low-margin threshold")
    plt.title("Computed RAS Margin Distribution on Adversarial Benchmark")
    plt.xlabel("Margin between best and runner-up penalty")
    plt.ylabel("Query count")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def _confusion_markdown(disagreement: dict[str, Any], sensitivity: dict[str, Any]) -> str:
    summary = disagreement["summary"]
    lines = [
        "# RAS Confusion and Ambiguity Summary",
        "",
        "This artifact is analysis-only. It does not change the production router.",
        "",
        f"Total adversarial items: `{summary['total']}`.",
        f"Version disagreement count: `{summary['version_disagreement_count']}`.",
        f"Low computed-RAS margin count: `{summary['low_margin_count']}`.",
        f"Advisory ambiguity flag count: `{summary['advisory_ambiguity_count']}`.",
        "",
        "## Computed RAS Confusion",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in summary["route_confusion_computed_ras"].items())
    lines.extend(["", "## Feature Ablation Summary", ""])
    for feature, row in sensitivity["feature_ablation_summary"].items():
        lines.append(f"- `{feature}`: {row['route_changed']}/{row['tested']} ablations changed the selected route")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The ambiguity flag is advisory only. It indicates either a small production RAS margin or disagreement between analysis variants.",
            "It should be used for explanation, caution, and demo interpretation, not automatic production override.",
        ]
    )
    return "\n".join(lines) + "\n"
