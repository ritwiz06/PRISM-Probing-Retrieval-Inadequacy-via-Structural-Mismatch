# Router Baseline Summary

Computed RAS remains the production router. All other routers are analysis-only baselines.

## Protocol

- Classifier curated protocol: 4-fold stratified cross-validation on curated benchmark.
- Classifier external protocol: Classifier trained on full curated 80-query benchmark and evaluated on external mini-benchmark.
- Classifier combined protocol: Combined result uses curated cross-validation predictions plus external train-curated predictions.

## Combined Router Results

| Router | Route accuracy | Answer accuracy | Predicted distribution |
| --- | ---: | ---: | --- |
| computed_ras | 1.000 | 1.000 | {'bm25': 28, 'dense': 28, 'kg': 28, 'hybrid': 28} |
| keyword_rule_router | 0.884 | 0.929 | {'bm25': 28, 'dense': 21, 'kg': 31, 'hybrid': 32} |
| classifier_router | 0.964 | 1.000 | {'bm25': 30, 'dense': 29, 'kg': 25, 'hybrid': 28} |
| random_router | 0.357 | 0.598 | {'kg': 25, 'bm25': 32, 'hybrid': 28, 'dense': 27} |

## Strongest Fixed Backend Baselines

- curated: always_hybrid with answer_accuracy=0.688, route_accuracy=0.250.
- external: always_hybrid with answer_accuracy=0.688, route_accuracy=0.250.
- combined: always_hybrid with answer_accuracy=0.688, route_accuracy=0.250.

## Takeaways

- Computed RAS combined route accuracy is 1.000 and answer accuracy is 1.000.
- Keyword router combined route accuracy is 0.884; classifier router combined route accuracy is 0.964.
- Strongest fixed backend on combined answer accuracy is always_hybrid at 0.688.
- No route or answer misses occurred for computed RAS on this combined benchmark, so low-confidence routing cannot be correlated with misses here.

## Artifacts

- JSON: `data/eval/router_baselines.json`
- CSV: `data/eval/router_baselines.csv`
- Confidence JSON: `data/eval/route_confidence.json`
- Router comparison plot: `data/eval/router_baseline_comparison.png`
- Predicted distribution plot: `data/eval/router_predicted_distribution.png`
- Confidence plot: `data/eval/route_confidence_correctness.png`
