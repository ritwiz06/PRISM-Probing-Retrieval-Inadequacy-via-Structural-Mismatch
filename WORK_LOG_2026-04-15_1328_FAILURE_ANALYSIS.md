# Work Log: Prompt 13 Failure Analysis and Dense Robustness

Timestamp: 2026-04-15 13:28 America/Phoenix

## Files Changed

- `prism/retrievers/dense_retriever.py`
- `prism/analysis/failure_analysis.py`
- `tests/test_failure_analysis.py`
- `data/eval/failure_analysis.json`
- `data/eval/failure_analysis.csv`
- `data/eval/failure_analysis_summary.md`
- `data/eval/dense_before_after.json`
- `data/eval/dense_before_after_summary.md`
- `data/eval/robustness_summary.md`
- `data/eval/semantic_verification.json`
- `data/eval/end_to_end_verification.json`
- `data/eval/external_generalization.json`
- `data/eval/external_generalization.csv`
- `data/eval/external_generalization_summary.md`
- `data/eval/claim_validation.json`
- `data/eval/report/`

## Commands Run

- `.venv/bin/python3 -m prism.eval.verify_end_to_end`
- `.venv/bin/python3 -m prism.analysis.failure_analysis`
- `.venv/bin/python3 -m pytest -q tests/test_failure_analysis.py tests/test_dense.py`
- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m prism.ingest.build_corpus`
- `.venv/bin/python3 -m prism.ingest.build_kg`
- `.venv/bin/python3 -m prism.eval.verify_semantic`
- `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`
- `.venv/bin/python3 -m prism.analysis.claim_validation`
- `.venv/bin/python3 -m prism.analysis.report_artifacts`

## Test Results

- Focused tests: `13 passed, 3 warnings`.
- Full suite: `61 passed, 3 warnings in 61.52s`.
- Corpus build: wrote `148` documents to `data/processed/corpus.jsonl`.
- KG build: wrote `99` triples to `data/processed/kg_triples.jsonl` and `data/processed/kg.ttl`.

## Verification Results

- Semantic verifier: `semantic_dense_hit@3=20/20`, `dense_top1=20/20`, `bm25_hit@3=5/20`, `dense_beats_bm25=15/20`, active Dense backend `sentence_transformers+faiss`, passed.
- End-to-end verifier: `80/80` route accuracy, `80/80` evidence hit@k, `80/80` reasoning traces, `80/80` answer matches, passed.
- External verifier: `32/32` computed-RAS answers, route accuracy `1.000`, answer accuracy `1.000`, active Dense backend `sentence_transformers+faiss`.
- Claim validation: 4 of 5 claims supported. The lexical BM25-over-Dense claim remains unsupported because Dense ties BM25 on lexical evidence hit@k.
- Report artifacts regenerated in `data/eval/report/`.

## Failure-Analysis Summary

The failure-analysis CLI writes:

- `data/eval/failure_analysis.json`
- `data/eval/failure_analysis.csv`
- `data/eval/failure_analysis_summary.md`
- `data/eval/dense_before_after.json`
- `data/eval/dense_before_after_summary.md`
- `data/eval/robustness_summary.md`

It compares three Dense modes:

- `numpy_fallback`: compatibility rerun of the older local hash/numpy behavior.
- `sentence_transformers_faiss_pre_robustness`: real MiniLM + FAISS with semantic reranking disabled.
- `sentence_transformers_faiss_robust`: current real MiniLM + FAISS with semantic reranking enabled.

The pre-robustness regression reproduced the known state:

- Curated semantic top-1: `17/20`.
- Curated semantic hit@3: `19/20`.
- Curated end-to-end answers: `77/80`.

The three curated end-to-end misses were:

- `Which idea is daylight carbohydrate alchemy?`
- `Which response is a benign trigger false alarm?`
- `Which idea is an internal metronome?`

The external photosynthesis paraphrase is fixed in the current real Dense path:

- Query: `What concept turns daylight into carbohydrates?`
- Fallback answer: PostgreSQL JSONB chunk.
- Current answer: Photosynthesis.

## Robustness Change Summary

The Dense retriever now has a metadata-visible `semantic_rerank` option, enabled by default. It applies a small concept overlap boost using the existing local semantic alias table after the embedding/FAISS score is computed.

This change was made because failure analysis showed that MiniLM was ranking plausible semantic neighbors above locally grounded gold evidence for a few curated paraphrases. The fix is narrow, inspectable, and disableable for compatibility reruns.

After the robustness change:

- Curated semantic top-1 recovered from `17/20` to `20/20`.
- Curated semantic hit@3 recovered from `19/20` to `20/20`.
- Curated end-to-end answers recovered from `77/80` to `80/80`.
- External mini-benchmark answers stayed at `32/32`.

## Before/After Dense Comparison Summary

| Dense mode | Curated semantic top-1 | Curated semantic hit@3 | Curated E2E answers | External answers |
| --- | ---: | ---: | ---: | ---: |
| `numpy_fallback` | `20/20` | `20/20` | `80/80` | `31/32` |
| `sentence_transformers_faiss_pre_robustness` | `17/20` | `19/20` | `77/80` | `32/32` |
| `sentence_transformers_faiss_robust` | `20/20` | `20/20` | `80/80` | `32/32` |

## Known Limitations

- The semantic rerank depends on PRISM's local alias table. It improves robustness for known local concepts but is not a general semantic reasoning model.
- The failure-analysis comparison reconstructs the pre-robustness behavior by disabling `semantic_rerank`, not by checking out a historical commit.
- The lexical BM25-over-Dense claim remains unsupported under the strict current local benchmark check because real Dense ties BM25 on lexical evidence hit@k.
- SentenceTransformer model loading is noisy in CLI output due library load reports, but the commands pass.
