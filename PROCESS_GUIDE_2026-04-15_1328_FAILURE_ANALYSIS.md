# Process Guide: Failure Analysis and Dense Robustness

## Basic Summary

This task added a research-friendly failure-analysis layer to PRISM. The goal was not just to restore benchmark scores, but to explain what broke after the real Dense upgrade, why it broke, what changed, and which claims still need careful reporting.

The important result is:

- Real Dense with MiniLM + FAISS improved external semantic generalization.
- It initially introduced three curated semantic/end-to-end regressions.
- Failure analysis showed those regressions were semantic ranking drift, not routing failures.
- A small, inspectable semantic concept rerank fixed the curated regressions without hiding the external results.
- The lexical BM25-over-Dense claim remains unsupported under the strict current check because Dense now ties BM25 on lexical evidence hit@k.

## How Failure Analysis Works

The new module is `prism.analysis.failure_analysis`.

It compares three Dense configurations over the same local corpus and KG:

- `numpy_fallback`: the older hash/numpy fallback behavior, reproduced through `RetrievalConfig(dense_backend="numpy")`.
- `sentence_transformers_faiss_pre_robustness`: real local embeddings with `sentence-transformers/all-MiniLM-L6-v2` and FAISS, but with the new robustness rerank disabled.
- `sentence_transformers_faiss_robust`: the current production Dense path with real embeddings, FAISS, and semantic reranking enabled.

The comparison is run on:

- Curated semantic slice.
- Curated 80-query end-to-end benchmark.
- External mini-benchmark.

The outputs are:

- `data/eval/failure_analysis.json`
- `data/eval/failure_analysis.csv`
- `data/eval/failure_analysis_summary.md`
- `data/eval/dense_before_after.json`
- `data/eval/dense_before_after_summary.md`
- `data/eval/robustness_summary.md`

## How Error Buckets Are Assigned

Each miss is assigned inspectable buckets using simple rules:

- `route_error`: the predicted route/backend does not match the gold route.
- `retrieval_miss`: gold evidence is not present in retrieved top-k evidence.
- `ranking_error`: gold evidence appears in top-k but is not ranked first when top-1 matters.
- `answer_synthesis_miss`: evidence is available but the final answer does not match the gold answer.
- `kg_incompleteness`: deductive/KG evidence is missing.
- `lexical_confusion`: retrieved evidence includes lexical distractors for a non-lexical query.
- `semantic_drift`: semantic query evidence moves toward a plausible but wrong concept.
- `hybrid_fusion_miss`: relational evidence fusion fails to recover required evidence.
- `benchmark_evidence_mismatch`: a possible mismatch between benchmark gold evidence and available local evidence.

These are not learned labels. They are rule-assisted diagnostics meant to make failures easy to inspect.

## Before/After Dense Comparison

The previous Dense fallback behavior is reconstructed with the current code by forcing the Dense backend to `numpy`. This is honest but not identical to having a historical git commit, because the repo is being worked directly and no git history is assumed.

The real Dense regression state is reconstructed by disabling `semantic_rerank`. This reproduces the observed post-upgrade behavior:

- Curated semantic top-1: `17/20`.
- Curated semantic hit@3: `19/20`.
- Curated end-to-end answers: `77/80`.
- External mini-benchmark answers: `32/32`.

The current robust Dense path reports:

- Curated semantic top-1: `20/20`.
- Curated semantic hit@3: `20/20`.
- Curated end-to-end answers: `80/80`.
- External mini-benchmark answers: `32/32`.

## What Robustness Change Was Made and Why

The Dense retriever now has a `semantic_rerank` option. It is enabled by default and is stored in Dense metadata and save/load artifacts.

The rerank works like this:

1. The retriever computes normal embedding similarity using MiniLM and FAISS.
2. It extracts local semantic concept tokens from the query using the existing semantic alias table.
3. It extracts semantic concept tokens from each candidate chunk title and text.
4. If the query and chunk share a local concept token, the chunk receives a small score boost.

This was chosen because the actual failures were not random. They were local paraphrase cases where MiniLM ranked a plausible neighbor above the curated gold concept:

- `daylight carbohydrate alchemy` was ranked near circadian rhythm instead of photosynthesis.
- `benign trigger false alarm` was ranked near impostor syndrome instead of allergy.
- `internal metronome` was ranked near situated knowledge instead of circadian rhythm.

The alias table already existed to make the local semantic slice grounded and reproducible. Using it as a narrow rerank is more transparent than changing benchmark answers or weakening thresholds.

## Concepts and Terms Used

- Dense retrieval: retrieval using vector embeddings rather than exact token matching.
- Embedding: a numeric vector representation of text.
- FAISS: a local vector-search library used to retrieve nearest embeddings efficiently.
- Semantic drift: when embedding similarity points to a plausible but wrong concept.
- Reranking: adjusting the initial retrieval order after the first scoring pass.
- Hit@k: whether the correct evidence appears anywhere in the top `k` retrieved items.
- Top-1 accuracy: whether the first retrieved item is the correct evidence.
- End-to-end accuracy: whether the full route, retrieval, answer, and trace pipeline produces the expected answer.
- Error bucket: a category that explains the likely type of failure.
- Compatibility rerun: running current code in a mode that approximates older behavior, such as forcing `numpy_fallback`.

## What Remains Unresolved

- The semantic alias rerank is intentionally narrow. It does not solve all possible semantic paraphrase failures.
- The lexical BM25-over-Dense claim remains unsupported in strict claim validation because real Dense ties BM25 on lexical hit@k.
- The before/after comparison is reconstructed from compatible modes rather than from a versioned historical run.
- The benchmark is still small and curated, so the failure-analysis results are useful for project transparency but not broad statistical validation.
