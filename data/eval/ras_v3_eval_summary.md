# RAS V3 Evaluation Summary

Production router after evaluation: `computed_ras`.
Decision: `keep_analysis_only`.

## Protocol

- Fit data: curated 80-query benchmark, generalization_v2 dev, public raw dev, and adversarial dev.
- Held-out reporting: external mini, generalization_v2 test, public raw test, adversarial test, and open-corpus smoke are reporting/sanity layers.
- Not used for tuning: adversarial_test, generalization_v2_test, public_raw_test, external_mini, human_annotations

## Adversarial Test Comparison

| System | Route accuracy | Answer accuracy | Evidence hit@k | Mean margin |
| --- | ---: | ---: | ---: | ---: |
| computed_ras | 0.750 | 0.917 | 0.958 | 0.542 |
| computed_ras_v2 | 0.708 | 0.875 | 0.917 | 0.542 |
| ras_v3 | 0.833 | 0.917 | 0.958 | 2.582 |
| calibrated_rescue | 0.875 | 0.958 | 0.958 | 0.754 |
| classifier_router | 0.792 | 0.875 | 0.958 | 0.207 |
| keyword_router | 0.625 | 0.917 | 1.000 | 0.900 |
| always_bm25 | 0.250 | 0.750 | 0.917 | 0.000 |
| always_dense | 0.250 | 0.833 | 0.917 | 0.000 |
| always_kg | 0.250 | 0.458 | 0.500 | 0.000 |
| always_hybrid | 0.250 | 0.625 | 1.000 | 0.000 |

## Guardrail Datasets

- curated: computed RAS answer=1.000, RAS_V3 answer=1.000, delta=+0.000.
- external_mini: computed RAS answer=1.000, RAS_V3 answer=1.000, delta=+0.000.
- generalization_v2_test: computed RAS answer=1.000, RAS_V3 answer=1.000, delta=+0.000.
- public_raw_test: computed RAS answer=1.000, RAS_V3 answer=1.000, delta=+0.000.

## Baseline Takeaways

- adversarial_test: strongest answer system is calibrated_rescue at 0.958; RAS_V3=0.917, computed RAS=0.917.
- curated: strongest answer system is computed_ras at 1.000; RAS_V3=1.000, computed RAS=1.000.
- external_mini: strongest answer system is computed_ras at 1.000; RAS_V3=1.000, computed RAS=1.000.
- generalization_v2_test: strongest answer system is computed_ras at 1.000; RAS_V3=1.000, computed RAS=1.000.
- public_raw_test: strongest answer system is computed_ras at 1.000; RAS_V3=1.000, computed RAS=1.000.

## Promotion Decision

- RAS_V3 remains analysis-only because at least one strict guardrail was not met.
- Adversarial answer delta vs computed RAS: +0.000
- Human alignment delta vs computed RAS: +0.000
- Beats calibrated rescue: False

## Artifacts

- json: `data/eval/ras_v3_eval.json`
- csv: `data/eval/ras_v3_eval.csv`
- markdown: `data/eval/ras_v3_eval_summary.md`
- feature_weights: `data/eval/ras_v3_feature_weights.json`
- explanations: `data/eval/ras_v3_explanations.json`
- case_studies: `data/eval/ras_v3_case_studies.md`
- paper: `data/eval/ras_v3_for_paper.md`
- human_json: `data/human_eval/ras_v3_vs_human_summary.json`
- human_markdown: `data/human_eval/ras_v3_vs_human_summary.md`
- comparison_plot: `data/eval/ras_v3_router_comparison.png`
- tag_plot: `data/eval/ras_v3_adversarial_tag_breakdown.png`
- weights_plot: `data/eval/ras_v3_feature_weights.png`
- model: `data/eval/ras_v3_model.json`
