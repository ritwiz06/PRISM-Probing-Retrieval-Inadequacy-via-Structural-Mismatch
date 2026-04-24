# PRISM Human-Evaluation Results For Paper

## Study Setup

- Standard packet size: 36.
- Comparative packet size: 28.
- Standard evaluator count: 4.
- Comparative evaluator count: 4.

## Standard Human-Eval Findings

- route_appropriateness: mean 2.896.
- evidence_sufficiency: mean 2.917.
- answer_faithfulness: mean 2.917.
- trace_faithfulness: mean 2.931.
- trace_clarity: mean 2.944.
- overall_usefulness: mean 2.875.
- Trace faithfulness mean: 2.9305555555555554.
- Trace clarity mean: 2.9444444444444446.

## Comparative Findings

- computed_ras_vs_always_bm25: A win 0.625, B win 0.000, tie 0.375.
- computed_ras_vs_always_dense: A win 0.375, B win 0.125, tie 0.500.
- computed_ras_vs_calibrated_rescue: A win 0.000, B win 0.062, tie 0.938.
- computed_ras_vs_classifier_router: A win 0.042, B win 0.042, tie 0.917.
- Adjudication queue size: 12.

## Agreement And Caveats

- Agreement should be interpreted cautiously because the evaluator pool and packet sizes are small.
- Forced-choice comparative judgments can hide nuance.
- Automatic correctness is normalized string matching, not a substitute for human support judgments.

## Threats To Validity

- Small annotator pool can make preference estimates unstable.
- Forced-choice A/B/Tie judgments can hide nuance.
- Comparative packet size is practical but limited.
- Evaluator familiarity with PRISM may bias preferences.
- Hard-case construction overlaps with the systems being compared.
