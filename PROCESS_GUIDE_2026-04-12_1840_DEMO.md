# Process Guide: Prompt 8 Demo App and Presentation Utilities

## Basic Summary

This step added the local PRISM demo layer. The goal is to make the core project idea visible during a presentation: different query structures need different retrieval representations. The app shows the full path from query to parsed features, RAS scores, selected backend, evidence, answer, and reasoning trace.

## How The Demo App Is Structured

The Streamlit entry point is `prism/demo/app.py`.

The app itself stays small. Most non-UI logic lives in `prism/demo/data.py`, which prepares view models for the UI and export tools. This separation keeps the demo testable without trying to test Streamlit rendering internals.

The main demo modules are:

- `prism/demo/app.py`: Streamlit interface.
- `prism/demo/data.py`: query presets, benchmark loading, view-model assembly, evidence formatting, and export payload construction.
- `prism/demo/export_examples.py`: CLI for exporting curated demo examples.
- `prism/demo/report_summary.py`: CLI for printing presentation-ready project status.

## How The Demo Reuses The PRISM Pipeline

The demo calls `prism.app.pipeline.answer_query()` instead of reimplementing routing or retrieval.

That means the UI uses the same path as the tested CLI:

- Parse query features.
- Compute RAS scores.
- Select the minimum-RAS backend.
- Retrieve evidence from BM25, Dense, KG, or Hybrid.
- Synthesize the structured answer.
- Return a reasoning trace.

`answer_query()` now accepts an optional preloaded retriever dictionary. This is an additive change that keeps the old behavior working while letting Streamlit cache retrievers for faster interactive use.

## What UI Sections Map To PRISM Concepts

The query input maps to the user question PRISM must answer.

The preset panel maps to the four route families:

- Lexical queries route to BM25.
- Semantic queries route to Dense.
- Deductive queries route to KG.
- Relational queries route to Hybrid.

The RAS score table maps to computed representation adequacy. Lower RAS is better, and the selected backend is the backend with the lowest score.

The selected backend metric shows which representation PRISM chose.

The final answer panel shows deterministic answer synthesis from retrieved evidence.

The evidence panel shows retrieved document ids, chunk ids, triple/path ids, snippets, and metadata.

The backend-specific metadata table shows the details that make backend differences visible:

- BM25 rank or score metadata when present.
- Dense chunk or parent document metadata when present.
- KG query mode plus triple/path metadata when present.
- Hybrid component ids, contributing backends, and fusion method when present.

The reasoning trace panel shows the inspectable route and evidence audit trail.

## How Benchmark Browsing Works

The benchmark browser loads all four existing slices:

- Lexical slice.
- Semantic slice.
- Deductive slice.
- Relational slice.

The presenter chooses a slice and then chooses a stored query. When that query is run, the UI can show the gold route, predicted route, and route match status.

This is useful in a live demo because the presenter can move between examples that exercise each backend without typing the queries manually.

## Export Examples CLI

The export command is:

```bash
.venv/bin/python3 -m prism.demo.export_examples
```

It writes `data/eval/demo_examples.json`.

The exported examples include:

- Query.
- Parsed features.
- RAS scores.
- Selected backend.
- Structured answer.
- Evidence.
- Reasoning trace.
- Optional gold route and gold answer if the query matches a benchmark item.

This file can be used to prepare slides, notes, screenshots, or demo scripts.

## Report Summary CLI

The report command is:

```bash
.venv/bin/python3 -m prism.demo.report_summary
```

It prints a compact local summary:

- Corpus document count.
- KG triple count.
- Lexical verification result.
- Semantic verification result.
- KG verification result.
- Hybrid verification result.
- End-to-end benchmark result.
- Demo example queries.

By default, it reads the existing verification JSON files when available. Passing `--refresh` reruns the verification functions.

## What Remains Limited About The Presentation Layer

The app is designed for a local sprint demo, not production deployment.

It uses Streamlit tables, metrics, and JSON expanders instead of a highly styled custom frontend.

It does not currently chart score distributions or compare all backend retrieval result lists side by side for every query. It focuses on the selected route and the metadata needed to explain why that route makes sense.

It still uses the deterministic Prompt 7 answerer, so answers are reproducible but less fluent than a local LLM-backed generator would be.

Streamlit requires binding a local port. In restricted sandboxes, that action may need explicit approval even though the app is local.

## Concepts And Topics Used

Streamlit is the local web app framework used for the demo.

View model means a UI-ready dictionary assembled from pipeline output. It keeps the Streamlit file simple and testable.

Benchmark slice means one of the curated query groups: lexical, semantic, deductive, or relational.

RAS score means Representation Adequacy Score. The UI shows all four backend scores so viewers can see why the router picked a backend.

Evidence metadata means backend-specific details attached to a retrieved item, such as BM25 score, Dense parent document, KG query mode, KG triple/path id, Hybrid component ids, and fusion method.

Reasoning trace means the concise, user-facing audit trail that records parsed features, routing scores, selected backend, retrieved evidence, and synthesis notes.

Presentation artifact means an exported JSON or text summary that can be used to prepare slides, notes, or a live demo script.
