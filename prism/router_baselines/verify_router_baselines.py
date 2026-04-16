from __future__ import annotations

import argparse
import csv
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

from prism.analysis.evaluation import BACKENDS, answer_matches_gold, evaluate_system, load_analysis_retrievers, load_combined_benchmark
from prism.app.pipeline import answer_query
from prism.external_benchmarks.loaders import load_external_mini_benchmark
from prism.ras.compute_ras import route_query
from prism.router_baselines.route_confidence import compute_route_confidence
from prism.router_baselines.rule_router import RouterPrediction, keyword_rule_route
from prism.utils import write_json

EVAL_DIR = Path("data/eval")
ROUTER_JSON = EVAL_DIR / "router_baselines.json"
ROUTER_CSV = EVAL_DIR / "router_baselines.csv"
ROUTER_MD = EVAL_DIR / "router_baselines_summary.md"
CONFIDENCE_JSON = EVAL_DIR / "route_confidence.json"
CONFIDENCE_MD = EVAL_DIR / "route_confidence_summary.md"
CLASSIFIER_MODEL_PATH = EVAL_DIR / "router_classifier.pkl"
ROUTER_COMPARISON_PLOT = EVAL_DIR / "router_baseline_comparison.png"
ROUTER_DISTRIBUTION_PLOT = EVAL_DIR / "router_predicted_distribution.png"
CONFIDENCE_PLOT = EVAL_DIR / "route_confidence_correctness.png"

ROUTER_SYSTEMS = ("computed_ras", "keyword_rule_router", "classifier_router", "random_router")
FIXED_SYSTEMS = ("always_bm25", "always_dense", "always_kg", "always_hybrid")


def verify_router_baselines(seed: int = 23) -> dict[str, object]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    curated_rows = _curated_rows()
    external_rows = _external_rows()
    combined_rows = curated_rows + external_rows
    retrievers = load_analysis_retrievers()

    # Load retrievers before sklearn cross-validation. On this machine, fitting
    # sklearn first can leave the Hugging Face HTTP client in a closed state and
    # incorrectly force Dense into numpy_fallback inside this analysis process.
    from prism.router_baselines.classifier_router import ClassifierRouter, cross_validate_classifier_router

    classifier_router = ClassifierRouter(seed=seed).fit(
        [row["query"] for row in curated_rows],
        [row["gold_route"] for row in curated_rows],
    )
    classifier_router.save(CLASSIFIER_MODEL_PATH)
    classifier_cv = cross_validate_classifier_router(
        [row["query"] for row in curated_rows],
        [row["gold_route"] for row in curated_rows],
        seed=seed,
        n_splits=4,
    )
    curated_classifier_predictions = {
        row["id"]: prediction for row, prediction in zip(curated_rows, classifier_cv.predictions)
    }

    datasets = {
        "curated": curated_rows,
        "external": external_rows,
        "combined": combined_rows,
    }
    router_results = {
        name: {
            dataset_name: _evaluate_router(
                name,
                rows,
                retrievers,
                seed=seed,
                classifier_router=classifier_router,
                curated_classifier_predictions=curated_classifier_predictions,
            )
            for dataset_name, rows in datasets.items()
        }
        for name in ROUTER_SYSTEMS
    }
    fixed_results = {
        name: {
            dataset_name: _evaluate_router(
                name,
                rows,
                retrievers,
                seed=seed,
                classifier_router=classifier_router,
                curated_classifier_predictions=curated_classifier_predictions,
            )
            for dataset_name, rows in datasets.items()
        }
        for name in FIXED_SYSTEMS
    }
    confidence_payload = _confidence_analysis(combined_rows, router_results["computed_ras"]["combined"], classifier_router)

    payload = {
        "seed": seed,
        "protocol": {
            "classifier_curated": classifier_cv.protocol,
            "classifier_external": "Classifier trained on full curated 80-query benchmark and evaluated on external mini-benchmark.",
            "classifier_combined": "Combined result uses curated cross-validation predictions plus external train-curated predictions.",
            "production_router": "computed_ras remains the production router; all other routers are analysis-only.",
        },
        "datasets": {
            "curated": _dataset_summary(curated_rows),
            "external": _dataset_summary(external_rows),
            "combined": _dataset_summary(combined_rows),
        },
        "router_systems": router_results,
        "fixed_backend_baselines": fixed_results,
        "strongest_fixed_backend": _strongest_fixed(fixed_results),
        "classifier_model_path": str(CLASSIFIER_MODEL_PATH),
        "classifier_curated_cv_route_accuracy": classifier_cv.accuracy,
        "route_confidence_summary": confidence_payload["summary"],
        "plots": {
            "router_comparison": str(ROUTER_COMPARISON_PLOT),
            "predicted_distribution": str(ROUTER_DISTRIBUTION_PLOT),
            "confidence_correctness": str(CONFIDENCE_PLOT),
        },
        "takeaways": _takeaways(router_results, fixed_results, confidence_payload),
    }

    write_json(ROUTER_JSON, payload)
    write_json(CONFIDENCE_JSON, confidence_payload)
    _write_router_csv(ROUTER_CSV, router_results, fixed_results)
    ROUTER_MD.write_text(_router_markdown(payload), encoding="utf-8")
    CONFIDENCE_MD.write_text(_confidence_markdown(confidence_payload), encoding="utf-8")
    _plot_router_comparison(router_results, fixed_results)
    _plot_predicted_distribution(router_results)
    _plot_confidence(confidence_payload)
    return payload


def _curated_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, row in enumerate(load_combined_benchmark()):
        rows.append(
            {
                "id": f"curated_{index:03d}",
                "benchmark": "curated",
                "family": row["slice"],
                "query": str(row["query"]),
                "gold_route": str(row["gold_route"]),
                "gold_answer": str(row["gold_answer"]),
            }
        )
    return rows


def _external_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in load_external_mini_benchmark():
        rows.append(
            {
                "id": item.id,
                "benchmark": "external",
                "family": item.route_family,
                "query": item.query,
                "gold_route": item.route_family,
                "gold_answer": item.gold_answer,
                "source_dataset": item.source_dataset,
            }
        )
    return rows


def _evaluate_router(
    router_name: str,
    rows: list[dict[str, object]],
    retrievers: dict[str, object],
    seed: int,
    classifier_router: ClassifierRouter,
    curated_classifier_predictions: dict[str, str],
) -> dict[str, object]:
    rng = random.Random(seed)
    route_correct = 0
    answer_correct = 0
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0))
    predicted_distribution: Counter[str] = Counter()
    confusion: Counter[str] = Counter()
    result_rows: list[dict[str, object]] = []

    for row in rows:
        prediction = _predict_route(router_name, row, rng, classifier_router, curated_classifier_predictions)
        backend = prediction.route
        payload = answer_query(
            str(row["query"]),
            top_k=5 if backend == "hybrid" else 3,
            retrievers=retrievers,
            backend_override=backend,
        )
        answer = str(payload["answer"]["final_answer"])
        route_ok = backend == row["gold_route"]
        answer_ok = answer_matches_gold(answer, str(row["gold_answer"]))
        route_correct += int(route_ok)
        answer_correct += int(answer_ok)
        predicted_distribution[backend] += 1
        confusion[f"{row['gold_route']}->{backend}"] += 1
        family_counter = per_family[str(row["family"])]
        family_counter["total"] += 1
        family_counter["route_correct"] += int(route_ok)
        family_counter["answer_correct"] += int(answer_ok)
        result_rows.append(
            {
                "id": row["id"],
                "benchmark": row["benchmark"],
                "family": row["family"],
                "query": row["query"],
                "gold_route": row["gold_route"],
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": row["gold_answer"],
                "answer": answer,
                "answer_correct": answer_ok,
                "router_scores": prediction.scores,
                "router_rationale": prediction.rationale,
            }
        )

    total = len(rows)
    return {
        "system": router_name,
        "total": total,
        "route_accuracy": route_correct / total if total else 0.0,
        "answer_accuracy": answer_correct / total if total else 0.0,
        "route_correct": route_correct,
        "answer_correct": answer_correct,
        "per_family": _counter_breakdown(per_family),
        "predicted_backend_distribution": dict(predicted_distribution),
        "confusion": dict(confusion),
        "results": result_rows,
    }


def _predict_route(
    router_name: str,
    row: dict[str, object],
    rng: random.Random,
    classifier_router: ClassifierRouter,
    curated_classifier_predictions: dict[str, str],
) -> RouterPrediction:
    query = str(row["query"])
    if router_name == "computed_ras":
        decision = route_query(query)
        return RouterPrediction(route=decision.selected_backend, scores=decision.ras_scores, rationale="Minimum computed RAS penalty.")
    if router_name == "keyword_rule_router":
        return keyword_rule_route(query)
    if router_name == "classifier_router":
        if row["benchmark"] == "curated":
            route = curated_classifier_predictions[str(row["id"])]
            scores = {backend: 1.0 if backend == route else 0.0 for backend in BACKENDS}
            return RouterPrediction(route=route, scores=scores, rationale="Held-out cross-validation prediction for curated query.")
        return classifier_router.predict(query)
    if router_name == "random_router":
        route = rng.choice(BACKENDS)
        return RouterPrediction(route=route, scores={backend: 0.25 for backend in BACKENDS}, rationale="Fixed-seed random router.")
    if router_name.startswith("always_"):
        route = router_name.removeprefix("always_")
        return RouterPrediction(route=route, scores={backend: 1.0 if backend == route else 0.0 for backend in BACKENDS}, rationale="Fixed-backend baseline.")
    raise ValueError(f"Unknown router: {router_name}")


def _confidence_analysis(
    rows: list[dict[str, object]],
    computed_result: dict[str, object],
    classifier_router: ClassifierRouter,
) -> dict[str, object]:
    computed_by_id = {row["id"]: row for row in computed_result["results"]}
    confidence_rows: list[dict[str, object]] = []
    buckets = defaultdict(lambda: Counter(total=0, route_misses=0, answer_misses=0))

    for row in rows:
        confidence = compute_route_confidence(str(row["query"]), classifier=classifier_router)
        result = computed_by_id[str(row["id"])]
        route_ok = bool(result["route_correct"])
        answer_ok = bool(result["answer_correct"])
        label = str(confidence["confidence_label"])
        buckets[label]["total"] += 1
        buckets[label]["route_misses"] += int(not route_ok)
        buckets[label]["answer_misses"] += int(not answer_ok)
        confidence_rows.append(
            {
                "id": row["id"],
                "benchmark": row["benchmark"],
                "family": row["family"],
                "query": row["query"],
                "gold_route": row["gold_route"],
                "predicted_backend": result["predicted_backend"],
                "route_correct": route_ok,
                "answer_correct": answer_ok,
                **confidence,
            }
        )

    low_confidence_examples = sorted(confidence_rows, key=lambda item: float(item["confidence_score"]))[:8]
    summary = {
        "total": len(confidence_rows),
        "bucket_summary": {
            label: {
                "total": counts["total"],
                "route_misses": counts["route_misses"],
                "answer_misses": counts["answer_misses"],
                "route_miss_rate": counts["route_misses"] / counts["total"] if counts["total"] else 0.0,
                "answer_miss_rate": counts["answer_misses"] / counts["total"] if counts["total"] else 0.0,
            }
            for label, counts in sorted(buckets.items())
        },
        "low_confidence_miss_correlation": _confidence_correlation_statement(buckets),
        "low_confidence_examples": low_confidence_examples,
    }
    return {"summary": summary, "rows": confidence_rows}


def _confidence_correlation_statement(buckets: dict[str, Counter[str]]) -> str:
    total_misses = sum(counts["route_misses"] + counts["answer_misses"] for counts in buckets.values())
    if total_misses == 0:
        return "No route or answer misses occurred for computed RAS on this combined benchmark, so low-confidence routing cannot be correlated with misses here."
    low = buckets.get("low", Counter())
    return (
        f"Low-confidence bucket contains {low['route_misses']} route misses and {low['answer_misses']} answer misses; "
        "inspect route_confidence.json for example-level details."
    )


def _counter_breakdown(counters: dict[str, Counter[str]]) -> dict[str, dict[str, object]]:
    return {
        family: {
            "total": counts["total"],
            "route_accuracy": counts["route_correct"] / counts["total"] if counts["total"] else 0.0,
            "answer_accuracy": counts["answer_correct"] / counts["total"] if counts["total"] else 0.0,
            "route_correct": counts["route_correct"],
            "answer_correct": counts["answer_correct"],
        }
        for family, counts in sorted(counters.items())
    }


def _dataset_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    counts = Counter(str(row["family"]) for row in rows)
    return {"total": len(rows), "family_counts": dict(sorted(counts.items()))}


def _strongest_fixed(fixed_results: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    strongest: dict[str, object] = {}
    for dataset_name in ("curated", "external", "combined"):
        winner = max(FIXED_SYSTEMS, key=lambda name: fixed_results[name][dataset_name]["answer_accuracy"])
        strongest[dataset_name] = {
            "system": winner,
            "answer_accuracy": fixed_results[winner][dataset_name]["answer_accuracy"],
            "route_accuracy": fixed_results[winner][dataset_name]["route_accuracy"],
        }
    return strongest


def _takeaways(
    router_results: dict[str, dict[str, dict[str, object]]],
    fixed_results: dict[str, dict[str, dict[str, object]]],
    confidence_payload: dict[str, object],
) -> list[str]:
    combined_ras = router_results["computed_ras"]["combined"]
    combined_keyword = router_results["keyword_rule_router"]["combined"]
    combined_classifier = router_results["classifier_router"]["combined"]
    strongest = _strongest_fixed(fixed_results)["combined"]
    return [
        f"Computed RAS combined route accuracy is {combined_ras['route_accuracy']:.3f} and answer accuracy is {combined_ras['answer_accuracy']:.3f}.",
        f"Keyword router combined route accuracy is {combined_keyword['route_accuracy']:.3f}; classifier router combined route accuracy is {combined_classifier['route_accuracy']:.3f}.",
        f"Strongest fixed backend on combined answer accuracy is {strongest['system']} at {strongest['answer_accuracy']:.3f}.",
        confidence_payload["summary"]["low_confidence_miss_correlation"],
    ]


def _write_router_csv(
    path: Path,
    router_results: dict[str, dict[str, dict[str, object]]],
    fixed_results: dict[str, dict[str, dict[str, object]]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["system", "system_type", "dataset", "total", "route_accuracy", "answer_accuracy", "route_correct", "answer_correct", "predicted_backend_distribution"],
        )
        writer.writeheader()
        for system_type, systems in (("router", router_results), ("fixed_backend", fixed_results)):
            for system, by_dataset in systems.items():
                for dataset, row in by_dataset.items():
                    writer.writerow(
                        {
                            "system": system,
                            "system_type": system_type,
                            "dataset": dataset,
                            "total": row["total"],
                            "route_accuracy": row["route_accuracy"],
                            "answer_accuracy": row["answer_accuracy"],
                            "route_correct": row["route_correct"],
                            "answer_correct": row["answer_correct"],
                            "predicted_backend_distribution": row["predicted_backend_distribution"],
                        }
                    )


def _router_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Router Baseline Summary",
        "",
        "Computed RAS remains the production router. All other routers are analysis-only baselines.",
        "",
        "## Protocol",
        "",
        f"- Classifier curated protocol: {payload['protocol']['classifier_curated']}.",
        f"- Classifier external protocol: {payload['protocol']['classifier_external']}",
        f"- Classifier combined protocol: {payload['protocol']['classifier_combined']}",
        "",
        "## Combined Router Results",
        "",
        "| Router | Route accuracy | Answer accuracy | Predicted distribution |",
        "| --- | ---: | ---: | --- |",
    ]
    for name in ROUTER_SYSTEMS:
        row = payload["router_systems"][name]["combined"]
        lines.append(f"| {name} | {row['route_accuracy']:.3f} | {row['answer_accuracy']:.3f} | {row['predicted_backend_distribution']} |")
    lines.extend(
        [
            "",
            "## Strongest Fixed Backend Baselines",
            "",
            *[
                f"- {dataset}: {row['system']} with answer_accuracy={row['answer_accuracy']:.3f}, route_accuracy={row['route_accuracy']:.3f}."
                for dataset, row in payload["strongest_fixed_backend"].items()
            ],
            "",
            "## Takeaways",
            "",
            *[f"- {item}" for item in payload["takeaways"]],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{ROUTER_JSON}`",
            f"- CSV: `{ROUTER_CSV}`",
            f"- Confidence JSON: `{CONFIDENCE_JSON}`",
            f"- Router comparison plot: `{ROUTER_COMPARISON_PLOT}`",
            f"- Predicted distribution plot: `{ROUTER_DISTRIBUTION_PLOT}`",
            f"- Confidence plot: `{CONFIDENCE_PLOT}`",
            "",
        ]
    )
    return "\n".join(lines)


def _confidence_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Route Confidence Summary",
        "",
        "Confidence is computed from the margin between the best and second-best computed RAS scores plus agreement with keyword and classifier routers.",
        "",
        f"Total examples: {summary['total']}.",
        f"Miss correlation: {summary['low_confidence_miss_correlation']}",
        "",
        "## Bucket Summary",
        "",
        "| Confidence | Total | Route misses | Answer misses |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, row in summary["bucket_summary"].items():
        lines.append(f"| {label} | {row['total']} | {row['route_misses']} | {row['answer_misses']} |")
    lines.extend(["", "## Lowest-Confidence Examples", ""])
    for row in summary["low_confidence_examples"]:
        lines.append(
            f"- `{row['query']}`: selected={row['selected_backend']}, competitor={row['top_competing_backend']}, "
            f"label={row['confidence_label']}, score={row['confidence_score']}."
        )
    lines.extend(["", f"JSON artifact: `{CONFIDENCE_JSON}`", ""])
    return "\n".join(lines)


def _plot_router_comparison(
    router_results: dict[str, dict[str, dict[str, object]]],
    fixed_results: dict[str, dict[str, dict[str, object]]],
) -> None:
    plt = _matplotlib_pyplot()
    systems = list(ROUTER_SYSTEMS) + list(FIXED_SYSTEMS)
    values = [router_results[name]["combined"]["answer_accuracy"] if name in router_results else fixed_results[name]["combined"]["answer_accuracy"] for name in systems]
    plt.figure(figsize=(10, 5))
    plt.bar(systems, values, color=["#1f77b4" if name in ROUTER_SYSTEMS else "#888888" for name in systems])
    plt.ylabel("Combined answer accuracy")
    plt.ylim(0, 1.05)
    plt.xticks(rotation=30, ha="right")
    plt.title("Router and Fixed-Backend Baseline Comparison")
    plt.tight_layout()
    plt.savefig(ROUTER_COMPARISON_PLOT)
    plt.close()


def _plot_predicted_distribution(router_results: dict[str, dict[str, dict[str, object]]]) -> None:
    plt = _matplotlib_pyplot()
    labels = list(ROUTER_SYSTEMS)
    bottoms = [0] * len(labels)
    plt.figure(figsize=(10, 5))
    for backend in BACKENDS:
        values = [router_results[name]["combined"]["predicted_backend_distribution"].get(backend, 0) for name in labels]
        plt.bar(labels, values, bottom=bottoms, label=backend)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    plt.ylabel("Predicted route count")
    plt.title("Predicted Backend Distribution By Router")
    plt.legend()
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(ROUTER_DISTRIBUTION_PLOT)
    plt.close()


def _plot_confidence(confidence_payload: dict[str, object]) -> None:
    plt = _matplotlib_pyplot()
    order = ["low", "medium", "high"]
    summary = confidence_payload["summary"]["bucket_summary"]
    totals = [summary.get(label, {}).get("total", 0) for label in order]
    misses = [summary.get(label, {}).get("route_misses", 0) + summary.get(label, {}).get("answer_misses", 0) for label in order]
    plt.figure(figsize=(7, 4))
    plt.bar(order, totals, label="total", color="#9ecae1")
    plt.bar(order, misses, label="misses", color="#de2d26")
    plt.ylabel("Example count")
    plt.title("Route Confidence vs Misses")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CONFIDENCE_PLOT)
    plt.close()


def _matplotlib_pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRISM router baselines and route confidence.")
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    payload = verify_router_baselines(seed=args.seed)
    combined = payload["router_systems"]["computed_ras"]["combined"]
    keyword = payload["router_systems"]["keyword_rule_router"]["combined"]
    classifier = payload["router_systems"]["classifier_router"]["combined"]
    print(
        f"router_baselines_total={payload['datasets']['combined']['total']} "
        f"computed_ras_route_accuracy={combined['route_accuracy']:.3f} "
        f"computed_ras_answer_accuracy={combined['answer_accuracy']:.3f} "
        f"keyword_route_accuracy={keyword['route_accuracy']:.3f} "
        f"classifier_route_accuracy={classifier['route_accuracy']:.3f} "
        f"json={ROUTER_JSON} confidence={CONFIDENCE_JSON}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
