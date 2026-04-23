# PROCESS GUIDE 2026-04-22 13:32 - RAS_V4 Joint Adequacy

## Basic Summary

RAS_V4 extends PRISM routing from route-only adequacy to joint route-and-evidence adequacy. It asks two questions for every candidate backend: whether the backend representation fits the query, and whether the evidence retrieved by that backend looks strong enough to support an answer. RAS_V4 is additive and analysis-only; production still uses computed RAS.

## How RAS_V4 Features Are Defined

RAS_V4 builds one feature vector per query/backend candidate. The vector has two groups:

- `route__*` features: RAS_V3-style route suitability signals, including lexical, semantic, deductive, relational, ambiguity, source-type, and query-local graph features.
- `evidence__*` features: top-k evidence support signals, including score gaps, query overlap, identifier matches, KG/path signals, hybrid agreement, noise indicators, and answerability markers.

The final model scores `bm25`, `dense`, `kg`, and `hybrid` independently, then selects the backend with the highest joint adequacy score.

## How Evidence-Adequacy Features Are Computed

Evidence adequacy is computed from retrieved items only. It does not use gold labels at inference time.

Signals include:

- `top1_score`, `topk_score_mean`, and `top1_top2_gap` for retrieval confidence.
- `query_overlap_top1` and `query_overlap_topk` for lexical/evidence grounding.
- `identifier_exact_match` and `title_or_id_match` for public and identifier-heavy queries.
- `source_diversity` and `redundancy` for evidence breadth and repeated support.
- `kg_fact_or_path_present` and `kg_path_completeness` for structured reasoning.
- `hybrid_component_agreement` for fused BM25/Dense/KG agreement.
- `semantic_snippet_consistency` for concept overlap.
- `negation_or_distractor_contamination` and `public_noise_indicator` for noisy evidence risk.
- `answerability_marker` for snippets that contain answer-like factual language.

These diagnostics are stored with each RAS_V4 candidate so decisions can be audited.

## How Weights Are Learned and Tuned

RAS_V4 uses a lightweight, deterministic logistic regression over candidate backend feature vectors. The model is trained as a binary adequacy scorer: each query/backend candidate is positive when the candidate backend matches the benchmark route family and negative otherwise.

Training and tuning protocol:

- Fit data: curated benchmark, generalization_v2 dev split, public raw dev split, and adversarial dev split.
- Held-out reporting: external mini-benchmark, generalization_v2 test, public raw test, adversarial test, and open-corpus smoke.
- Not used for tuning: adversarial test, generalization_v2 test, public raw test, external mini, and human annotations.

The learned model is saved to `data/eval/ras_v4_model.json` with feature names, weights, intercept, and protocol metadata.

## How Explanations Are Produced

For every RAS_V4 decision, PRISM records:

- per-backend combined adequacy score
- route-only contribution
- evidence-only contribution
- final route margin
- top positive and negative feature contributions
- evidence diagnostics
- a natural-language rationale

The main explanation artifacts are `data/eval/ras_v4_explanations.json` and `data/eval/ras_v4_case_studies.md`.

## How RAS_V4 Is Compared to Earlier Routers and Rescue

The verifier compares:

- `computed_ras`
- `computed_ras_v2`
- `ras_v3`
- `calibrated_rescue`
- `classifier_router`
- `ras_v4`
- `ras_v4_rescue`
- fixed backend baselines

Metrics include route accuracy, answer accuracy, evidence hit@k, top-1 evidence hit, per-family accuracy, adversarial tag breakdown, route confusion, route margin, and contribution summaries.

The key result is that RAS_V4 preserves stable guardrails but does not improve adversarial answer accuracy by itself. On adversarial test, RAS_V4 answer accuracy is `0.917`, matching computed RAS and RAS_V3. RAS_V4 plus rescue reaches `0.958`, matching calibrated rescue.

## How Human Alignment Is Measured

RAS_V4 is compared to existing real comparative human-eval preferences. The analysis checks whether RAS_V4 route choices align with the route used by the human-majority preferred system when that can be inferred from the comparative packet.

Current result:

- Majority-preference items evaluated: `2`
- Computed RAS preferred-route alignment: `1.000`
- RAS_V4 preferred-route alignment: `1.000`
- Alignment delta: `+0.000`

This is a limited proxy because RAS_V4 outputs were not directly annotated by humans.

## Artifacts Generated

- `data/eval/ras_v4_eval.json`
- `data/eval/ras_v4_eval.csv`
- `data/eval/ras_v4_eval_summary.md`
- `data/eval/ras_v4_model.json`
- `data/eval/ras_v4_feature_weights.json`
- `data/eval/ras_v4_explanations.json`
- `data/eval/ras_v4_case_studies.md`
- `data/eval/ras_v4_vs_rescue_summary.md`
- `data/eval/ras_v4_for_paper.md`
- `data/eval/ras_v4_router_comparison.png`
- `data/eval/ras_v4_adversarial_tag_breakdown.png`
- `data/eval/ras_v4_route_vs_evidence_contribution.png`
- `data/human_eval/ras_v4_vs_human_summary.json`
- `data/human_eval/ras_v4_vs_human_summary.md`

## What Remains Unresolved

RAS_V4 is not promoted to production because it does not materially improve adversarial answer accuracy over computed RAS. The main unresolved issue is that hard-case answer quality often depends on post-route top-k evidence rescue, not only backend selection. A future publishable version should either integrate answer-layer support more directly or collect human judgments specifically over RAS_V4 outputs.

## Concepts and Topics Used

- Representation Adequacy Score
- route adequacy
- evidence adequacy
- interpretable routing
- logistic regression
- top-k evidence diagnostics
- answerability estimation
- route margin and confidence
- adversarial hard-case evaluation
- calibrated rescue
- human-eval alignment
- production guardrails
