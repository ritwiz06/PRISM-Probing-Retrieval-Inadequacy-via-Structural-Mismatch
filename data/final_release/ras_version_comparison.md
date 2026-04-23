# RAS Version Comparison

| Version | Status | Model type | Selection rule | Uses evidence | Learned | Strength | Weakness |
|---|---|---|---|---:|---:|---|---|
| computed_ras | production | heuristic penalty table | argmin penalty | False | False | stable on curated/external/generalization/public benchmarks | route-boundary hard cases and top-k evidence rescue failures |
| computed_ras_v2 | analysis-only | rule overlay on computed_ras | computed_ras plus narrow overrides | False | False | surfaces hard-case route heuristics | not strong enough to replace production computed_ras |
| ras_v3 | analysis-only | multiclass sparse linear route model | argmax linear route adequacy score | False | True | formalizes route adequacy | route-only improvements do not close answer-accuracy gap on adversarial hard cases |
| ras_v4 | analysis-only | binary linear joint route/evidence adequacy model | argmax combined route + evidence adequacy score | True | True | makes evidence adequacy explicit and publication-friendly | recorded results still keep it analysis-only; rescue overlay remains complementary |
| calibrated_rescue | research overlay | calibrated hard-case router plus top-k rescue | optional overlay, not a core RAS version | True | False | stronger adversarial answer accuracy in recorded artifacts | overlay behavior, not the production route selection mechanism |

## Empirical Snapshot

```json
{
  "ras_v3": {
    "path": "data/eval/ras_v3_eval.json",
    "status": "keep_analysis_only",
    "computed_ras": {
      "route_accuracy": 0.75,
      "answer_accuracy": 0.9166666666666666
    },
    "ras_v3": {
      "route_accuracy": 0.8333333333333334,
      "answer_accuracy": 0.9166666666666666
    },
    "calibrated_rescue": {
      "route_accuracy": 0.875,
      "answer_accuracy": 0.9583333333333334
    }
  },
  "ras_v4": {
    "path": "data/eval/ras_v4_eval.json",
    "status": "keep_analysis_only",
    "computed_ras": {
      "route_accuracy": 0.75,
      "answer_accuracy": 0.9166666666666666
    },
    "ras_v4": {
      "route_accuracy": 0.75,
      "answer_accuracy": 0.9166666666666666
    },
    "calibrated_rescue": {
      "route_accuracy": 0.875,
      "answer_accuracy": 0.9583333333333334
    },
    "ras_v4_rescue": {
      "route_accuracy": 0.75,
      "answer_accuracy": 0.9583333333333334
    }
  },
  "calibrated": {
    "path": "data/eval/calibrated_router.json",
    "computed_ras_calibrated_topk_rescue": {
      "route_accuracy": 0.875,
      "answer_accuracy": 0.9583333333333334
    }
  }
}
```

Promotion decision: `computed_ras remains production; RAS_V3/RAS_V4/rescue remain research overlays.`
