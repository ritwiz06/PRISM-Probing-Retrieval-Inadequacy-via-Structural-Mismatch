# Work Log: Prompt 11 External Mini-Benchmark and Generalization Evaluation

Timestamp: 2026-04-12 19:15 America/Phoenix

## Basic Summary

Prompt 11 added a separate external mini-benchmark layer for PRISM. The curated 80-query benchmark remains unchanged, and the new external benchmark is cached separately at `data/processed/external_mini_benchmark.jsonl`. The verifier evaluates computed RAS and fixed-backend baselines on a 32-example public-source-style normalized subset.

## Files Changed

- `prism/app/pipeline.py`
- `prism/external_benchmarks/__init__.py`
- `prism/external_benchmarks/loaders.py`
- `prism/external_benchmarks/mini_benchmark.py`
- `prism/external_benchmarks/verify_generalization.py`
- `tests/test_external_benchmarks.py`
- `data/processed/external_mini_benchmark.jsonl`
- `data/eval/external_generalization.json`
- `data/eval/external_generalization.csv`
- `data/eval/external_generalization_summary.md`
- `WORK_LOG_2026-04-12_1915_EXTERNAL_BENCHMARK.md`
- `PROCESS_GUIDE_2026-04-12_1915_EXTERNAL_BENCHMARK.md`

## What Was Implemented

- Added `prism.external_benchmarks` package.
- Added `ExternalBenchmarkItem` normalized schema.
- Added a cached external mini-benchmark builder CLI:
  - `.venv/bin/python3 -m prism.external_benchmarks.mini_benchmark`
- Added a generalization verifier CLI:
  - `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`
- Added JSON, CSV, and Markdown artifacts for external generalization results.
- Added a small additive `backend_override` option to `prism.app.pipeline.answer_query()` so the external verifier can evaluate fixed-backend baselines while still reusing the normal PRISM parsing, retrieval, answer synthesis, and trace path.
- Added tests for normalized schema, mini-benchmark build/load, family counts, generalization result structure, and curated benchmark pipeline compatibility.

## Commands Run

- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest tests/test_external_benchmarks.py -q`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m prism.ingest.build_corpus`
- `.venv/bin/python3 -m prism.ingest.build_kg`
- `.venv/bin/python3 -m prism.eval.verify_end_to_end`
- `.venv/bin/python3 -m prism.external_benchmarks.mini_benchmark`
- `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`

## Test Results

- External benchmark tests: 5 passed.
- Full test suite after implementation: 55 passed.
- Final full test suite after artifact/Markdown update: 55 passed in 3.46s.
- Curated end-to-end verifier still passed: total 80, route accuracy 1.000, evidence hit@k 1.000, traces 80/80, answers 80/80.

## External Mini-Benchmark Summary

- Total examples: 32.
- Route family counts:
  - BM25: 8.
  - Dense: 8.
  - KG: 8.
  - Hybrid: 8.
- Source dataset labels:
  - BEIR: 8.
  - Natural Questions: 8.
  - WebQSP: 8.
  - HotpotQA: 8.
- Cached normalized benchmark path:
  - `data/processed/external_mini_benchmark.jsonl`

## Generalization Result Summary

- Computed RAS route accuracy: 1.000.
- Computed RAS answer accuracy: 0.969.
- Computed RAS predicted backend distribution:
  - BM25: 8.
  - Dense: 8.
  - KG: 8.
  - Hybrid: 8.
- Strongest fixed-backend baseline: always BM25 and always Hybrid tied at answer accuracy 0.5625.
- Other baselines:
  - Always Dense: answer accuracy 0.375.
  - Always KG: answer accuracy 0.34375.
  - Random router with seed 11: answer accuracy 0.46875.
- Per-family computed RAS answer accuracy:
  - BM25: 8/8.
  - Dense: 7/8.
  - KG: 8/8.
  - Hybrid: 8/8.
- Known miss: semantic item `ext_sem_003`, query `What concept turns daylight into carbohydrates?`, expected `Photosynthesis`, but the Dense fallback retrieved a PostgreSQL JSONB chunk.

## Generated Artifacts

- JSON:
  - `data/eval/external_generalization.json`
- CSV:
  - `data/eval/external_generalization.csv`
- Markdown:
  - `data/eval/external_generalization_summary.md`

## Known Limitations

- This is a small normalized mini-benchmark, not a full public benchmark download.
- Examples are public-dataset-style normalized items with provenance labels; they are included only when they can be mapped cleanly to a PRISM route family and local evidence.
- The external benchmark is useful as a lightweight generalization check, not broad external validity.
- Dense retrieval still depends on the local numpy/hash fallback on this machine, which caused one semantic miss.
- Answer accuracy uses the same deterministic normalized answer matcher as the rest of PRISM, not human grading.
