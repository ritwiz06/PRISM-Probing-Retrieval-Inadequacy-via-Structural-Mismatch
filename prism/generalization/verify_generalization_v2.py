from __future__ import annotations

import argparse
import csv
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

from prism.analysis.evaluation import BACKENDS, answer_matches_gold, build_retrievers
from prism.app.pipeline import answer_query
from prism.generalization.benchmark_builder import build_generalization_benchmark
from prism.generalization.loaders import GeneralizationItem, benchmark_counts, load_generalization_benchmark
from prism.generalization.noisy_corpus import CLEAN_CORPUS_PATH, NOISY_CORPUS_PATH, build_noisy_corpus
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.ras.compute_ras import route_query
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json

SYSTEMS = ("computed_ras", "always_bm25", "always_dense", "always_kg", "always_hybrid", "random_router")
JSON_PATH = Path("data/eval/generalization_v2.json")
CSV_PATH = Path("data/eval/generalization_v2.csv")
MARKDOWN_PATH = Path("data/eval/generalization_v2_summary.md")
CLEAN_NOISY_PLOT = Path("data/eval/generalization_v2_clean_vs_noisy.png")
BASELINE_PLOT = Path("data/eval/generalization_v2_baseline_comparison.png")
CORPUS_MODES = ("clean", "noisy")
SPLITS = ("dev", "test")


def verify_generalization_v2(
    seed: int = 23,
    split: str = "all",
    corpus_mode: str = "both",
) -> dict[str, object]:
    build_generalization_benchmark()
    clean_path = build_corpus()
    noisy_summary = build_noisy_corpus(clean_path, NOISY_CORPUS_PATH)
    build_kg(corpus_path=str(clean_path))

    items = load_generalization_benchmark()
    selected_splits = _selected_splits(split)
    selected_modes = _selected_modes(corpus_mode)
    retrievers_by_mode = {mode: _load_retrievers_for_mode(mode, clean_path, Path(noisy_summary["path"])) for mode in selected_modes}

    runs: dict[str, dict[str, dict[str, object]]] = {}
    for mode in selected_modes:
        runs[mode] = {}
        for split_name in selected_splits:
            split_items = [item for item in items if item.split == split_name]
            runs[mode][split_name] = {
                system: _evaluate_system(system, split_items, retrievers_by_mode[mode], seed=seed)
                for system in SYSTEMS
            }

    deltas = _clean_noisy_deltas(runs)
    payload = {
        "seed": seed,
        "benchmark": {
            "path": "data/processed/generalization_v2_benchmark.jsonl",
            "total": len(items),
            "counts": benchmark_counts(items),
            "note": "Held-out public-source-style suite kept separate from curated and external mini-benchmark data.",
        },
        "corpora": {
            "clean": {"path": str(clean_path), "document_count": len(read_jsonl_documents(clean_path))},
            "noisy": noisy_summary,
        },
        "selected_splits": selected_splits,
        "selected_corpus_modes": selected_modes,
        "systems": runs,
        "clean_vs_noisy_deltas": deltas,
        "takeaways": _takeaways(runs, deltas),
        "threats_to_validity": _threats_to_validity(),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    _plot_clean_vs_noisy(payload, CLEAN_NOISY_PLOT)
    _plot_baselines(payload, BASELINE_PLOT)
    return payload


def _load_retrievers_for_mode(mode: str, clean_path: Path, noisy_path: Path) -> dict[str, object]:
    corpus_path = clean_path if mode == "clean" else noisy_path
    kg_path = Path("data/processed/kg_triples.jsonl")
    if not kg_path.exists():
        build_kg(corpus_path=str(clean_path))
    return build_retrievers(read_jsonl_documents(corpus_path), read_jsonl_triples(kg_path))


def _evaluate_system(
    system_name: str,
    items: list[GeneralizationItem],
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
        payload = answer_query(
            item.query,
            top_k=5 if backend == "hybrid" else 3,
            retrievers=retrievers,
            backend_override=backend,
        )
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
                "split": item.split,
                "source_dataset": item.source_dataset,
                "route_family": item.route_family,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": item.gold_answer,
                "answer": final_answer,
                "answer_correct": answer_ok,
                "top_evidence_ids": [row["item_id"] for row in payload["top_evidence"]],
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


def _select_backend(system_name: str, item: GeneralizationItem, rng: random.Random) -> str:
    if system_name == "computed_ras":
        return route_query(item.query).selected_backend
    if system_name == "random_router":
        return rng.choice(BACKENDS)
    if system_name.startswith("always_"):
        return system_name.removeprefix("always_")
    raise ValueError(f"Unknown generalization system: {system_name}")


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


def _selected_splits(split: str) -> list[str]:
    if split == "all":
        return list(SPLITS)
    if split not in SPLITS:
        raise ValueError(f"Unsupported split: {split}")
    return [split]


def _selected_modes(corpus_mode: str) -> list[str]:
    if corpus_mode == "both":
        return list(CORPUS_MODES)
    if corpus_mode not in CORPUS_MODES:
        raise ValueError(f"Unsupported corpus mode: {corpus_mode}")
    return [corpus_mode]


def _clean_noisy_deltas(runs: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    if "clean" not in runs or "noisy" not in runs:
        return {}
    deltas: dict[str, object] = {}
    for split_name in sorted(set(runs["clean"]) & set(runs["noisy"])):
        clean_ras = runs["clean"][split_name]["computed_ras"]
        noisy_ras = runs["noisy"][split_name]["computed_ras"]
        family_deltas = {}
        for family, clean_row in clean_ras["per_family"].items():
            noisy_row = noisy_ras["per_family"].get(family, {"answer_accuracy": 0.0})
            family_deltas[family] = {
                "clean_answer_accuracy": clean_row["answer_accuracy"],
                "noisy_answer_accuracy": noisy_row["answer_accuracy"],
                "delta": noisy_row["answer_accuracy"] - clean_row["answer_accuracy"],
            }
        deltas[split_name] = {
            "clean_answer_accuracy": clean_ras["answer_accuracy"],
            "noisy_answer_accuracy": noisy_ras["answer_accuracy"],
            "delta": noisy_ras["answer_accuracy"] - clean_ras["answer_accuracy"],
            "per_family": family_deltas,
            "most_degraded_family": _most_degraded_family(family_deltas),
        }
    return deltas


def _most_degraded_family(family_deltas: dict[str, dict[str, float]]) -> str:
    if not family_deltas:
        return ""
    return min(family_deltas, key=lambda family: family_deltas[family]["delta"])


def _best_fixed_backend(systems: dict[str, dict[str, object]]) -> tuple[str, dict[str, object]]:
    fixed = {name: row for name, row in systems.items() if name.startswith("always_")}
    name = max(fixed, key=lambda key: fixed[key]["answer_accuracy"])
    return name, fixed[name]


def _takeaways(
    runs: dict[str, dict[str, dict[str, object]]],
    deltas: dict[str, object],
) -> list[str]:
    rows: list[str] = []
    for mode, splits in runs.items():
        for split_name, systems in splits.items():
            ras = systems["computed_ras"]
            best_fixed_name, best_fixed = _best_fixed_backend(systems)
            verdict = "beats" if ras["answer_accuracy"] >= best_fixed["answer_accuracy"] else "does not beat"
            rows.append(
                f"{mode}/{split_name}: computed RAS answer accuracy {ras['answer_accuracy']:.3f} "
                f"{verdict} strongest fixed backend {best_fixed_name} at {best_fixed['answer_accuracy']:.3f}."
            )
    for split_name, row in deltas.items():
        rows.append(
            f"{split_name}: noisy corpus delta for computed RAS is {row['delta']:.3f}; "
            f"most degraded family is {row['most_degraded_family'] or 'none'}."
        )
    return rows


def _threats_to_validity() -> list[str]:
    return [
        "The suite is normalized and public-source-style, not a full official benchmark download.",
        "Items are grounded in PRISM's local corpus/KG so evidence is available offline.",
        "Noisy-corpus stress testing is synthetic and measures robustness to curated distractors, not arbitrary web noise.",
        "The test split should be treated as held-out for reporting; benchmark construction changes should be justified using dev cases.",
        "Answer accuracy uses normalized string matching, which is useful for local regression checks but not a substitute for human grading.",
    ]


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "corpus_mode",
                "split",
                "system",
                "total",
                "route_accuracy",
                "answer_accuracy",
                "route_correct",
                "answer_correct",
                "predicted_backend_distribution",
            ],
        )
        writer.writeheader()
        for mode, splits in payload["systems"].items():
            for split_name, systems in splits.items():
                for system, row in systems.items():
                    writer.writerow(
                        {
                            "corpus_mode": mode,
                            "split": split_name,
                            "system": system,
                            "total": row["total"],
                            "route_accuracy": row["route_accuracy"],
                            "answer_accuracy": row["answer_accuracy"],
                            "route_correct": row["route_correct"],
                            "answer_correct": row["answer_correct"],
                            "predicted_backend_distribution": row["predicted_backend_distribution"],
                        }
                    )


def _markdown(payload: dict[str, object]) -> str:
    benchmark = payload["benchmark"]
    corpora = payload["corpora"]
    lines = [
        "# Generalization V2 Clean Vs Noisy Summary",
        "",
        f"Benchmark size: {benchmark['total']} examples.",
        f"Benchmark path: `{benchmark['path']}`.",
        f"Counts by split: {benchmark['counts']['split']}.",
        f"Counts by route family: {benchmark['counts']['route_family']}.",
        f"Source datasets/styles: {benchmark['counts']['source_dataset']}.",
        "",
        "## Corpus Modes",
        "",
        f"- Clean corpus: `{corpora['clean']['path']}` with {corpora['clean']['document_count']} documents.",
        f"- Noisy corpus: `{corpora['noisy']['path']}` with {corpora['noisy']['total']} documents, including {corpora['noisy']['noise_count']} added distractors.",
        "",
        "## Clean Vs Noisy Results",
        "",
    ]
    for mode, splits in payload["systems"].items():
        for split_name, systems in splits.items():
            ras = systems["computed_ras"]
            best_fixed_name, best_fixed = _best_fixed_backend(systems)
            lines.extend(
                [
                    f"### {mode.title()} Corpus / {split_name.title()} Split",
                    "",
                    f"- Computed RAS route accuracy: {ras['route_accuracy']:.3f}.",
                    f"- Computed RAS answer accuracy: {ras['answer_accuracy']:.3f} ({ras['answer_correct']}/{ras['total']}).",
                    f"- Strongest fixed-backend baseline: `{best_fixed_name}` at answer accuracy {best_fixed['answer_accuracy']:.3f}.",
                    f"- Predicted backend distribution: {ras['predicted_backend_distribution']}.",
                    "- Per-family computed RAS answer accuracy:",
                    *[
                        f"  - {family}: {row['answer_accuracy']:.3f} ({row['answer_correct']}/{row['total']})"
                        for family, row in ras["per_family"].items()
                    ],
                    "",
                ]
            )
    if payload["clean_vs_noisy_deltas"]:
        lines.extend(["## Noisy-Corpus Degradation", ""])
        for split_name, row in payload["clean_vs_noisy_deltas"].items():
            lines.extend(
                [
                    f"- {split_name}: clean={row['clean_answer_accuracy']:.3f}, noisy={row['noisy_answer_accuracy']:.3f}, delta={row['delta']:.3f}.",
                    f"- {split_name}: most degraded family is `{row['most_degraded_family'] or 'none'}`.",
                ]
            )
        lines.append("")
    lines.extend(
        [
            "## Main Takeaways",
            "",
            *[f"- {item}" for item in payload["takeaways"]],
            "",
            "## Threats To Validity",
            "",
            *[f"- {item}" for item in payload["threats_to_validity"]],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{JSON_PATH}`",
            f"- CSV: `{CSV_PATH}`",
            f"- Markdown: `{MARKDOWN_PATH}`",
            f"- Plot: `{CLEAN_NOISY_PLOT}`",
            f"- Plot: `{BASELINE_PLOT}`",
            "",
        ]
    )
    return "\n".join(lines)


def _matplotlib_pyplot():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib_cache")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_clean_vs_noisy(payload: dict[str, object], path: Path) -> None:
    if "clean" not in payload["systems"] or "noisy" not in payload["systems"]:
        return
    plt = _matplotlib_pyplot()
    split_name = "test" if "test" in payload["systems"]["clean"] else next(iter(payload["systems"]["clean"]))
    clean = payload["systems"]["clean"][split_name]["computed_ras"]["per_family"]
    noisy = payload["systems"]["noisy"][split_name]["computed_ras"]["per_family"]
    families = sorted(clean)
    x_positions = list(range(len(families)))
    width = 0.36
    _, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([x - width / 2 for x in x_positions], [clean[f]["answer_accuracy"] for f in families], width, label="clean")
    ax.bar([x + width / 2 for x in x_positions], [noisy[f]["answer_accuracy"] for f in families], width, label="noisy")
    ax.set_title("Computed RAS clean vs noisy answer accuracy")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x_positions, families)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_baselines(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    mode = "noisy" if "noisy" in payload["systems"] else next(iter(payload["systems"]))
    split_name = "test" if "test" in payload["systems"][mode] else next(iter(payload["systems"][mode]))
    systems = payload["systems"][mode][split_name]
    names = list(SYSTEMS)
    values = [systems[name]["answer_accuracy"] for name in names]
    _, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(names, values, color=["#1f77b4" if name == "computed_ras" else "#9aa4b2" for name in names])
    ax.set_title(f"PRISM vs baselines on {mode}/{split_name}")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRISM on held-out clean/noisy generalization v2.")
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--split", choices=["all", *SPLITS], default="all")
    parser.add_argument("--corpus-mode", choices=["both", *CORPUS_MODES], default="both")
    args = parser.parse_args()
    payload = verify_generalization_v2(seed=args.seed, split=args.split, corpus_mode=args.corpus_mode)
    test_clean = payload["systems"].get("clean", {}).get("test", {}).get("computed_ras")
    test_noisy = payload["systems"].get("noisy", {}).get("test", {}).get("computed_ras")
    clean_answer = f"{test_clean['answer_accuracy']:.3f}" if test_clean else "n/a"
    noisy_answer = f"{test_noisy['answer_accuracy']:.3f}" if test_noisy else "n/a"
    print(
        f"generalization_v2_total={payload['benchmark']['total']} "
        f"splits={payload['benchmark']['counts']['split']} "
        f"families={payload['benchmark']['counts']['route_family']} "
        f"clean_test_answer_accuracy={clean_answer} "
        f"noisy_test_answer_accuracy={noisy_answer} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
