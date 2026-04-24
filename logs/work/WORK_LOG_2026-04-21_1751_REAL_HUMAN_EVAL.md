# WORK LOG: Real Human-Eval Annotation Analysis

Timestamp: 2026-04-21 17:51

## Summary

Implemented the real-annotation analysis pass for PRISM's standard and comparative human-evaluation layers. The previous placeholder summaries now load the four evaluator annotation files, validate schemas and item ids, compute real rubric statistics, agreement summaries, comparative win/loss/tie results, human-vs-automatic mismatch summaries, adjudication queues, and report-ready plots/Markdown outputs.

No production routing, retrieval, answering, benchmark gold labels, or demo behavior was changed.

## Files Changed

- `prism/human_eval/validation.py`
- `prism/human_eval/load_annotations.py`
- `prism/human_eval/analyze_annotations.py`
- `prism/human_eval/compare_annotations.py`
- `tests/test_human_eval.py`
- `data/human_eval/annotation_validation_summary.json`
- `data/human_eval/annotation_validation_summary.csv`
- `data/human_eval/annotation_validation_summary.md`
- `data/human_eval/human_eval_summary.json`
- `data/human_eval/human_eval_summary.csv`
- `data/human_eval/human_eval_summary.md`
- `data/human_eval/trace_validity_summary.md`
- `data/human_eval/disagreement_cases.json`
- `data/human_eval/human_vs_automatic_summary.md`
- `data/human_eval/human_eval_results_for_paper.md`
- `data/human_eval/comparative_summary.json`
- `data/human_eval/comparative_summary.csv`
- `data/human_eval/comparative_summary.md`
- `data/human_eval/comparative_results_for_report.md`
- `data/human_eval/adjudication_queue.json`
- `data/human_eval/human_scores_by_dimension.png`
- `data/human_eval/human_scores_by_source.png`
- `data/human_eval/human_scores_by_route_family.png`
- `data/human_eval/comparative_win_rates_by_system_pair.png`
- `data/human_eval/comparative_preferences_by_route_family.png`
- `WORK_LOG_2026-04-21_1751_REAL_HUMAN_EVAL.md`
- `PROCESS_GUIDE_2026-04-21_1751_REAL_HUMAN_EVAL.md`

## Commands Run

- `.venv/bin/python3 --version`
- `sed -n '1,220p' WORK_LOG_2026-04-21_1647_COMPARATIVE_HUMAN_EVAL.md`
- `sed -n '1,220p' PROCESS_GUIDE_2026-04-21_1647_COMPARATIVE_HUMAN_EVAL.md`
- `find data/human_eval/annotations -maxdepth 1 -type f -print`
- `find data/human_eval/comparative_annotations -maxdepth 1 -type f -print`
- `.venv/bin/python3 -m pytest -q tests/test_human_eval.py`
- `.venv/bin/python3 -m prism.human_eval.analyze_annotations`
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
- `.venv/bin/python3 -m prism.human_eval.compare_annotations`

## Test Results

- Focused human-eval tests: `10 passed in 0.96s`
- Full test suite: `109 passed, 3 warnings in 59.04s`
- Corpus build: wrote 148 documents to `data/processed/corpus.jsonl`
- KG build: wrote 99 triples to `data/processed/kg_triples.jsonl` and `data/processed/kg.ttl`
- Curated end-to-end verification: `80/80` answers, `80/80` traces, route accuracy `1.000`
- External mini-benchmark: `32/32`, RAS route accuracy `1.000`, RAS answer accuracy `1.000`
- Generalization v2: clean test answer accuracy `1.000`, noisy test answer accuracy `0.975`
- Structure shift: extracted KG degrades deductive accuracy as expected; mixed mode restores curated-level accuracy
- Public raw corpus: test answer accuracy `1.000`, evidence hit@k `1.000`
- Public graph: public-graph test answer accuracy `1.000`, evidence hit@k `1.000`
- Adversarial benchmark: normal computed RAS answer accuracy `0.729` overall, `0.917` on test
- Calibration verifier: adversarial test normal answer `0.917`, calibrated/rescue answer `0.958`

## Annotation Validation Summary

- Standard annotation files: 4
- Standard rows: 144 valid / 144 total
- Standard evaluators: 4
- Standard recognized packet items: 36 / 36
- Comparative annotation files: 4
- Comparative rows: 112 valid / 112 total
- Comparative evaluators: 4
- Comparative recognized packet items: 28 / 28
- Validation issues: 0

The loader now scans all non-hidden files in the annotation folders, validates required columns, checks item ids against the packet exports, checks score ranges, checks A/B/Tie comparative choices, and writes JSON/CSV/Markdown validation artifacts.

## Standard Human-Eval Results Summary

- Packet size: 36
- Annotation count: 144
- Evaluator count: 4
- Route appropriateness mean: `2.896`
- Evidence sufficiency mean: `2.917`
- Answer faithfulness mean: `2.917`
- Trace faithfulness mean: `2.931`
- Trace clarity mean: `2.944`
- Overall usefulness mean: `2.875`
- All rubric medians: `3.0`
- Major error type percent agreement: `1.0`
- Major error type Cohen kappa: `1.0`
- Automatic-correct but weak human support annotations: 4
- Automatic-incorrect but strong human support annotations: 0
- Weak trace support annotations: 10

## Comparative Human-Eval Results Summary

- Packet size: 28
- Annotation count: 112
- Evaluator count: 4
- Adjudication queue size: 12
- Mean evaluator confidence: `2.759`
- Confidence distribution: `{'3': 85, '2': 27}`

System-pair overall preference rates:

- `computed_ras_vs_always_bm25`: A win `0.625`, B win `0.000`, tie `0.375`
- `computed_ras_vs_always_dense`: A win `0.375`, B win `0.125`, tie `0.500`
- `computed_ras_vs_calibrated_rescue`: A win `0.000`, B win `0.062`, tie `0.938`
- `computed_ras_vs_classifier_router`: A win `0.042`, B win `0.042`, tie `0.917`

Human-vs-automatic notes:

- System B preferred when both systems were automatically correct: 6
- Calibrated rescue preferred while both systems were automatically correct: 2
- System B preferred despite computed RAS being automatically correct: 6
- Classifier router preferred on adversarial items: 2

## Adjudication Summary

The real adjudication queue contains 12 items. Items enter the queue when evaluators split on the overall preference, mark explicit adjudication, or create a low-confidence pattern that needs review. Each queue record includes:

- comparative item id
- query
- compared systems
- vote pattern
- confidence pattern
- major difference types
- evaluator notes
- suggested reason for adjudication

## Known Limitations

- The evaluator pool is small, so agreement and preference rates should be treated as pilot-study evidence.
- Most rubric scores are high and clustered near 3, limiting the sensitivity of mean-score comparisons.
- The comparative packet is intentionally small and hard-case focused, so it is not a broad random estimate of all PRISM behavior.
- Automatic correctness is normalized string matching; human support judgments capture evidence and trace quality that automatic metrics miss.
- Cohen kappa is meaningful for categorical major error labels, but ordinal rubric agreement remains approximate.
