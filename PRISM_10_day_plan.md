# PRISM 10-Day Solo Build Plan

## Goal
Ship a working end-to-end demo and a report for a multi-representation RAG router with:
- Dense retrieval
- BM25 retrieval
- KG retrieval
- Hybrid retrival
- Computed RAS router
- Optional local-LLM router baseline
- Streamlit demo UI
- Evaluation script and report figures

## Non-negotiable scope
1. Working demo with all four backends.
2. Computed RAS working and used in production route selection.
3. Evaluation on a manageable benchmark slice (80-120 queries total).
4. Report with architecture, claims, experiments, and failure analysis.

## Scope cuts
- Do NOT build a full Wikipedia dump pipeline.
- Do NOT depend on paid APIs.
- Do NOT make the local LLM router the only router.
- Do NOT start with GraphRAG-style community summarization.
- Do NOT chase huge benchmarks before the demo works.

## Recommended stack
- Python 3.11
- Ollama for local generation/routing baseline
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 or BAAI/bge-small-en-v1.5
- Dense index: faiss-cpu
- Sparse index: rank-bm25
- KG: RDFLib + NetworkX
- UI: Streamlit
- Tests: pytest

## Repo structure
```text
prism/
  AGENTS.md
  README.md
  pyproject.toml
  .env.example
  data/
    raw/
    processed/
    indices/
    eval/
  configs/
    default.yaml
  prism/
    __init__.py
    config.py
    schemas.py
    ingest/
      wikipedia_fetch.py
      formal_docs_fetch.py
      build_corpus.py
      build_kg.py
    retrievers/
      base.py
      bm25_retriever.py
      dense_retriever.py
      kg_retriever.py
      hybrid_retriever.py
    ras/
      feature_parser.py
      penalty_table.py
      compute_ras.py
      llm_router.py
    answer/
      prompt_builder.py
      generator.py
      trace.py
      soundness.py
    eval/
      datasets.py
      metrics.py
      gold_labels.py
      run_eval.py
      analyze_results.py
    ui/
      app.py
  tests/
    test_bm25.py
    test_dense.py
    test_kg.py
    test_ras.py
    test_pipeline.py
```

## Build order
1. BM25 backend
2. Dense backend
3. KG backend
4. Hybrid Backend
5. Computed RAS parser + router
6. End-to-end pipeline
7. UI
8. Evaluation harness
9. Local LLM router baseline
10. Reasoning trace + soundness checks
11. Report and demo polish

## Data strategy
### Corpus
Use a mixed small corpus:
- 400-500 Wikipedia pages for semantic, deductive, and relational questions
- 100-150 formal documentation pages for exact-match lexical questions (API docs, RFCs, standards, or medical/legal snippets)

### KG strategy
Build a medium local KG only for entities and relations needed by the evaluation set.
Do NOT attempt a general KG extraction system from all Wikipedia text.
Use one or more of:
- hand-curated triples for demo-critical examples
- Wikidata-derived triples cached locally
- infobox/category/page-link extraction for limited predicates

### Evaluation set
Target 80 queries total:
- 20 deductive
- 20 semantic
- 20 lexical exact-match
- 20 relational / multi-hop

For each query store:
- gold route
- gold answer
- gold evidence doc or triple ids
- optional notes on why the route is correct

## RAS production strategy
### Production route selector
Use computed RAS as the default route selector.

### Comparison baseline
Add a local-LLM router that predicts:
- features
- selected representation
- approximate RAS scores

### Why this order
Computed RAS is deterministic and demo-safe.
The LLM router is useful as an experiment, not as the only working path.

## Day-by-day plan
### Day 1 - bootstrap + corpus + BM25
- Create repo skeleton, pyproject, config system, tests, AGENTS.md
- Build corpus ingestion scripts
- Implement BM25 retriever and smoke test
- Save first 200-250 documents locally

Acceptance:
- `pytest -q` passes for BM25 tests
- `python -m prism.ingest.build_corpus` creates local corpus files
- `python -m prism.eval.run_eval --backend bm25 --smoke` works

### Day 2 - dense retrieval
- Add embedding model wrapper
- Build chunking + FAISS index
- Implement dense retriever
- Add retrieval comparison notebook or script

Acceptance:

- Dense top-k retrieval works on at least 10 smoke queries
- Index build + load + query are stable

### Day 3 - KG ingest

- Define local KG schema
- Build triple store and NetworkX mirror
- Create initial triples for 30-50 entities / relations
- Implement SPARQL templates for membership, property, and relation lookup

Acceptance:
- At least 20 deductive/relational test queries work through KG only
- Graph serializes to Turtle/JSON-LD and reloads cleanly

### Day 4 - complete KG backend
- Add multi-hop traversal support
- Add provenance for triples and text evidence
- Add KG result linearization for answer generation
- Expand KG coverage to evaluation set

Acceptance:
- KG answers demo-critical queries such as class/property and relation-chain examples
- `test_kg.py` and end-to-end smoke tests pass

### Day 5 - computed RAS + parser
- Implement feature parser (rules first, LLM fallback optional)
- Encode penalty table
- Implement computed RAS scorer and router
- Add tests for canonical examples

Acceptance:
- Queries like “Can a mammal fly?”, “What does HIPAA §164.512 say?”, and “What feels like climate anxiety?” route correctly
- RAS values are logged and explainable

### Day 6 - end-to-end answering + traces
- Implement answer generator prompt using only retrieved evidence
- Add deterministic reasoning trace JSON
- Add soundness checks:
  - selected backend has minimum RAS
  - answer cites evidence ids
  - universal claims require explicit counterexample or full-support check

Acceptance:
- One command runs full pipeline on a query and prints answer + trace

### Day 7 - UI + hybrid backend
- Build Streamlit UI with tabs:
  - query
  - parsed features
  - RAS table
  - selected backend
  - evidence pane
  - final answer
  - compare all backends
- Implement hybrid backend with RRF across dense and KG evidence

Acceptance:
- Demo UI is usable end to end
- Hybrid backend runs for relational queries

### Day 8 - evaluation harness
- Finalize 80-query benchmark slice
- Implement metrics:
  - route accuracy
  - retrieval hit@k / recall@k
  - answer exact match / token F1 when possible
  - RAS vs failure correlation
- Add baselines:
  - always-dense
  - always-BM25
  - always-KG
  - random router
  - computed-RAS router
  - optional LLM router

Acceptance:
- One evaluation command produces CSV/JSON results and plots

### Day 9 - experiments + analysis
- Run full evaluation
- Identify top 10 failures
- Fix major bugs in parser, KG coverage, and prompts
- Freeze the demo query set

Acceptance:
- Stable numbers and screenshots for report
- Demo never crashes on chosen presentation queries

### Day 10 - report + final polish
- Write report
- Export figures and tables
- Prepare 20 demo questions and expected outcomes
- Add README setup steps
- Record backup screenshots/video if live demo fails

Acceptance:
- Report draft complete
- README reproducible from clean clone
- Presentation demo script ready

## Metrics to ship
Minimum:
- Route accuracy
- Retrieval hit@k
- Answer exact match / F1 on answerable subsets
- RAS/failure correlation

Nice-to-have:
- Trace validity manual review on 30 queries
- Simple contradiction/support check over answer/evidence

## Demo requirements
Each demo run should show:
1. parsed query features
2. per-representation RAS table
3. selected route
4. retrieved evidence
5. answer
6. reasoning trace
7. optional comparison with the wrong backend

## Risk management
### If KG is behind
Use a curated KG for the 30 deductive + relational demo/eval queries.
Do not block the whole project on automatic KG extraction.

### If the LLM router is flaky
Keep computed RAS as default and evaluate the LLM router as an ablation.

### If evaluation is behind
Ship 80 high-quality labeled queries instead of a larger noisy benchmark.

### If UI is behind
Ship a Streamlit single-page app rather than FastAPI + frontend split.

## Commands Codex should be able to run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pytest -q
python -m prism.ingest.build_corpus
python -m prism.ingest.build_kg
python -m prism.eval.run_eval --smoke
python -m prism.eval.run_eval --full
streamlit run prism/ui/app.py
```

## Definition of done
The project is done when all of the following are true:
- All three retrievers return evidence for their intended query types
- Computed RAS routes queries correctly on the labeled set
- End-to-end app answers queries with visible evidence and trace
- Evaluation script compares at least 5 baselines
- Report includes architecture, claims, metrics, results, and failure analysis
