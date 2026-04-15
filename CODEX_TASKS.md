# Codex Task Prompts

## Task 1 - Bootstrap the repository
Create a Python 3.11 project for PRISM with editable install support, tests, config loading, logging, and the folder structure described in PRISM_10_day_plan.md. Add smoke-test CLIs for corpus build, KG build, and evaluation. Use small modular files and write pytest tests for the empty pipeline wiring. Do not use any paid APIs. Run pytest -q and fix all failures.

## Task 2 - Implement BM25 retrieval
Implement a BM25 retriever using rank-bm25. Add preprocessing, index build, save/load, and top-k retrieval with document ids and scores. Add tests and a smoke eval script. Ensure lexical exact-match queries are handled with high precision. Run pytest -q and a 5-query smoke test.

## Task 3 - Implement dense retrieval
Implement chunking, embedding, FAISS indexing, save/load, and top-k retrieval. Use a small local embedding model suitable for laptop inference. Return chunk ids, scores, and source metadata. Add tests and compare BM25 vs dense on a small sample.

## Task 4 - Implement the KG backend
Implement a local RDFLib triple store plus a NetworkX mirror. Support loading triples from CSV/JSON, serializing to Turtle, and querying with SPARQL templates for membership, property, and relation lookup. Add 2-hop traversal support for relational queries. Add tests and a smoke CLI.

## Task 5 - Implement computed RAS
Implement a feature parser that extracts scope, predicate type, entity type, and hop count using deterministic heuristics first. Implement the penalty table and a scorer that returns per-representation RAS plus the selected backend. Add tests for canonical routing examples.

## Task 6 - Build the end-to-end pipeline
Implement query -> parse -> RAS -> retrieve -> answer -> trace. The answer generator must only use retrieved evidence. Add deterministic soundness checks and return a structured JSON trace. Add a CLI that runs the full pipeline for one query.

## Task 7 - Add the Streamlit UI
Implement a Streamlit app with sections for query input, parsed features, RAS table, selected route, retrieved evidence, answer, and full reasoning trace. Add an option to compare the chosen route with the other two backends.

## Task 8 - Add evaluation harness
Implement benchmark loading, gold route labels, answer metrics, retrieval hit@k, route accuracy, and RAS/failure correlation. Add baselines for always-dense, always-BM25, always-KG, random router, computed-RAS router, and an optional local-LLM router.

## Task 9 - Add local LLM router baseline
Implement an optional Ollama-based router that predicts query features, route, and approximate RAS scores. This is a baseline only; computed RAS remains the production router. Add evaluation code to compare agreement.

## Task 10 - Polish for demo
Add README instructions, sample data, seeded demo queries, and figure-generation scripts for the report. Ensure the repo can be run from a clean clone with a short setup sequence.
