from __future__ import annotations

from pathlib import Path

from prism.external_benchmarks.loaders import ExternalBenchmarkItem, benchmark_counts, load_external_mini_benchmark
from prism.external_benchmarks.mini_benchmark import build_external_mini_benchmark
from prism.external_benchmarks.verify_generalization import verify_generalization
from prism.eval.verify_end_to_end import verify_end_to_end


def test_external_item_schema() -> None:
    item = ExternalBenchmarkItem(
        id="demo",
        query="RFC-7231",
        source_dataset="BEIR",
        route_family="bm25",
        gold_answer="HTTP semantics.",
    )
    assert item.id == "demo"
    assert item.route_family == "bm25"
    assert item.source_dataset == "BEIR"


def test_mini_benchmark_build_and_load(tmp_path: Path) -> None:
    path = tmp_path / "external_mini.jsonl"
    summary = build_external_mini_benchmark(path)
    items = load_external_mini_benchmark(path)
    assert summary["total"] == 32
    assert len(items) == 32
    assert path.exists()


def test_external_family_counts(tmp_path: Path) -> None:
    path = tmp_path / "external_mini.jsonl"
    build_external_mini_benchmark(path)
    counts = benchmark_counts(load_external_mini_benchmark(path))
    assert counts["route_family"] == {"bm25": 8, "dense": 8, "hybrid": 8, "kg": 8}
    assert len(counts["source_dataset"]) >= 3


def test_generalization_result_structure() -> None:
    payload = verify_generalization(seed=11)
    assert payload["benchmark"]["total"] >= 32
    assert {"computed_ras", "always_bm25", "always_dense", "always_kg", "always_hybrid", "random_router"} <= set(payload["systems"])
    assert "per_family" in payload["systems"]["computed_ras"]
    assert Path("data/eval/external_generalization.json").exists()
    assert Path("data/eval/external_generalization.csv").exists()
    assert Path("data/eval/external_generalization_summary.md").exists()


def test_curated_benchmark_pipeline_still_runs() -> None:
    payload = verify_end_to_end()
    assert payload["total"] == 80
    assert payload["passed"] is True
