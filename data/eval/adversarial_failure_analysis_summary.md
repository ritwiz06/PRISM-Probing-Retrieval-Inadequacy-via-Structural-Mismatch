# Adversarial Failure Analysis

Source: `data/eval/adversarial_eval.json`.
Computed RAS answer accuracy: 0.729.
Computed RAS route accuracy: 0.729.
Computed RAS evidence hit@k: 0.896.
Computed RAS top-1 evidence hit: 0.688.

## Bucket Counts

- KG incompleteness: 2
- answer synthesis miss: 8
- evidence present in top-k but not top-1: 10
- identifier ambiguity: 1
- lexical over-trigger: 11
- public-document noise: 5
- relational bridge confusion: 2
- retrieval miss: 5
- route boundary confusion: 13

## Hardest Examples

- `adv_bm25_dev_01` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['identifier ambiguity', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=In plain language, what is RFC-7231 really about, not RFC-7230 routing?
- `adv_dense_dev_02` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'lexical over-trigger', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=What process turns daylight into stored chemical energy even if PostgreSQL JSONB also stores values?
- `adv_dense_test_06` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'lexical over-trigger', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=Which idea says tiny starting changes cause large later effects, not numpy.linalg.svd decomposition?
- `adv_kg_dev_01` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'lexical over-trigger', 'KG incompleteness', 'retrieval miss'] query=Under the closed-world demo structure, can a mammal fly despite RFC-7231 also mentioning methods?
- `adv_kg_dev_04` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['KG incompleteness', 'relational bridge confusion', 'retrieval miss'] query=Can a penguin fly if the public page says bird and wings nearby?
- `adv_hybrid_dev_03` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['public-document noise', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=What relation connects bat and mosquito when public text also mentions disease?
- `adv_hybrid_dev_04` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['relational bridge confusion', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=What bridge connects salmon and vertebrate, not the semantic concept water cycle?
- `adv_dense_dev_03` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'random_router', 'always_bm25', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'lexical over-trigger', 'public-document noise', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=What concept explains city neighborhoods acting like a heat section 164.512 trap?
- `adv_bm25_dev_06` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'retrieval miss'] query=Which sklearn class makes raw documents into TF-IDF features even though the query says topic meaning and semantic search?
- `adv_bm25_test_06` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'always_dense', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'public-document noise', 'retrieval miss'] query=Python dataclasses generated special methods, but do not route class substring to KG.
- `adv_dense_dev_05` failed_by=['computed_ras', 'keyword_rule_router', 'random_router', 'always_bm25', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'lexical over-trigger', 'evidence present in top-k but not top-1', 'answer synthesis miss'] query=Which condition is an immune false alarm for harmless pollen, not ICD-10 J18.9 pneumonia?
- `adv_dense_test_02` failed_by=['computed_ras', 'keyword_rule_router', 'classifier_router', 'always_bm25', 'always_kg', 'always_hybrid'] buckets=['route boundary confusion', 'lexical over-trigger'] query=What model keeps materials in use rather than waste, despite the exact phrase jsonb_set in the distractor?

## Baseline Subtype Wins

- classifier_router beats computed_ras on lexical_semantic_overlap: 0.800 vs 0.600.
- always_dense beats computed_ras on misleading_exact_term: 0.812 vs 0.438.
- classifier_router beats computed_ras on public_document_noise: 0.800 vs 0.700.
- random_router beats computed_ras on route_boundary_ambiguity: 0.800 vs 0.600.

## Tag Summary

- identifier_ambiguity: route_miss=0.000, answer_miss=0.125, evidence_miss=0.000, top1_topk_gap=0.125.
- identifier_with_distractor_language: route_miss=0.000, answer_miss=0.000, evidence_miss=0.000, top1_topk_gap=0.000.
- lexical_semantic_overlap: route_miss=0.467, answer_miss=0.400, evidence_miss=0.133, top1_topk_gap=0.267.
- misleading_exact_term: route_miss=0.625, answer_miss=0.562, evidence_miss=0.188, top1_topk_gap=0.438.
- noisy_structure: route_miss=0.091, answer_miss=0.182, evidence_miss=0.182, top1_topk_gap=0.000.
- public_document_noise: route_miss=0.400, answer_miss=0.300, evidence_miss=0.100, top1_topk_gap=0.200.
- route_boundary_ambiguity: route_miss=0.500, answer_miss=0.400, evidence_miss=0.200, top1_topk_gap=0.300.
- top1_topk_gap_risk: route_miss=0.000, answer_miss=0.091, evidence_miss=0.000, top1_topk_gap=0.182.
- wrong_bridge_distractor: route_miss=0.000, answer_miss=0.143, evidence_miss=0.071, top1_topk_gap=0.143.

## Known Limitations

- Hard cases are hand-constructed and intentionally route-boundary-heavy.
- Failure buckets are rule-assisted and inspectable, not learned labels.
- Answer correctness still uses normalized exact/soft string matching.

## Artifacts

- JSON: `data/eval/adversarial_failure_analysis.json`
- Markdown: `data/eval/adversarial_failure_analysis_summary.md`
