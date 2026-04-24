# Process Guide: Open-Corpus Workspace And RAS V2 Experiment

## Basic Summary

This step turned PRISM from a fixed benchmark/demo system into a reusable source-pack and open-corpus workspace. Users can now build runtime corpora from built-in source packs or local documents, inspect route behavior across BM25/Dense/KG/Hybrid, and see a query-local graph for the current query.

The work is additive. Computed RAS remains the production router. The new `computed_ras_v2` route variant is an analysis-only hard-case experiment because it improves adversarial accuracy slightly but does not beat the calibrated rescue layer.

## How Open-Corpus Ingestion Works

Open-corpus ingestion lives in:

- `prism/open_corpus/normalize_documents.py`
- `prism/open_corpus/load_local_docs.py`
- `prism/open_corpus/load_urls.py`
- `prism/open_corpus/workspace.py`

All input documents are normalized into a common document schema with:

- document id
- title
- source type
- provenance
- raw text
- cleaned text
- optional section metadata
- optional source URL

Supported local file types:

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.json`

Runtime corpora are written under:

- `data/runtime_corpora/<corpus_name>/documents.jsonl`
- `data/runtime_corpora/<corpus_name>/metadata.json`

The open-corpus path is separate from the curated benchmark corpus. Existing benchmark files and gold labels are not modified.

## How Source Packs Work

Source packs live in:

- `prism/open_corpus/source_packs.py`
- `prism/open_corpus/build_source_pack.py`

Each source pack is an explicit list of reproducible source documents with provenance metadata. The current packs are:

- `wikipedia`
- `rfc_specs`
- `medical_codes`
- `policy_docs`
- `cs_api_docs`

The builder command is:

```bash
.venv/bin/python3 -m prism.open_corpus.build_source_pack --pack wikipedia
```

It writes:

- `data/runtime_corpora/source_pack_<pack>/documents.jsonl`
- `data/runtime_corpora/source_pack_<pack>/metadata.json`

The current implementation uses compact cached/source-listed content so demos do not require web search or a paid API. URL loading is available separately for user-provided URL lists.

## How Index Building Works

Runtime index building lives in:

- `prism/open_corpus/build_indexes.py`

It builds:

- a BM25 index over normalized runtime documents
- a Dense index using the current Dense retriever backend

Dense still reports its active backend through existing metadata. On this machine it uses:

- `sentence_transformers+faiss`

Index artifacts are kept under the runtime corpus folder so open-corpus experiments do not overwrite curated benchmark indexes.

## How Query-Local Graph Construction Works

Query-local graph construction lives in:

- `prism/open_corpus/query_local_graph.py`

It builds a small graph from the selected runtime documents for the current query. This graph is not the curated demo KG, not the extracted local KG, and not the public graph benchmark artifact.

The extractor is lightweight and rule-based. It currently recognizes controlled relation patterns such as:

- `is_a`
- `has_property`
- `uses`
- `connects_to`
- `enables`

Each extracted edge includes:

- normalized subject
- relation
- normalized object
- source document id
- source title
- evidence text
- extraction confidence
- extraction method

The graph is designed to be inspectable during a run. It is useful for explaining possible local structure, not for claiming full graph extraction quality.

## How The UI Uses These Modes

The Streamlit app lives in:

- `prism/demo/app.py`

Benchmark mode remains the default and preserves the existing demo-safe path.

The sidebar now includes a corpus/source selector:

- benchmark mode
- source-pack mode
- local demo folder mode

When an open-corpus mode is selected, the app calls:

- `prism/open_corpus/view_model.py`

The open-corpus view model provides:

- selected corpus metadata
- runtime document counts
- query-local graph summary
- route comparisons for BM25, Dense, KG, and Hybrid
- routing-mode comparisons for computed RAS, `computed_ras_v2`, keyword router, and optional LLM router
- final answer and reasoning trace through the existing PRISM pipeline

The app remains useful when optional LLM runtime is unavailable. The LLM row is reported as unavailable rather than crashing.

## How `computed_ras_v2` Works

The route-improvement experiment lives in:

- `prism/ras/route_improvement.py`

It is a wrapper around the existing computed RAS decision. It keeps the original route unless narrow hard-case signals justify an analysis-time adjustment.

Signals used:

- RAS score margin
- identifier-heavy query detection
- lexical-vs-semantic ambiguity
- relational bridge markers
- deductive markers
- source-type hints
- query-local graph availability hooks

Examples of adjustments:

- strong identifiers keep BM25
- relational bridge language can prefer Hybrid
- deductive class-membership language can prefer KG
- identifier-like but conceptually paraphrased ambiguity can prefer Dense instead of lexical over-triggering

Current result:

- computed RAS answer accuracy on the adversarial suite: `0.729`
- `computed_ras_v2` answer accuracy on the adversarial suite: `0.750`
- calibrated rescue answer accuracy on the adversarial suite: `0.958`

Because `computed_ras_v2` is not the best route strategy and has not justified replacing the stable default, it remains analysis-only.

## Artifacts Generated

Runtime corpus artifacts:

- `data/runtime_corpora/source_pack_wikipedia/documents.jsonl`
- `data/runtime_corpora/source_pack_wikipedia/metadata.json`
- `data/runtime_corpora/source_pack_rfc_specs/documents.jsonl`
- `data/runtime_corpora/source_pack_rfc_specs/metadata.json`
- `data/runtime_corpora/local_demo_docs/`
- `data/runtime_corpora/open_corpus_smoke/`

Evaluation artifacts:

- `data/eval/open_corpus_smoke.json`
- `data/eval/open_corpus_smoke.csv`
- `data/eval/open_corpus_smoke.md`
- `data/eval/open_workspace_summary.md`
- `data/eval/open_workspace_vs_baselines.json`
- `data/eval/open_domain_extension_for_paper.md`
- `data/eval/ras_v2_summary.md`

Plots:

- `data/eval/open_corpus_route_usage.png`
- `data/eval/ras_v2_adversarial_route_comparison.png`

## What Remains Unresolved

PRISM is now a practical source-pack/open-corpus workspace, but it is not a web-scale search engine. The current ingestion layer works best when a user provides documents, folders, URLs, or source packs.

Open limitations:

- query-local graph extraction is rule-based and noisy
- PDF ingestion was not added
- source packs are intentionally compact
- arbitrary web search is out of scope
- `computed_ras_v2` does not replace the production router
- local LLM routing remains optional and unavailable unless a local endpoint is running

## Concepts And Topics Used

Open-corpus mode:

PRISM runs over user-provided or source-pack documents instead of only the fixed benchmark corpus.

Source pack:

A small, explicit, cached set of documents for a topic family such as RFC specs or Wikipedia-style facts.

Runtime corpus:

A normalized corpus written under `data/runtime_corpora/` with its own metadata and indexes.

Query-local graph:

A small graph extracted from the current query's local evidence. It helps inspect possible structural links without replacing the curated KG.

Route comparison:

The UI shows what BM25, Dense, KG, and Hybrid would retrieve for the same query so the representation-routing decision is visible.

`computed_ras_v2`:

An optional hard-case route experiment that adds interpretable arbitration signals on top of computed RAS. It is analysis-only.
