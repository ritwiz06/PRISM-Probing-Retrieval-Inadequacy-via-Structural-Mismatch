# RAS V3 For Paper

RAS_V3 formalizes PRISM routing as a feature-based linear adequacy model over BM25, Dense, KG, and Hybrid route families.

## What Changed

- Computed RAS uses a fixed penalty table over parsed query families.
- RAS_V2 added narrow hard-case arbitration heuristics.
- RAS_V3 exposes a route feature vector, learned route weights, per-route scores, margins, and per-feature contributions.

## Training Protocol

- curated 80-query benchmark, generalization_v2 dev, public raw dev, and adversarial dev.
- Held-out reporting: external mini, generalization_v2 test, public raw test, adversarial test, and open-corpus smoke are reporting/sanity layers.
- Human annotations are used only for post-hoc alignment analysis, not training.

## Main Result

- Adversarial test computed RAS answer accuracy: 0.917.
- Adversarial test RAS_V3 answer accuracy: 0.917.
- Adversarial test calibrated rescue answer accuracy: 0.958.
- Promotion decision: `keep_analysis_only`.

## Human Alignment

- Computed RAS alignment with human-preferred route: 1.000.
- RAS_V3 alignment with human-preferred route: 1.000.
- Delta: +0.000.

## Interpretation

RAS_V3 remains analysis-only because at least one strict guardrail was not met.
RAS remains the central contribution because the model is still an explicit adequacy-scoring framework, not a black-box replacement.

## Threats To Validity

- RAS_V3 uses small local/dev training data.
- Hard-case benchmarks include hand-constructed ambiguity cases.
- Answer metrics remain normalized string matching.
- Human alignment compares route choices to existing comparative preferences, not newly annotated RAS_V3 answers.
- Calibrated rescue may still outperform pure route scoring because it changes evidence ordering after retrieval.
