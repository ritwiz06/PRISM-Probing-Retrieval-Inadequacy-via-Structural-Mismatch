# PRISM Work Log: Hybrid Retrieval

Date and time: 2026-04-11 23:55 America/Phoenix

## Task Summary

Implemented the real Hybrid retrieval backend and relational evaluation slice for PRISM. Hybrid now composes the existing BM25, Dense, and KG retrievers through a Reciprocal Rank Fusion workflow and adds relational fused evidence bundles that preserve both structured KG evidence and text evidence.

## Files Changed

- `prism/retrievers/hybrid_retriever.py`
- `prism/retrievers/kg_retriever.py`
- `prism/ingest/wikipedia_fetch.py`
- `prism/eval/relational_slice.py`
- `prism/eval/verify_hybrid.py`
- `prism/eval/datasets.py`
- `prism/eval/gold_labels.py`
- `prism/ras/feature_parser.py`
- `tests/test_hybrid.py`
- `tests/test_pipeline.py`
- `WORK_LOG_2026-04-11_2355_HYBRID.md`
- `PROCESS_GUIDE_2026-04-11_2355_HYBRID.md`

## What Changed

- Replaced the old score-addition hybrid placeholder with a real `HybridRetriever`.
- Added `HybridConfig` with:
  - RRF `k` constant
  - enabled backend list
  - backend weights
  - candidate multiplier
- Hybrid now reuses existing retrievers instead of duplicating BM25, Dense, or KG internals.
- Added Reciprocal Rank Fusion over heterogeneous evidence from:
  - Dense chunks
  - BM25 document hits
  - KG triples and paths
- Added provenance-preserving fused `RetrievedItem` metadata:
  - contributing backend names
  - component ids
  - per-backend raw ranks
  - per-backend raw scores
  - fusion method
  - evidence type
  - parent doc id where available
  - chunk id where available
  - triple id or path id where available
  - KG source doc id where available
- Added relational bundle support for queries such as `What bridge connects bat and vertebrate?`
- Added 20 local relational text snippets to the curated corpus path.
- Updated cached corpus handling so relational snippets are merged even when an older raw cache exists.
- Extended KG query templates to support `bridge`, `links`, and direct relation fallback for connect-style prompts.
- Added 20-query relational benchmark slice.
- Added `python3 -m prism.eval.verify_hybrid`.
- Updated smoke evaluation to include five relational Hybrid queries.
- Extended relational routing markers to include `connect`, `connects`, `bridge`, and `links`.
- Added tests for RRF output, sorted fused retrieval, relational bundle provenance, relational slice loading, Hybrid routing, and Hybrid verification thresholds.

## Commands Run

- `.venv/bin/python3 --version`
- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m prism.ingest.build_corpus`
- `.venv/bin/python3 -m prism.ingest.build_kg`
- `.venv/bin/python3 -m prism.eval.run_eval --backend hybrid --smoke`
- `.venv/bin/python3 -m prism.eval.verify_hybrid`
- `.venv/bin/python3 -m prism.eval.verify_kg`
- `.venv/bin/python3 -m prism.eval.verify_semantic`
- `.venv/bin/python3 -m prism.eval.verify_lexical`

## Test Results

- `.venv/bin/python3 -m pip install -e .`: passed
- `.venv/bin/python3 -m pytest -q`: passed with `34 passed in 0.45s`
- `.venv/bin/python3 -m prism.ingest.build_corpus`: passed and wrote `148` documents
- `.venv/bin/python3 -m prism.ingest.build_kg`: passed and wrote `99` triples
- `.venv/bin/python3 -m prism.eval.run_eval --backend hybrid --smoke`: passed with `route_accuracy=0.9565217391304348`
- `.venv/bin/python3 -m prism.eval.verify_hybrid`: passed
- `.venv/bin/python3 -m prism.eval.verify_kg`: passed
- `.venv/bin/python3 -m prism.eval.verify_semantic`: passed
- `.venv/bin/python3 -m prism.eval.verify_lexical`: passed

## Relational Verification Summary

- Relational queries: `20`
- Top-k: `5`
- Required Hybrid hit@k: `15/20`
- Actual Hybrid hit@k: `20/20`
- Hybrid top-1: `17/20`
- Dense hit@k on relational slice: `0/20`
- KG hit@k on relational slice: `0/20`
- BM25 hit@k on relational slice: `0/20`
- Required Hybrid beats Dense: `12/20`
- Actual Hybrid beats Dense: `20/20`
- Required Hybrid beats KG: `10/20`
- Actual Hybrid beats KG: `20/20`
- Hybrid beats BM25: `20/20`
- Verification artifact: `data/eval/hybrid_verification.json`

## Fusion Behavior Summary

- Default fusion method: `rrf`
- Relational fused bundle method: `rrf+relational_bundle`
- RRF scoring uses `1 / (rrf_k + rank)` multiplied by backend weight.
- Default RRF constant: `60`
- Default backend weights:
  - Dense: `1.0`
  - KG: `1.2`
  - BM25: `0.9`
- Verification top results were relational bundles with contributions from:
  - `kg`
  - `bm25`
- Hybrid results preserve component ids so relational gold evidence can require both KG structure and text evidence.

## Known Limitations

- Hybrid persistence/save-load was not added because the backend composes live retrievers and does not own a standalone index yet.
- Relational bundle logic is pragmatic and query-template oriented, not a general evidence graph optimizer.
- Current relational verification intentionally defines gold evidence as fused KG plus text evidence, so single backends do not satisfy the complete relational gold condition.
- Dense is still using the numpy fallback on this machine, so Dense-vs-Hybrid contrast should be revisited after enabling a real SentenceTransformer model.
- The relational corpus snippets are curated and small, not mined from a real Wikipedia pipeline.
- Answer generation still echoes retrieved evidence and is not yet a local LLM answer generator.

## Concepts and Topics Used

- Hybrid retrieval: combining multiple retrieval backends for one query.
- Reciprocal Rank Fusion: a rank-based method that combines result lists without requiring comparable raw scores.
- Provenance-preserving fusion: keeping component backend ids, ranks, scores, and source ids in fused metadata.
- Deduplication: grouping text hits by parent document and KG hits by triple/path identity where reasonable.
- Relational bundle: a fused evidence item containing both KG structure and text evidence.
- Heterogeneous evidence: evidence from different representations, such as BM25 documents, Dense chunks, and KG paths.
- Structural mismatch: the reason Hybrid is needed for relational queries that are incomplete under a single representation.
