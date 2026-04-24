# Process Guide: UI Polish and Guided Demo Layer

## Basic Summary

This pass makes the existing PRISM Streamlit app presenter-friendly without changing routing, retrieval, benchmark labels, or scientific claims. The production router remains `computed_ras`. `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, and optional LLM routing remain clearly labeled research overlays.

The UI now emphasizes interpretation: what query was asked, which bounded corpus is being used, why a backend was selected, what evidence supports the answer, and how to present the system live.

## Improved Visual Hierarchy

The app uses reusable UI helpers in `prism/demo/ui_components.py`.

Core presentation components:

- Hero panel for the project thesis and production/research distinction.
- Card layout for route status, evidence status, benchmark results, human-eval highlights, and release status.
- Route badges for `bm25`, `dense`, `kg`, and `hybrid`.
- Mode badges that distinguish production `computed_ras` from research overlays.
- Step headers for the main query flow.
- Evidence cards with rank, score, source type, backend label, and snippet.
- Info and warning cards for optional or unavailable features.

The main `Demo / Query` tab now follows a four-step flow:

1. Query + Corpus.
2. Route Decision.
3. Evidence.
4. Answer + Trace.

This makes the demo easier for a first-time viewer to follow and keeps evidence/provenance visible before the final answer.

## Walkthrough Page

The new `Guided Demo` tab is designed for live presentation.

It includes:

- A short explanation of what PRISM is.
- A live demo sequence with exact preset names.
- What to show for each step.
- A talk track for each step.
- A safe fallback flow for benchmark mode.
- A tab map explaining what each UI page is for.

The fallback sequence stays in benchmark mode and avoids optional dependencies such as source packs, URL fetching, query-local graph extraction, or local LLM runtime.

## Preset Grouping

`DemoPreset` now includes two additive metadata fields:

- `category`: presentation grouping, such as `lexical`, `semantic`, `deductive`, `relational`, `open-corpus`, or `hard-case`.
- `badge`: compact UI label, such as `Exact ID`, `Conceptual`, `Bridge`, or `Boundary`.

These fields do not change query behavior. They only improve sidebar grouping, presenter readability, and release documentation.

## Fallback And Empty States

The UI is defensive around optional or partial artifacts.

Handled cases:

- Missing human-eval or paper artifacts show explanatory info cards.
- No query-local graph shows a clear text-evidence fallback.
- Open-corpus URL/local-folder failures show a safe fallback message.
- Optional LLM remains labeled as optional and unavailable unless a local endpoint exists.
- Benchmark mode remains the default safe path.

## Generated Artifacts

The final release builder now generates and verifies:

- `data/final_release/demo_walkthrough_quick_reference.md`
- `data/final_release/ui_tour.md`

Existing final release artifacts are preserved:

- `data/final_release/final_project_overview.md`
- `data/final_release/paper_ready_summary.md`
- `data/final_release/demo_runbook.md`
- `data/final_release/reproducibility_runbook.md`
- `data/final_release/central_claim_summary.md`
- `data/final_release/artifact_manifest.json`
- `data/final_release/known_results_summary.json`
- `data/final_release/release_status.json`
- `data/final_release/release_checklist.md`

## What Remains Unresolved

- Visual quality should still be reviewed manually in a browser before a final live presentation.
- Streamlit gives limited low-level layout control compared with a custom frontend.
- Open-corpus mode remains bounded source-pack/local-corpus QA, not arbitrary web-scale search.
- RAS_V3 and RAS_V4 remain analysis-only because current recorded results do not justify replacing production `computed_ras`.
- Calibrated rescue remains useful on hard cases but is still a research/demo overlay.

## Concepts And Topics Used

- Streamlit layout and styling.
- Presenter-focused information hierarchy.
- Representation-aware routing.
- Production vs research-mode separation.
- Evidence-first answer presentation.
- Human-eval result summarization.
- Release artifact generation and verification.
- Graceful empty-state and fallback design.
