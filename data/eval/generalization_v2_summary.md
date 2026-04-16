# Generalization V2 Clean Vs Noisy Summary

Benchmark size: 80 examples.
Benchmark path: `data/processed/generalization_v2_benchmark.jsonl`.
Counts by split: {'dev': 40, 'test': 40}.
Counts by route family: {'bm25': 20, 'dense': 20, 'hybrid': 20, 'kg': 20}.
Source datasets/styles: {'2WikiMultihopQA-style': 8, 'BEIR-BioASQ': 2, 'BEIR-CodeSearch': 9, 'BEIR-FiQA': 2, 'BEIR-Robust': 7, 'CWQ-style': 5, 'GrailQA-style': 5, 'HotpotQA-style': 12, 'MSMARCO-style': 5, 'NaturalQuestions-style': 8, 'TriviaQA-style': 7, 'WebQSP-style': 10}.

## Corpus Modes

- Clean corpus: `data/processed/corpus.jsonl` with 148 documents.
- Noisy corpus: `data/processed/corpus_noisy.jsonl` with 208 documents, including 60 added distractors.

## Clean Vs Noisy Results

### Clean Corpus / Dev Split

- Computed RAS route accuracy: 0.975.
- Computed RAS answer accuracy: 1.000 (40/40).
- Strongest fixed-backend baseline: `always_dense` at answer accuracy 0.925.
- Predicted backend distribution: {'bm25': 9, 'hybrid': 11, 'dense': 10, 'kg': 10}.
- Per-family computed RAS answer accuracy:
  - bm25: 1.000 (10/10)
  - dense: 1.000 (10/10)
  - hybrid: 1.000 (10/10)
  - kg: 1.000 (10/10)

### Clean Corpus / Test Split

- Computed RAS route accuracy: 0.950.
- Computed RAS answer accuracy: 1.000 (40/40).
- Strongest fixed-backend baseline: `always_hybrid` at answer accuracy 0.900.
- Predicted backend distribution: {'bm25': 8, 'dense': 12, 'kg': 10, 'hybrid': 10}.
- Per-family computed RAS answer accuracy:
  - bm25: 1.000 (10/10)
  - dense: 1.000 (10/10)
  - hybrid: 1.000 (10/10)
  - kg: 1.000 (10/10)

### Noisy Corpus / Dev Split

- Computed RAS route accuracy: 0.975.
- Computed RAS answer accuracy: 0.975 (39/40).
- Strongest fixed-backend baseline: `always_bm25` at answer accuracy 0.925.
- Predicted backend distribution: {'bm25': 9, 'hybrid': 11, 'dense': 10, 'kg': 10}.
- Per-family computed RAS answer accuracy:
  - bm25: 0.900 (9/10)
  - dense: 1.000 (10/10)
  - hybrid: 1.000 (10/10)
  - kg: 1.000 (10/10)

### Noisy Corpus / Test Split

- Computed RAS route accuracy: 0.950.
- Computed RAS answer accuracy: 0.975 (39/40).
- Strongest fixed-backend baseline: `always_dense` at answer accuracy 0.900.
- Predicted backend distribution: {'bm25': 8, 'dense': 12, 'kg': 10, 'hybrid': 10}.
- Per-family computed RAS answer accuracy:
  - bm25: 0.900 (9/10)
  - dense: 1.000 (10/10)
  - hybrid: 1.000 (10/10)
  - kg: 1.000 (10/10)

## Noisy-Corpus Degradation

- dev: clean=1.000, noisy=0.975, delta=-0.025.
- dev: most degraded family is `bm25`.
- test: clean=1.000, noisy=0.975, delta=-0.025.
- test: most degraded family is `bm25`.

## Main Takeaways

- clean/dev: computed RAS answer accuracy 1.000 beats strongest fixed backend always_dense at 0.925.
- clean/test: computed RAS answer accuracy 1.000 beats strongest fixed backend always_hybrid at 0.900.
- noisy/dev: computed RAS answer accuracy 0.975 beats strongest fixed backend always_bm25 at 0.925.
- noisy/test: computed RAS answer accuracy 0.975 beats strongest fixed backend always_dense at 0.900.
- dev: noisy corpus delta for computed RAS is -0.025; most degraded family is bm25.
- test: noisy corpus delta for computed RAS is -0.025; most degraded family is bm25.

## Threats To Validity

- The suite is normalized and public-source-style, not a full official benchmark download.
- Items are grounded in PRISM's local corpus/KG so evidence is available offline.
- Noisy-corpus stress testing is synthetic and measures robustness to curated distractors, not arbitrary web noise.
- The test split should be treated as held-out for reporting; benchmark construction changes should be justified using dev cases.
- Answer accuracy uses normalized string matching, which is useful for local regression checks but not a substitute for human grading.

## Artifacts

- JSON: `data/eval/generalization_v2.json`
- CSV: `data/eval/generalization_v2.csv`
- Markdown: `data/eval/generalization_v2_summary.md`
- Plot: `data/eval/generalization_v2_clean_vs_noisy.png`
- Plot: `data/eval/generalization_v2_baseline_comparison.png`
