# Calibrated Router And Top-k Rescue Evaluation

This is an optional analysis layer. Computed RAS remains the production router by default.

## Protocol

- Config selected using adversarial dev split route accuracy only; adversarial test is held out.
- Top-k rescue reorders retrieved evidence only; it does not fetch new evidence and does not use gold labels.
- Adversarial test, curated, external, generalization_v2 test, and public raw test are evaluation-only sanity checks.

## Selected Calibrator

- `classifier_heavier` with config `{'name': 'classifier_heavier', 'classifier_probability_threshold': 0.35, 'classifier_margin_threshold': 0.04, 'allow_classifier_override': True, 'allow_semantic_bait_override': True, 'allow_structural_override': True, 'allow_identifier_kg_suppression': True}`.

## Adversarial Test Comparison

| System | Route accuracy | Answer accuracy | Evidence hit@k | Top-1 evidence hit | Overrides | Rescues |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| computed_ras | 0.750 | 0.917 | 0.958 | 0.875 | 0 | 0 |
| computed_ras_calibrated | 0.875 | 0.958 | 0.958 | 0.917 | 3 | 0 |
| computed_ras_topk_rescue | 0.750 | 0.958 | 0.958 | 0.917 | 0 | 2 |
| computed_ras_calibrated_topk_rescue | 0.875 | 0.958 | 0.958 | 0.917 | 3 | 0 |
| classifier_router | 0.792 | 0.875 | 0.958 | 0.875 | 0 | 0 |
| always_bm25 | 0.250 | 0.750 | 0.917 | 0.792 | 0 | 0 |
| always_dense | 0.250 | 0.833 | 0.917 | 0.792 | 0 | 0 |
| always_kg | 0.250 | 0.458 | 0.500 | 0.458 | 0 | 0 |
| always_hybrid | 0.250 | 0.625 | 1.000 | 0.625 | 0 | 0 |

## Cross-Benchmark Sanity Checks

- curated: normal answer=1.000, calibrated+rescue answer=1.000, delta=+0.000.
- external_mini: normal answer=1.000, calibrated+rescue answer=1.000, delta=+0.000.
- generalization_v2_test: normal answer=1.000, calibrated+rescue answer=1.000, delta=+0.000.
- public_raw_test: normal answer=1.000, calibrated+rescue answer=1.000, delta=+0.000.

## Per-Ambiguity Tag On Adversarial Test

- identifier_ambiguity: answer=1.000, route=1.000, top1=1.000.
- identifier_with_distractor_language: answer=1.000, route=1.000, top1=1.000.
- lexical_semantic_overlap: answer=0.857, route=0.857, top1=0.857.
- misleading_exact_term: answer=0.833, route=0.833, top1=0.667.
- noisy_structure: answer=1.000, route=1.000, top1=1.000.
- public_document_noise: answer=1.000, route=0.667, top1=1.000.
- route_boundary_ambiguity: answer=1.000, route=0.667, top1=0.833.
- top1_topk_gap_risk: answer=1.000, route=1.000, top1=1.000.
- wrong_bridge_distractor: answer=1.000, route=1.000, top1=1.000.

## Takeaways

- Adversarial test normal computed RAS answer accuracy 0.917.
- Calibrated-only answer accuracy 0.958.
- Top-k rescue-only answer accuracy 0.958.
- Calibrated+rescue answer accuracy 0.958.
- Strongest fixed backend on adversarial test is always_dense at 0.833.
- Failure delta fixed 1 prior failures and regressed 0.

## Tradeoffs

- curated: calibrated+rescue stayed flat by +0.000 answer accuracy versus normal RAS.
- external_mini: calibrated+rescue stayed flat by +0.000 answer accuracy versus normal RAS.
- generalization_v2_test: calibrated+rescue stayed flat by +0.000 answer accuracy versus normal RAS.
- public_raw_test: calibrated+rescue stayed flat by +0.000 answer accuracy versus normal RAS.
- Calibration and rescue remain optional analysis modes; production computed RAS stays unchanged.

## Artifacts

- json: `data/eval/calibrated_router.json`
- csv: `data/eval/calibrated_router.csv`
- markdown: `data/eval/calibrated_router_summary.md`
- failure_delta_json: `data/eval/calibrated_failure_delta.json`
- failure_delta_markdown: `data/eval/calibrated_failure_delta_summary.md`
- adversarial_test_plot: `data/eval/calibrated_adversarial_test_comparison.png`
- failure_delta_plot: `data/eval/calibrated_failure_delta.png`
