# PRISM

**PRISM** is a representation-aware question answering system that routes each query to the retrieval representation that best matches its structure.

Instead of forcing every question through one retrieval pipeline, PRISM chooses among:

- `BM25` for lexical and identifier-heavy lookups
- `Dense` retrieval for semantic and paraphrastic queries
- `KG` retrieval for deductive and class/property reasoning
- `Hybrid` retrieval for relational or multi-hop cases

The project’s central idea is that **retrieval failure is often a structural mismatch problem**, not just a ranking problem. PRISM operationalizes that idea with a family of routing methods built around the **Representation Adequacy Score (RAS)**.

## Status

- Production router: `computed_ras`
- Research overlays: `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, optional local LLM experiments
- Demo app: ready
- Release package: ready
- Reproducibility handoff: ready

PRISM is intentionally positioned as **representation-aware QA over benchmark corpora, source packs, and runtime corpora**. It is **not** an arbitrary web-scale search engine.

## Why PRISM

A single retrieval strategy is rarely optimal across all query types.

- Exact identifiers such as RFC numbers and medical codes benefit from lexical matching.
- Conceptual or paraphrased questions benefit from dense semantic retrieval.
- Deductive questions benefit from structured graph reasoning.
- Relational bridge questions often require combined evidence.

PRISM makes that routing decision explicit, inspectable, and measurable.

## Core Contributions

- A multi-representation QA system with `BM25`, `Dense`, `KG`, and `Hybrid` backends
- A production routing policy based on `computed_ras`
- Benchmark layers for curated, held-out, public-source, adversarial, and open-corpus evaluation
- Calibration and rescue overlays for hard ambiguity cases
- Human-evaluation and comparative human-evaluation pipelines
- Open-corpus and source-pack support for reusable bounded-domain QA
- A Streamlit demo workspace with guided walkthroughs, RAS explainability, and executive summary views
- A final release package under [`data/final_release/`](data/final_release)

## Architecture

At a high level, PRISM follows this flow:

1. Parse query features.
2. Score route families with a representation-aware router.
3. Select a backend: `bm25`, `dense`, `kg`, or `hybrid`.
4. Retrieve evidence with provenance.
5. Generate an answer and reasoning trace grounded in retrieved evidence.
6. Expose route scores, evidence, and traces in the UI and evaluation artifacts.

The strongest high-level visual summaries live in:

- [`data/final_release/figures/architecture_diagram.png`](data/final_release/figures/architecture_diagram.png)
- [`data/final_release/figures/ras_family_overview.png`](data/final_release/figures/ras_family_overview.png)
- [`data/final_release/central_claim_summary.md`](data/final_release/central_claim_summary.md)

## Current Results Snapshot

These are the current recorded release-level headline results:

| Layer | Headline result |
| --- | --- |
| Curated end-to-end | `80/80`, route accuracy `1.000`, evidence hit@k `1.000` |
| External mini-benchmark | Answer accuracy `1.000` |
| Generalization v2 | Clean test `1.000`, noisy test `0.975` |
| Public raw-document benchmark | Test answer accuracy `1.000` |
| Public graph benchmark | Test answer accuracy `1.000` |
| Adversarial benchmark | Computed RAS test answer accuracy `0.917` |
| Calibrated rescue on adversarial test | Answer accuracy `0.958` |
| Open-corpus smoke evaluation | Passed |
| Human evaluation | 4 annotators, 36-item standard packet |
| Comparative human evaluation | 4 annotators, 28-item comparative packet |

Important interpretation:

- `computed_ras` remains the production router because it is the stable default across the benchmark stack.
- `calibrated_rescue` is stronger on adversarial answer accuracy, but it remains a research/demo overlay rather than the default production path.
- `ras_v3` and `ras_v4` improved interpretability and formalization, but they were **not promoted** to production.

For the full release summary, see:

- [`data/final_release/final_project_overview.md`](data/final_release/final_project_overview.md)
- [`data/final_release/final_wrapup_report.md`](data/final_release/final_wrapup_report.md)
- [`data/final_release/known_results_summary.json`](data/final_release/known_results_summary.json)

## Production vs Research Modes

PRISM keeps this distinction explicit:

### Production

- Router: `computed_ras`
- Goal: stable, explainable, benchmark-safe routing

### Research overlays

- `calibrated_rescue`
- `classifier_router`
- `ras_v3`
- `ras_v4`
- optional local LLM experiments

These layers are included for analysis, comparison, and demos. They are not presented as silent production replacements.

## Repository Highlights

### Main package

- [`prism/`](prism/) core package
- [`prism/demo/app.py`](prism/demo/app.py) Streamlit workspace
- [`prism/finalize/`](prism/finalize/) release build and verification tools
- [`prism/ras_v3/`](prism/ras_v3/) interpretable feature-based RAS model
- [`prism/ras_v4/`](prism/ras_v4/) joint route-and-evidence adequacy model
- [`prism/ras_explainer/`](prism/ras_explainer/) RAS explanation and export layer
- [`prism/open_corpus/`](prism/open_corpus/) runtime corpora and source packs
- [`prism/human_eval/`](prism/human_eval/) standard and comparative human-eval tooling

### Key artifact folders

- [`data/eval/`](data/eval/) evaluation outputs
- [`data/human_eval/`](data/human_eval/) annotation inputs and analysis
- [`data/runtime_corpora/`](data/runtime_corpora/) open-corpus artifacts
- [`data/final_release/`](data/final_release/) final project package

## Installation

PRISM targets **Python 3.11+**.

Recommended setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Developer dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Quickstart

Run the core local setup and smoke checks:

```bash
.venv/bin/python3 -m pip install -e .
.venv/bin/python3 -m pytest -q
.venv/bin/python3 -m prism.ingest.build_corpus
.venv/bin/python3 -m prism.ingest.build_kg
.venv/bin/python3 -m prism.eval.verify_end_to_end
```

Launch the demo app:

```bash
.venv/bin/python3 -m streamlit run prism/demo/app.py
```

## Reproducibility

The main reproducibility sequence is documented in:

- [`data/final_release/reproducibility_runbook.md`](data/final_release/reproducibility_runbook.md)

The full project release can be rebuilt with:

```bash
.venv/bin/python3 -m prism.analysis.report_artifacts
.venv/bin/python3 -m prism.finalize.build_release
.venv/bin/python3 -m prism.finalize.verify_release
```

## Demo and Presentation

PRISM includes a polished Streamlit workspace with:

- `Executive Summary`
- `Results at a Glance`
- `Guided Demo`
- `RAS Explainer`
- `Demo / Query`
- `Open Corpus`
- `Compare Routers`
- `Evidence / Graph`
- `Human Eval`
- `Results / Paper`

For live demos and presentation support, see:

- [`data/final_release/demo_runbook.md`](data/final_release/demo_runbook.md)
- [`data/final_release/demo_walkthrough_quick_reference.md`](data/final_release/demo_walkthrough_quick_reference.md)
- [`data/final_release/final_speaker_script.md`](data/final_release/final_speaker_script.md)
- [`data/final_release/one_minute_pitch.md`](data/final_release/one_minute_pitch.md)
- [`data/final_release/three_minute_pitch.md`](data/final_release/three_minute_pitch.md)

## Evaluation Layers

PRISM currently includes:

- curated end-to-end benchmark
- external mini-benchmark
- `generalization_v2` clean/noisy evaluation
- extracted KG / structure-shift evaluation
- public raw-document evaluation
- public graph grounding evaluation
- adversarial hard-case evaluation
- calibration / rescue evaluation
- human-eval and comparative human-eval analysis
- open-corpus smoke evaluation
- `ras_v3` and `ras_v4` comparison layers

The final release package includes summary charts, figures, and wrap-up documents for these layers.

## RAS Documentation

The Representation Adequacy Score is the main scientific thread running through the project.

Key documents:

- [`data/final_release/ras_overview.md`](data/final_release/ras_overview.md)
- [`data/final_release/ras_math_guide.md`](data/final_release/ras_math_guide.md)
- [`data/final_release/ras_version_comparison.md`](data/final_release/ras_version_comparison.md)
- [`data/final_release/ras_visual_explanation.md`](data/final_release/ras_visual_explanation.md)
- [`data/final_release/ras_quick_reference.md`](data/final_release/ras_quick_reference.md)

## Final Release Package

If you want the shortest path to understanding the finished project, start here:

1. [`data/final_release/final_project_overview.md`](data/final_release/final_project_overview.md)
2. [`data/final_release/executive_summary.md`](data/final_release/executive_summary.md)
3. [`data/final_release/final_wrapup_report.md`](data/final_release/final_wrapup_report.md)
4. [`data/final_release/final_artifact_index.md`](data/final_release/final_artifact_index.md)
5. [`data/final_release/ui_tour.md`](data/final_release/ui_tour.md)

## Limitations

- PRISM is not presented as arbitrary web-scale search.
- Production routing remains `computed_ras`; research layers are kept explicit.
- Adversarial hard cases remain the main weakness area.
- Calibrated rescue helps on those hard cases, which means route adequacy alone is not the whole optimization target.

## License

This project is released under the terms of the [MIT License](LICENSE).
