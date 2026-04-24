# External Mini-Benchmark Generalization Summary

Benchmark size: 32 examples.
Source datasets used: BEIR, HotpotQA, Natural Questions, WebQSP.
Counts per route family: {'bm25': 8, 'dense': 8, 'hybrid': 8, 'kg': 8}.

## PRISM Performance

Computed RAS route accuracy: 1.000.
Computed RAS answer accuracy: 0.969.
Strongest fixed-backend baseline: always_bm25 at answer accuracy 0.562.
Predicted backend distribution: {'bm25': 8, 'dense': 8, 'kg': 8, 'hybrid': 8}.
Dense backend status: {'active_backend': 'numpy_fallback', 'embedding_backend': 'numpy_fallback', 'model_name': 'hashing-semantic-fallback', 'index_backend': 'numpy', 'faiss_active': False, 'chunk_count': 148, 'fallback_reason': 'Could not load sentence-transformers model sentence-transformers/all-MiniLM-L6-v2: RuntimeError: Cannot send a request, as the client has been closed.', 'semantic_rerank': True}.

## Per-Family Computed RAS Results

- bm25: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.
- dense: route_accuracy=1.000, answer_accuracy=0.875, correct=7/8.
- hybrid: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.
- kg: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.

## Main Takeaways

- Computed RAS answer accuracy is 0.969.
- Strongest fixed-backend baseline is always_bm25 at 0.562.
- External mini-benchmark remains separate from the curated 80-query benchmark.

## Known Caveats

- This is a small normalized mini-benchmark, not a full public benchmark download.
- Examples were included only when they could be mapped cleanly to a PRISM route family.
- Performance should be interpreted as a lightweight generalization check, not broad external validation.
- The benchmark is cached separately from the curated 80-query benchmark.

## Artifacts

- JSON: `data/eval/external_generalization.json`
- CSV: `data/eval/external_generalization.csv`
- Markdown: `data/eval/external_generalization_summary.md`
