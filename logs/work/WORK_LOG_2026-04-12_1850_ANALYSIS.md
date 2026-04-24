# Work Log: Prompt 9 Analysis, Ablations, Claim Validation, and Report Artifacts

Timestamp: 2026-04-12 18:50 America/Phoenix

## Basic Summary

Prompt 9 added the research/results layer for PRISM. The repo can now evaluate computed RAS routing against fixed-backend and random baselines, validate the main PRISM claims against the local benchmark, run Hybrid ablations, and generate report-ready JSON, CSV, Markdown, and PNG artifacts.

## Files Changed

- `pyproject.toml`
- `prism/analysis/__init__.py`
- `prism/analysis/evaluation.py`
- `prism/analysis/claim_validation.py`
- `prism/analysis/run_ablations.py`
- `prism/analysis/report_artifacts.py`
- `tests/test_analysis.py`
- `data/eval/claim_validation.json`
- `data/eval/ablation_results.json`
- `data/eval/report/artifact_manifest.json`
- `data/eval/report/prism_report_summary.json`
- `data/eval/report/baseline_comparison.csv`
- `data/eval/report/per_slice_backend_comparison.csv`
- `data/eval/report/ablation_impacts.csv`
- `data/eval/report/claim_validation.csv`
- `data/eval/report/prism_report_summary.md`
- `data/eval/report/overall_baseline_comparison.png`
- `data/eval/report/per_slice_backend_performance.png`
- `data/eval/report/predicted_backend_distribution.png`
- `data/eval/report/ablation_impact.png`
- `WORK_LOG_2026-04-12_1850_ANALYSIS.md`
- `PROCESS_GUIDE_2026-04-12_1850_ANALYSIS.md`

## What Was Implemented

- Added `matplotlib` as the plotting dependency.
- Added shared analysis evaluation in `prism.analysis.evaluation`.
- Added baseline systems:
  - computed RAS router,
  - always BM25,
  - always Dense,
  - always KG,
  - always Hybrid,
  - random router with fixed seed,
  - oracle route.
- Added claim validation in `prism.analysis.claim_validation`.
- Added Hybrid ablations in `prism.analysis.run_ablations`:
  - no KG in Hybrid,
  - no BM25 in Hybrid,
  - no Dense in Hybrid.
- Added report artifact generation in `prism.analysis.report_artifacts`.
- Added tests for baseline structure, claim output shape, ablation output shape, report artifact generation, and combined benchmark loading.

## Commands Run

- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest tests/test_analysis.py -q`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m prism.ingest.build_corpus`
- `.venv/bin/python3 -m prism.ingest.build_kg`
- `.venv/bin/python3 -m prism.eval.verify_lexical`
- `.venv/bin/python3 -m prism.eval.verify_semantic`
- `.venv/bin/python3 -m prism.eval.verify_kg`
- `.venv/bin/python3 -m prism.eval.verify_hybrid`
- `.venv/bin/python3 -m prism.eval.verify_end_to_end`
- `.venv/bin/python3 -m prism.analysis.claim_validation`
- `.venv/bin/python3 -m prism.analysis.run_ablations`
- `.venv/bin/python3 -m prism.analysis.report_artifacts`

## Test Results

- Analysis tests: 5 passed.
- Full test suite: 50 passed in 1.69s on the final run.
- A first analysis test run failed because `matplotlib` was not installed yet; this was resolved by installing the updated editable package.
- A later analysis test run aborted because matplotlib selected a macOS GUI backend in headless mode; this was resolved by forcing the `Agg` backend and setting writable cache directories before importing pyplot.

## Existing Verification Results

- Corpus build succeeded and wrote 148 documents.
- KG build succeeded and wrote 99 triples plus Turtle output.
- Lexical verification succeeded: top-1 20/20, accuracy 1.00.
- Semantic verification succeeded: Dense hit@3 20/20, Dense top-1 20/20, BM25 hit@3 5/20, Dense beats BM25 15/20, active backend `numpy`.
- KG verification succeeded: KG hit@3 20/20, KG top-1 19/20, Dense hit@3 0/20, BM25 hit@3 0/20, KG beats Dense 20/20, triples 99.
- Hybrid verification succeeded: Hybrid hit@5 20/20, Hybrid top-1 17/20, Dense hit@5 0/20, KG hit@5 0/20, BM25 hit@5 0/20, Hybrid beats Dense 20/20, Hybrid beats KG 20/20.
- End-to-end verification succeeded: total 80, route accuracy 1.000, evidence hit@k 1.000, traces 80/80, answers 80/80, passed `True`.

## Baseline Comparison Summary

- Computed RAS: route accuracy 1.000, evidence hit@k 1.000, answer accuracy 1.000.
- Always BM25: route accuracy 0.250, evidence hit@k 0.3125, answer accuracy 0.5125.
- Always Dense: route accuracy 0.250, evidence hit@k 0.4000, answer accuracy 0.4625.
- Always KG: route accuracy 0.250, evidence hit@k 0.2500, answer accuracy 0.3125.
- Always Hybrid: route accuracy 0.250, evidence hit@k 0.5625, answer accuracy 0.5500.
- Random router with seed 7: route accuracy 0.375, evidence hit@k 0.4750, answer accuracy 0.5375.
- Oracle route: route accuracy 1.000, evidence hit@k 1.000, answer accuracy 1.000.
- Computed RAS has a clear overall advantage over the strongest fixed-backend baseline in this local benchmark: answer accuracy 1.000 vs 0.550 for always Hybrid.

## Claim Validation Summary

- Supported: lexical queries favor BM25 over Dense on evidence hit@k, margin 0.400.
- Supported: semantic queries favor Dense over BM25 on evidence hit@k, margin 0.750.
- Supported: deductive queries favor KG over Dense and BM25 on evidence hit@k, margin 1.000.
- Supported: relational queries favor Hybrid over single backends on evidence hit@k, margin 1.000.
- Supported: computed RAS routing beats or matches the strongest fixed-backend baseline overall on answer accuracy, margin 0.450.

## Ablation Summary

- `hybrid_no_kg`: relational evidence hit@k 0.000, delta vs full Hybrid -1.000.
- `hybrid_no_bm25`: relational evidence hit@k 1.000, delta vs full Hybrid 0.000.
- `hybrid_no_dense`: relational evidence hit@k 1.000, delta vs full Hybrid 0.000.
- In the current relational slice, KG is essential for Hybrid’s all-gold-evidence criterion, while either BM25 or Dense text evidence can satisfy the text side of the fused evidence requirement.

## Artifact Generation Summary

- Report directory: `data/eval/report/`.
- JSON summaries:
  - `data/eval/claim_validation.json`
  - `data/eval/ablation_results.json`
  - `data/eval/report/prism_report_summary.json`
  - `data/eval/report/artifact_manifest.json`
- CSV tables:
  - `data/eval/report/baseline_comparison.csv`
  - `data/eval/report/per_slice_backend_comparison.csv`
  - `data/eval/report/ablation_impacts.csv`
  - `data/eval/report/claim_validation.csv`
- Markdown summary:
  - `data/eval/report/prism_report_summary.md`
- PNG plots:
  - `data/eval/report/overall_baseline_comparison.png`
  - `data/eval/report/per_slice_backend_performance.png`
  - `data/eval/report/predicted_backend_distribution.png`
  - `data/eval/report/ablation_impact.png`

## Known Limitations

- The benchmark is curated and local, so claim validation demonstrates the project thesis within this dataset rather than proving it universally.
- Answer accuracy uses the project’s normalized deterministic matcher, not human grading.
- The random router baseline is deterministic with a fixed seed, but it is still only one sampled random assignment.
- Hybrid ablation results reflect the current relational slice design; the no-BM25 and no-Dense ablations are not harmful here because either text backend can supply the needed text evidence.
- Plots are intentionally simple matplotlib figures for report use, not polished publication graphics.
