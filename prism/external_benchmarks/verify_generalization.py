from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

from prism.analysis.evaluation import BACKENDS, answer_matches_gold
from prism.app.pipeline import answer_query, load_retrievers
from prism.external_benchmarks.loaders import ExternalBenchmarkItem, benchmark_counts, load_external_mini_benchmark
from prism.utils import write_json

SYSTEMS = ("computed_ras", "always_bm25", "always_dense", "always_kg", "always_hybrid", "random_router")
JSON_PATH = Path("data/eval/external_generalization.json")
CSV_PATH = Path("data/eval/external_generalization.csv")
MARKDOWN_PATH = Path("data/eval/external_generalization_summary.md")


def verify_generalization(seed: int = 11) -> dict[str, object]:
    items = load_external_mini_benchmark()
    retrievers = load_retrievers()
    systems = {name: _evaluate_system(name, items, retrievers, seed=seed) for name in SYSTEMS}
    counts = benchmark_counts(items)
    dense_status = retrievers["dense"].backend_status
    payload = {
        "benchmark": {
            "total": len(items),
            "counts": counts,
            "path": "data/processed/external_mini_benchmark.jsonl",
            "note": "Small normalized public-source-style mini-benchmark kept separate from the curated 80-query benchmark.",
        },
        "dense_backend_status": dense_status,
        "seed": seed,
        "systems": systems,
        "takeaways": _takeaways(systems),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    _write_csv(CSV_PATH, systems)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    return payload


def _evaluate_system(
    system_name: str,
    items: list[ExternalBenchmarkItem],
    retrievers: dict[str, object],
    seed: int,
) -> dict[str, object]:
    rng = random.Random(seed)
    route_correct = 0
    answer_correct = 0
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0))
    per_source = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0))
    predicted_distribution: Counter[str] = Counter()
    rows: list[dict[str, object]] = []

    for item in items:
        backend = _select_backend(system_name, item, rng)
        payload = answer_query(item.query, top_k=5 if backend == "hybrid" else 3, retrievers=retrievers, backend_override=backend)
        final_answer = str(payload["answer"]["final_answer"])
        route_ok = backend == item.route_family
        answer_ok = answer_matches_gold(final_answer, item.gold_answer)
        route_correct += int(route_ok)
        answer_correct += int(answer_ok)
        predicted_distribution[backend] += 1
        for counter in (per_family[item.route_family], per_source[item.source_dataset]):
            counter["total"] += 1
            counter["route_correct"] += int(route_ok)
            counter["answer_correct"] += int(answer_ok)
        rows.append(
            {
                "id": item.id,
                "query": item.query,
                "source_dataset": item.source_dataset,
                "route_family": item.route_family,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": item.gold_answer,
                "answer": final_answer,
                "answer_correct": answer_ok,
                "reasoning_trace_generated": bool(payload["reasoning_trace"]),
            }
        )

    total = len(items)
    return {
        "system": system_name,
        "total": total,
        "route_accuracy": route_correct / total if total else 0.0,
        "answer_accuracy": answer_correct / total if total else 0.0,
        "route_correct": route_correct,
        "answer_correct": answer_correct,
        "predicted_backend_distribution": dict(predicted_distribution),
        "per_family": _counter_breakdown(per_family),
        "per_source_dataset": _counter_breakdown(per_source),
        "results": rows,
    }


def _select_backend(system_name: str, item: ExternalBenchmarkItem, rng: random.Random) -> str:
    if system_name == "computed_ras":
        from prism.ras.compute_ras import route_query

        return route_query(item.query).selected_backend
    if system_name == "random_router":
        return rng.choice(BACKENDS)
    if system_name.startswith("always_"):
        return system_name.removeprefix("always_")
    raise ValueError(f"Unknown external benchmark system: {system_name}")


def _counter_breakdown(counters: dict[str, Counter[str]]) -> dict[str, dict[str, object]]:
    return {
        name: {
            "total": counter["total"],
            "route_accuracy": counter["route_correct"] / counter["total"] if counter["total"] else 0.0,
            "answer_accuracy": counter["answer_correct"] / counter["total"] if counter["total"] else 0.0,
            "route_correct": counter["route_correct"],
            "answer_correct": counter["answer_correct"],
        }
        for name, counter in sorted(counters.items())
    }


def _takeaways(systems: dict[str, dict[str, object]]) -> list[str]:
    fixed = {name: row for name, row in systems.items() if name.startswith("always_")}
    best_fixed = max(fixed, key=lambda name: fixed[name]["answer_accuracy"])
    ras = systems["computed_ras"]
    return [
        f"Computed RAS answer accuracy is {ras['answer_accuracy']:.3f}.",
        f"Strongest fixed-backend baseline is {best_fixed} at {fixed[best_fixed]['answer_accuracy']:.3f}.",
        "External mini-benchmark remains separate from the curated 80-query benchmark.",
    ]


def _write_csv(path: Path, systems: dict[str, dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["system", "total", "route_accuracy", "answer_accuracy", "route_correct", "answer_correct", "predicted_backend_distribution"],
        )
        writer.writeheader()
        for name, row in systems.items():
            writer.writerow({key: row.get(key) for key in writer.fieldnames} | {"system": name})


def _markdown(payload: dict[str, object]) -> str:
    benchmark = payload["benchmark"]
    systems = payload["systems"]
    fixed = {name: row for name, row in systems.items() if name.startswith("always_")}
    best_fixed = max(fixed, key=lambda name: fixed[name]["answer_accuracy"])
    counts = benchmark["counts"]
    ras = systems["computed_ras"]
    return "\n".join(
        [
            "# External Mini-Benchmark Generalization Summary",
            "",
            f"Benchmark size: {benchmark['total']} examples.",
            f"Source datasets used: {', '.join(counts['source_dataset'])}.",
            f"Counts per route family: {counts['route_family']}.",
            "",
            "## PRISM Performance",
            "",
            f"Computed RAS route accuracy: {ras['route_accuracy']:.3f}.",
            f"Computed RAS answer accuracy: {ras['answer_accuracy']:.3f}.",
            f"Strongest fixed-backend baseline: {best_fixed} at answer accuracy {fixed[best_fixed]['answer_accuracy']:.3f}.",
            f"Predicted backend distribution: {ras['predicted_backend_distribution']}.",
            f"Dense backend status: {payload['dense_backend_status']}.",
            "",
            "## Per-Family Computed RAS Results",
            "",
            *[
                f"- {family}: route_accuracy={row['route_accuracy']:.3f}, answer_accuracy={row['answer_accuracy']:.3f}, correct={row['answer_correct']}/{row['total']}."
                for family, row in ras["per_family"].items()
            ],
            "",
            "## Main Takeaways",
            "",
            *[f"- {item}" for item in payload["takeaways"]],
            "",
            "## Known Caveats",
            "",
            "- This is a small normalized mini-benchmark, not a full public benchmark download.",
            "- Examples were included only when they could be mapped cleanly to a PRISM route family.",
            "- Performance should be interpreted as a lightweight generalization check, not broad external validation.",
            "- The benchmark is cached separately from the curated 80-query benchmark.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{JSON_PATH}`",
            f"- CSV: `{CSV_PATH}`",
            f"- Markdown: `{MARKDOWN_PATH}`",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRISM on the external mini-benchmark.")
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    payload = verify_generalization(seed=args.seed)
    ras = payload["systems"]["computed_ras"]
    print(
        f"external_generalization_total={payload['benchmark']['total']} "
        f"ras_route_accuracy={ras['route_accuracy']:.3f} "
        f"ras_answer_accuracy={ras['answer_accuracy']:.3f} "
        f"dense_backend={payload['dense_backend_status']['active_backend']} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for name, row in payload["systems"].items():
        print(f"{name}: route_accuracy={row['route_accuracy']:.3f} answer_accuracy={row['answer_accuracy']:.3f}")


if __name__ == "__main__":
    main()
