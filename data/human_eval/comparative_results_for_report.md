# Comparative Human-Eval Results For Report

## What Was Compared

System A is normal computed RAS. System B is one of: calibrated rescue, classifier router, or a fixed-backend baseline.

## Why These Items Were Selected

The packet prioritizes adversarial, public raw, held-out, and curated examples where routing, evidence, or traces are likely to differ.

## What Evaluators Judge

Evaluators choose A, B, or Tie for answer support, trace faithfulness, trace clarity, route appropriateness, and overall preference.

## Current Takeaways

- computed_ras_vs_always_bm25: B win rate 0.000; tie rate 0.375.
- computed_ras_vs_always_dense: B win rate 0.125; tie rate 0.500.
- computed_ras_vs_calibrated_rescue: B win rate 0.062; tie rate 0.938.
- computed_ras_vs_classifier_router: B win rate 0.042; tie rate 0.917.

## Human Vs Automatic

- Calibrated rescue preferred while both systems automatically correct: 2.
- Classifier router preferred on adversarial items: 2.
- System B preferred when System A was automatically correct: 6.

## Threats To Validity

- Small annotator pool can make preference estimates unstable.
- Forced-choice A/B/Tie judgments can hide nuance.
- Comparative packet size is practical but limited.
- Evaluator familiarity with PRISM may bias preferences.
- Hard-case construction overlaps with the systems being compared.
