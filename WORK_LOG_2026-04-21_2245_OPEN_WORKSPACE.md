# WORK LOG: Open-Corpus Workspace And RAS V2 Experiment

Timestamp: 2026-04-21 22:45

## Summary

Added an additive generalized PRISM workspace layer. The new layer lets PRISM normalize user/local/source-pack documents into runtime corpora, build reusable BM25 and Dense indexes, construct query-local graphs from retrieved/open-corpus evidence, expose open-corpus inspection in the Streamlit demo, and evaluate a lightweight `computed_ras_v2` routing experiment against hard-case weaknesses.

Computed RAS remains the production router. `computed_ras_v2` is report-facing and analysis-only because it improves adversarial answer accuracy slightly but does not beat calibrated rescue or justify replacing the stable default.

## Files Changed

- `prism/open_corpus/__init__.py`
- `prism/open_corpus/normalize_documents.py`
- `prism/open_corpus/load_local_docs.py`
- `prism/open_corpus/load_urls.py`
- `prism/open_corpus/source_packs.py`
- `prism/open_corpus/build_source_pack.py`
- `prism/open_corpus/build_indexes.py`
- `prism/open_corpus/query_local_graph.py`
- `prism/open_corpus/workspace.py`
- `prism/open_corpus/view_model.py`
- `prism/open_corpus/verify_open_corpus.py`
- `prism/ras/route_improvement.py`
- `prism/demo/app.py`
- `tests/test_open_corpus.py`
- `data/runtime_corpora/source_pack_wikipedia/documents.jsonl`
- `data/runtime_corpora/source_pack_wikipedia/metadata.json`
- `data/runtime_corpora/source_pack_rfc_specs/documents.jsonl`
- `data/runtime_corpora/source_pack_rfc_specs/metadata.json`
- `data/runtime_corpora/local_demo_docs/`
- `data/runtime_corpora/open_corpus_smoke/`
- `data/eval/open_corpus_smoke.json`
- `data/eval/open_corpus_smoke.csv`
- `data/eval/open_corpus_smoke.md`
- `data/eval/open_workspace_summary.md`
- `data/eval/open_workspace_vs_baselines.json`
- `data/eval/open_domain_extension_for_paper.md`
- `data/eval/ras_v2_summary.md`
- `data/eval/open_corpus_route_usage.png`
- `data/eval/ras_v2_adversarial_route_comparison.png`
- `WORK_LOG_2026-04-21_2245_OPEN_WORKSPACE.md`
- `PROCESS_GUIDE_2026-04-21_2245_OPEN_WORKSPACE.md`

## Commands Run

- `.venv/bin/python3 -m pip install -e .`
- `.venv/bin/python3 -m pytest -q tests/test_open_corpus.py`
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
- `.venv/bin/python3 -m prism.open_corpus.build_source_pack --pack wikipedia`
- `.venv/bin/python3 -m prism.open_corpus.build_source_pack --pack rfc_specs`
- `.venv/bin/python3 -m prism.open_corpus.verify_open_corpus`
- `.venv/bin/python3 -m streamlit run prism/demo/app.py --server.headless true`

## Test Results

- Focused open-corpus tests: `6 passed in 2.05s`
- Full test suite: `120 passed, 3 warnings in 86.49s`
- Corpus build: wrote `148` documents to `data/processed/corpus.jsonl`
- KG build: wrote `99` triples to `data/processed/kg_triples.jsonl` and `data/processed/kg.ttl`
- Curated end-to-end verification: `80/80` answers, route accuracy `1.000`, evidence hit@k `1.000`
- External mini-benchmark: `32/32`, RAS route accuracy `1.000`, answer accuracy `1.000`, Dense backend `sentence_transformers+faiss`
- Generalization v2: clean test answer accuracy `1.000`, noisy test answer accuracy `0.975`
- Structure shift: curated and mixed KG modes retain perfect targeted performance; extracted-only mode documents expected deductive degradation
- Public raw corpus: test answer accuracy `1.000`, evidence hit@k `1.000`
- Public graph: test answer accuracy `1.000`, evidence hit@k `1.000`
- Adversarial benchmark: computed RAS overall route and answer accuracy `0.729`; test answer accuracy `0.917`
- Calibration verifier: adversarial test normal answer accuracy `0.917`; calibrated/rescue answer accuracy `0.958`
- Standard human eval: `36` packet items and `144` annotations loaded
- Comparative human eval: `28` packet items loaded with adjudication artifacts
- Open-corpus smoke: `5/5` examples passed, answer accuracy `1.000`, route accuracy `1.000`, evidence hit@k `1.000`
- Streamlit smoke: app booted in headless mode and exposed `http://localhost:8501`; stopped cleanly with Ctrl-C

## Open-Corpus / Source-Pack Summary

The open-corpus layer supports:

- local files and folders through `load_local_docs`
- URL lists with local caching through `load_urls`
- normalized `.txt`, `.md`, `.html`, `.htm`, and `.json` inputs
- built-in source packs through `source_packs`
- runtime corpus artifacts under `data/runtime_corpora/<name>/`
- BM25 and Dense index artifacts under each runtime corpus index folder

Implemented built-in source packs:

- `wikipedia`
- `rfc_specs`
- `medical_codes`
- `policy_docs`
- `cs_api_docs`

The acceptance run explicitly rebuilt:

- `source_pack_wikipedia`: `4` documents
- `source_pack_rfc_specs`: `3` documents

The source-pack implementation is intentionally cached and source-listed. It does not require web search or a paid API.

## Query-Local Graph Summary

Added a lightweight query-local graph builder in `prism/open_corpus/query_local_graph.py`.

The graph is built on demand from the current query and the selected runtime corpus documents. It extracts controlled, inspectable edges such as:

- `is_a`
- `has_property`
- `uses`
- `connects_to`
- `enables`

Each edge records source document provenance, text evidence, confidence, and extraction method. Query-local graph artifacts are exportable as JSON and JSONL triples, and the Streamlit UI shows node/edge counts and graph/path evidence when open-corpus modes are active.

## UI Enhancement Summary

The existing Streamlit app keeps benchmark mode as the default. It now adds an optional corpus/source selector:

- benchmark mode
- source-pack mode
- local demo folder mode

For open-corpus modes, the UI shows:

- selected corpus/source pack
- parsed query features through the existing pipeline
- computed RAS route and answer output
- BM25, Dense, KG, and Hybrid route comparisons
- computed RAS, `computed_ras_v2`, keyword router, and optional LLM router comparisons
- retrieved evidence
- query-local graph summary and path/triple evidence
- final answer and reasoning trace

Optional LLM routing remains clearly unavailable or experimental when the local endpoint is not reachable.

## Route-Improvement Summary

Added `computed_ras_v2` in `prism/ras/route_improvement.py` as an interpretable, analysis-only experiment. It starts with computed RAS and applies narrow hard-case adjustments based on:

- route margin
- identifier-heavy query detection
- lexical-vs-semantic ambiguity
- relational bridge markers
- deductive markers
- source-type hints
- query-local graph availability hooks

Adversarial comparison:

- computed RAS answer accuracy: `0.729`
- `computed_ras_v2` answer accuracy: `0.750`
- calibrated rescue answer accuracy: `0.958`
- classifier-router answer accuracy: `0.875`

Conclusion: `computed_ras_v2` improves over computed RAS on hard cases but is not strong enough to replace the production router. It remains analysis-only.

## Known Limitations

- This is source-pack/open-corpus QA, not web-scale open-domain QA.
- URL loading is lightweight and cached, but network fetching depends on source availability and is not needed for the built-in pack fallback.
- PDF support was not added because the current repo did not already expose a reliable PDF text path.
- Query-local graph extraction is rule-based and should be treated as inspectable support, not full information extraction.
- Runtime corpora are smaller than real enterprise or web corpora.
- `computed_ras_v2` is useful for analysis but does not beat calibrated rescue on adversarial hard cases.
