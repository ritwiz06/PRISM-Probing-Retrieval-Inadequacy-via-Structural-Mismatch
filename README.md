# PRISM

PRISM is a local-first multi-representation RAG router project for probing retrieval inadequacy via structural mismatch.

This bootstrap provides:

- Editable install support via `pyproject.toml`
- Config loading from YAML-like files and environment variables
- Structured logging
- Smoke CLIs for corpus build, KG build, and evaluation
- Minimal retriever/router wiring with pytest coverage

## Quickstart

```bash
pip install -e .
pytest -q
python -m prism.ingest.build_corpus
python -m prism.ingest.build_kg
python -m prism.eval.run_eval --smoke
```
