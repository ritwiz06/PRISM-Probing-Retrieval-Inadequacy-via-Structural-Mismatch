# Public Raw-Document Corpus Evaluation

Public corpus path: `data/processed/public_corpus.jsonl`.
Public documents available: 48 of 48 registry sources.
Fetch summary: {'fetched': 0, 'cached': 48, 'fallback_snapshot': 0, 'skipped': 0, 'raw_dir': 'data/raw/public_corpus'}.
Cached content status counts: {'fallback_snapshot': 1, 'fetched': 47}.
Corpus counts by route family: {'bm25': 12, 'dense': 12, 'hybrid': 12, 'kg': 12}.
Enriched metadata path: `data/processed/public_corpus_enriched_metadata.json` with 22 identifier-bearing documents.

Benchmark path: `data/processed/public_corpus_benchmark.jsonl`.
Benchmark size: 48 examples.
Benchmark counts: {'split': {'dev': 24, 'test': 24}, 'route_family': {'bm25': 12, 'dense': 12, 'hybrid': 12, 'kg': 12}, 'source_dataset_style': {'2WikiMultihopQA-style bridge': 5, 'BEIR-style lexical': 4, 'CWQ-style structured': 1, 'GrailQA-style structured': 2, 'HotpotQA-style bridge': 7, 'MS MARCO-style semantic': 2, 'Natural Questions-style semantic': 7, 'TriviaQA-style semantic': 3, 'WebQSP-style structured': 9, 'medical code lookup': 1, 'official docs': 5, 'official regulation': 2}}.
Public-doc grounding coverage: {'total': 48, 'grounded': 48, 'coverage': 1.0, 'by_family': {'bm25': {'total': 12, 'grounded': 12}, 'dense': {'total': 12, 'grounded': 12}, 'kg': {'total': 12, 'grounded': 12}, 'hybrid': {'total': 12, 'grounded': 12}}}.

## Results

### Dev Split

- Computed RAS route accuracy: 0.917.
- Computed RAS answer accuracy: 0.958 (23/24).
- Computed RAS evidence hit@k: 0.875 (21/24).
- Strongest fixed-backend baseline: `always_bm25` at answer accuracy 0.875.
- Predicted backend distribution: {'bm25': 5, 'dense': 6, 'kg': 7, 'hybrid': 6}.
- Per-family computed RAS:
  - bm25: answer=1.000, evidence_hit@k=1.000, total=6
  - dense: answer=0.833, evidence_hit@k=0.833, total=6
  - hybrid: answer=1.000, evidence_hit@k=1.000, total=6
  - kg: answer=1.000, evidence_hit@k=0.667, total=6

### Test Split

- Computed RAS route accuracy: 0.917.
- Computed RAS answer accuracy: 1.000 (24/24).
- Computed RAS evidence hit@k: 1.000 (24/24).
- Strongest fixed-backend baseline: `always_bm25` at answer accuracy 0.958.
- Predicted backend distribution: {'bm25': 4, 'dense': 8, 'kg': 6, 'hybrid': 6}.
- Per-family computed RAS:
  - bm25: answer=1.000, evidence_hit@k=1.000, total=6
  - dense: answer=1.000, evidence_hit@k=1.000, total=6
  - hybrid: answer=1.000, evidence_hit@k=1.000, total=6
  - kg: answer=1.000, evidence_hit@k=1.000, total=6

## Public Robustness Before/After

- Previous public test reference: computed RAS answer=0.917 (22/24), route=0.875, strongest fixed=always_bm25 at 0.958.
- dev: baseline answer=0.958; public lexical=0.958; public arbitrated=0.958.
- dev: public arbitrated route delta=0.042; gap vs strongest fixed backend after arbitration=0.083.
- test: baseline answer=1.000; public lexical=1.000; public arbitrated=1.000.
- test: public arbitrated route delta=0.083; gap vs strongest fixed backend after arbitration=0.042.

## Main Takeaways

- dev: computed RAS answer accuracy 0.958 beats or matches strongest fixed backend always_bm25 at 0.875; weakest family is dense.
- test: computed RAS answer accuracy 1.000 beats or matches strongest fixed backend always_bm25 at 0.958; weakest family is bm25.

## Threats To Validity

- The public raw corpus is small and source-selected, so results are not a web-scale claim.
- Network failures can cause fallback public snapshots to be used; fetch status is reported in artifacts.
- Fetched pages may include formatting noise, navigation text, and boilerplate not present in normalized local corpora.
- Deductive and relational public queries still rely partly on the compact demo KG, which can mismatch public-page wording.
- Answer matching is normalized string matching, not human grading.

## Artifacts

- JSON: `data/eval/public_corpus_eval.json`
- CSV: `data/eval/public_corpus_eval.csv`
- Markdown: `data/eval/public_corpus_eval_summary.md`
- Plot: `data/eval/public_corpus_baselines.png`
- Plot: `data/eval/public_corpus_family_accuracy.png`
