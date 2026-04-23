# PROCESS GUIDE 2026-04-22 14:21 - Final Release Layer

## Basic Summary

This finalization pass turns PRISM into a polished demo and paper package without changing the core method. The production router remains `computed_ras`. Calibrated rescue, classifier routing, RAS_V3, RAS_V4, and optional local LLM routing are visible research overlays, not silent production replacements.

## How The Final Demo Modes Work

The Streamlit app now has top-level tabs:

- `Demo / Query`: primary query flow with selected backend, RAS scores, answer, and trace.
- `Open Corpus`: source-pack, local-folder, local-demo, and URL-list runtime corpus metadata.
- `Compare Routers`: production vs research routing modes.
- `Evidence / Graph`: retrieved evidence, backend metadata, and query-local graph/path view.
- `Human Eval`: standard/comparative human-eval summaries.
- `Results / Paper`: final-release central claim and report summaries.

Benchmark mode remains the default safe path. Open-corpus modes are additive and keep runtime corpora under `data/runtime_corpora/`.

## How Presets Work

Demo presets live in `prism/demo/presets.py`. Each preset includes:

- title
- query
- expected route
- expected evidence source
- presenter note
- intended demo mode
- safe-fallback flag

The presenter walkthrough lives in `prism/demo/demo_script_data.py`. It defines a short sequence that covers lexical, semantic, deductive, relational, open-corpus, and hard-case examples. The safe fallback sequence uses benchmark mode only.

## How Open-Corpus UI Support Works

The open-corpus view model accepts:

- built-in source packs
- bundled local demo folder
- user-provided local folder path
- small URL list

Runtime metadata exposes corpus name, document count, source types, index status, graph availability, selected backend, top evidence, route comparisons, and routing-mode comparisons. If URL fetching fails or no folder/URL is provided, the UI falls back to the bundled local demo corpus and shows a warning instead of crashing.

## How The Release Package Is Built

Run:

```bash
.venv/bin/python3 -m prism.finalize.build_release
```

This writes `data/final_release/` with:

- `final_project_overview.md`
- `paper_ready_summary.md`
- `demo_runbook.md`
- `reproducibility_runbook.md`
- `central_claim_summary.md`
- `artifact_manifest.json`
- `known_results_summary.json`
- `release_checklist.md`
- `release_status.json`

The package includes the main thesis, production-vs-research mode distinction, demo flow, reproducibility commands, artifact paths, current results, and known limitations.

## How Release Verification Works

Run:

```bash
.venv/bin/python3 -m prism.finalize.verify_release
```

The verifier checks:

- curated benchmark artifacts
- external mini-benchmark artifacts
- generalization_v2 artifacts
- structure-shift artifacts
- public raw and public graph artifacts
- adversarial and calibration artifacts
- RAS_V3 and RAS_V4 summaries
- human-eval and comparative human-eval summaries
- open-corpus summaries
- report artifacts
- demo app availability
- generated release package files

It reports readiness for class/project demo, paper draft submission, and reproducibility handoff. Current status: class demo `ready`, paper draft `ready_with_caveats`, reproducibility handoff `ready`.

## Artifacts Generated

- `data/final_release/final_project_overview.md`
- `data/final_release/paper_ready_summary.md`
- `data/final_release/demo_runbook.md`
- `data/final_release/reproducibility_runbook.md`
- `data/final_release/central_claim_summary.md`
- `data/final_release/artifact_manifest.json`
- `data/final_release/known_results_summary.json`
- `data/final_release/release_checklist.md`
- `data/final_release/release_status.json`

## What Remains Unresolved

RAS_V3 and RAS_V4 are not promoted to production. Calibrated rescue remains stronger on adversarial answer accuracy, but it is still a research/demo overlay. Open-corpus mode is useful for bounded source packs and local documents, not arbitrary web-scale QA. Optional LLM experiments depend on whether a local LLM runtime is available.

## Concepts and Topics Used

- final demo workflow
- production-vs-research mode separation
- representation-aware routing
- computed RAS production guardrail
- calibrated rescue overlay
- RAS_V3 route adequacy
- RAS_V4 route-and-evidence adequacy
- source-pack/open-corpus QA
- query-local graph inspection
- human-eval reporting
- release artifact manifest
- reproducibility handoff
