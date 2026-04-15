from __future__ import annotations

from pathlib import Path

from prism.analysis.claim_validation import _claim
from prism.analysis.evaluation import evaluate_system, load_combined_benchmark
from prism.analysis.report_artifacts import generate_report_artifacts
from prism.analysis.run_ablations import run_ablations


def test_baseline_result_structure() -> None:
    payload = evaluate_system("computed_ras")
    assert payload["total"] == 80
    assert "per_slice" in payload
    assert {"lexical", "semantic", "deductive", "relational"} <= set(payload["per_slice"])
    assert 0.0 <= payload["route_accuracy"] <= 1.0


def test_claim_output_shape() -> None:
    row = _claim("demo", 1.0, 0.5, "Demo claim.")
    assert row["name"] == "demo"
    assert row["supported"] is True
    assert row["margin"] == 0.5


def test_ablation_output_shape() -> None:
    payload = run_ablations()
    assert len(payload["ablation_impacts"]) == 3
    assert {row["ablation"] for row in payload["ablation_impacts"]} == {"hybrid_no_kg", "hybrid_no_bm25", "hybrid_no_dense"}


def test_report_artifact_file_generation(tmp_path: Path) -> None:
    payload = generate_report_artifacts(tmp_path)
    assert Path(payload["json_summary"]).exists()
    assert len(payload["csv_tables"]) >= 2
    assert all(Path(path).exists() for path in payload["csv_tables"])
    assert Path(payload["markdown_summary"]).exists()
    assert len(payload["plots"]) >= 3
    assert all(Path(path).exists() for path in payload["plots"])


def test_combined_benchmark_sizes() -> None:
    rows = load_combined_benchmark()
    assert len(rows) == 80
    assert {row["slice"] for row in rows} == {"lexical", "semantic", "deductive", "relational"}
