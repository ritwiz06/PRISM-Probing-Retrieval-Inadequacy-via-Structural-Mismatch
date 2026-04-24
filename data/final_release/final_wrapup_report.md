# Final Wrap-Up Report

## Problem

PRISM studies retrieval inadequacy caused by structural mismatch. A query can fail not because retrieval is impossible, but because the wrong representation was used.

## System Design

The system routes queries to BM25, Dense, KG, or Hybrid evidence. The production router is `computed_ras`, which remains deterministic and explicit. Research layers include calibrated rescue, classifier routing, RAS_V3, and RAS_V4.

## Main Benchmarks

```json
[
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
```

## Strongest Results

- Stable curated, external, held-out, public raw, public graph, and open-corpus smoke performance.
- Public raw-document and public-graph evaluations remain strong without changing the production router.
- Human evaluation supports evidence/trace usefulness.

## Hardest Failure Cases

Adversarial route-boundary cases remain the main weakness.

```json
[
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
```

## RAS Evolution

- `computed_ras`: production heuristic router.
- `computed_ras_v2`: narrow hard-case refinement, analysis-only.
- `ras_v3`: interpretable route-only model.
- `ras_v4`: interpretable joint route-and-evidence adequacy model.

## Why Calibrated Rescue Matters

Calibrated rescue remains important because route adequacy alone does not fully recover adversarial answer accuracy. Rescue improves answerability by making better use of top-k evidence after retrieval.

## Human Evaluation Summary

```json
[
  {
    "dimension": "route appropriateness",
    "mean_score": 2.8958333333333335
  },
  {
    "dimension": "evidence sufficiency",
    "mean_score": 2.9166666666666665
  },
  {
    "dimension": "answer faithfulness",
    "mean_score": 2.9166666666666665
  },
  {
    "dimension": "trace faithfulness",
    "mean_score": 2.9305555555555554
  },
  {
    "dimension": "trace clarity",
    "mean_score": 2.9444444444444446
  },
  {
    "dimension": "overall usefulness",
    "mean_score": 2.875
  }
]
```

Comparative human preferences:

```json
[
  {
    "pair": "computed_ras_vs_always_bm25",
    "a_win_rate": 0.625,
    "b_win_rate": 0.0,
    "tie_rate": 0.375
  },
  {
    "pair": "computed_ras_vs_always_dense",
    "a_win_rate": 0.375,
    "b_win_rate": 0.125,
    "tie_rate": 0.5
  },
  {
    "pair": "computed_ras_vs_calibrated_rescue",
    "a_win_rate": 0.0,
    "b_win_rate": 0.0625,
    "tie_rate": 0.9375
  },
  {
    "pair": "computed_ras_vs_classifier_router",
    "a_win_rate": 0.041666666666666664,
    "b_win_rate": 0.041666666666666664,
    "tie_rate": 0.9166666666666666
  }
]
```

## Open-Corpus / Generalization Summary

PRISM now supports bounded source-pack, local-folder, and URL-list corpora. This extends the system beyond fixed benchmarks while preserving reproducibility and provenance.

## Final Production vs Research Conclusion

Production router remains `computed_ras`.

Research overlays remain:
- `calibrated_rescue`
- `classifier_router`
- `ras_v3`
- `ras_v4`
- optional local LLM

The final project is presentation-ready and submission-ready, but the scientific story remains explicit and conservative.

```json
{
  "production_router": "computed_ras",
  "production_decision": "computed_ras remains production default",
  "research_overlays": [
    "calibrated_rescue",
    "ras_v3",
    "ras_v4",
    "classifier_router",
    "optional_llm"
  ],
  "source_pack_names": [
    "cs_api_docs",
    "medical_codes",
    "policy_docs",
    "rfc_specs",
    "wikipedia"
  ],
  "curated": {
    "total": 80,
    "route_accuracy": 1.0,
    "evidence_hit_at_k": 1.0,
    "passed": true,
    "path": "data/eval/end_to_end_verification.json"
  },
  "external_mini": {
    "total": 32,
    "route_accuracy": 1.0,
    "answer_accuracy": 0.96875,
    "dense_backend": "numpy_fallback",
    "path": "data/eval/external_generalization.json"
  },
  "generalization_v2": {
    "route_accuracy": 0.95,
    "answer_accuracy": 0.975,
    "evidence_hit_at_k": null,
    "top1_evidence_hit": null,
    "path": "data/eval/generalization_v2.json"
  },
  "public_raw": {
    "route_accuracy": 0.9166666666666666,
    "answer_accuracy": 0.875,
    "evidence_hit_at_k": 0.9166666666666666,
    "top1_evidence_hit": null,
    "path": "data/eval/public_corpus_eval.json"
  },
  "public_graph_test": {
    "route_accuracy": 1.0,
    "answer_accuracy": 1.0,
    "evidence_hit_at_k": 1.0,
    "top1_evidence_hit": null,
    "path": "data/eval/public_graph_eval.json"
  },
  "adversarial": {
    "route_accuracy": 0.7291666666666666,
    "answer_accuracy": 0.7291666666666666,
    "evidence_hit_at_k": 0.8958333333333334,
    "top1_evidence_hit": 0.6875,
    "path": "data/eval/adversarial_eval.json"
  },
  "adversarial_test": {
    "route_accuracy": 0.75,
    "answer_accuracy": 0.9166666666666666,
    "evidence_hit_at_k": 0.9583333333333334,
    "top1_evidence_hit": 0.875,
    "path": "data/eval/adversarial_eval.json"
  },
  "calibrated_adversarial_test": {
    "route_accuracy": 0.875,
    "answer_accuracy": 0.9583333333333334,
    "evidence_hit_at_k": 0.9583333333333334,
    "top1_evidence_hit": 0.9166666666666666,
    "path": "data/eval/calibrated_router.json"
  },
  "ras_v3_adversarial_test": {
    "route_accuracy": 0.8333333333333334,
    "answer_accuracy": 0.9166666666666666,
    "evidence_hit_at_k": 0.9583333333333334,
    "top1_evidence_hit": 0.875,
    "path": "data/eval/ras_v3_eval.json"
  },
  "ras_v4_adversarial_test": {
    "route_accuracy": 0.75,
    "answer_accuracy": 0.9166666666666666,
    "evidence_hit_at_k": 0.9583333333333334,
    "top1_evidence_hit": 0.875,
    "path": "data/eval/ras_v4_eval.json"
  },
  "ras_v4_rescue_adversarial_test": {
    "route_accuracy": 0.75,
    "answer_accuracy": 0.9583333333333334,
    "evidence_hit_at_k": 0.9583333333333334,
    "top1_evidence_hit": 0.9166666666666666,
    "path": "data/eval/ras_v4_eval.json"
  },
  "human_eval": {
    "status": "annotations_loaded",
    "packet_size": 36,
    "annotation_count": 144,
    "evaluator_count": 4,
    "path": "data/human_eval/human_eval_summary.json"
  },
  "comparative_human_eval": {
    "status": "comparative_annotations_loaded",
    "packet_size": 28,
    "annotation_count": 112,
    "evaluator_count": 4,
    "path": "data/human_eval/comparative_summary.json"
  },
  "open_corpus_smoke": {
    "status": "passed",
    "path": "data/eval/open_corpus_smoke.json"
  }
}
```
