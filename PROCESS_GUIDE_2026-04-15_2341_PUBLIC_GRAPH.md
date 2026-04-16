# Process Guide: Public Graph Grounding

## Basic Summary

This step adds a public-graph layer so PRISM can test deductive and relational reasoning using structure derived from cached public raw documents, not only the compact curated demo KG. The production demo path is unchanged: computed RAS remains the router, and the curated demo KG remains the default KG unless a public-graph evaluation CLI explicitly selects another structure mode.

## What Was Implemented

New package:

- `prism/public_graph/`

Main modules:

- `entity_normalization.py`: normalizes entity aliases such as `bats` to `bat` and keeps relation names in a controlled predicate set.
- `extract_graph.py`: extracts public graph triples from cached public corpus documents using lightweight source-aware profiles and conservative text patterns.
- `build_public_graph.py`: writes the extracted public graph as JSONL triples, Turtle, and metadata.
- `loaders.py`: defines the public-structure benchmark item schema and loader.
- `benchmark_builder.py`: creates a separate public-structure benchmark with KG and Hybrid examples.
- `verify_public_graph.py`: evaluates `demo_kg`, `public_graph`, and `mixed_public_demo` structure modes.
- `compare_structure_grounding.py`: writes a compact comparison of demo KG vs public graph vs mixed mode.

Tests were added in `tests/test_public_graph.py`.

## How The Public Graph Is Built

The public graph is built from the processed public raw corpus at:

- `data/processed/public_corpus.jsonl`

The graph builder reads public `Document` objects and extracts triples with:

- subject
- predicate
- object
- source document id
- extraction confidence
- pattern/source metadata

The current output artifacts are:

- `data/processed/public_graph_triples.jsonl`
- `data/processed/public_graph.ttl`
- `data/processed/public_graph_metadata.json`

The public graph is separate from:

- the curated demo KG at `data/processed/kg_triples.jsonl`
- the local extracted KG at `data/processed/kg_extracted_triples.jsonl`

This separation matters because each graph answers a different research question:

- Demo KG: does PRISM work with clean curated structure?
- Local extracted KG: what happens when structure is extracted from normalized local corpus text?
- Public graph: what happens when structure is extracted from cached public raw-document text?

## How Entities And Relations Are Normalized

Entity normalization maps common surface forms to canonical entity strings.

Examples:

- `bats` -> `bat`
- `penguins` -> `penguin`
- `mammals` -> `mammal`
- `vertebrates` -> `vertebrate`

Relation normalization keeps the graph small and inspectable.

Controlled predicates include:

- `is_a`
- `capable_of`
- `not_capable_of`
- `has_property`
- `produces`
- `eats`

This is intentionally simple. The goal is not to build a full public web knowledge graph; the goal is to test PRISM under a more realistic structure-grounding shift while keeping the pipeline local and reproducible.

## Structure Modes

The public-graph evaluation supports three structure modes:

- `demo_kg`: uses the compact curated demo KG only.
- `public_graph`: uses only the graph extracted from public raw documents.
- `mixed_public_demo`: merges demo KG and public graph triples.

Mixed mode deduplicates identical subject-predicate-object triples. When an overlap is found, provenance is preserved in:

- `data/processed/public_graph_mixed_metadata.json`

The merged triple keeps a clear source trail so later reasoning traces can distinguish demo KG support from public graph support.

## How The Public-Structure Benchmark Is Grounded

The public-structure benchmark is stored at:

- `data/processed/public_structure_benchmark.jsonl`

It contains:

- `32` total examples
- `16` dev examples
- `16` test examples
- `16` KG/deductive examples
- `16` Hybrid/relational examples

Each benchmark item includes:

- query
- split
- route family (`kg` or `hybrid`)
- gold answer
- gold source document ids
- gold public graph triple ids
- optional evidence text

The benchmark is intentionally separate from the curated, external, generalization_v2, and public raw-document benchmark suites. That keeps the research claims clean: this suite specifically asks whether public-derived structure supports deductive and relational behavior.

## How Public-Graph Evaluation Works

Run:

```bash
.venv/bin/python3 -m prism.public_graph.verify_public_graph
```

The verifier:

1. Builds or refreshes the public corpus.
2. Builds or refreshes the demo KG.
3. Builds the public graph.
4. Builds the public-structure benchmark.
5. Builds retrievers for each structure mode.
6. Runs computed RAS, always-KG, and always-Hybrid systems.
7. Reports route accuracy, answer accuracy, evidence hit@k, per-family accuracy, and structure-mode deltas.

The output artifacts are:

- `data/eval/public_graph_eval.json`
- `data/eval/public_graph_eval.csv`
- `data/eval/public_graph_eval_summary.md`
- `data/eval/public_graph_mode_performance.png`
- `data/eval/public_graph_dev_test_modes.png`

## How Structure-Mode Comparison Works

Run:

```bash
.venv/bin/python3 -m prism.public_graph.compare_structure_grounding
```

The comparison reads `data/eval/public_graph_eval.json` and writes:

- `data/eval/public_structure_comparison.json`
- `data/eval/public_structure_comparison_summary.md`

It compares:

- demo KG answer accuracy
- public graph answer accuracy
- mixed public+demo answer accuracy
- per-family deltas for KG and Hybrid queries
- evidence hit@k deltas

The current result shows public graph matching demo KG on the public-structure benchmark. This is a positive targeted grounding result, but not a broad claim that rule-based public graph extraction generalizes to arbitrary public text.

## Concepts And Terms Used

- Public graph: a graph of triples extracted from cached public raw-document text.
- Triple: a structured fact in subject-predicate-object form, such as `bat is_a mammal`.
- Turtle: an RDF serialization format used to store triples in a graph-friendly text format.
- Provenance: metadata showing where evidence came from, such as a source document id or graph mode.
- Structure mode: the graph source used during evaluation, such as `demo_kg`, `public_graph`, or `mixed_public_demo`.
- Deductive query: a query that needs structured facts, class membership, properties, or counterexamples.
- Relational query: a query that needs a bridge/path between entities and often benefits from Hybrid evidence.
- Evidence hit@k: whether expected supporting evidence appears in the top retrieved results.
- Mixed mode: a graph mode that combines curated and public-derived triples while preserving overlap metadata.

## What Remains Unresolved

- Public graph extraction is rule/profile-based and not a general information extraction solution.
- The public graph is small and source-selected.
- Public graph benchmark examples are grounded in the extracted graph, so they test targeted public-structure support rather than arbitrary public reasoning.
- Alias normalization and predicate normalization remain limited.
- The evaluation uses normalized answer matching, not human judgment.
- The production demo still uses the curated KG by default, which is the safer behavior for live presentation.
