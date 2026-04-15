# AGENTS.md

## Project
PRISM: Probing Retrieval Inadequacy via Structural Mismatch.
Goal: a working multi-representation RAG router with Dense, BM25, and KG backends, plus computed RAS and a demo UI.

## Non-negotiable constraints
- Solo 10-day sprint
- No paid APIs in the runtime path
- Local models only via Ollama or llama.cpp
- Default router is computed RAS, not an LLM-only router
- Optimize for reliability and reproducibility over novelty theater

## Engineering rules
- Prefer small, modular Python files
- Add tests for every retrieval backend and router logic
- Use typed dataclasses or Pydantic models for shared schemas
- Keep configs in YAML or env vars, not hardcoded literals
- Every module must expose a small CLI or callable entry point
- Never break smoke tests without fixing them in the same task

## Preferred stack
- Python 3.11
- Streamlit for UI
- RDFLib + NetworkX for KG
- rank-bm25 for sparse retrieval
- sentence-transformers + faiss-cpu for dense retrieval
- Ollama for local answer generation and optional LLM router baseline

## Retrieval routing policy
- Deductive / class-scope / property or membership -> KG
- Semantic / similarity / conceptual -> Dense
- Lexical / exact identifier / formal entity -> BM25
- Relational / multi-hop -> Hybrid

## Soundness rules
- The selected backend must be the minimum-RAS backend
- Final answer must cite retrieved evidence ids
- If the answer claims “all” or other universal scope, trace must show either exhaustive support or counterexample check
- If evidence is insufficient, answer must say insufficient evidence

## Commands
```bash
pip install -e .
pytest -q
python -m prism.ingest.build_corpus
python -m prism.ingest.build_kg
python -m prism.eval.run_eval --smoke
streamlit run prism/ui/app.py
```

## What success looks like
- A user asks a query in the UI
- The app shows parsed features and RAS scores
- The router chooses a backend
- Evidence is shown with provenance
- The system answers and explains why that backend was chosen

## What not to do
- Do not build a full Wikipedia-scale pipeline
- Do not depend on cloud APIs for core functionality
- Do not replace deterministic routing with vague prompt-only behavior
- Do not add heavy frameworks unless necessary
