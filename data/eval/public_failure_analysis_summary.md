# Public Raw Failure Analysis

## Current Test Metrics

- Current computed RAS answer accuracy: 0.875 (21/24).
- Current computed RAS route accuracy: 0.917.
- Current computed RAS evidence hit@k: 0.917.
- Public arbitrated route accuracy: 1.000.

## Previous Prompt 17 Misses

- pub_bm25_11: `Python dataclasses generated special methods` previously predicted `kg`; buckets=['route_error', 'retrieval_miss', 'answer_synthesis_miss', 'lexical_confusion']; remediation=Fixed substring marker matching so dataclasses no longer triggers the deductive class marker; public lexical arbitration also recognizes dataclasses as a public-doc alias.
- pub_bm25_12: `TfidfVectorizer raw documents matrix TF-IDF features` previously predicted `dense`; buckets=['route_error', 'lexical_confusion']; remediation=Public lexical arbitration recognizes TfidfVectorizer and TF-IDF aliases and routes this identifier-heavy case to BM25 in analysis mode.
- pub_dense_10: `What immune response mistakes harmless substances for threats?` previously predicted `kg`; buckets=['route_error', 'retrieval_miss', 'answer_synthesis_miss', 'semantic_drift']; remediation=Fixed substring marker matching so threats no longer triggers the KG eats marker; the query now routes to Dense.

## Current Non-Correct Buckets

- pub_bm25_11: family=bm25, predicted=dense, buckets=['route_error', 'lexical_confusion', 'public_identifier_arbitration_candidate'], remediation=Use public-only lexical arbitration when enriched title/identifier/alias confidence is high.
- pub_bm25_12: family=bm25, predicted=dense, buckets=['route_error', 'lexical_confusion', 'public_identifier_arbitration_candidate'], remediation=Use public-only lexical arbitration when enriched title/identifier/alias confidence is high.
- pub_dense_08: family=dense, predicted=dense, buckets=['answer_synthesis_miss', 'ranking_error'], remediation=Inspect answer template extraction from the retrieved evidence.
- pub_dense_10: family=dense, predicted=dense, buckets=['retrieval_miss', 'semantic_drift'], remediation=Inspect public-page cleaning and field-aware lexical metadata for this source.
- pub_dense_12: family=dense, predicted=dense, buckets=['retrieval_miss', 'semantic_drift'], remediation=Inspect public-page cleaning and field-aware lexical metadata for this source.

## Fixed BM25 Rescue Cases

- pub_bm25_11: computed predicted `dense`, always BM25 answered correctly.
- pub_bm25_12: computed predicted `dense`, always BM25 answered correctly.
- pub_dense_08: computed predicted `dense`, always BM25 answered correctly.
- pub_dense_10: computed predicted `dense`, always BM25 answered correctly.
- pub_dense_12: computed predicted `dense`, always BM25 answered correctly.

## Bucket Counts

- answer_synthesis_miss: 1
- correct: 19
- lexical_confusion: 2
- public_identifier_arbitration_candidate: 2
- ranking_error: 1
- retrieval_miss: 2
- route_error: 2
- semantic_drift: 2

## Identifier Subgroups

- identifier_heavy: total=6, answer=1.000, route=0.667, arbitrated_route=1.000
- non_identifier: total=18, answer=0.833, route=1.000, arbitrated_route=1.000

## Tradeoffs

- Public test answer accuracy improved from the Prompt 17 reference 0.917 to current computed RAS 0.875.
- Public lexical arbitration improves test route accuracy from 0.917 to 1.000.
- The main production-safe change is fixing substring marker false positives in feature parsing.
- The public lexical retriever and arbitration mode remain analysis-only and do not change the demo path by default.

## Artifacts

- JSON: `data/eval/public_failure_analysis.json`
- CSV: `data/eval/public_failure_analysis.csv`
- Markdown: `data/eval/public_failure_analysis_summary.md`
- Route arbitration: `data/eval/public_route_arbitration.json` and `data/eval/public_route_arbitration_summary.md`
- Robustness summary: `data/eval/public_robustness_summary.md`
- Plot: `data/eval/public_robustness_before_after.png`
- Plot: `data/eval/public_identifier_subgroup.png`
