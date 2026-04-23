# WORK LOG: Optional Local LLM Experiments

Timestamp: 2026-04-21 21:58

## Summary

Added an analysis-only local LLM experiment layer for PRISM. The new layer can route queries with a local Ollama-compatible model, optionally refine deterministic PRISM answers/traces using only retrieved evidence, compare LLM routing against existing router baselines, and connect LLM route choices to the real comparative human-eval artifacts.

Computed RAS remains the production router. No production retrieval, answering, benchmark gold labels, demo behavior, or human annotations were changed.

## Files Changed

- `prism/llm_experiments/__init__.py`
- `prism/llm_experiments/local_llm_client.py`
- `prism/llm_experiments/router_prompt.py`
- `prism/llm_experiments/llm_router.py`
- `prism/llm_experiments/answer_refiner.py`
- `prism/llm_experiments/trace_refiner.py`
- `prism/llm_experiments/compare_to_human_eval.py`
- `prism/llm_experiments/verify_llm_router.py`
- `tests/test_llm_experiments.py`
- `data/eval/llm_router_eval.json`
- `data/eval/llm_router_eval.csv`
- `data/eval/llm_router_eval_summary.md`
- `data/eval/llm_experiment_results_for_paper.md`
- `data/eval/llm_router_comparison.png`
- `data/eval/llm_adversarial_tag_breakdown.png`
- `data/human_eval/llm_vs_human_summary.json`
- `data/human_eval/llm_vs_human_summary.md`
- `WORK_LOG_2026-04-21_2158_LLM_EXPERIMENTS.md`
- `PROCESS_GUIDE_2026-04-21_2158_LLM_EXPERIMENTS.md`

## Commands Run

- `.venv/bin/python3 --version`
- `sed -n '1,220p' WORK_LOG_2026-04-21_1751_REAL_HUMAN_EVAL.md`
- `sed -n '1,260p' PROCESS_GUIDE_2026-04-21_1751_REAL_HUMAN_EVAL.md`
- `.venv/bin/python3 -m pytest -q tests/test_llm_experiments.py`
- `.venv/bin/python3 -m prism.llm_experiments.verify_llm_router`
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
- `.venv/bin/python3 -m prism.analysis.report_artifacts`
- `.venv/bin/python3 -m prism.llm_experiments.verify_llm_router`

## Test Results

- Focused LLM tests: `5 passed in 2.12s`
- Full test suite: `114 passed, 3 warnings in 87.07s`
- Corpus build: wrote 148 documents to `data/processed/corpus.jsonl`
- KG build: wrote 99 triples to `data/processed/kg_triples.jsonl` and `data/processed/kg.ttl`
- Curated end-to-end verification: `80/80` answers, route accuracy `1.000`
- External mini-benchmark: `32/32`, RAS answer accuracy `1.000`
- Generalization v2: clean test answer accuracy `1.000`, noisy test answer accuracy `0.975`
- Structure shift: curated and mixed modes retain `1.000`; extracted mode degrades deductive performance as expected
- Public raw corpus: test answer accuracy `1.000`, evidence hit@k `1.000`
- Public graph: test answer accuracy `1.000`, evidence hit@k `1.000`
- Adversarial benchmark: computed RAS answer accuracy `0.729` overall and `0.917` on test
- Calibration verifier: adversarial test normal answer `0.917`; calibrated/rescue answer `0.958`
- Human eval: standard annotations loaded, 36 items, 144 annotations
- Comparative human eval: comparative annotations loaded, 28 items, 112 annotations

## LLM Router Summary

Implemented an optional local LLM router with an Ollama-compatible client. The router prompt includes:

- query
- PRISM route definitions
- parsed query feature flags
- computed RAS scores
- optional evidence availability hints

The LLM is required to return JSON with:

- predicted route
- confidence
- rationale
- optional alternative route ranking

Current runtime result:

- Provider: `ollama`
- Model: `llama3.1:8b`
- Endpoint: `http://127.0.0.1:11434/api/generate`
- Availability: `False`
- Error: `<urlopen error [Errno 1] Operation not permitted>`

Because the local LLM endpoint was unavailable in this sandbox, no LLM route accuracy or answer accuracy claims were made. The verifier still wrote complete partial artifacts with setup guidance and non-LLM baseline comparisons.

## LLM Answer/Trace Refinement Summary

Added an evidence-grounded answer/trace refiner. It runs only after PRISM has already selected a route, retrieved evidence, and generated the deterministic structured answer.

The refiner prompt requires the LLM to:

- use only retrieved evidence
- preserve evidence ids
- preserve selected backend
- avoid outside facts
- say insufficient evidence when evidence is insufficient

If the local LLM is unavailable, the refiner returns the original deterministic answer and trace unchanged, with metadata explaining that refinement was skipped.

## LLM-Vs-Human Summary

Added `data/human_eval/llm_vs_human_summary.json` and Markdown output. The comparison is designed to map LLM route choices to the human-majority preferred route in the comparative packet.

Current result:

- Status: `llm_unavailable`
- Comparative packet size: 28
- Annotation count: 112
- Alignment could not be computed because local LLM route choices were unavailable

The summary explicitly states that this is not a direct human judgment of LLM-generated answers. If a local LLM is later available, rerunning `python -m prism.llm_experiments.verify_llm_router` will populate the alignment fields.

## Known Limitations

- Local Ollama was not reachable in the sandbox, so LLM runtime metrics are pending.
- The available artifacts are a harness and baseline context, not evidence that an LLM improves PRISM.
- The current live LLM path uses a simple JSON prompt and parser; prompt robustness may need improvement once a model is connected.
- Human-alignment comparison is approximate: it compares route choices to the human-majority preferred system route, not to newly annotated LLM outputs.
- Evidence-grounded refinement is implemented but not scored by humans yet.
