# PROCESS GUIDE - 2026-04-18 08:10 - Calibrated Hard-Case Rescue

## Basic Summary

This task added an optional hard-case rescue layer. Earlier adversarial results showed that computed RAS still fails on route-boundary cases, misleading exact terms, and cases where the right evidence is in top-k but not top-1. The new calibration layer tests whether a small, interpretable overlay can rescue some of those cases without changing PRISM's production behavior.

Computed RAS remains the default production router. The calibrated router and top-k rescue are analysis modes.

## What Was Implemented

The new package is `prism/calibration/`.

- `route_calibrator.py` implements the optional route calibrator.
- `dev_tuning.py` selects a calibrator profile using adversarial dev only.
- `topk_rescue.py` reorders already-retrieved top-k evidence when a query contains an explicit distractor or negated span.
- `verify_calibrated_router.py` evaluates normal RAS, calibrated RAS, top-k rescue, combined calibration+rescue, classifier router, and fixed-backend baselines.

The main generated artifacts are:

- `data/eval/calibrated_router.json`
- `data/eval/calibrated_router.csv`
- `data/eval/calibrated_router_summary.md`
- `data/eval/calibrated_dev_tuning.json`
- `data/eval/calibrated_failure_delta.json`
- `data/eval/calibrated_failure_delta_summary.md`
- `data/eval/calibrated_adversarial_test_comparison.png`
- `data/eval/calibrated_failure_delta.png`

## How The Calibrated Router Works

The calibrated router starts from the normal computed RAS result. It does not replace RAS with a learned model.

It looks at a small set of interpretable signals:

- computed RAS selected backend,
- RAS confidence/margin,
- keyword router prediction,
- classifier router prediction and class probabilities,
- identifier-heavy query patterns,
- semantic wording such as "concept", "idea", "process", or "meaning",
- misleading exact-term cues such as "not", "despite", "although", or "rather than",
- deductive cues such as "closed-world", "can a", "are all", or "what property",
- relational cues such as "bridge" or "connects",
- explicit instructions not to route a substring to KG.

The calibrator can override RAS only in narrow conditions:

- Semantic bait override: if RAS chooses BM25 because of an exact term, but the query has semantic wording and a distractor/negation cue, it can switch to Dense.
- Structural override: if the query clearly asks for membership, property, or relation reasoning, it can switch to KG or Hybrid.
- Identifier/KG suppression: if the query says not to route a class-like substring to KG and also contains identifier/API evidence, it can switch back to BM25.
- Classifier disagreement override: if RAS has low/medium confidence and the classifier strongly disagrees on a hard-boundary query, it can defer to the classifier route.

The calibrator returns metadata with:

- original RAS backend,
- final calibrated backend,
- whether an override fired,
- confidence label,
- route rationale,
- detected signals,
- auxiliary keyword/classifier routes.

## How Dev-Only Tuning Was Done

The tuning code is in `dev_tuning.py`.

The protocol is intentionally narrow:

- Use only adversarial `dev`.
- Score candidate calibrator profiles by route accuracy.
- Select the best dev profile.
- Keep adversarial `test` held out until final evaluation.
- Use curated/external/generalization/public benchmarks only as sanity checks, not tuning targets.

The selected profile in this run was `classifier_heavier`.

This means the reported adversarial test improvement is not from tuning directly on test labels.

## How Top-k Rescue Works

The top-k rescue layer handles a different failure mode. Sometimes the router and retriever retrieve the correct evidence somewhere in top-k, but the answer generator uses the wrong top-1 item.

Top-k rescue:

- does not fetch new evidence,
- does not use gold labels,
- only reorders already-retrieved evidence,
- is disabled unless the query contains an explicit negated or distractor span,
- requires a clear score margin before changing the top evidence.

It scores each evidence item using:

- overlap with query terms,
- identifier matches,
- penalties for matching terms that appear in negated/distractor spans,
- small source/backend consistency bonuses.

Example intuition:

If the query says "not numpy.linalg.svd" and top-1 evidence is about `numpy.linalg.svd`, but top-k also includes "butterfly effect", rescue can promote the butterfly effect evidence because the numpy evidence matches the negated distractor.

## How Before/After Evaluation Works

The verifier compares these systems:

- normal computed RAS,
- computed RAS + calibrated router,
- computed RAS + top-k rescue,
- computed RAS + calibrated router + top-k rescue,
- classifier router,
- always BM25,
- always Dense,
- always KG,
- always Hybrid.

It evaluates on:

- adversarial dev,
- adversarial test,
- curated benchmark,
- external mini-benchmark,
- generalization v2 test,
- public raw-document benchmark test.

Metrics include:

- route accuracy,
- answer accuracy,
- evidence hit@k,
- top-1 evidence hit,
- per-family accuracy,
- per-ambiguity-tag accuracy for adversarial items,
- deltas versus normal computed RAS.

## Results In This Run

Adversarial test normal computed RAS:

- route accuracy `0.750`
- answer accuracy `0.917`
- evidence hit@k `0.958`
- top-1 evidence hit `0.875`

Adversarial test calibrated+rescue:

- route accuracy `0.875`
- answer accuracy `0.958`
- evidence hit@k `0.958`
- top-1 evidence hit `0.917`

The combined optional layer fixed `1` prior adversarial test failure and caused `0` regressions in the failure-delta comparison.

Earlier benchmark sanity checks stayed flat:

- curated answer accuracy remained `1.000`,
- external mini answer accuracy remained `1.000`,
- generalization v2 test answer accuracy remained `1.000`,
- public raw test answer accuracy remained `1.000`.

## What Artifacts Are Generated

`calibrated_router.json` contains full structured results for all evaluated datasets and systems.

`calibrated_router.csv` contains flat metrics suitable for tables.

`calibrated_router_summary.md` is the report-ready explanation of protocol, results, tradeoffs, and artifacts.

`calibrated_dev_tuning.json` records the dev-only candidate profile comparison and selected calibrator.

`calibrated_failure_delta.json` records before/after failure bucket changes on adversarial test.

`calibrated_failure_delta_summary.md` gives a compact failure-bucket comparison.

`calibrated_adversarial_test_comparison.png` visualizes adversarial test answer accuracy across normal, calibrated, rescued, classifier, and fixed-backend systems.

`calibrated_failure_delta.png` visualizes before/after failure-bucket counts.

## Concepts And Topics Used

Calibration means adjusting a model or decision rule using observed development-set behavior. Here it means selectively correcting computed RAS on hard route-boundary cases.

Held-out test means data not used for tuning. The adversarial test split is used only after selecting the calibrator on adversarial dev.

Route margin means the difference between the best and second-best RAS route scores. A small margin means the router is less decisive.

Top-k rescue means using evidence beyond the first retrieved result when the correct evidence appears in the retrieved set but is not ranked first.

Negated distractor means a phrase the query explicitly says is not the target, such as "not RFC-7230" or "not numpy.linalg.svd".

Failure delta means comparing failure buckets before and after an intervention to see which error types shrink or remain.

Sanity benchmark means a benchmark used to check for regressions, not to tune the new method.

Analysis-only mode means the code exists for experiments and reports, but the production app does not use it by default.

## What Remains Unresolved

The calibrator is tuned on a small adversarial dev split, so it may not generalize to all future hard cases.

The classifier router is useful as a signal, but it is not the production router and should not silently replace computed RAS.

Top-k rescue can improve answer accuracy without improving retrieval coverage; this should be described as better evidence use, not better retrieval.

The remaining adversarial test miss still involves hard route/evidence ambiguity and should stay visible in the failure artifacts.

The calibrated route is more complex to explain than plain computed RAS. For the demo and final narrative, computed RAS remains the safer default unless explicitly discussing robustness experiments.
