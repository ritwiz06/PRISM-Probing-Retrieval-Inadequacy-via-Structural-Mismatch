# PRISM Report Artifact Summary

Corpus size: 148 documents.
KG size: 99 triples.
Benchmark sizes: {'lexical': 20, 'semantic': 20, 'deductive': 20, 'relational': 20, 'total': 80}.

## Overall Results

Computed RAS route accuracy: 1.000.
Computed RAS answer accuracy: 1.000.
Strongest fixed-backend answer baseline: always_hybrid at 0.675.
Computed RAS evidence hit@k: 1.000.

## Claim Validation

- Not supported: Lexical queries favor BM25 over Dense on evidence hit@k. margin=0.000.
- Supported: Semantic queries favor Dense over BM25 on evidence hit@k. margin=0.750.
- Supported: Deductive queries favor KG over Dense and BM25 on evidence hit@k. margin=1.000.
- Supported: Relational queries favor Hybrid over single backends on evidence hit@k. margin=1.000.
- Supported: Computed RAS routing beats or matches the strongest fixed-backend baseline overall on answer accuracy. margin=0.325.

## Generated Tables

- `data/eval/report/baseline_comparison.csv`
- `data/eval/report/per_slice_backend_comparison.csv`
- `data/eval/report/ablation_impacts.csv`
- `data/eval/report/claim_validation.csv`

## Generated Plots

- `data/eval/report/overall_baseline_comparison.png`
- `data/eval/report/per_slice_backend_performance.png`
- `data/eval/report/predicted_backend_distribution.png`
- `data/eval/report/ablation_impact.png`
