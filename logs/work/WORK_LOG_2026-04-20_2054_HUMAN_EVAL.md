# Work Log: Human Evaluation and Trace Validity Layer

Timestamp: 2026-04-20 20:54 America/Phoenix

## Summary

Added an additive human-evaluation layer for PRISM. The new layer exports a balanced evaluator packet, a rubric, an annotation template, and analysis artifacts for future human annotations. No production routing, retrieval, answering, benchmark gold labels, or demo behavior were changed.

## Files Changed

- `prism/human_eval/__init__.py`
- `prism/human_eval/sample_builder.py`
- `prism/human_eval/export_packets.py`
- `prism/human_eval/rubric.py`
- `prism/human_eval/load_annotations.py`
- `prism/human_eval/analyze_annotations.py`
- `tests/test_human_eval.py`
- `data/human_eval/eval_packet.json`
- `data/human_eval/eval_packet.csv`
- `data/human_eval/eval_packet.md`
- `data/human_eval/rubric.md`
- `data/human_eval/annotation_template.csv`
- `data/human_eval/human_eval_summary.json`
- `data/human_eval/human_eval_summary.csv`
- `data/human_eval/human_eval_summary.md`
- `data/human_eval/trace_validity_summary.md`
- `data/human_eval/disagreement_cases.json`
- `WORK_LOG_2026-04-20_2054_HUMAN_EVAL.md`
- `PROCESS_GUIDE_2026-04-20_2054_HUMAN_EVAL.md`

## Commands Run

- `.venv/bin/python3 --version`
- `find . -maxdepth 1 -type f -name 'WORK_LOG_*' -print`
- `find . -maxdepth 1 -type f -name 'PROCESS_GUIDE_*' -print`
- `sed -n '1,220p' WORK_LOG_2026-04-18_0810_CALIBRATION.md`
- `sed -n '1,220p' PROCESS_GUIDE_2026-04-18_0810_CALIBRATION.md`
- `git status --short`
- `sed -n '1,240p' prism/app/pipeline.py`
- `sed -n '1,240p' prism/demo/data.py`
- `sed -n '1,220p' prism/generalization/loaders.py`
- `sed -n '1,220p' prism/public_corpus/loaders.py`
- `sed -n '1,220p' prism/adversarial/loaders.py`
- `.venv/bin/python3 -m pytest -q tests/test_human_eval.py`
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
- `.venv/bin/python3 -m prism.human_eval.analyze_annotations`

## Test Results

- Focused human-eval tests: `5 passed in 1.82s`.
- Full test suite: `104 passed, 3 warnings in 104.55s`.
- Editable install: completed successfully.

## Acceptance Results

- Corpus build: wrote `148` corpus documents to `data/processed/corpus.jsonl`.
- KG build: wrote `99` triples to `data/processed/kg_triples.jsonl` and Turtle to `data/processed/kg.ttl`.
- Curated end-to-end verifier: `80/80` answers, route accuracy `1.000`, evidence hit@k `1.000`, traces `80/80`.
- External mini-benchmark verifier: `32/32` answers, route accuracy `1.000`, dense backend `sentence_transformers+faiss`.
- Generalization v2 verifier: `80` total examples; clean test answer accuracy `1.000`; noisy test answer accuracy `0.975`.
- Structure-shift verifier: evaluated `curated`, `extracted`, and `mixed` KG modes; extracted degraded deductive accuracy while mixed recovered curated performance.
- Public corpus verifier: `48` examples; public test computed-RAS answer accuracy `1.000`.
- Public graph verifier: `32` examples; public-graph test answer accuracy `1.000`.
- Adversarial verifier: `48` hard examples; computed-RAS answer accuracy `0.729` overall and `0.917` on test; strongest fixed backend overall was `always_dense` at `0.771`.
- Calibration verifier: adversarial test normal answer accuracy `0.917`; calibrated-only, rescue-only, and calibrated+rescue answer accuracy `0.958`.
- Report artifacts: regenerated under `data/eval/report/`.

## Evaluation-Packet Summary

The human-eval packet is deterministic and balanced enough for a small team annotation pass.

- Packet size: `36`.
- Benchmark sources: `adversarial=12`, `curated=8`, `generalization_v2=8`, `public_raw=8`.
- Route families: `bm25=9`, `dense=9`, `kg=9`, `hybrid=9`.
- System variants: `computed_ras=32`, `calibrated_ras=4`.
- Automatic correctness labels: `35` automatically correct, `1` automatically incorrect.
- Outputs:
  - `data/human_eval/eval_packet.json`
  - `data/human_eval/eval_packet.csv`
  - `data/human_eval/eval_packet.md`

## Rubric and Agreement-Analysis Summary

The rubric scores six dimensions on a 1 to 3 ordinal scale:

- route appropriateness
- evidence sufficiency
- answer faithfulness
- trace faithfulness
- trace clarity
- overall usefulness

The annotation template also captures evaluator id, item id, major error type, usability, and free-text notes.

No completed human annotation CSV files exist yet under `data/human_eval/annotations/`, so the analysis layer wrote placeholder summaries instead of fabricating results.

Generated outputs:

- `data/human_eval/rubric.md`
- `data/human_eval/annotation_template.csv`
- `data/human_eval/human_eval_summary.json`
- `data/human_eval/human_eval_summary.csv`
- `data/human_eval/human_eval_summary.md`
- `data/human_eval/trace_validity_summary.md`
- `data/human_eval/disagreement_cases.json`

## Human-Eval Workflow Summary

1. Run `.venv/bin/python3 -m prism.human_eval.export_packets`.
2. Give evaluators `data/human_eval/eval_packet.md` and `data/human_eval/rubric.md`.
3. Copy `data/human_eval/annotation_template.csv` to `data/human_eval/annotations/<evaluator_id>.csv`.
4. Each evaluator fills scores and notes.
5. Run `.venv/bin/python3 -m prism.human_eval.analyze_annotations`.
6. Use generated summaries for trace-validity, support, agreement, and disagreement-case reporting.

## Known Limitations

- No real human annotations have been collected yet, so agreement metrics are currently placeholders.
- Packet size is practical for a class/team workflow but not enough for strong statistical claims.
- Automatic correctness labels still come from normalized answer matching and should not be treated as human judgment.
- The calibrated examples are included for auditability, but calibrated routing remains analysis-only.
- Cohen's kappa support is intentionally lightweight and most useful after at least two annotators label overlapping items.
