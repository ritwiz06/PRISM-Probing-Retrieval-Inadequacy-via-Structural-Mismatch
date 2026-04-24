# Work Log: Prompt 12 Dense Backend Upgrade

Timestamp: 2026-04-12 20:20 America/Phoenix

## Basic Summary

Prompt 12 upgraded PRISM Dense retrieval from the numpy/hash fallback path to a real local sentence-transformers backend with FAISS indexing. The active backend after installation and one-time model caching is `sentence_transformers+faiss` using `sentence-transformers/all-MiniLM-L6-v2`.

## Files Changed

- `pyproject.toml`
- `configs/default.yaml`
- `prism/config.py`
- `prism/retrievers/dense_retriever.py`
- `prism/eval/verify_semantic.py`
- `prism/external_benchmarks/verify_generalization.py`
- `prism/analysis/dense_diagnostics.py`
- `prism/analysis/report_artifacts.py`
- `tests/test_dense.py`
- `data/eval/semantic_verification.json`
- `data/eval/external_generalization.json`
- `data/eval/external_generalization.csv`
- `data/eval/external_generalization_summary.md`
- `data/eval/dense_diagnostics.json`
- `data/eval/dense_upgrade_summary.md`
- `data/eval/claim_validation.json`
- `data/eval/ablation_results.json`
- `data/eval/report/prism_report_summary.json`
- `data/eval/report/prism_report_summary.md`
- `WORK_LOG_2026-04-12_2020_DENSE_UPGRADE.md`
- `PROCESS_GUIDE_2026-04-12_2020_DENSE_UPGRADE.md`

## What Was Implemented

- Added `sentence-transformers` and `faiss-cpu` as runtime dependencies.
- Changed the default Dense backend from `numpy` to `sentence-transformers`.
- Added explicit Dense backend status reporting:
  - active backend,
  - embedding backend,
  - model name,
  - index backend,
  - FAISS active flag,
  - chunk count,
  - fallback reason.
- Updated Dense retrieval metadata to include active backend/model/index information.
- Added local-first sentence-transformers loading with `local_files_only=True` when possible.
- Preserved fallback to the existing deterministic numpy/hash model if sentence-transformers cannot load.
- Fixed the FAISS score/index mapping bug so FAISS search scores map back to the correct corpus chunks.
- Added `prism.analysis.dense_diagnostics` CLI.
- Updated semantic verifier output and external generalization artifacts to surface Dense backend status.
- Updated tests for backend selection, metadata, diagnostics shape, sorted retrieval, and save/load compatibility.

## Commands Run

- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pip install faiss-cpu`
- `.venv/bin/python3 -m pytest tests/test_dense.py -q`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m prism.ingest.build_corpus`
- `.venv/bin/python3 -m prism.ingest.build_kg`
- `.venv/bin/python3 -m prism.eval.verify_semantic`
- `.venv/bin/python3 -m prism.eval.verify_end_to_end`
- `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`
- `.venv/bin/python3 -m prism.analysis.report_artifacts`
- `.venv/bin/python3 -m prism.analysis.claim_validation`
- `.venv/bin/python3 -m prism.analysis.run_ablations`
- `.venv/bin/python3 -m prism.analysis.dense_diagnostics`

## Test Results

- Focused Dense tests: 10 passed.
- Full test suite before documentation: 58 passed in 229.59s.
- Final full test suite after documentation: 58 passed with 3 warnings in 35.33s.

## Dense Backend Status Summary

- Previous active Dense backend: `numpy_fallback`.
- New active Dense backend: `sentence_transformers+faiss`.
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
- FAISS active: true.
- Corpus chunk count: 148.
- Fallback reason: none.
- One-time model download/cache was required. After caching, normal runs use the local model.

## Semantic And Generalization Impact Summary

- Curated semantic verifier:
  - Previous fallback result: Dense hit@3 20/20, Dense top-1 20/20.
  - New sentence-transformers+FAISS result: Dense hit@3 19/20, Dense top-1 17/20.
  - This is a small drop on the curated semantic slice, but it still passes the required semantic threshold.
- Curated end-to-end verifier:
  - Route accuracy: 1.000.
  - Evidence hit@k: 0.988.
  - Traces: 80/80.
  - Answers: 77/80.
  - Passed: true.
- External mini-benchmark:
  - Previous fallback result: 31/32 overall, Dense family 7/8.
  - New sentence-transformers+FAISS result: 32/32 overall, Dense family 8/8.
  - The previous photosynthesis miss is fixed: `What concept turns daylight into carbohydrates?` now retrieves `sem_photosynthesis`.
- Claim validation:
  - The lexical claim is now not supported under the strict BM25-over-Dense check because Dense ties BM25 on lexical evidence hit@k.
  - Other claims remain supported.

## Known Limitations

- The real Dense backend improves external semantic generalization but slightly reduces curated semantic top-1/top-k compared with the earlier hand-shaped numpy fallback.
- The test suite is slower because several paths instantiate the local MiniLM model.
- sentence-transformers prints model loading reports during CLI runs.
- If the cached model is removed and network is unavailable, PRISM will fall back to `numpy_fallback`.
- The current Dense model is small and laptop-friendly, not a domain-specialized embedding model.
