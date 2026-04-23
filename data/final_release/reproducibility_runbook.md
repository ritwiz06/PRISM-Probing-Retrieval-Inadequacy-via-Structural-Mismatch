# Reproducibility Runbook

Run these commands from the repo root:

```bash
.venv/bin/python3 -m pip install -e .
```
```bash
.venv/bin/python3 -m pytest -q
```
```bash
.venv/bin/python3 -m prism.ingest.build_corpus
```
```bash
.venv/bin/python3 -m prism.ingest.build_kg
```
```bash
.venv/bin/python3 -m prism.eval.verify_end_to_end
```
```bash
.venv/bin/python3 -m prism.external_benchmarks.verify_generalization
```
```bash
.venv/bin/python3 -m prism.generalization.verify_generalization_v2
```
```bash
.venv/bin/python3 -m prism.kg_extraction.verify_structure_shift
```
```bash
.venv/bin/python3 -m prism.public_corpus.verify_public_corpus
```
```bash
.venv/bin/python3 -m prism.public_graph.verify_public_graph
```
```bash
.venv/bin/python3 -m prism.adversarial.verify_adversarial
```
```bash
.venv/bin/python3 -m prism.calibration.verify_calibrated_router
```
```bash
.venv/bin/python3 -m prism.human_eval.analyze_annotations
```
```bash
.venv/bin/python3 -m prism.human_eval.compare_annotations
```
```bash
.venv/bin/python3 -m prism.open_corpus.verify_open_corpus
```
```bash
.venv/bin/python3 -m prism.ras_v3.verify_ras_v3
```
```bash
.venv/bin/python3 -m prism.ras_v4.verify_ras_v4
```
```bash
.venv/bin/python3 -m prism.analysis.report_artifacts
```
```bash
.venv/bin/python3 -m prism.finalize.build_release
```
```bash
.venv/bin/python3 -m prism.finalize.verify_release
```

Runtime corpora are under `data/runtime_corpora/`. Human-eval inputs and summaries are under `data/human_eval/`.