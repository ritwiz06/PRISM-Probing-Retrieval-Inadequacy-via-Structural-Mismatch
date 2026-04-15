# Dense Before/After Comparison

Compatibility reruns over the same local corpus/KG. The pre-robustness run disables semantic_rerank to reproduce the Dense-upgrade regression state.

| Run | Dense backend | Semantic top1 | Semantic hit@3 | E2E answers | External answers |
| --- | --- | ---: | ---: | ---: | ---: |
| numpy_fallback | numpy_fallback rerank=True | 20/20 | 20/20 | 80/80 | 31/32 |
| sentence_transformers_faiss_pre_robustness | sentence_transformers+faiss rerank=False | 17/20 | 19/20 | 77/80 | 32/32 |
| sentence_transformers_faiss_robust | sentence_transformers+faiss rerank=True | 20/20 | 20/20 | 80/80 | 32/32 |

Robustness change: Enabled a small metadata-visible semantic concept rerank that uses the existing local semantic alias table to correct real-embedding semantic drift.

Claim note: The lexical BM25-over-Dense claim should be reported cautiously when real Dense ties BM25 on lexical hit@k; this analysis does not hide that tradeoff.
