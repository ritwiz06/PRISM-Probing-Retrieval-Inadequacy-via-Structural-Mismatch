from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from prism.analysis.claim_validation import validate_claims
from prism.analysis.evaluation import evaluate_systems, load_combined_benchmark
from prism.analysis.run_ablations import run_ablations
from prism.config import load_config
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json

REPORT_DIR = Path("data/eval/report")


def generate_report_artifacts(output_dir: str | Path = REPORT_DIR) -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    baseline = evaluate_systems()
    claims = validate_claims()
    ablations = run_ablations()
    corpus_size, kg_size = _artifact_sizes()
    benchmark = load_combined_benchmark()
    benchmark_sizes = _benchmark_sizes(benchmark)

    summary = {
        "corpus_size": corpus_size,
        "kg_size": kg_size,
        "benchmark_sizes": benchmark_sizes,
        "baseline_evaluation": {
            name: _system_summary(row) for name, row in baseline["systems"].items()
        },
        "claim_validation": claims,
        "ablation_impacts": ablations["ablation_impacts"],
    }
    json_path = output_path / "prism_report_summary.json"
    write_json(json_path, summary)

    baseline_csv = output_path / "baseline_comparison.csv"
    per_slice_csv = output_path / "per_slice_backend_comparison.csv"
    ablation_csv = output_path / "ablation_impacts.csv"
    claim_csv = output_path / "claim_validation.csv"
    _write_baseline_csv(baseline_csv, baseline)
    _write_per_slice_csv(per_slice_csv, baseline)
    _write_ablation_csv(ablation_csv, ablations)
    _write_claim_csv(claim_csv, claims)

    plots = [
        _plot_overall_baselines(output_path / "overall_baseline_comparison.png", baseline),
        _plot_per_slice_performance(output_path / "per_slice_backend_performance.png", baseline),
        _plot_predicted_distribution(output_path / "predicted_backend_distribution.png", baseline),
        _plot_ablation_impacts(output_path / "ablation_impact.png", ablations),
    ]
    markdown_path = output_path / "prism_report_summary.md"
    markdown_path.write_text(_markdown_summary(summary, plots, [baseline_csv, per_slice_csv, ablation_csv, claim_csv]), encoding="utf-8")

    payload = {
        "output_dir": str(output_path),
        "json_summary": str(json_path),
        "csv_tables": [str(baseline_csv), str(per_slice_csv), str(ablation_csv), str(claim_csv)],
        "markdown_summary": str(markdown_path),
        "plots": [str(path) for path in plots],
        "summary": summary,
    }
    write_json(output_path / "artifact_manifest.json", payload)
    return payload


def _artifact_sizes() -> tuple[int, int]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    corpus_size = len(read_jsonl_documents(corpus_path)) if corpus_path.exists() else 0
    kg_size = len(read_jsonl_triples(kg_path)) if kg_path.exists() else 0
    return corpus_size, kg_size


def _benchmark_sizes(benchmark: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in benchmark:
        slice_name = str(row["slice"])
        counts[slice_name] = counts.get(slice_name, 0) + 1
    counts["total"] = len(benchmark)
    return counts


def _system_summary(row: dict[str, object]) -> dict[str, object]:
    return {
        "route_accuracy": row["route_accuracy"],
        "evidence_hit_at_k": row["evidence_hit_at_k"],
        "answer_accuracy": row["answer_accuracy"],
        "predicted_distribution": row["predicted_distribution"],
    }


def _write_baseline_csv(path: Path, baseline: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["system", "route_accuracy", "evidence_hit_at_k", "answer_accuracy", "route_correct", "evidence_hits", "answer_matches", "total"])
        writer.writeheader()
        for name, row in baseline["systems"].items():
            writer.writerow({key: row.get(key) for key in writer.fieldnames} | {"system": name})


def _write_per_slice_csv(path: Path, baseline: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["system", "slice", "route_accuracy", "evidence_hit_at_k", "answer_accuracy", "route_correct", "evidence_hits", "answer_matches", "total"])
        writer.writeheader()
        for name, row in baseline["systems"].items():
            for slice_name, metrics in row["per_slice"].items():
                writer.writerow({key: metrics.get(key) for key in writer.fieldnames} | {"system": name, "slice": slice_name})


def _write_ablation_csv(path: Path, ablations: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["ablation", "relational_evidence_hit_at_k", "relational_answer_accuracy", "delta_vs_full_hybrid_evidence_hit_at_k"],
        )
        writer.writeheader()
        writer.writerows(ablations["ablation_impacts"])


def _write_claim_csv(path: Path, claims: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "statement", "primary_metric", "baseline_metric", "margin", "supported"])
        writer.writeheader()
        writer.writerows(claims["claims"])


def _plot_overall_baselines(path: Path, baseline: dict[str, object]) -> Path:
    names = list(baseline["systems"])
    values = [baseline["systems"][name]["answer_accuracy"] for name in names]
    plt.figure(figsize=(10, 5))
    plt.bar(names, values, color="#2f6f73")
    plt.xticks(rotation=30, ha="right")
    plt.ylim(0, 1.05)
    plt.ylabel("Answer Accuracy")
    plt.title("Overall Baseline Comparison")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _plot_per_slice_performance(path: Path, baseline: dict[str, object]) -> Path:
    systems = ["always_bm25", "always_dense", "always_kg", "always_hybrid", "computed_ras"]
    slices = ["lexical", "semantic", "deductive", "relational"]
    width = 0.15
    positions = list(range(len(slices)))
    plt.figure(figsize=(10, 5))
    for index, system in enumerate(systems):
        values = [baseline["systems"][system]["per_slice"][slice_name]["evidence_hit_at_k"] for slice_name in slices]
        offsets = [pos + (index - 2) * width for pos in positions]
        plt.bar(offsets, values, width=width, label=system)
    plt.xticks(positions, slices)
    plt.ylim(0, 1.05)
    plt.ylabel("Evidence Hit@k")
    plt.title("Per-Slice Backend Performance")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _plot_predicted_distribution(path: Path, baseline: dict[str, object]) -> Path:
    distribution = baseline["systems"]["computed_ras"]["predicted_distribution"]
    names = ["bm25", "dense", "kg", "hybrid"]
    values = [distribution.get(name, 0) for name in names]
    plt.figure(figsize=(7, 5))
    plt.bar(names, values, color="#9a6a2f")
    plt.ylabel("Predicted Queries")
    plt.title("Computed RAS Predicted Backend Distribution")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _plot_ablation_impacts(path: Path, ablations: dict[str, object]) -> Path:
    rows = ablations["ablation_impacts"]
    names = [row["ablation"] for row in rows]
    values = [row["delta_vs_full_hybrid_evidence_hit_at_k"] for row in rows]
    plt.figure(figsize=(8, 5))
    plt.bar(names, values, color="#7a3e48")
    plt.axhline(0, color="black", linewidth=1)
    plt.ylabel("Delta Evidence Hit@k")
    plt.title("Hybrid Ablation Impact On Relational Slice")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _markdown_summary(summary: dict[str, object], plots: list[Path], tables: list[Path]) -> str:
    systems = summary["baseline_evaluation"]
    claims = summary["claim_validation"]["claims"]
    best_fixed = max(
        (name for name in systems if name.startswith("always_")),
        key=lambda name: systems[name]["answer_accuracy"],
    )
    return "\n".join(
        [
            "# PRISM Report Artifact Summary",
            "",
            f"Corpus size: {summary['corpus_size']} documents.",
            f"KG size: {summary['kg_size']} triples.",
            f"Benchmark sizes: {summary['benchmark_sizes']}.",
            "",
            "## Overall Results",
            "",
            f"Computed RAS route accuracy: {systems['computed_ras']['route_accuracy']:.3f}.",
            f"Computed RAS answer accuracy: {systems['computed_ras']['answer_accuracy']:.3f}.",
            f"Strongest fixed-backend answer baseline: {best_fixed} at {systems[best_fixed]['answer_accuracy']:.3f}.",
            f"Computed RAS evidence hit@k: {systems['computed_ras']['evidence_hit_at_k']:.3f}.",
            "",
            "## Claim Validation",
            "",
            *[
                f"- {'Supported' if row['supported'] else 'Not supported'}: {row['statement']} margin={row['margin']:.3f}."
                for row in claims
            ],
            "",
            "## Generated Tables",
            "",
            *[f"- `{path}`" for path in tables],
            "",
            "## Generated Plots",
            "",
            *[f"- `{path}`" for path in plots],
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PRISM report-ready artifacts.")
    parser.add_argument("--output-dir", default=str(REPORT_DIR))
    args = parser.parse_args()
    payload = generate_report_artifacts(args.output_dir)
    print(f"report_dir={payload['output_dir']}")
    print(f"json_summary={payload['json_summary']}")
    print(f"csv_tables={len(payload['csv_tables'])} plots={len(payload['plots'])} markdown={payload['markdown_summary']}")


if __name__ == "__main__":
    main()
