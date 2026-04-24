# Process Guide: Router Baselines And Route Confidence

## Basic Summary

This task added an optional router-evaluation layer to PRISM. It does not change the production demo path. Computed RAS is still the production router, but now PRISM can compare it against stronger router-specific baselines:

- computed RAS,
- a deterministic keyword rule router,
- a local TF-IDF classifier router,
- a fixed-seed random router,
- fixed-backend baselines from the existing analysis layer.

The main result is that computed RAS remains the best router on the current combined benchmark: `1.000` route accuracy and `1.000` answer accuracy over 112 curated + external examples.

## How Each Router Baseline Works

## Computed RAS

Computed RAS is the production router. It parses query features, computes representation mismatch penalties, and selects the backend with the lowest penalty.

This remains unchanged and lives in:

- `prism/ras/feature_parser.py`
- `prism/ras/penalty_table.py`
- `prism/ras/compute_ras.py`

## Keyword Rule Router

The keyword router is a transparent deterministic baseline in:

- `prism/router_baselines/rule_router.py`

It looks for obvious markers:

- lexical markers such as `RFC`, `HIPAA`, code identifiers, dotted API names, section numbers,
- deductive markers such as `can a`, `are all`, `is a`, `what property`,
- relational markers such as `bridge`, `connects`, `relation`, `path`,
- semantic markers such as `feels like`, `which concept`, `meaning`, `called`.

It returns:

- predicted route,
- simple normalized scores,
- a short rationale string.

## Classifier Router

The classifier router is a local lightweight baseline in:

- `prism/router_baselines/classifier_router.py`

It uses:

- `TfidfVectorizer` with character n-grams,
- `LogisticRegression`,
- fixed random seed,
- local save/load through pickle.

It returns:

- predicted route,
- class probabilities,
- a rationale string.

It is not used in production. It exists to answer the research question: can a small learned router compete with computed RAS on this local benchmark?

## Random Router

The random router is a fixed-seed baseline. It chooses from:

- `bm25`,
- `dense`,
- `kg`,
- `hybrid`.

It is included to show the floor for route accuracy and answer accuracy.

## Classifier-Router Evaluation Protocol

The evaluation avoids pretending that train-on-test is a fair result.

For the curated 80-query benchmark:

- The classifier uses 4-fold stratified cross-validation.
- Each curated prediction is made by a model that did not train on that specific query.

For the external 32-query mini-benchmark:

- The classifier trains on the full curated benchmark.
- It is evaluated on the separate external mini-benchmark.

For the combined 112-query summary:

- Curated rows use cross-validation predictions.
- External rows use the train-on-curated classifier.

This protocol is written into:

- `data/eval/router_baselines.json`
- `data/eval/router_baselines_summary.md`

## How Route Confidence Is Computed

Route confidence is analysis-only and lives in:

- `prism/router_baselines/route_confidence.py`

It combines three signals:

1. RAS margin: the difference between the best and second-best RAS backend scores.
2. Keyword agreement: whether the keyword router agrees with computed RAS.
3. Classifier agreement: whether the classifier router agrees with computed RAS.

The output includes:

- numeric confidence score,
- `high`, `medium`, or `low` label,
- selected backend,
- top competing backend,
- RAS scores,
- parsed features,
- route rationale.

The current combined run has:

- `107` high-confidence examples,
- `5` medium-confidence examples,
- `0` low-confidence examples,
- `0` route misses,
- `0` answer misses.

Because computed RAS has no misses on this benchmark, the analysis cannot show that lower confidence correlates with failures here. It can still identify the lowest-margin examples for inspection.

## Artifacts Generated

Router baseline artifacts:

- `data/eval/router_baselines.json`
- `data/eval/router_baselines.csv`
- `data/eval/router_baselines_summary.md`
- `data/eval/router_baseline_comparison.png`
- `data/eval/router_predicted_distribution.png`

Route confidence artifacts:

- `data/eval/route_confidence.json`
- `data/eval/route_confidence_summary.md`
- `data/eval/route_confidence_correctness.png`

Local classifier artifact:

- `data/eval/router_classifier.pkl`

The pickle model is a local generated artifact and is ignored by git because `*.pkl` is ignored.

## Concepts And Topics Used

- Router: the component that chooses which retrieval backend should answer a query.
- Route family: the intended representation family, such as lexical, semantic, deductive, or relational.
- Baseline: a comparison system used to judge whether PRISM's router is actually useful.
- TF-IDF: a local text feature representation based on term frequency and inverse document frequency.
- Logistic regression: a lightweight classifier used here to predict the route family.
- Cross-validation: splitting data into folds so each item is tested by a model that did not train on that exact item.
- Confusion matrix: counts of gold route versus predicted route.
- Predicted backend distribution: how often a router chooses each backend.
- RAS margin: how far the best computed RAS route is from the next-best route.
- Confidence bucket: a high, medium, or low label derived from route margin and router agreement.

## What Remains Unresolved

- The classifier router has only 80 curated training examples, so it is not a broad general-purpose router.
- The current benchmark is still small and balanced; broader public route benchmarks would be needed for stronger external validity.
- Confidence analysis is limited by the fact that computed RAS has no misses in this benchmark.
- The keyword router is intentionally simple and may underperform on ambiguous natural queries.
- The learned classifier is useful evidence, but replacing computed RAS with it would weaken PRISM's interpretability claim.
