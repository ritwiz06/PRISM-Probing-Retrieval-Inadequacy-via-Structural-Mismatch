from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from prism.demo.demo_script_data import demo_script_payload
from prism.demo.presets import presets_payload
from prism.open_corpus.source_packs import list_source_packs
from prism.ras_explainer.export_explainer_artifacts import write_release_docs
from prism.utils import read_json, write_json

FINAL_RELEASE_DIR = Path("data/final_release")

CRITICAL_ARTIFACTS: dict[str, str] = {
    "curated_end_to_end": "data/eval/end_to_end_verification.json",
    "external_mini": "data/eval/external_generalization_summary.md",
    "generalization_v2": "data/eval/generalization_v2_summary.md",
    "structure_shift": "data/eval/structure_shift_summary.md",
    "public_raw": "data/eval/public_corpus_eval_summary.md",
    "public_graph": "data/eval/public_graph_eval_summary.md",
    "adversarial": "data/eval/adversarial_eval_summary.md",
    "calibration": "data/eval/calibrated_router_summary.md",
    "ras_v3": "data/eval/ras_v3_eval_summary.md",
    "ras_v4": "data/eval/ras_v4_eval_summary.md",
    "human_eval": "data/human_eval/human_eval_summary.md",
    "comparative_human_eval": "data/human_eval/comparative_summary.md",
    "open_corpus": "data/eval/open_workspace_summary.md",
    "report_artifacts": "data/eval/report/prism_report_summary.md",
    "demo_app": "prism/demo/app.py",
}

OPTIONAL_ARTIFACTS: dict[str, str] = {
    "llm_experiments": "data/eval/llm_router_eval_summary.md",
    "ras_v4_vs_human": "data/human_eval/ras_v4_vs_human_summary.md",
    "ras_v4_vs_rescue": "data/eval/ras_v4_vs_rescue_summary.md",
    "release_plots_ras_v4": "data/eval/ras_v4_router_comparison.png",
}


def build_release(output_dir: str | Path = FINAL_RELEASE_DIR) -> dict[str, object]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    results = _known_results()
    manifest = _artifact_manifest(target)
    files = {
        "final_project_overview": target / "final_project_overview.md",
        "paper_ready_summary": target / "paper_ready_summary.md",
        "demo_runbook": target / "demo_runbook.md",
        "demo_walkthrough_quick_reference": target / "demo_walkthrough_quick_reference.md",
        "ui_tour": target / "ui_tour.md",
        "ras_overview": target / "ras_overview.md",
        "ras_math_guide": target / "ras_math_guide.md",
        "ras_version_comparison": target / "ras_version_comparison.md",
        "ras_visual_explanation": target / "ras_visual_explanation.md",
        "ras_quick_reference": target / "ras_quick_reference.md",
        "reproducibility_runbook": target / "reproducibility_runbook.md",
        "central_claim_summary": target / "central_claim_summary.md",
        "artifact_manifest": target / "artifact_manifest.json",
        "known_results_summary": target / "known_results_summary.json",
    }
    files["final_project_overview"].write_text(_final_project_overview(results), encoding="utf-8")
    files["paper_ready_summary"].write_text(_paper_ready_summary(results), encoding="utf-8")
    files["demo_runbook"].write_text(_demo_runbook(), encoding="utf-8")
    files["demo_walkthrough_quick_reference"].write_text(_demo_walkthrough_quick_reference(), encoding="utf-8")
    files["ui_tour"].write_text(_ui_tour(), encoding="utf-8")
    write_release_docs(target)
    files["reproducibility_runbook"].write_text(_reproducibility_runbook(), encoding="utf-8")
    files["central_claim_summary"].write_text(_central_claim_summary(results), encoding="utf-8")
    write_json(files["artifact_manifest"], manifest)
    write_json(files["known_results_summary"], results)
    status = {
        "output_dir": str(target),
        "production_router": "computed_ras",
        "research_overlays": ["calibrated_rescue", "classifier_router", "ras_v3", "ras_v4", "optional_llm"],
        "generated_files": {name: str(path) for name, path in files.items()},
        "manifest": manifest,
        "known_results": results,
        "readiness": {
            "class_project_demo": "ready",
            "paper_draft_submission": "ready_with_caveats",
            "reproducibility_handoff": "ready",
        },
    }
    write_json(target / "release_status.json", status)
    (target / "release_checklist.md").write_text(_release_checklist(status), encoding="utf-8")
    print(
        "final_release_built "
        f"output_dir={target} production_router=computed_ras "
        f"class_demo={status['readiness']['class_project_demo']} paper={status['readiness']['paper_draft_submission']}"
    )
    return status


def _known_results() -> dict[str, object]:
    results: dict[str, object] = {
        "production_router": "computed_ras",
        "production_decision": "computed_ras remains production default",
        "research_overlays": ["calibrated_rescue", "ras_v3", "ras_v4", "classifier_router", "optional_llm"],
        "source_pack_names": list_source_packs(),
    }
    _merge_if_json(results, "curated", "data/eval/end_to_end_verification.json", ["total", "route_accuracy", "evidence_hit_at_k", "answer_matches", "passed"])
    _merge_external_mini(results)
    _merge_system_metric(results, "generalization_v2", "data/eval/generalization_v2.json", ("noisy", "test", "computed_ras"))
    _merge_system_metric(results, "public_raw", "data/eval/public_corpus_eval.json", ("test", "computed_ras"))
    _merge_system_metric(results, "adversarial", "data/eval/adversarial_eval.json", ("combined", "computed_ras"))
    _merge_system_metric(results, "calibrated_adversarial_test", "data/eval/calibrated_router.json", ("adversarial_test", "computed_ras_calibrated_topk_rescue"))
    _merge_system_metric(results, "ras_v3_adversarial_test", "data/eval/ras_v3_eval.json", ("adversarial_test", "ras_v3"))
    _merge_system_metric(results, "ras_v4_adversarial_test", "data/eval/ras_v4_eval.json", ("adversarial_test", "ras_v4"))
    _merge_system_metric(results, "ras_v4_rescue_adversarial_test", "data/eval/ras_v4_eval.json", ("adversarial_test", "ras_v4_rescue"))
    _merge_if_json(results, "human_eval", "data/human_eval/human_eval_summary.json", ["status", "packet_size", "annotation_count", "evaluator_count"])
    _merge_if_json(results, "comparative_human_eval", "data/human_eval/comparative_summary.json", ["status", "packet_size", "annotation_count", "evaluator_count"])
    _merge_if_json(results, "open_corpus_smoke", "data/eval/open_corpus_smoke.json", ["status"])
    return results


def _merge_if_json(target: dict[str, object], key: str, path: str, fields: list[str]) -> None:
    file_path = Path(path)
    if not file_path.exists():
        target[key] = {"status": "missing", "path": path}
        return
    try:
        payload = read_json(file_path)
    except (json.JSONDecodeError, OSError):
        target[key] = {"status": "unreadable", "path": path}
        return
    if isinstance(payload, dict):
        target[key] = {field: payload.get(field) for field in fields if field in payload} | {"path": path}
    else:
        target[key] = {"status": "non_dict", "path": path}


def _merge_system_metric(target: dict[str, object], key: str, path: str, lookup: tuple[str, ...]) -> None:
    file_path = Path(path)
    if not file_path.exists():
        target[key] = {"status": "missing", "path": path}
        return
    try:
        payload: Any = read_json(file_path)
        current: Any = payload.get("systems", payload)
        for part in lookup:
            current = current[part]
        if isinstance(current, dict):
            target[key] = {
                "route_accuracy": current.get("route_accuracy"),
                "answer_accuracy": current.get("answer_accuracy"),
                "evidence_hit_at_k": current.get("evidence_hit_at_k"),
                "top1_evidence_hit": current.get("top1_evidence_hit"),
                "path": path,
            }
        else:
            target[key] = {"status": "unexpected_shape", "path": path}
    except (KeyError, TypeError, json.JSONDecodeError, OSError):
        target[key] = {"status": "lookup_failed", "path": path, "lookup": list(lookup)}


def _merge_external_mini(target: dict[str, object]) -> None:
    path = "data/eval/external_generalization.json"
    file_path = Path(path)
    if not file_path.exists():
        target["external_mini"] = {"status": "missing", "path": path}
        return
    try:
        payload = read_json(file_path)
        system = payload["systems"]["computed_ras"]
        dense = payload.get("dense_backend_status", {})
        target["external_mini"] = {
            "total": payload.get("benchmark", {}).get("total"),
            "route_accuracy": system.get("route_accuracy"),
            "answer_accuracy": system.get("answer_accuracy"),
            "dense_backend": dense.get("active_backend"),
            "path": path,
        }
    except (KeyError, TypeError, json.JSONDecodeError, OSError):
        target["external_mini"] = {"status": "lookup_failed", "path": path}


def _artifact_manifest(output_dir: Path) -> dict[str, object]:
    critical = [{"name": name, "path": path, "exists": Path(path).exists(), "required": True} for name, path in CRITICAL_ARTIFACTS.items()]
    optional = [{"name": name, "path": path, "exists": Path(path).exists(), "required": False} for name, path in OPTIONAL_ARTIFACTS.items()]
    return {
        "output_dir": str(output_dir),
        "production_router": "computed_ras",
        "critical_artifacts": critical,
        "optional_artifacts": optional,
        "generated_release_artifacts": [
            "final_project_overview.md",
            "paper_ready_summary.md",
            "demo_runbook.md",
            "demo_walkthrough_quick_reference.md",
            "ui_tour.md",
            "ras_overview.md",
            "ras_math_guide.md",
            "ras_version_comparison.md",
            "ras_visual_explanation.md",
            "ras_quick_reference.md",
            "reproducibility_runbook.md",
            "central_claim_summary.md",
            "artifact_manifest.json",
            "known_results_summary.json",
            "release_checklist.md",
            "release_status.json",
        ],
    }


def _final_project_overview(results: dict[str, object]) -> str:
    return f"""# Final PRISM Project Overview

PRISM is a representation-aware retrieval system that routes each query to BM25, Dense, KG, or Hybrid retrieval using computed RAS as the production router.

Production router: `computed_ras`.

Research overlays: `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, and optional local LLM experiments. These are comparison layers unless explicitly enabled in a research/demo mode.

Current release posture:

- Class/project demo: ready.
- Paper draft package: ready with caveats.
- Reproducibility handoff: ready.

Known result snapshot:

```json
{json.dumps(results, indent=2)}
```
"""


def _paper_ready_summary(results: dict[str, object]) -> str:
    return f"""# Paper-Ready Summary

PRISM tests the claim that retrieval failures often come from structural mismatch between the query and the retrieval representation. Computed RAS operationalizes this by estimating which representation is adequate for a query and routing to BM25, Dense, KG, or Hybrid.

RAS_V3 formalizes route adequacy as an interpretable feature-based model. RAS_V4 extends this to joint route-and-evidence adequacy by adding evidence diagnostics from top-k retrieval. The key empirical finding is honest: route adequacy helps and remains interpretable, but route-only adequacy is insufficient on hard adversarial cases. Calibrated top-k rescue remains complementary and stronger on adversarial answer accuracy.

Human evaluation with four annotators supports the usefulness of PRISM's evidence and trace presentation, while comparative results retain ties and adjudication cases. The project should not claim that RAS_V3 or RAS_V4 replace computed RAS in production. Instead, the publishable story is that RAS provides a transparent framework for representation-aware routing, and RAS_V4 exposes why answer support must be modeled alongside route choice.

Relevant result snapshot:

```json
{json.dumps(results, indent=2)}
```
"""


def _demo_runbook() -> str:
    script = demo_script_payload()
    return f"""# Demo Runbook

## Launch

```bash
.venv/bin/python3 -m streamlit run prism/demo/app.py
```

## Default Demo Rule

Benchmark mode is the most reproducible path. Production mode is `computed_ras`.

## Demonstration Flow

1. Run `Lexical: exact RFC identifier` and show parsed query features, RAS scores, BM25 evidence, answer, and trace.
2. Run `Semantic: paraphrased feeling` and show Dense evidence.
3. Run `Deductive: animal capability` and show KG evidence.
4. Run `Relational: bridge path` and show Hybrid evidence.
5. Switch to `source-pack mode` with `Open Corpus: source-pack climate anxiety` if source packs are available.
6. Run `Hard Case: misleading exact term` to compare the production router with research overlays.

## Fallback

If source packs, optional LLM, URL fetching, or graph extraction are unavailable, the benchmark sequence remains fully reproducible: {", ".join(script["safe_fallback_sequence"])}.

## Presets

```json
{json.dumps(script["presets"], indent=2)}
```
"""


def _demo_walkthrough_quick_reference() -> str:
    script = demo_script_payload()
    steps = "\n".join(
        (
            f"{row['step']}. **{row['title']}**\n"
            f"   - Mode: `{row['mode']}`\n"
            f"   - Preset: `{row['preset']}`\n"
            f"   - Show: {', '.join(str(item) for item in row.get('show', []))}\n"
            f"   - Narrative: {row['talk_track']}"
        )
        for row in script["script_steps"]
    )
    return f"""# Demo Walkthrough Quick Reference

This one-page sequence supports a compact live demonstration. Start in benchmark mode for the most reproducible path; switch to open-corpus mode only when source-pack behavior is part of the story.

Production router: `computed_ras`.

Research overlays: `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, and optional local LLM. These are comparison layers, not the production default.

## Live Sequence

{steps}

## Safe Fallback

If source packs, optional LLM, URL fetching, or query-local graph extraction are unavailable, stay in benchmark mode and run:

{", ".join(f"`{item}`" for item in script["safe_fallback_sequence"])}

## Presentation Cues

- Show route scores before evidence so the audience understands the routing decision.
- Show evidence before answer so support and provenance remain visible.
- Keep the distinction clear: computed RAS is production; rescue, classifier, RAS_V3, RAS_V4, and LLM are research overlays.
- Open-corpus mode is bounded source-pack/local-corpus QA, not arbitrary web-scale search.
"""


def _ui_tour() -> str:
    return """# PRISM UI Tour

The Streamlit app is organized as a polished research workspace.

## Guided Demo

This page presents a clean walkthrough of the main demonstration scenarios, with optional presenter notes hidden behind an explicit toggle.

## Demo / Query

The main production path. It is organized into four visible steps:

- Query + Corpus: shows the user query, selected source mode, and production-router reminder.
- Route Decision: shows computed RAS route scores, the selected backend, route margin, and benchmark route status where available.
- Evidence: shows ranked evidence cards with backend/source badges and provenance metadata.
- Answer + Trace: shows the final answer and structured reasoning trace.

## RAS Explainer

Explains what Representation Adequacy Score means, how `computed_ras`, `computed_ras_v2`, `ras_v3`, and `ras_v4` differ, and why calibrated rescue is an overlay rather than a production router. It includes a stepwise routing walkthrough, route-score charts, query-level feature inspection, version votes, and advisory ambiguity flags.

## Open Corpus

Shows bounded source-pack, local-folder, URL-list, or bundled local-demo runtime-corpus metadata. It reports document count, source types, index readiness, and query-local graph availability.

## Compare Routers

Shows production `computed_ras` beside research overlays: calibrated rescue, classifier router, RAS_V3, RAS_V4, and optional LLM routing if available.

## Evidence / Graph

Shows full ranked evidence, backend-specific metadata, and query-local graph/path evidence when extracted.

## Human Eval

Shows real standard and comparative annotation summaries, including evaluator count, packet sizes, human-score charts, and comparative preference tables.

## Results / Paper

Shows the final paper-facing story, benchmark snapshot, central claim, RAS_V4 caveats, and report artifacts.

## Empty-State Behavior

If optional artifacts are missing, the UI displays explanatory panels instead of blank sections. Benchmark mode remains the safe default.
"""


def _reproducibility_runbook() -> str:
    commands = [
        ".venv/bin/python3 -m pip install -e .",
        ".venv/bin/python3 -m pytest -q",
        ".venv/bin/python3 -m prism.ingest.build_corpus",
        ".venv/bin/python3 -m prism.ingest.build_kg",
        ".venv/bin/python3 -m prism.eval.verify_end_to_end",
        ".venv/bin/python3 -m prism.external_benchmarks.verify_generalization",
        ".venv/bin/python3 -m prism.generalization.verify_generalization_v2",
        ".venv/bin/python3 -m prism.kg_extraction.verify_structure_shift",
        ".venv/bin/python3 -m prism.public_corpus.verify_public_corpus",
        ".venv/bin/python3 -m prism.public_graph.verify_public_graph",
        ".venv/bin/python3 -m prism.adversarial.verify_adversarial",
        ".venv/bin/python3 -m prism.calibration.verify_calibrated_router",
        ".venv/bin/python3 -m prism.human_eval.analyze_annotations",
        ".venv/bin/python3 -m prism.human_eval.compare_annotations",
        ".venv/bin/python3 -m prism.open_corpus.verify_open_corpus",
        ".venv/bin/python3 -m prism.ras_v3.verify_ras_v3",
        ".venv/bin/python3 -m prism.ras_v4.verify_ras_v4",
        ".venv/bin/python3 -m prism.analysis.report_artifacts",
        ".venv/bin/python3 -m prism.finalize.build_release",
        ".venv/bin/python3 -m prism.finalize.verify_release",
    ]
    return "# Reproducibility Runbook\n\nRun these commands from the repo root:\n\n" + "\n".join(f"```bash\n{command}\n```" for command in commands) + "\n\nRuntime corpora are under `data/runtime_corpora/`. Human-eval inputs and summaries are under `data/human_eval/`."


def _central_claim_summary(results: dict[str, object]) -> str:
    return f"""# Central Claim Summary

PRISM's central contribution is representation-aware routing: a query should be routed to the retrieval representation whose structure is adequate for the requested evidence. Exact identifiers fit BM25, conceptual paraphrases fit Dense, deductive membership/property questions fit KG, and relational bridge questions fit Hybrid.

The final results support a more nuanced thesis:

- Route adequacy matters and computed RAS is reliable on curated, external, public raw, and generalization benchmarks.
- Route-only adequacy is not sufficient on hard adversarial route-boundary cases.
- RAS_V3 makes route adequacy more formal and interpretable.
- RAS_V4 is more publishable as a research model because it decomposes route adequacy and evidence adequacy.
- Calibrated top-k rescue remains complementary: it improves hard-case answer accuracy by recovering answer-bearing evidence after retrieval.
- Human evaluation supports the faithfulness/usefulness story, but ties and adjudication cases should stay visible.

Production router remains `computed_ras`. RAS_V3, RAS_V4, calibrated rescue, classifier routing, and optional LLM experiments are research overlays.

This is source-pack/open-corpus QA over bounded user-selected corpora, not arbitrary web-scale open-domain QA.

Selected known results:

```json
{json.dumps(results, indent=2)}
```
"""


def _release_checklist(status: dict[str, object]) -> str:
    manifest = status["manifest"]
    critical = manifest["critical_artifacts"]
    optional = manifest["optional_artifacts"]
    missing_critical = [row for row in critical if not row["exists"]]
    lines = [
        "# Release Checklist",
        "",
        f"Production router: `{status['production_router']}`.",
        "",
        "## Readiness",
        "",
        f"- Class/project demo: `{status['readiness']['class_project_demo']}`",
        f"- Paper draft submission: `{status['readiness']['paper_draft_submission']}`",
        f"- Reproducibility handoff: `{status['readiness']['reproducibility_handoff']}`",
        "",
        "## Critical Artifacts",
        "",
    ]
    lines.extend(f"- [{'x' if row['exists'] else ' '}] {row['name']}: `{row['path']}`" for row in critical)
    lines.extend(["", "## Optional Artifacts", ""])
    lines.extend(f"- [{'x' if row['exists'] else ' '}] {row['name']}: `{row['path']}`" for row in optional)
    lines.extend(["", "## Limitations", ""])
    lines.append("- RAS_V3 and RAS_V4 remain analysis-only.")
    lines.append("- Calibrated rescue is a research/demo comparison overlay unless explicitly enabled.")
    lines.append("- Open-corpus mode is bounded source-pack/local-corpus QA, not web-scale QA.")
    if missing_critical:
        lines.extend(["", "## Missing Critical Items", ""])
        lines.extend(f"- {row['name']}: `{row['path']}`" for row in missing_critical)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the final PRISM release package.")
    parser.add_argument("--output-dir", default=str(FINAL_RELEASE_DIR))
    args = parser.parse_args()
    build_release(args.output_dir)


if __name__ == "__main__":
    main()
