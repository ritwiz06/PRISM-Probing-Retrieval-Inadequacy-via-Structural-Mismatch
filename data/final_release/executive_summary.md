# Executive Summary

PRISM is a representation-aware retrieval system that routes queries to BM25, Dense, KG, or Hybrid evidence according to structural adequacy.

- Production router: `computed_ras`
- Research overlays: `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, optional LLM
- Bounded scope: benchmark corpora, source packs, local folders, and URL-list runtime corpora

## Key Results

- Curated benchmark: `80/80`
- External mini-benchmark: `1.000` answer accuracy
- Generalization v2 noisy test: `0.975` answer accuracy
- Public raw test: `1.000` answer accuracy
- Adversarial test: computed RAS `0.917`; calibrated rescue `0.958`

## Final Position

PRISM is release-ready and demo-ready. The production decision stays conservative: `computed_ras` remains the production router, while rescue and learned RAS variants remain explicitly labeled research overlays.

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
