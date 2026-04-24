# Final Speaker Script

## Opening

PRISM asks a simple question: if different questions require different evidence structures, why force every query through the same retriever?

## Core Story

1. PRISM extracts route-relevant signals from the query.
2. The production router, `computed_ras`, selects BM25, Dense, KG, or Hybrid.
3. Evidence stays visible and cited.
4. Research overlays remain visible, but the production decision stays explicit.

## Results To Show

- Benchmark overview: [
  {
    "benchmark": "Curated",
    "route_accuracy": 1.0,
    "answer_accuracy": 1.0
  },
  {
    "benchmark": "External Mini",
    "route_accuracy": 1.0,
    "answer_accuracy": 0.96875
  },
  {
    "benchmark": "GenV2 Clean",
    "route_accuracy": 0.95,
    "answer_accuracy": 1.0
  },
  {
    "benchmark": "GenV2 Noisy",
    "route_accuracy": 0.95,
    "answer_accuracy": 0.975
  },
  {
    "benchmark": "Public Raw",
    "route_accuracy": 0.9166666666666666,
    "answer_accuracy": 0.875
  },
  {
    "benchmark": "Public Graph",
    "route_accuracy": 1.0,
    "answer_accuracy": 1.0
  },
  {
    "benchmark": "Adversarial Test",
    "route_accuracy": 0.75,
    "answer_accuracy": 0.9166666666666666
  }
]
- Adversarial router comparison: [
  {
    "system": "computed_ras",
    "answer_accuracy": 0.9166666666666666,
    "route_accuracy": 0.75,
    "status": "production"
  },
  {
    "system": "calibrated_rescue",
    "answer_accuracy": 0.9583333333333334,
    "route_accuracy": 0.875,
    "status": "research overlay"
  },
  {
    "system": "classifier_router",
    "answer_accuracy": 0.875,
    "route_accuracy": 0.7916666666666666,
    "status": "research baseline"
  },
  {
    "system": "ras_v3",
    "answer_accuracy": 0.9166666666666666,
    "route_accuracy": 0.8333333333333334,
    "status": "analysis-only"
  },
  {
    "system": "ras_v4",
    "answer_accuracy": 0.9166666666666666,
    "route_accuracy": 0.75,
    "status": "analysis-only"
  }
]

## Closing

Route adequacy matters, but route-only adequacy is not enough on hard cases. That is why calibrated rescue remains part of the research story even though `computed_ras` remains the production router.
