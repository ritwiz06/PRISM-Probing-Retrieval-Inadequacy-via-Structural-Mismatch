# Process Guide: RAS V3 Framework

## Basic Summary

RAS_V3 is an additive, publishable routing experiment for PRISM. It turns RAS from a fixed penalty-table heuristic into an explicit feature-based linear routing model while preserving interpretability.

RAS_V3 is not the production router. Computed RAS remains the production default because RAS_V3 did not pass the strict promotion guardrails.

## How RAS_V3 Features Are Defined

Feature extraction lives in:

- `prism/ras_v3/features.py`

Each query is converted into a stable numeric feature vector. Important feature groups:

- lexical/formal identifier features
- semantic abstraction and paraphrase features
- deductive membership/property cue features
- relational bridge/path features
- route ambiguity and low-margin RAS features
- computed RAS selected-route one-hot features
- keyword-router selected-route one-hot features
- source/corpus-type features
- query-local graph availability
- public-document noise
- top-k rescue opportunity as an analysis feature

The feature vector is intentionally inspectable. `RASV3FeatureVector.metadata` records active features, computed RAS context, keyword-router context, parsed query-family signals, and route-boundary signals.

## How Weights Are Learned / Tuned

The model lives in:

- `prism/ras_v3/model.py`

RAS_V3 currently uses balanced multinomial logistic regression. This keeps the model lightweight and interpretable:

- no deep router training
- no paid APIs
- no hosted services
- learned coefficients are saved as JSON
- each route has a coefficient for each feature

The saved model artifact is:

- `data/eval/ras_v3_model.json`

Training protocol:

- curated 80-query benchmark
- generalization_v2 dev split
- public raw dev split
- adversarial dev split

Held out from tuning:

- adversarial test
- generalization_v2 test
- public raw test
- external mini-benchmark
- human annotations

Human annotations are used only for post-hoc alignment analysis.

## How Explanations Are Produced

Explanation logic lives in:

- `prism/ras_v3/scoring.py`
- `prism/ras_v3/explain.py`

For each query, RAS_V3 produces:

- per-route linear adequacy scores
- selected backend
- route margin
- active feature list
- per-feature contribution for each route
- natural-language rationale

The route selected by RAS_V3 is the backend with the highest learned adequacy score. This differs from original computed RAS, where lower penalty is better.

Artifacts:

- `data/eval/ras_v3_explanations.json`
- `data/eval/ras_v3_case_studies.md`
- `data/eval/ras_v3_feature_weights.json`

## How RAS_V3 Is Compared To Earlier Routers

The verifier lives in:

- `prism/ras_v3/verify_ras_v3.py`

It compares:

- computed RAS
- computed RAS v2
- RAS_V3
- calibrated rescue
- classifier router
- keyword router
- always BM25
- always Dense
- always KG
- always Hybrid

Evaluation layers:

- curated benchmark
- external mini-benchmark
- generalization_v2 test
- public raw-document test
- adversarial dev and test
- open-corpus smoke as a functional reference

Metrics:

- route accuracy
- answer accuracy
- evidence hit@k
- top-1 evidence hit
- per-family accuracy
- adversarial tag breakdown
- route confusion
- predicted backend distribution
- route margin / low-margin counts

Current adversarial test result:

- computed RAS answer accuracy: `0.917`
- RAS_V3 answer accuracy: `0.917`
- calibrated rescue answer accuracy: `0.958`

RAS_V3 improves adversarial route accuracy but not adversarial answer accuracy.

## How Human Alignment Is Measured

Human comparison output lives in:

- `data/human_eval/ras_v3_vs_human_summary.json`
- `data/human_eval/ras_v3_vs_human_summary.md`

The analysis reads the existing comparative human-eval packet and annotations. For items with a clear majority A/B preference, it compares:

- the route used by the human-preferred system output
- computed RAS route
- RAS_V3 route

Current result:

- majority-preference items evaluated: `2`
- computed RAS route alignment: `1.000`
- RAS_V3 route alignment: `1.000`
- delta: `+0.000`

Important limitation:

RAS_V3 outputs were not separately shown to human annotators. This is route-alignment analysis against existing preferences, not direct human evaluation of RAS_V3 answers.

## Promotion Decision

Promotion rules:

- adversarial overall must improve materially
- adversarial test must improve
- curated/external/generalization/public tests must not regress meaningfully
- model must remain interpretable
- human-eval alignment must not get worse
- RAS_V3 should beat calibrated rescue if it is replacing the central route path

Current decision:

- `keep_analysis_only`

Reason:

- RAS_V3 improves adversarial route accuracy
- RAS_V3 does not improve adversarial answer accuracy over computed RAS
- calibrated rescue remains better on adversarial answer accuracy
- human route-alignment does not improve
- guardrail benchmarks do not regress

Production default remains:

- `computed_ras`

## Artifacts Generated

Evaluation artifacts:

- `data/eval/ras_v3_eval.json`
- `data/eval/ras_v3_eval.csv`
- `data/eval/ras_v3_eval_summary.md`
- `data/eval/ras_v3_for_paper.md`

Model and interpretability artifacts:

- `data/eval/ras_v3_model.json`
- `data/eval/ras_v3_feature_weights.json`
- `data/eval/ras_v3_explanations.json`
- `data/eval/ras_v3_case_studies.md`

Human-alignment artifacts:

- `data/human_eval/ras_v3_vs_human_summary.json`
- `data/human_eval/ras_v3_vs_human_summary.md`

Plots:

- `data/eval/ras_v3_router_comparison.png`
- `data/eval/ras_v3_adversarial_tag_breakdown.png`
- `data/eval/ras_v3_feature_weights.png`

## What Remains Unresolved

RAS_V3 is more formal and interpretable than the fixed RAS table, but it is not yet a production replacement.

Open issues:

- adversarial route gains do not translate into answer gains
- answer quality still depends on retrieval and synthesis after route selection
- calibrated rescue remains stronger because it can reorder top-k evidence
- human alignment is limited by the number of clear majority-preference items
- a stronger future study should add RAS_V3 outputs directly to comparative human evaluation

## Concepts And Topics Used

Feature-based routing:

The route is selected by explicit query/corpus features rather than by opaque prompting.

Linear adequacy score:

Each route receives a weighted score. Higher means the route is predicted to be more adequate for the query.

Per-feature contribution:

The score can be decomposed into individual feature contributions for a route.

Guardrail dataset:

A benchmark layer used to check that a new route model does not regress stable PRISM behavior.

Analysis-only router:

A router variant used for experiments and report artifacts, not the default app path.

Human route alignment:

A post-hoc comparison between a router's selected route and the route used by the system output humans preferred in comparative evaluation.
