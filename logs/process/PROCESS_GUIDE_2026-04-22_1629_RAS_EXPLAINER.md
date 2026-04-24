# PROCESS GUIDE 2026-04-22 16:29 - RAS Explainer

## Basic summary
This layer makes PRISM's Representation Adequacy Score easier to explain in a paper, poster, and live demo. It adds a unified RAS explainer package, release-ready RAS math documents, sensitivity artifacts, and a dedicated Streamlit `RAS Explainer` page. It does not change production routing: `computed_ras` remains the default production router, while `computed_ras_v2`, `ras_v3`, `ras_v4`, calibrated rescue, classifier routing, and optional LLM routing remain research comparisons or overlays.

## What RAS is in PRISM
RAS is PRISM's representation-aware routing mechanism. Instead of asking one retriever to solve every query, PRISM estimates which representation is most adequate for the query:
- `bm25` for lexical or identifier-heavy exact-match cases.
- `dense` for semantic or paraphrase-heavy cases.
- `kg` for deductive, class/property, or membership-style cases.
- `hybrid` for relational, bridge, or multi-hop cases.

The central idea is that retrieval failures are often structural rather than merely ranking failures. A query can be easy for the right representation and brittle for the wrong one.

## How each RAS version is computed
`computed_ras` is the production router. It parses query features, starts each route with a baseline penalty, applies transparent feature penalties/bonuses from the penalty table, and selects the minimum-scoring route. The score is a heuristic inadequacy penalty, not a learned probability.

`computed_ras_v2` is an analysis-only deterministic refinement. It starts from `computed_ras` and applies narrow override rules for hard cases, including relational bridge cues, deductive cues without strong identifiers, identifier-heavy cues, source-pack priors, and low-margin ambiguity. It is not promoted to production.

`ras_v3` is an interpretable learned route model. It builds a route feature vector and applies sparse linear weights per route. Each candidate route receives a linear score, and the highest score wins. Explanations expose per-feature contributions and route margins.

`ras_v4` is an interpretable joint route-and-evidence adequacy model. It combines route suitability features with evidence adequacy features computed from retrieved top-k evidence. Its explanation decomposes the final backend score into route contribution, evidence contribution, intercept, and top contributing features.

`calibrated_rescue` is not a core RAS version. It is a research overlay that can alter hard-case behavior through calibrated route rescue and top-k evidence rescue. It remains useful because route-only adequacy does not fully solve adversarial answer errors.

## How the math/scoring explanation is organized
The explainer package separates documentation from artifact export:
- `prism/ras_explainer/math_docs.py` describes the actual scoring logic and formulas/pseudo-formulas.
- `prism/ras_explainer/version_compare.py` builds structured summaries for UI and release docs.
- `prism/ras_explainer/sensitivity.py` builds feature-ablation, route-margin, and version-disagreement artifacts.
- `prism/ras_explainer/export_explainer_artifacts.py` writes final-release docs and evaluation artifacts.

The release docs generated under `data/final_release/` are:
- `ras_overview.md`
- `ras_math_guide.md`
- `ras_version_comparison.md`
- `ras_visual_explanation.md`
- `ras_quick_reference.md`

## How the new UI page works
The Streamlit app now includes a `RAS Explainer` tab. The page is structured for live presentation:
- beginner explanation of representation-aware routing
- technical explanation of the RAS variants
- math/scoring explanation with implementation-aligned formulas
- version comparison table and chart
- query-level route inspection
- sensitivity and disagreement artifact summary

The main `Demo / Query` page also includes a compact route inspection panel showing route scores, margin, selected route, feature effects, and version agreement.

## How the stepwise walkthrough works
The RAS Explainer page includes an animation-like story mode implemented as a Streamlit stepper/slider. It walks through:
1. query arrival
2. query feature extraction
3. route score computation
4. winner selection
5. ambiguity/disagreement check
6. evidence retrieval and answer generation

This avoids fragile front-end animation while still giving a presenter-friendly visual sequence.

## What artifacts are generated
Final-release artifacts:
- `data/final_release/ras_overview.md`
- `data/final_release/ras_math_guide.md`
- `data/final_release/ras_version_comparison.md`
- `data/final_release/ras_visual_explanation.md`
- `data/final_release/ras_quick_reference.md`

Evaluation/explainer artifacts:
- `data/eval/ras_explainer_summary.json`
- `data/eval/ras_sensitivity.json`
- `data/eval/ras_version_disagreement.json`
- `data/eval/ras_feature_ablation.csv`
- `data/eval/ras_margin_distribution.png`
- `data/eval/ras_confusion_summary.md`

Release tooling now includes these artifacts in the final package and release verification.

## What remains unresolved
- RAS_V4 remains analysis-only because it does not beat calibrated rescue on adversarial answer accuracy.
- Calibrated rescue remains complementary and stronger on adversarial answer accuracy, but it is still an overlay rather than the production router.
- The new route ambiguity indicator is advisory-only and should not be interpreted as a validated abstention policy.
- The RAS explainer uses compact artifact-based sensitivity analysis for speed and reproducibility; deeper full-retrieval ablations could be added later.

## Concepts and topics used
- representation-aware retrieval
- route adequacy
- evidence adequacy
- route margin
- feature contribution
- sensitivity analysis
- route-version disagreement
- calibrated rescue
- top-k evidence rescue
- production router vs research overlays
- source-pack/local/open-corpus QA boundaries
