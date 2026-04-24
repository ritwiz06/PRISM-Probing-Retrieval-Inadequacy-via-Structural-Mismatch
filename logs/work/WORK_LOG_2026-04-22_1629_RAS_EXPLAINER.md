# WORK LOG 2026-04-22 16:29 - RAS Explainer

## Files changed
- Added `prism/ras_explainer/__init__.py`
- Added `prism/ras_explainer/math_docs.py`
- Added `prism/ras_explainer/version_compare.py`
- Added `prism/ras_explainer/sensitivity.py`
- Added `prism/ras_explainer/export_explainer_artifacts.py`
- Updated `prism/demo/app.py`
- Updated `prism/finalize/build_release.py`
- Updated `prism/finalize/verify_release.py`
- Added `tests/test_ras_explainer.py`
- Updated `tests/test_finalize.py`
- Generated `data/final_release/ras_overview.md`
- Generated `data/final_release/ras_math_guide.md`
- Generated `data/final_release/ras_version_comparison.md`
- Generated `data/final_release/ras_visual_explanation.md`
- Generated `data/final_release/ras_quick_reference.md`
- Generated `data/eval/ras_explainer_summary.json`
- Generated `data/eval/ras_sensitivity.json`
- Generated `data/eval/ras_version_disagreement.json`
- Generated `data/eval/ras_feature_ablation.csv`
- Generated `data/eval/ras_margin_distribution.png`
- Generated `data/eval/ras_confusion_summary.md`

## Commands run
- `.venv/bin/python3 -m py_compile prism/ras_explainer/*.py prism/demo/app.py prism/finalize/build_release.py prism/finalize/verify_release.py`
- `.venv/bin/python3 -m pytest tests/test_ras_explainer.py tests/test_finalize.py -q`
- `.venv/bin/python3 -m prism.ras_explainer.export_explainer_artifacts`
- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m prism.ingest.build_corpus`
- `.venv/bin/python3 -m prism.ingest.build_kg`
- `.venv/bin/python3 -m prism.eval.verify_end_to_end`
- `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`
- `.venv/bin/python3 -m prism.generalization.verify_generalization_v2`
- `.venv/bin/python3 -m prism.kg_extraction.verify_structure_shift`
- `.venv/bin/python3 -m prism.public_corpus.verify_public_corpus`
- `.venv/bin/python3 -m prism.public_graph.verify_public_graph`
- `.venv/bin/python3 -m prism.adversarial.verify_adversarial`
- `.venv/bin/python3 -m prism.calibration.verify_calibrated_router`
- `.venv/bin/python3 -m prism.human_eval.analyze_annotations`
- `.venv/bin/python3 -m prism.human_eval.compare_annotations`
- `.venv/bin/python3 -m prism.open_corpus.verify_open_corpus`
- `.venv/bin/python3 -m prism.ras_v3.verify_ras_v3`
- `.venv/bin/python3 -m prism.ras_v4.verify_ras_v4`
- `.venv/bin/python3 -m prism.analysis.report_artifacts`
- `.venv/bin/python3 -m prism.finalize.build_release`
- `.venv/bin/python3 -m prism.finalize.verify_release`
- `.venv/bin/python3 -m prism.ras_explainer.export_explainer_artifacts`
- `.venv/bin/python3 -m streamlit run prism/demo/app.py --server.headless true`

## Test results
- Focused RAS/finalize tests: `11 passed in 12.85s`.
- Full test suite: `141 passed in 261.17s`.
- End-to-end curated verifier: `80/80` answers, route accuracy `1.000`, evidence hit@k `1.000`.
- External mini-benchmark verifier: `32/32`, computed RAS answer accuracy `1.000`.
- Generalization v2 verifier: clean test answer accuracy `1.000`, noisy test answer accuracy `0.975`.
- Structure-shift verifier passed; extracted KG remains visibly weaker than curated/mixed on deductive generalization, which is reported honestly.
- Public raw verifier passed with public test answer accuracy `1.000`.
- Public graph verifier passed with public-structure test answer accuracy `1.000`.
- Adversarial verifier passed; computed RAS remains weaker on hard cases than some comparison systems.
- Calibration verifier passed; adversarial test calibrated+top-k rescue answer accuracy `0.958` vs normal computed RAS `0.917`.
- RAS_V3 verifier passed; RAS_V3 remains analysis-only.
- RAS_V4 verifier passed; RAS_V4 remains analysis-only and calibrated rescue remains strongest on adversarial test answer accuracy.
- Streamlit smoke launched successfully at `http://localhost:8503`.

## RAS explainer summary
- Added a unified explainer layer for `computed_ras`, `computed_ras_v2`, `ras_v3`, `ras_v4`, and `calibrated_rescue` as an overlay comparison.
- The explainer documents actual implementation behavior rather than invented formulas:
  - `computed_ras`: heuristic penalty scoring where the minimum route score wins.
  - `computed_ras_v2`: narrow deterministic override rules layered on top of computed RAS for analysis.
  - `ras_v3`: learned sparse linear route-scoring model with per-feature contributions.
  - `ras_v4`: learned joint route/evidence adequacy model with route contribution, evidence contribution, and expected answerability terms.
  - `calibrated_rescue`: analysis overlay that can improve post-route evidence use but is not a core RAS version.

## UI visualization summary
- Added a new `RAS Explainer` tab to the Streamlit app.
- Added beginner, technical, and math/scoring explanations for RAS.
- Added route score charts, RAS version comparison charts, query-level route inspection, RAS_V3 contribution views where available, and sensitivity artifact summaries.
- Added a stepwise story-mode walkthrough:
  1. query arrives
  2. query features are extracted
  3. candidate route scores are computed
  4. route is selected
  5. ambiguity is checked
  6. evidence and answer follow
- Added query-level “Why this route?” and “Why not alternatives?” inspection to the main demo flow.

## Optional improvement summary
- Added an advisory-only route ambiguity indicator.
- The indicator flags small computed-RAS margins and disagreement among RAS versions.
- It does not change routing, retrieval, answer generation, benchmark labels, or production behavior.
- It is intended for explainability, live demo interpretation, and future research triage.

## Release artifact updates
- Final release now includes:
  - `ras_overview.md`
  - `ras_math_guide.md`
  - `ras_version_comparison.md`
  - `ras_visual_explanation.md`
  - `ras_quick_reference.md`
- Release builder and verifier now treat the RAS explainer docs as part of the final package.
- UI tour/release documentation now mentions the `RAS Explainer` page.

## Known limitations
- The sensitivity layer uses lightweight, artifact-based comparisons for RAS_V4 where possible to avoid slow full retriever/model recomputation during explainer export.
- The ambiguity indicator is not a production abstention policy; it is a transparent advisory signal only.
- RAS_V4 improves the explanation story but does not beat calibrated rescue on adversarial answer accuracy.
- Production router remains `computed_ras`.
- PRISM remains source-pack/local/open-corpus QA, not arbitrary web-scale search.
