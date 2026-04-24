# WORK LOG 2026-04-22 14:21 - Final Release Layer

## Summary

Implemented the final PRISM release layer: presenter-friendly demo presets, a tabbed Streamlit demo workspace, open-corpus runtime metadata views, final release package generation, release verification, and finalization tests. Production routing remains `computed_ras`; calibrated rescue, RAS_V3, RAS_V4, classifier routing, and optional LLM routing remain explicitly labeled research overlays.

## Files Changed

- `prism/demo/app.py`
- `prism/demo/data.py`
- `prism/demo/presets.py`
- `prism/demo/demo_script_data.py`
- `prism/open_corpus/view_model.py`
- `prism/finalize/__init__.py`
- `prism/finalize/build_release.py`
- `prism/finalize/verify_release.py`
- `tests/test_finalize.py`
- `data/final_release/final_project_overview.md`
- `data/final_release/paper_ready_summary.md`
- `data/final_release/demo_runbook.md`
- `data/final_release/reproducibility_runbook.md`
- `data/final_release/central_claim_summary.md`
- `data/final_release/artifact_manifest.json`
- `data/final_release/known_results_summary.json`
- `data/final_release/release_checklist.md`
- `data/final_release/release_status.json`

## Commands Run

- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest -q`
- `.venv/bin/python3 -m pytest tests/test_demo.py tests/test_open_corpus.py tests/test_finalize.py -q`
- `.venv/bin/python3 -m py_compile prism/demo/app.py prism/open_corpus/view_model.py prism/finalize/build_release.py prism/finalize/verify_release.py prism/demo/presets.py prism/demo/demo_script_data.py`
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
- `.venv/bin/python3 -m streamlit run prism/demo/app.py --server.headless true`

## Test Results

- Full test suite: `134 passed, 3 warnings`.
- Focused finalization/demo/open-corpus tests: `14 passed, 3 warnings`.
- Curated benchmark: `80/80`, route accuracy `1.000`, evidence hit@k `1.000`.
- External mini-benchmark: `32/32`, computed RAS answer accuracy `1.000`, Dense backend `sentence_transformers+faiss`.
- Generalization_v2: clean test answer accuracy `1.000`, noisy test answer accuracy `0.975`.
- Structure shift: curated and mixed KG remain strong; extracted-only deductive degradation is still reported honestly.
- Public raw test: computed RAS answer accuracy `1.000`.
- Public graph test: public graph answer accuracy `1.000`.
- Adversarial benchmark: combined computed RAS answer accuracy `0.729`; adversarial test computed RAS answer accuracy `0.917`.
- Calibration: adversarial test calibrated rescue answer accuracy `0.958`.
- Open-corpus smoke: passed, answer accuracy `1.000`.
- RAS_V3: remains `keep_analysis_only`.
- RAS_V4: remains `keep_analysis_only`; RAS_V4 + rescue matches calibrated rescue at `0.958` on adversarial test.
- Release verifier: `ready=True`, class demo `ready`, paper draft `ready_with_caveats`, reproducibility handoff `ready`, missing critical artifacts `0`.
- Streamlit smoke: app launched successfully at `http://localhost:8501`; server was left running because stop/kill approval was not granted.

## UI Finalization Summary

The Streamlit app now presents a final-demo workspace with top-level tabs:

- `Demo / Query`
- `Open Corpus`
- `Compare Routers`
- `Evidence / Graph`
- `Human Eval`
- `Results / Paper`

The sidebar clearly marks production mode as `computed_ras` and research overlays as `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, and optional local LLM routing. The app keeps benchmark mode as the default safe path and adds source-pack, local-demo-folder, local-folder, and URL-list workspace modes with graceful fallback behavior.

## Release-Package Summary

The final release package is generated under `data/final_release/` and includes:

- `final_project_overview.md`
- `paper_ready_summary.md`
- `demo_runbook.md`
- `reproducibility_runbook.md`
- `central_claim_summary.md`
- `artifact_manifest.json`
- `known_results_summary.json`
- `release_checklist.md`
- `release_status.json`

The verifier checks all critical benchmark, analysis, human-eval, RAS, open-corpus, and demo artifacts. It reports the project ready for class/project demo, ready with caveats for paper draft submission, and ready for reproducibility handoff.

## Central-Claim Summary

The final package states the central thesis directly: PRISM contributes representation-aware routing. Route adequacy matters, but route-only adequacy is insufficient on hard adversarial cases. RAS_V3 formalizes route adequacy, RAS_V4 decomposes route and evidence adequacy, and calibrated top-k rescue remains complementary. Human eval supports faithfulness/usefulness while preserving ties and adjudication cases.

## Known Limitations

- Production router remains `computed_ras`; RAS_V3 and RAS_V4 are not promoted.
- Calibrated rescue improves hard-case answer accuracy but remains a research/demo comparison overlay unless explicitly enabled.
- The open-corpus workspace is source-pack/local-corpus QA, not web-scale open-domain search.
- Optional local LLM behavior depends on local runtime availability.
- Streamlit is currently running from the smoke test because process termination approval was declined.
