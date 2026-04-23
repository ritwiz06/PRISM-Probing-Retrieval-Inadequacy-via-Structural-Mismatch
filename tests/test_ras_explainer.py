from __future__ import annotations

from pathlib import Path

from prism.ras_explainer.export_explainer_artifacts import export_explainer_artifacts, write_release_docs
from prism.ras_explainer.math_docs import ras_math_payload, sample_computed_ras_breakdown
from prism.ras_explainer.version_compare import build_version_comparison, explain_query


def test_ras_math_payload_structure() -> None:
    payload = ras_math_payload()
    assert payload["production_router"] == "computed_ras"
    assert {"computed_ras", "computed_ras_v2", "ras_v3", "ras_v4", "calibrated_rescue"} <= set(payload)
    assert "argmin" in str(payload["computed_ras"]["formula"])
    assert payload["ras_v4"]["evidence_feature_count"] > 0


def test_query_explanation_structure() -> None:
    explanation = explain_query("Which concept feels like RFC-7231 but is about worry?")
    assert explanation["computed_ras"]["selected_backend"]
    assert "computed_ras_v2" in explanation
    assert "route_votes" in explanation
    assert explanation["ambiguity_flag"]["status"] == "advisory_only"


def test_computed_ras_breakdown_structure() -> None:
    breakdown = sample_computed_ras_breakdown("RFC-7231")
    assert breakdown["score_convention"] == "lower is better"
    assert breakdown["selected_backend"] in {"bm25", "dense", "kg", "hybrid"}
    assert set(breakdown["scores"]) == {"bm25", "dense", "kg", "hybrid"}


def test_version_comparison_structure() -> None:
    comparison = build_version_comparison()
    names = {row["name"] for row in comparison["versions"]}
    assert {"computed_ras", "computed_ras_v2", "ras_v3", "ras_v4", "calibrated_rescue"} <= names
    assert comparison["promotion_decision"]


def test_explainer_export_without_sensitivity(tmp_path: Path) -> None:
    release_dir = tmp_path / "release"
    eval_dir = tmp_path / "eval"
    summary = export_explainer_artifacts(release_dir=release_dir, eval_dir=eval_dir, include_sensitivity=False)
    assert summary["production_router"] == "computed_ras"
    assert (release_dir / "ras_overview.md").exists()
    assert (release_dir / "ras_math_guide.md").exists()
    assert (release_dir / "ras_quick_reference.md").exists()
    assert (eval_dir / "ras_explainer_summary.json").exists()


def test_write_release_docs_structure(tmp_path: Path) -> None:
    docs = write_release_docs(tmp_path)
    assert {"ras_overview", "ras_math_guide", "ras_version_comparison", "ras_visual_explanation", "ras_quick_reference"} <= set(docs)
    assert all(Path(path).exists() for path in docs.values())
