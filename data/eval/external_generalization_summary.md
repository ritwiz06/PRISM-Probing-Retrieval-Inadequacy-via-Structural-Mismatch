# External Mini-Benchmark Generalization Summary

Benchmark size: 32 examples.
Source datasets used: BEIR, HotpotQA, Natural Questions, WebQSP.
Counts per route family: {'bm25': 8, 'dense': 8, 'hybrid': 8, 'kg': 8}.

## PRISM Performance

Computed RAS route accuracy: 1.000.
Computed RAS answer accuracy: 1.000.
Strongest fixed-backend baseline: always_hybrid at answer accuracy 0.688.
Predicted backend distribution: {'bm25': 8, 'dense': 8, 'kg': 8, 'hybrid': 8}.
Dense backend status: {'active_backend': 'sentence_transformers+faiss', 'embedding_backend': 'sentence_transformers', 'model_name': 'sentence-transformers/all-MiniLM-L6-v2', 'index_backend': 'faiss', 'faiss_active': True, 'chunk_count': 148, 'fallback_reason': '', 'semantic_rerank': True}.

## Per-Family Computed RAS Results

- bm25: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.
- dense: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.
- hybrid: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.
- kg: route_accuracy=1.000, answer_accuracy=1.000, correct=8/8.

## Main Takeaways

- Computed RAS answer accuracy is 1.000.
- Strongest fixed-backend baseline is always_hybrid at 0.688.
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
