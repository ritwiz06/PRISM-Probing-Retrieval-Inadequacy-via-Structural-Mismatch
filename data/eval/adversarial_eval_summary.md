# Adversarial Hard-Case Evaluation

This suite is intentionally harder than the clean curated/public benchmarks. It targets route-boundary ambiguity, near-miss evidence, and misleading exact terms.

Benchmark path: `data/processed/adversarial_benchmark.jsonl`.
Benchmark total: 48.
Benchmark counts: {'split': {'dev': 24, 'test': 24}, 'intended_route_family': {'bm25': 12, 'dense': 12, 'hybrid': 12, 'kg': 12}, 'difficulty': {'adversarial': 24, 'hard': 24}, 'ambiguity_tags': {'identifier_ambiguity': 8, 'identifier_with_distractor_language': 3, 'lexical_semantic_overlap': 15, 'misleading_exact_term': 16, 'noisy_structure': 11, 'public_document_noise': 10, 'route_boundary_ambiguity': 10, 'top1_topk_gap_risk': 11, 'wrong_bridge_distractor': 14}}.
Retrieval context: {'document_count': 256, 'triple_count': 103, 'corpus_mode': 'noisy local corpus plus public raw corpus; mixed demo KG plus public graph triples'}.

## Combined Results

| System | Route accuracy | Answer accuracy | Evidence hit@k | Top-1 evidence hit |
| --- | ---: | ---: | ---: | ---: |
| computed_ras | 0.729 | 0.729 | 0.896 | 0.688 |
| keyword_rule_router | 0.604 | 0.708 | 0.938 | 0.667 |
| classifier_router | 0.833 | 0.792 | 0.938 | 0.750 |
| random_router | 0.292 | 0.604 | 0.792 | 0.542 |
| always_bm25 | 0.250 | 0.604 | 0.896 | 0.625 |
| always_dense | 0.250 | 0.771 | 0.896 | 0.729 |
| always_kg | 0.250 | 0.417 | 0.458 | 0.438 |
| always_hybrid | 0.250 | 0.625 | 1.000 | 0.583 |

## Computed RAS By Ambiguity Tag

- identifier_ambiguity: answer=0.875, route=1.000, evidence_hit@k=1.000, top1=0.875.
- identifier_with_distractor_language: answer=1.000, route=1.000, evidence_hit@k=1.000, top1=1.000.
- lexical_semantic_overlap: answer=0.600, route=0.533, evidence_hit@k=0.867, top1=0.600.
- misleading_exact_term: answer=0.438, route=0.375, evidence_hit@k=0.812, top1=0.375.
- noisy_structure: answer=0.818, route=0.909, evidence_hit@k=0.818, top1=0.818.
- public_document_noise: answer=0.700, route=0.600, evidence_hit@k=0.900, top1=0.700.
- route_boundary_ambiguity: answer=0.600, route=0.500, evidence_hit@k=0.800, top1=0.500.
- top1_topk_gap_risk: answer=0.909, route=1.000, evidence_hit@k=1.000, top1=0.818.
- wrong_bridge_distractor: answer=0.857, route=1.000, evidence_hit@k=0.929, top1=0.786.

## Strongest Fixed Backend

- always_dense at answer accuracy 0.771.

## Takeaways

- Computed RAS hard-benchmark route accuracy is 0.729; answer accuracy is 0.729.
- Strongest fixed backend is always_dense at answer accuracy 0.771.
- Weakest ambiguity tag for computed RAS is misleading_exact_term.
- Low confidence is more error-prone on hard cases: low combined miss rate=1.000, high combined miss rate=0.324.
- Semantic rerank delta: no_rerank answer accuracy 0.708 vs normal 0.729.
- Public lexical arbitration delta: arbitrated answer accuracy 0.708 vs normal 0.729.
- Structure subset public_graph answer accuracy 0.750 vs mixed 0.833.
- dev: computed RAS answer accuracy 0.542; evidence hit@k 0.833.
- test: computed RAS answer accuracy 0.917; evidence hit@k 0.958.

## Threats To Validity

- Hard cases are hand-constructed and source-selected, so they diagnose stress behavior rather than estimate real-world prevalence.
- The benchmark is intentionally small and adversarial; scores should not be compared directly to clean curated benchmark scores.
- Some examples are grounded in compact local/public artifacts, not broad web-scale evidence.
- Answer matching is normalized string matching rather than human evaluation.
- A baseline may win on a subtype because the subtype is intentionally route-boundary-heavy.

## Artifacts

- JSON: `data/eval/adversarial_eval.json`
- CSV: `data/eval/adversarial_eval.csv`
- Markdown: `data/eval/adversarial_eval_summary.md`
- Confidence JSON: `data/eval/adversarial_confidence.json`
- Confidence Markdown: `data/eval/adversarial_confidence_summary.md`
- Ablation Markdown: `data/eval/adversarial_ablation_summary.md`
- Plot: `data/eval/adversarial_baselines_by_tag.png`
- Plot: `data/eval/adversarial_confidence_error_rate.png`
- Plot: `data/eval/adversarial_top1_topk_gap.png`
