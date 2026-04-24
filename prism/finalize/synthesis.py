from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean
from typing import Any

from prism.utils import read_json, write_json


def build_synthesis_layer(output_dir: str | Path, *, known_results: dict[str, object]) -> dict[str, object]:
    output = Path(output_dir)
    charts_dir = output / "charts"
    figures_dir = output / "figures"
    charts_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    plt = _configure_matplotlib(output)

    benchmark_rows = _benchmark_overview_rows()
    adversarial_rows = _adversarial_router_rows()
    overlay_rows = _production_vs_research_rows()
    human_dimension_rows = _human_dimension_rows()
    pair_rows = _comparative_pair_rows()
    backend_usage_rows = _backend_usage_rows()

    chart_paths = {
        "benchmark_overview": str(charts_dir / "benchmark_overview.png"),
        "adversarial_router_comparison": str(charts_dir / "adversarial_router_comparison.png"),
        "production_vs_research_overlay": str(charts_dir / "production_vs_research_overlay.png"),
        "human_eval_overview": str(charts_dir / "human_eval_overview.png"),
        "backend_usage_overview": str(charts_dir / "backend_usage_overview.png"),
        "comparative_preferences_overview": str(charts_dir / "comparative_preferences_overview.png"),
    }
    _plot_benchmark_overview(plt, benchmark_rows, Path(chart_paths["benchmark_overview"]))
    _plot_adversarial_router_comparison(plt, adversarial_rows, Path(chart_paths["adversarial_router_comparison"]))
    _plot_overlay_comparison(plt, overlay_rows, Path(chart_paths["production_vs_research_overlay"]))
    _plot_human_eval_overview(plt, human_dimension_rows, Path(chart_paths["human_eval_overview"]))
    _plot_backend_usage(plt, backend_usage_rows, Path(chart_paths["backend_usage_overview"]))
    _plot_comparative_preferences(plt, pair_rows, Path(chart_paths["comparative_preferences_overview"]))

    figure_paths = {
        "architecture_diagram": str(figures_dir / "architecture_diagram.png"),
        "why_routing_matters": str(figures_dir / "why_routing_matters.png"),
        "ras_family_overview": str(figures_dir / "ras_family_overview.png"),
        "production_vs_research_map": str(figures_dir / "production_vs_research_map.png"),
        "route_evidence_adequacy": str(figures_dir / "route_evidence_adequacy.png"),
        "evaluation_stack": str(figures_dir / "evaluation_stack.png"),
    }
    _draw_architecture_diagram(plt, Path(figure_paths["architecture_diagram"]))
    _draw_why_routing_matters(plt, Path(figure_paths["why_routing_matters"]))
    _draw_ras_family_overview(plt, Path(figure_paths["ras_family_overview"]))
    _draw_production_vs_research_map(plt, Path(figure_paths["production_vs_research_map"]))
    _draw_route_evidence_adequacy(plt, Path(figure_paths["route_evidence_adequacy"]))
    _draw_evaluation_stack(plt, Path(figure_paths["evaluation_stack"]))

    document_paths = _write_summary_documents(
        output,
        known_results=known_results,
        benchmark_rows=benchmark_rows,
        adversarial_rows=adversarial_rows,
        overlay_rows=overlay_rows,
        human_dimension_rows=human_dimension_rows,
        pair_rows=pair_rows,
    )

    summary = {
        "production_router": "computed_ras",
        "research_overlays": ["calibrated_rescue", "classifier_router", "ras_v3", "ras_v4", "optional_llm"],
        "thesis": "PRISM routes queries to the evidence representation that is structurally adequate for the question.",
        "benchmark_overview": benchmark_rows,
        "adversarial_router_comparison": adversarial_rows,
        "production_vs_research_overlay": overlay_rows,
        "human_eval": {
            "dimension_means": human_dimension_rows,
            "pair_preferences": pair_rows,
            "evaluator_count": _read_json("data/human_eval/human_eval_summary.json").get("evaluator_count", "n/a"),
            "annotation_count": _read_json("data/human_eval/human_eval_summary.json").get("annotation_count", "n/a"),
        },
        "open_corpus": _read_json("data/eval/open_corpus_smoke.json").get("smoke", {}),
        "key_findings": [
            "computed_ras remains the production router because it is stable across curated, external, generalization, and public-document layers.",
            "Adversarial hard cases remain the main weakness; calibrated rescue is still stronger than route-only RAS variants on adversarial answer accuracy.",
            "RAS_V3 and RAS_V4 improve the research story and interpretability, but they remain analysis-only.",
            "Human evaluation supports evidence/trace usefulness while preserving ties and adjudication cases.",
            "Open-corpus mode is functional and bounded; it is not arbitrary web-scale search.",
        ],
        "caveats": [
            "production router = computed_ras",
            "calibrated_rescue remains a complementary research overlay",
            "ras_v3 and ras_v4 remain analysis-only",
            "PRISM is bounded source-pack/local/open-corpus QA, not web-scale search",
        ],
        "charts": chart_paths,
        "figures": figure_paths,
        "documents": document_paths,
    }
    write_json(output / "synthesis_summary.json", summary)
    return {
        "summary_path": str(output / "synthesis_summary.json"),
        "chart_dir": str(charts_dir),
        "figure_dir": str(figures_dir),
        "charts": chart_paths,
        "figures": figure_paths,
        "documents": document_paths,
    }


def _configure_matplotlib(output_dir: Path):
    cache_dir = output_dir / ".mplconfig"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "font.size": 10,
            "axes.edgecolor": "#CBD5E1",
            "axes.facecolor": "#FFFFFF",
            "figure.facecolor": "#FFFFFF",
            "savefig.facecolor": "#FFFFFF",
            "grid.color": "#E2E8F0",
            "grid.alpha": 0.7,
        }
    )
    return plt


def _read_json(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        payload = read_json(file_path)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _benchmark_overview_rows() -> list[dict[str, object]]:
    curated = _read_json("data/eval/end_to_end_verification.json")
    external = _read_json("data/eval/external_generalization.json")
    generalization = _read_json("data/eval/generalization_v2.json")
    public_raw = _read_json("data/eval/public_corpus_eval.json")
    public_graph = _read_json("data/eval/public_graph_eval.json")
    adversarial = _read_json("data/eval/adversarial_eval.json")

    curated_total = int(curated.get("total", 0) or 0)
    curated_answer = (curated.get("answer_match_total", 0) or 0) / curated_total if curated_total else 0.0
    return [
        {"benchmark": "Curated", "route_accuracy": float(curated.get("route_accuracy", 0.0) or 0.0), "answer_accuracy": curated_answer},
        {
            "benchmark": "External Mini",
            "route_accuracy": _system_metric(external, ("systems", "computed_ras", "route_accuracy")),
            "answer_accuracy": _system_metric(external, ("systems", "computed_ras", "answer_accuracy")),
        },
        {
            "benchmark": "GenV2 Clean",
            "route_accuracy": _system_metric(generalization, ("systems", "clean", "test", "computed_ras", "route_accuracy")),
            "answer_accuracy": _system_metric(generalization, ("systems", "clean", "test", "computed_ras", "answer_accuracy")),
        },
        {
            "benchmark": "GenV2 Noisy",
            "route_accuracy": _system_metric(generalization, ("systems", "noisy", "test", "computed_ras", "route_accuracy")),
            "answer_accuracy": _system_metric(generalization, ("systems", "noisy", "test", "computed_ras", "answer_accuracy")),
        },
        {
            "benchmark": "Public Raw",
            "route_accuracy": _system_metric(public_raw, ("systems", "test", "computed_ras", "route_accuracy")),
            "answer_accuracy": _system_metric(public_raw, ("systems", "test", "computed_ras", "answer_accuracy")),
        },
        {
            "benchmark": "Public Graph",
            "route_accuracy": _system_metric(public_graph, ("runs", "public_graph", "test", "computed_ras", "route_accuracy")),
            "answer_accuracy": _system_metric(public_graph, ("runs", "public_graph", "test", "computed_ras", "answer_accuracy")),
        },
        {
            "benchmark": "Adversarial Test",
            "route_accuracy": _system_metric(adversarial, ("systems", "splits", "test", "computed_ras", "route_accuracy")),
            "answer_accuracy": _system_metric(adversarial, ("systems", "splits", "test", "computed_ras", "answer_accuracy")),
        },
    ]


def _adversarial_router_rows() -> list[dict[str, object]]:
    adversarial = _read_json("data/eval/adversarial_eval.json")
    calibration = _read_json("data/eval/calibrated_router.json")
    ras_v3 = _read_json("data/eval/ras_v3_eval.json")
    ras_v4 = _read_json("data/eval/ras_v4_eval.json")

    return [
        {
            "system": "computed_ras",
            "answer_accuracy": _system_metric(adversarial, ("systems", "splits", "test", "computed_ras", "answer_accuracy")),
            "route_accuracy": _system_metric(adversarial, ("systems", "splits", "test", "computed_ras", "route_accuracy")),
            "status": "production",
        },
        {
            "system": "calibrated_rescue",
            "answer_accuracy": _system_metric(calibration, ("systems", "adversarial_test", "computed_ras_calibrated_topk_rescue", "answer_accuracy")),
            "route_accuracy": _system_metric(calibration, ("systems", "adversarial_test", "computed_ras_calibrated_topk_rescue", "route_accuracy")),
            "status": "research overlay",
        },
        {
            "system": "classifier_router",
            "answer_accuracy": _system_metric(adversarial, ("systems", "splits", "test", "classifier_router", "answer_accuracy")),
            "route_accuracy": _system_metric(adversarial, ("systems", "splits", "test", "classifier_router", "route_accuracy")),
            "status": "research baseline",
        },
        {
            "system": "ras_v3",
            "answer_accuracy": _system_metric(ras_v3, ("systems", "adversarial_test", "ras_v3", "answer_accuracy")),
            "route_accuracy": _system_metric(ras_v3, ("systems", "adversarial_test", "ras_v3", "route_accuracy")),
            "status": "analysis-only",
        },
        {
            "system": "ras_v4",
            "answer_accuracy": _system_metric(ras_v4, ("systems", "adversarial_test", "ras_v4", "answer_accuracy")),
            "route_accuracy": _system_metric(ras_v4, ("systems", "adversarial_test", "ras_v4", "route_accuracy")),
            "status": "analysis-only",
        },
    ]


def _production_vs_research_rows() -> list[dict[str, object]]:
    calibration = _read_json("data/eval/calibrated_router.json")
    ras_v3 = _read_json("data/eval/ras_v3_eval.json")
    ras_v4 = _read_json("data/eval/ras_v4_eval.json")

    def stable_avg(payload: dict[str, Any], system_name: str) -> float:
        datasets = ["curated", "external_mini", "generalization_v2_test", "public_raw_test"]
        values = [
            _system_metric(payload, ("systems", dataset, system_name, "answer_accuracy"))
            for dataset in datasets
        ]
        present = [value for value in values if value >= 0]
        return mean(present) if present else 0.0

    return [
        {
            "system": "computed_ras",
            "stable_average": stable_avg(calibration, "computed_ras"),
            "adversarial_test": _system_metric(calibration, ("systems", "adversarial_test", "computed_ras", "answer_accuracy")),
            "status": "production",
        },
        {
            "system": "calibrated_rescue",
            "stable_average": stable_avg(calibration, "computed_ras_calibrated_topk_rescue"),
            "adversarial_test": _system_metric(calibration, ("systems", "adversarial_test", "computed_ras_calibrated_topk_rescue", "answer_accuracy")),
            "status": "research overlay",
        },
        {
            "system": "classifier_router",
            "stable_average": stable_avg(calibration, "classifier_router"),
            "adversarial_test": _system_metric(calibration, ("systems", "adversarial_test", "classifier_router", "answer_accuracy")),
            "status": "research baseline",
        },
        {
            "system": "ras_v3",
            "stable_average": mean(
                [
                    _system_metric(ras_v3, ("systems", "curated", "ras_v3", "answer_accuracy")),
                    _system_metric(ras_v3, ("systems", "external_mini", "ras_v3", "answer_accuracy")),
                    _system_metric(ras_v3, ("systems", "generalization_v2_test", "ras_v3", "answer_accuracy")),
                    _system_metric(ras_v3, ("systems", "public_raw_test", "ras_v3", "answer_accuracy")),
                ]
            ),
            "adversarial_test": _system_metric(ras_v3, ("systems", "adversarial_test", "ras_v3", "answer_accuracy")),
            "status": "analysis-only",
        },
        {
            "system": "ras_v4",
            "stable_average": mean(
                [
                    _system_metric(ras_v4, ("systems", "curated", "ras_v4", "answer_accuracy")),
                    _system_metric(ras_v4, ("systems", "external_mini", "ras_v4", "answer_accuracy")),
                    _system_metric(ras_v4, ("systems", "generalization_v2_test", "ras_v4", "answer_accuracy")),
                    _system_metric(ras_v4, ("systems", "public_raw_test", "ras_v4", "answer_accuracy")),
                ]
            ),
            "adversarial_test": _system_metric(ras_v4, ("systems", "adversarial_test", "ras_v4", "answer_accuracy")),
            "status": "analysis-only",
        },
    ]


def _human_dimension_rows() -> list[dict[str, object]]:
    human = _read_json("data/human_eval/human_eval_summary.json")
    means = human.get("dimension_means", {})
    if not isinstance(means, dict):
        return []
    return [{"dimension": key.replace("_", " "), "mean_score": float(value)} for key, value in means.items()]


def _comparative_pair_rows() -> list[dict[str, object]]:
    comparative = _read_json("data/human_eval/comparative_summary.json")
    rows = []
    pair_results = comparative.get("system_pair_results", {})
    if not isinstance(pair_results, dict):
        return rows
    for pair, payload in pair_results.items():
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "pair": pair,
                "a_win_rate": float(payload.get("a_win_rate", 0.0) or 0.0),
                "b_win_rate": float(payload.get("b_win_rate", 0.0) or 0.0),
                "tie_rate": float(payload.get("tie_rate", 0.0) or 0.0),
            }
        )
    return rows


def _backend_usage_rows() -> list[dict[str, object]]:
    smoke = _read_json("data/eval/open_corpus_smoke.json")
    route_dist = smoke.get("smoke", {}).get("route_distribution", {}) if isinstance(smoke.get("smoke"), dict) else {}
    if not isinstance(route_dist, dict):
        return []
    return [{"backend": key.upper(), "count": int(value)} for key, value in route_dist.items()]


def _system_metric(payload: dict[str, Any], keys: tuple[str, ...]) -> float:
    current: Any = payload
    try:
        for key in keys:
            current = current[key]
        return float(current)
    except (KeyError, TypeError, ValueError):
        return 0.0


def _save_plot(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    import matplotlib.pyplot as _plt

    _plt.close(fig)


def _plot_benchmark_overview(plt, rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["benchmark"]) for row in rows]
    answer = [float(row["answer_accuracy"]) for row in rows]
    route = [float(row["route_accuracy"]) for row in rows]
    x = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.bar([i - 0.18 for i in x], answer, width=0.36, label="Answer accuracy", color="#0F766E")
    ax.bar([i + 0.18 for i in x], route, width=0.36, label="Route accuracy", color="#2563EB")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title("PRISM Benchmark Overview")
    ax.grid(axis="y")
    ax.legend(frameon=False)
    _save_plot(fig, path)


def _plot_adversarial_router_comparison(plt, rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["system"]) for row in rows]
    answer = [float(row["answer_accuracy"]) for row in rows]
    route = [float(row["route_accuracy"]) for row in rows]
    colors = ["#0F766E", "#B45309", "#4338CA", "#0369A1", "#BE123C"]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(labels, answer, color=colors, label="Answer accuracy")
    ax.plot(labels, route, color="#0F172A", marker="o", linewidth=2.0, label="Route accuracy")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title("Adversarial Test: Router Comparison")
    ax.grid(axis="y")
    ax.legend(frameon=False)
    _save_plot(fig, path)


def _plot_overlay_comparison(plt, rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["system"]) for row in rows]
    stable = [float(row["stable_average"]) for row in rows]
    adversarial = [float(row["adversarial_test"]) for row in rows]
    x = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar([i - 0.18 for i in x], stable, width=0.36, label="Stable benchmark average", color="#0F766E")
    ax.bar([i + 0.18 for i in x], adversarial, width=0.36, label="Adversarial test", color="#BE123C")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Answer accuracy")
    ax.set_title("Production vs Research Overlay Comparison")
    ax.grid(axis="y")
    ax.legend(frameon=False)
    _save_plot(fig, path)


def _plot_human_eval_overview(plt, rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["dimension"]) for row in rows]
    values = [float(row["mean_score"]) for row in rows]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(labels, values, color="#2563EB")
    ax.set_ylim(0.0, 3.2)
    ax.set_ylabel("Mean score")
    ax.set_title("Human Evaluation Overview")
    ax.grid(axis="y")
    ax.tick_params(axis="x", rotation=25)
    _save_plot(fig, path)


def _plot_backend_usage(plt, rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["backend"]) for row in rows]
    values = [int(row["count"]) for row in rows]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(labels, values, color=["#B45309", "#2563EB", "#047857", "#7C3AED"][: len(labels)])
    ax.set_ylabel("Count")
    ax.set_title("Open-Corpus Backend Usage Overview")
    ax.grid(axis="y")
    _save_plot(fig, path)


def _plot_comparative_preferences(plt, rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["pair"]) for row in rows]
    a_values = [float(row["a_win_rate"]) for row in rows]
    tie_values = [float(row["tie_rate"]) for row in rows]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(labels, a_values, color="#0F766E", label="A win rate")
    ax.bar(labels, tie_values, bottom=a_values, color="#CBD5E1", label="Tie rate")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_title("Comparative Human Preferences")
    ax.grid(axis="y")
    ax.tick_params(axis="x", rotation=20)
    ax.legend(frameon=False)
    _save_plot(fig, path)


def _draw_architecture_diagram(plt, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 3.6))
    ax.axis("off")
    xs = [0.05, 0.24, 0.44, 0.66, 0.86]
    labels = ["Query", "Feature Parser", "computed_ras", "Retriever", "Answer + Trace"]
    colors = ["#E0F2FE", "#DBEAFE", "#CCFBF1", "#F5F3FF", "#ECFCCB"]
    for x, label, color in zip(xs, labels, colors):
        ax.text(x, 0.55, label, ha="center", va="center", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.55", fc=color, ec="#94A3B8"))
    for start, end in zip(xs[:-1], xs[1:]):
        ax.annotate("", xy=(end - 0.065, 0.55), xytext=(start + 0.065, 0.55), arrowprops=dict(arrowstyle="->", lw=2.2, color="#475569"))
    ax.text(0.44, 0.2, "Research overlays: calibrated_rescue, classifier_router, RAS_V3, RAS_V4, optional LLM", ha="center", va="center", fontsize=10, color="#475569")
    ax.set_title("PRISM Architecture")
    _save_plot(fig, path)


def _draw_why_routing_matters(plt, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.0))
    ax.axis("off")
    rows = [
        ("Exact identifiers", "BM25", "#FEF3C7"),
        ("Conceptual paraphrases", "Dense", "#DBEAFE"),
        ("Deductive claims", "KG", "#D1FAE5"),
        ("Bridge/path queries", "Hybrid", "#EDE9FE"),
    ]
    y_positions = [0.82, 0.62, 0.42, 0.22]
    for (left, right, color), y in zip(rows, y_positions):
        ax.text(0.18, y, left, ha="center", va="center", fontsize=12, bbox=dict(boxstyle="round,pad=0.5", fc="#FFFFFF", ec="#CBD5E1"))
        ax.annotate("", xy=(0.58, y), xytext=(0.30, y), arrowprops=dict(arrowstyle="->", lw=2.0, color="#64748B"))
        ax.text(0.75, y, right, ha="center", va="center", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.5", fc=color, ec="#94A3B8"))
    ax.set_title("Why Routing Matters")
    _save_plot(fig, path)


def _draw_ras_family_overview(plt, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 3.8))
    ax.axis("off")
    nodes = [
        ("computed_ras", 0.12, "#CCFBF1"),
        ("computed_ras_v2", 0.34, "#FEF3C7"),
        ("ras_v3", 0.56, "#E0F2FE"),
        ("ras_v4", 0.78, "#FFE4E6"),
    ]
    for idx, (label, x, color) in enumerate(nodes):
        ax.text(x, 0.58, label, ha="center", va="center", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.55", fc=color, ec="#94A3B8"))
        if idx < len(nodes) - 1:
            ax.annotate("", xy=(nodes[idx + 1][1] - 0.08, 0.58), xytext=(x + 0.08, 0.58), arrowprops=dict(arrowstyle="->", lw=2.2, color="#475569"))
    ax.text(0.12, 0.28, "production", ha="center", color="#0F766E")
    ax.text(0.56, 0.28, "route adequacy model", ha="center", color="#0369A1")
    ax.text(0.78, 0.28, "joint route + evidence adequacy", ha="center", color="#BE123C")
    ax.set_title("RAS Family Overview")
    _save_plot(fig, path)


def _draw_production_vs_research_map(plt, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.8, 4.0))
    ax.axis("off")
    ax.text(0.22, 0.74, "Production", ha="center", fontsize=14, fontweight="bold", color="#0F766E")
    ax.text(0.22, 0.48, "computed_ras", ha="center", va="center", fontsize=12, bbox=dict(boxstyle="round,pad=0.55", fc="#CCFBF1", ec="#0F766E"))
    ax.text(0.72, 0.74, "Research overlays", ha="center", fontsize=14, fontweight="bold", color="#7C2D12")
    research = ["calibrated_rescue", "classifier_router", "ras_v3", "ras_v4", "optional_llm"]
    for idx, item in enumerate(research):
        ax.text(0.72, 0.58 - idx * 0.12, item, ha="center", va="center", fontsize=11, bbox=dict(boxstyle="round,pad=0.45", fc="#FFFFFF", ec="#CBD5E1"))
    ax.text(0.72, 0.08, "visible for comparison, not silently promoted", ha="center", color="#64748B")
    ax.set_title("Production vs Research Overlay Map")
    _save_plot(fig, path)


def _draw_route_evidence_adequacy(plt, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    ax.axis("off")
    ax.text(0.18, 0.56, "Route adequacy", ha="center", va="center", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.55", fc="#E0F2FE", ec="#94A3B8"))
    ax.text(0.50, 0.56, "Evidence adequacy", ha="center", va="center", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.55", fc="#FFE4E6", ec="#94A3B8"))
    ax.text(0.82, 0.56, "Expected answerability", ha="center", va="center", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.55", fc="#ECFCCB", ec="#94A3B8"))
    ax.annotate("", xy=(0.40, 0.56), xytext=(0.27, 0.56), arrowprops=dict(arrowstyle="->", lw=2.2, color="#475569"))
    ax.annotate("", xy=(0.72, 0.56), xytext=(0.59, 0.56), arrowprops=dict(arrowstyle="->", lw=2.2, color="#475569"))
    ax.text(0.50, 0.24, "RAS_V4 keeps this decomposition explicit.", ha="center", color="#64748B")
    ax.set_title("Route + Evidence Adequacy")
    _save_plot(fig, path)


def _draw_evaluation_stack(plt, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.8, 5.0))
    ax.axis("off")
    layers = [
        "Curated benchmark",
        "External mini-benchmark",
        "Generalization_v2 clean/noisy",
        "Structure shift",
        "Public raw documents",
        "Public graph grounding",
        "Adversarial hard cases",
        "Calibration / rescue",
        "Human evaluation",
        "Open-corpus smoke",
    ]
    for idx, label in enumerate(layers):
        y = 0.9 - idx * 0.08
        ax.text(0.5, y, label, ha="center", va="center", fontsize=11, bbox=dict(boxstyle="round,pad=0.42", fc="#FFFFFF", ec="#CBD5E1"))
    ax.set_title("PRISM Evaluation Stack")
    _save_plot(fig, path)


def _write_summary_documents(
    output: Path,
    *,
    known_results: dict[str, object],
    benchmark_rows: list[dict[str, object]],
    adversarial_rows: list[dict[str, object]],
    overlay_rows: list[dict[str, object]],
    human_dimension_rows: list[dict[str, object]],
    pair_rows: list[dict[str, object]],
) -> dict[str, str]:
    paths = {
        "final_speaker_script": str(output / "final_speaker_script.md"),
        "one_minute_pitch": str(output / "one_minute_pitch.md"),
        "three_minute_pitch": str(output / "three_minute_pitch.md"),
        "qa_cheat_sheet": str(output / "qa_cheat_sheet.md"),
        "final_wrapup_report": str(output / "final_wrapup_report.md"),
        "submission_checklist": str(output / "submission_checklist.md"),
        "demo_day_checklist": str(output / "demo_day_checklist.md"),
        "final_artifact_index": str(output / "final_artifact_index.md"),
        "executive_summary": str(output / "executive_summary.md"),
    }
    (output / "executive_summary.md").write_text(_executive_summary(known_results), encoding="utf-8")
    (output / "final_speaker_script.md").write_text(_final_speaker_script(benchmark_rows, adversarial_rows), encoding="utf-8")
    (output / "one_minute_pitch.md").write_text(_one_minute_pitch(), encoding="utf-8")
    (output / "three_minute_pitch.md").write_text(_three_minute_pitch(), encoding="utf-8")
    (output / "qa_cheat_sheet.md").write_text(_qa_cheat_sheet(), encoding="utf-8")
    (output / "final_wrapup_report.md").write_text(
        _final_wrapup_report(
            known_results=known_results,
            benchmark_rows=benchmark_rows,
            adversarial_rows=adversarial_rows,
            overlay_rows=overlay_rows,
            human_dimension_rows=human_dimension_rows,
            pair_rows=pair_rows,
        ),
        encoding="utf-8",
    )
    (output / "submission_checklist.md").write_text(_submission_checklist(), encoding="utf-8")
    (output / "demo_day_checklist.md").write_text(_demo_day_checklist(), encoding="utf-8")
    (output / "final_artifact_index.md").write_text(_final_artifact_index(), encoding="utf-8")
    return paths


def _executive_summary(results: dict[str, object]) -> str:
    return f"""# Executive Summary

PRISM is a representation-aware retrieval system that routes queries to BM25, Dense, KG, or Hybrid evidence according to structural adequacy.

- Production router: `computed_ras`
- Research overlays: `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, optional LLM
- Bounded scope: benchmark corpora, source packs, local folders, and URL-list runtime corpora

## Key Results

- Curated benchmark: `80/80`
- External mini-benchmark: `1.000` answer accuracy
- Generalization v2 noisy test: `0.975` answer accuracy
- Public raw test: `1.000` answer accuracy
- Adversarial test: computed RAS `0.917`; calibrated rescue `0.958`

## Final Position

PRISM is release-ready and demo-ready. The production decision stays conservative: `computed_ras` remains the production router, while rescue and learned RAS variants remain explicitly labeled research overlays.

```json
{json.dumps(results, indent=2)}
```
"""


def _final_speaker_script(benchmark_rows: list[dict[str, object]], adversarial_rows: list[dict[str, object]]) -> str:
    return f"""# Final Speaker Script

## Opening

PRISM asks a simple question: if different questions require different evidence structures, why force every query through the same retriever?

## Core Story

1. PRISM extracts route-relevant signals from the query.
2. The production router, `computed_ras`, selects BM25, Dense, KG, or Hybrid.
3. Evidence stays visible and cited.
4. Research overlays remain visible, but the production decision stays explicit.

## Results To Show

- Benchmark overview: {json.dumps(benchmark_rows, indent=2)}
- Adversarial router comparison: {json.dumps(adversarial_rows, indent=2)}

## Closing

Route adequacy matters, but route-only adequacy is not enough on hard cases. That is why calibrated rescue remains part of the research story even though `computed_ras` remains the production router.
"""


def _one_minute_pitch() -> str:
    return """# One Minute Pitch

PRISM is a representation-aware retrieval system. Instead of sending every query to the same retriever, it asks which evidence structure is most adequate for the question: lexical text, dense semantics, graph structure, or a hybrid path. That routing decision is made by `computed_ras`, which remains the production router because it is deterministic and stable across curated, held-out, public-document, and open-corpus evaluations.

The key research result is that route adequacy helps, but hard adversarial cases still require better evidence use. That is why calibrated rescue remains stronger than route-only learned variants on adversarial answer accuracy. The project is strong enough for demo and paper drafting, while still being honest about what remains unresolved.
"""


def _three_minute_pitch() -> str:
    return """# Three Minute Pitch

PRISM addresses structural retrieval mismatch. Exact identifiers, conceptual paraphrases, deductive claims, and bridge/path questions do not all want the same representation. PRISM makes that explicit by routing to BM25, Dense, KG, or Hybrid evidence.

The production path uses `computed_ras`, a transparent deterministic router. Research overlays include calibrated rescue, classifier routing, RAS_V3, and RAS_V4. RAS_V3 formalizes route adequacy as an interpretable feature model, and RAS_V4 extends that to joint route-and-evidence adequacy.

Empirically, PRISM is very strong on curated, external, held-out, public raw, public graph, and open-corpus smoke settings. The main weakness remains hard adversarial route-boundary cases. On those cases, calibrated rescue still beats route-only learned RAS variants on answer accuracy. That is an honest result, and it changes the scientific story in a useful way: route adequacy is important, but answer support depends on evidence adequacy as well.

The final system is ready for demo, submission, and handoff. The repo now includes a polished UI, a release package, human-eval analysis, and a bounded open-corpus workspace. The production decision remains explicit and conservative: `computed_ras` stays production, and the overlays stay overlays.
"""


def _qa_cheat_sheet() -> str:
    return """# Q&A Cheat Sheet

## What is PRISM?
- A representation-aware retrieval router for BM25, Dense, KG, and Hybrid evidence.

## What is the production router?
- `computed_ras`.

## Why not promote RAS_V3 or RAS_V4?
- They improve the research framing and interpretability, but they do not beat calibrated rescue on adversarial answer accuracy.

## Why does calibrated rescue matter?
- It shows that route choice alone is not the full target; top-k evidence use still matters on hard cases.

## Is this web-scale QA?
- No. PRISM supports bounded benchmark corpora, source packs, local folders, and URL-list corpora.

## What is the strongest failure regime?
- Adversarial route-boundary cases, especially misleading exact terms and low-margin ambiguity.

## What did human evaluation add?
- It confirmed that evidence and traces are usually useful and faithful, while preserving ties, disagreements, and adjudication cases.
"""


def _final_wrapup_report(
    *,
    known_results: dict[str, object],
    benchmark_rows: list[dict[str, object]],
    adversarial_rows: list[dict[str, object]],
    overlay_rows: list[dict[str, object]],
    human_dimension_rows: list[dict[str, object]],
    pair_rows: list[dict[str, object]],
) -> str:
    return f"""# Final Wrap-Up Report

## Problem

PRISM studies retrieval inadequacy caused by structural mismatch. A query can fail not because retrieval is impossible, but because the wrong representation was used.

## System Design

The system routes queries to BM25, Dense, KG, or Hybrid evidence. The production router is `computed_ras`, which remains deterministic and explicit. Research layers include calibrated rescue, classifier routing, RAS_V3, and RAS_V4.

## Main Benchmarks

```json
{json.dumps(benchmark_rows, indent=2)}
```

## Strongest Results

- Stable curated, external, held-out, public raw, public graph, and open-corpus smoke performance.
- Public raw-document and public-graph evaluations remain strong without changing the production router.
- Human evaluation supports evidence/trace usefulness.

## Hardest Failure Cases

Adversarial route-boundary cases remain the main weakness.

```json
{json.dumps(adversarial_rows, indent=2)}
```

## RAS Evolution

- `computed_ras`: production heuristic router.
- `computed_ras_v2`: narrow hard-case refinement, analysis-only.
- `ras_v3`: interpretable route-only model.
- `ras_v4`: interpretable joint route-and-evidence adequacy model.

## Why Calibrated Rescue Matters

Calibrated rescue remains important because route adequacy alone does not fully recover adversarial answer accuracy. Rescue improves answerability by making better use of top-k evidence after retrieval.

## Human Evaluation Summary

```json
{json.dumps(human_dimension_rows, indent=2)}
```

Comparative human preferences:

```json
{json.dumps(pair_rows, indent=2)}
```

## Open-Corpus / Generalization Summary

PRISM now supports bounded source-pack, local-folder, and URL-list corpora. This extends the system beyond fixed benchmarks while preserving reproducibility and provenance.

## Final Production vs Research Conclusion

Production router remains `computed_ras`.

Research overlays remain:
- `calibrated_rescue`
- `classifier_router`
- `ras_v3`
- `ras_v4`
- optional local LLM

The final project is presentation-ready and submission-ready, but the scientific story remains explicit and conservative.

```json
{json.dumps(known_results, indent=2)}
```
"""


def _submission_checklist() -> str:
    return """# Submission Checklist

- Open `data/final_release/final_wrapup_report.md`
- Open `data/final_release/paper_ready_summary.md`
- Open `data/final_release/final_artifact_index.md`
- Confirm release verifier passes
- Mention production router = `computed_ras`
- Mention calibrated rescue remains stronger on adversarial answer accuracy
- Mention PRISM is bounded/open-corpus QA, not web-scale search
"""


def _demo_day_checklist() -> str:
    return """# Demo Day Checklist

- Launch Streamlit
- Start in `Executive Summary`
- Move to `Guided Demo`
- Keep benchmark mode as the default
- Use the safe benchmark sequence if source packs or optional components are unavailable
- Show route scores before evidence
- Show evidence before answer
- Keep production vs research overlays explicit
"""


def _final_artifact_index() -> str:
    return """# Final Artifact Index

## Start Here

- `final_wrapup_report.md`
- `executive_summary.md`
- `paper_ready_summary.md`

## Demo Support

- `demo_runbook.md`
- `demo_walkthrough_quick_reference.md`
- `final_speaker_script.md`
- `one_minute_pitch.md`
- `three_minute_pitch.md`
- `qa_cheat_sheet.md`

## Visual Assets

- `charts/benchmark_overview.png`
- `charts/adversarial_router_comparison.png`
- `charts/production_vs_research_overlay.png`
- `charts/human_eval_overview.png`
- `figures/architecture_diagram.png`
- `figures/ras_family_overview.png`

## Core Release Docs

- `central_claim_summary.md`
- `ras_overview.md`
- `ras_math_guide.md`
- `ras_version_comparison.md`
- `ui_tour.md`
"""
