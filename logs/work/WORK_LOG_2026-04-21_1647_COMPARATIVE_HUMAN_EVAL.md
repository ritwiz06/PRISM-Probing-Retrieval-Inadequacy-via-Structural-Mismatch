# Work Log: Comparative Human Evaluation and Adjudication Layer

Timestamp: 2026-04-21 16:47 America/Phoenix

## Summary

Added an additive comparative human-evaluation layer for PRISM. The new layer creates side-by-side packets comparing normal computed RAS against calibrated rescue, classifier routing, and fixed-backend baselines. It also exports a comparative rubric, annotation template, placeholder summaries, and an adjudication queue. Production routing, retrieval, answering, benchmark labels, and demo behavior were not changed.

## Files Changed

- `prism/human_eval/__init__.py`
- `prism/human_eval/comparative_sample_builder.py`
- `prism/human_eval/export_comparative_packets.py`
- `prism/human_eval/compare_annotations.py`
- `prism/human_eval/adjudication.py`
- `prism/human_eval/rubric.py`
- `tests/test_human_eval.py`
- `data/human_eval/comparative_packet.json`
- `data/human_eval/comparative_packet.csv`
- `data/human_eval/comparative_packet.md`
- `data/human_eval/comparative_rubric.md`
- `data/human_eval/comparative_annotation_template.csv`
- `data/human_eval/comparative_summary.json`
- `data/human_eval/comparative_summary.csv`
- `data/human_eval/comparative_summary.md`
- `data/human_eval/adjudication_queue.json`
- `data/human_eval/comparative_results_for_report.md`
- `data/human_eval/human_eval_workflow.md`
- `WORK_LOG_2026-04-21_1647_COMPARATIVE_HUMAN_EVAL.md`
- `PROCESS_GUIDE_2026-04-21_1647_COMPARATIVE_HUMAN_EVAL.md`

Existing Prompt 22 human-eval artifacts also remain present under `data/human_eval/`.

## Commands Run

- `test -x .venv/bin/python3 && .venv/bin/python3 --version || python3 -m venv .venv`
- `find . -maxdepth 1 -type f -name 'WORK_LOG_*' -print`
- `find . -maxdepth 1 -type f -name 'PROCESS_GUIDE_*' -print`
- `git status --short`
- `sed -n '1,260p' WORK_LOG_2026-04-20_2054_HUMAN_EVAL.md`
- `sed -n '1,260p' PROCESS_GUIDE_2026-04-20_2054_HUMAN_EVAL.md`
- `.venv/bin/python3 -m pytest -q tests/test_human_eval.py`
- `.venv/bin/python3 -m prism.human_eval.export_comparative_packets`
- `.venv/bin/python3 -m prism.human_eval.compare_annotations`
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
- `.venv/bin/python3 -m prism.analysis.report_artifacts`
- `.venv/bin/python3 -m prism.human_eval.export_packets`
- `.venv/bin/python3 -m prism.human_eval.export_comparative_packets`
- `.venv/bin/python3 -m prism.human_eval.analyze_annotations`

## Test Results

- Focused human-eval tests: `9 passed in 2.54s`.
- Full test suite: `108 passed, 3 warnings in 62.29s`.
- Editable install completed successfully.

## Acceptance Results

- Corpus build: wrote `148` documents to `data/processed/corpus.jsonl`.
- KG build: wrote `99` triples to `data/processed/kg_triples.jsonl`.
- Curated end-to-end verifier: `80/80` answers, route accuracy `1.000`, evidence hit@k `1.000`.
- External mini-benchmark verifier: `32/32` answers, route accuracy `1.000`.
- Generalization v2 verifier: clean test answer accuracy `1.000`, noisy test answer accuracy `0.975`.
- Structure-shift verifier: extracted KG degrades deductive accuracy; mixed KG recovers curated performance.
- Public corpus verifier: public test answer accuracy `1.000`, evidence hit@k `1.000`.
- Public graph verifier: public-graph test answer accuracy `1.000`, evidence hit@k `1.000`.
- Adversarial verifier: computed-RAS answer accuracy `0.729` overall and `0.917` on test; strongest fixed backend overall was `always_dense`.
- Calibration verifier: adversarial test normal answer accuracy `0.917`; calibrated/rescue variants `0.958`.
- Report artifacts regenerated successfully under `data/eval/report/`.
- Standard human-eval packet regenerated with `36` examples.
- Comparative human-eval packet generated with `28` examples.

## Comparative-Packet Summary

The comparative packet is side-by-side and evaluator-ready.

- Packet size: `28`.
- Benchmark sources: `adversarial=16`, `curated=4`, `generalization_v2=4`, `public_raw=4`.
- Route families: `bm25=7`, `dense=7`, `kg=7`, `hybrid=7`.
- System pairs:
  - `computed_ras_vs_calibrated_rescue=8`
  - `computed_ras_vs_classifier_router=12`
  - `computed_ras_vs_always_dense=4`
  - `computed_ras_vs_always_bm25=4`
- Disagreement-oriented tags include route disagreements, computed low-level audit cases, and one computed-hit/system-B-miss case.

Generated packet artifacts:

- `data/human_eval/comparative_packet.json`
- `data/human_eval/comparative_packet.csv`
- `data/human_eval/comparative_packet.md`

## Comparative Rubric and Adjudication Summary

The comparative rubric asks evaluators to choose `A`, `B`, or `Tie` for:

- better supported answer
- more faithful reasoning trace
- clearer reasoning trace
- more appropriate route
- overall preference

It also captures confidence from `1` to `3`, major difference type, an adjudication flag, and notes.

No comparative annotation CSVs exist yet under `data/human_eval/comparative_annotations/`, so the summary correctly reports `no_comparative_annotations` and keeps the adjudication queue empty.

Generated rubric/adjudication artifacts:

- `data/human_eval/comparative_rubric.md`
- `data/human_eval/comparative_annotation_template.csv`
- `data/human_eval/comparative_summary.json`
- `data/human_eval/comparative_summary.csv`
- `data/human_eval/comparative_summary.md`
- `data/human_eval/adjudication_queue.json`
- `data/human_eval/comparative_results_for_report.md`
- `data/human_eval/human_eval_workflow.md`

## Human-Eval Comparison Workflow Summary

1. Run `.venv/bin/python3 -m prism.human_eval.export_comparative_packets`.
2. Give evaluators `data/human_eval/comparative_packet.md` and `data/human_eval/comparative_rubric.md`.
3. Copy `data/human_eval/comparative_annotation_template.csv` to `data/human_eval/comparative_annotations/<evaluator_id>.csv`.
4. Evaluators fill A/B/Tie choices, confidence, major difference type, adjudication flag, and notes.
5. Rerun `.venv/bin/python3 -m prism.human_eval.export_comparative_packets` or `.venv/bin/python3 -m prism.human_eval.compare_annotations`.
6. Use `comparative_summary.*`, `adjudication_queue.json`, and `comparative_results_for_report.md` for report discussion.

## Known Limitations

- No real comparative human annotations have been collected yet, so win/loss/tie statistics are pending.
- Forced-choice A/B/Tie judgments are practical but can hide nuance.
- The packet is intentionally small and targeted, so it supports audit and discussion more than broad statistical claims.
- Current comparative outputs use local automatic correctness only as context; human judgments remain the source of truth once collected.
- The layer is analysis-only and does not automatically change production routing or demo behavior.
