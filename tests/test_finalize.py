from __future__ import annotations

from pathlib import Path

from prism.demo.demo_script_data import demo_script_payload
from prism.demo.presets import FINAL_DEMO_PRESETS, grouped_presets_payload, presets_payload
from prism.finalize.build_release import build_release
from prism.finalize.verify_release import verify_release


def test_final_demo_preset_structure() -> None:
    payload = presets_payload()
    assert len(payload) >= 8
    assert {preset.expected_route for preset in FINAL_DEMO_PRESETS} >= {"bm25", "dense", "kg", "hybrid"}
    first = payload[0]
    assert {"title", "query", "expected_route", "expected_evidence_source", "presenter_note", "category", "badge"} <= set(first)


def test_grouped_demo_preset_structure() -> None:
    grouped = grouped_presets_payload()
    assert {"lexical", "semantic", "deductive", "relational", "open-corpus", "hard-case"} <= set(grouped)
    assert all(rows for rows in grouped.values())


def test_demo_script_payload_shape() -> None:
    payload = demo_script_payload()
    assert payload["production_router"] == "computed_ras"
    assert "ras_v4" in payload["research_overlays"]
    assert payload["safe_fallback_sequence"]
    assert payload["script_steps"]


def test_release_build_artifact_structure(tmp_path: Path) -> None:
    status = build_release(tmp_path)
    assert status["production_router"] == "computed_ras"
    assert Path(status["generated_files"]["central_claim_summary"]).exists()
    assert Path(status["generated_files"]["demo_walkthrough_quick_reference"]).exists()
    assert Path(status["generated_files"]["ui_tour"]).exists()
    assert Path(status["generated_files"]["ras_math_guide"]).exists()
    assert Path(status["generated_files"]["ras_quick_reference"]).exists()
    assert Path(status["generated_files"]["artifact_manifest"]).exists()
    manifest = status["manifest"]
    assert manifest["critical_artifacts"]
    assert manifest["generated_release_artifacts"]
    assert "demo_walkthrough_quick_reference.md" in manifest["generated_release_artifacts"]
    assert "ras_math_guide.md" in manifest["generated_release_artifacts"]


def test_release_verifier_status_structure(tmp_path: Path) -> None:
    build_release(tmp_path)
    status = verify_release(tmp_path, build_if_missing=False)
    assert "ready" in status
    assert status["readiness"].keys() >= {"class_project_demo", "paper_draft_submission", "reproducibility_handoff"}
    assert "ras_v4" in status["analysis_only"]
    assert (tmp_path / "release_status.json").exists()
    assert (tmp_path / "release_checklist.md").exists()
    assert any(row["name"] == "ui_tour" for row in status["release_components"])
    assert any(row["name"] == "ras_quick_reference" for row in status["release_components"])
