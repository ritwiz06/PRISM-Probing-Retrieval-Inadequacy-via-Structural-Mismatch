# RAS V2 Route-Improvement Summary

Protocol: RAS v2 is analysis-only and evaluated on the adversarial benchmark after dev-informed heuristic design.
Production default: `computed_ras`.
Recommendation: `keep_analysis_only`.
Answer accuracy delta v2-minus-RAS: 0.02083333333333337.

## Systems
- computed_ras: route=0.7291666666666666 answer=0.7291666666666666 evidence=0.8958333333333334.
- computed_ras_v2: route=0.7291666666666666 answer=0.75 evidence=0.8958333333333334.
- computed_ras_calibrated_topk_rescue_test_reference: route=0.875 answer=0.9583333333333334 evidence=0.9583333333333334.
- classifier_router_test_reference: route=0.7916666666666666 answer=0.875 evidence=0.9583333333333334.

## Interpretation
RAS v2 remains analysis-only unless it shows material hard-case gains without regressions on curated/public/generalization benchmarks.
