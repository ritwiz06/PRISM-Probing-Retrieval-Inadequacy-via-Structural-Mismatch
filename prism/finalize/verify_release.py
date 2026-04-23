from __future__ import annotations

import argparse
from pathlib import Path

from prism.finalize.build_release import CRITICAL_ARTIFACTS, FINAL_RELEASE_DIR, OPTIONAL_ARTIFACTS, build_release
from prism.utils import read_json, write_json


def verify_release(output_dir: str | Path = FINAL_RELEASE_DIR, *, build_if_missing: bool = True) -> dict[str, object]:
    target = Path(output_dir)
    if build_if_missing and not (target / "artifact_manifest.json").exists():
        build_release(target)
    target.mkdir(parents=True, exist_ok=True)
    critical_rows = _rows(CRITICAL_ARTIFACTS, required=True)
    optional_rows = _rows(OPTIONAL_ARTIFACTS, required=False)
    release_rows = _rows(
        {
            "final_project_overview": str(target / "final_project_overview.md"),
            "paper_ready_summary": str(target / "paper_ready_summary.md"),
            "demo_runbook": str(target / "demo_runbook.md"),
            "demo_walkthrough_quick_reference": str(target / "demo_walkthrough_quick_reference.md"),
            "ui_tour": str(target / "ui_tour.md"),
            "ras_overview": str(target / "ras_overview.md"),
            "ras_math_guide": str(target / "ras_math_guide.md"),
            "ras_version_comparison": str(target / "ras_version_comparison.md"),
            "ras_visual_explanation": str(target / "ras_visual_explanation.md"),
            "ras_quick_reference": str(target / "ras_quick_reference.md"),
            "reproducibility_runbook": str(target / "reproducibility_runbook.md"),
            "central_claim_summary": str(target / "central_claim_summary.md"),
            "artifact_manifest": str(target / "artifact_manifest.json"),
            "known_results_summary": str(target / "known_results_summary.json"),
        },
        required=True,
    )
    missing_critical = [row for row in critical_rows + release_rows if not row["exists"]]
    status = {
        "production_router": "computed_ras",
        "research_overlays": ["calibrated_rescue", "classifier_router", "ras_v3", "ras_v4", "optional_llm"],
        "ready": not missing_critical,
        "readiness": {
            "class_project_demo": "ready" if not missing_critical else "blocked",
            "paper_draft_submission": "ready_with_caveats" if not missing_critical else "blocked",
            "reproducibility_handoff": "ready" if not missing_critical else "blocked",
        },
        "critical_components": critical_rows,
        "optional_components": optional_rows,
        "release_components": release_rows,
        "missing_critical": missing_critical,
        "analysis_only": ["calibrated_rescue", "classifier_router", "ras_v3", "ras_v4", "optional_llm"],
        "limitations": [
            "RAS_V3 and RAS_V4 are not production replacements.",
            "Calibrated rescue is not the default production path.",
            "Open-corpus mode is bounded source-pack/local-corpus QA, not web-scale search.",
            "Optional local LLM results depend on local runtime availability.",
        ],
    }
    write_json(target / "release_status.json", status)
    (target / "release_checklist.md").write_text(_markdown(status), encoding="utf-8")
    print(
        "release_verified "
        f"ready={status['ready']} class_demo={status['readiness']['class_project_demo']} "
        f"paper={status['readiness']['paper_draft_submission']} handoff={status['readiness']['reproducibility_handoff']} "
        f"missing_critical={len(missing_critical)}"
    )
    return status


def _rows(paths: dict[str, str], *, required: bool) -> list[dict[str, object]]:
    rows = []
    for name, path in paths.items():
        file_path = Path(path)
        rows.append({"name": name, "path": path, "exists": file_path.exists(), "required": required})
    return rows


def _markdown(status: dict[str, object]) -> str:
    lines = [
        "# Release Checklist",
        "",
        f"Release ready: `{status['ready']}`.",
        f"Production router: `{status['production_router']}`.",
        "",
        "## Readiness",
        "",
        f"- Class/project demo: `{status['readiness']['class_project_demo']}`",
        f"- Paper draft submission: `{status['readiness']['paper_draft_submission']}`",
        f"- Reproducibility handoff: `{status['readiness']['reproducibility_handoff']}`",
        "",
        "## Critical Components",
        "",
    ]
    lines.extend(f"- [{'x' if row['exists'] else ' '}] {row['name']}: `{row['path']}`" for row in status["critical_components"])
    lines.extend(["", "## Release Package Components", ""])
    lines.extend(f"- [{'x' if row['exists'] else ' '}] {row['name']}: `{row['path']}`" for row in status["release_components"])
    lines.extend(["", "## Optional Components", ""])
    lines.extend(f"- [{'x' if row['exists'] else ' '}] {row['name']}: `{row['path']}`" for row in status["optional_components"])
    lines.extend(["", "## Analysis-Only Components", ""])
    lines.extend(f"- `{name}`" for name in status["analysis_only"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in status["limitations"])
    if status["missing_critical"]:
        lines.extend(["", "## Missing Critical Components", ""])
        lines.extend(f"- {row['name']}: `{row['path']}`" for row in status["missing_critical"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the final PRISM release package.")
    parser.add_argument("--output-dir", default=str(FINAL_RELEASE_DIR))
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    verify_release(args.output_dir, build_if_missing=not args.no_build)


if __name__ == "__main__":
    main()
