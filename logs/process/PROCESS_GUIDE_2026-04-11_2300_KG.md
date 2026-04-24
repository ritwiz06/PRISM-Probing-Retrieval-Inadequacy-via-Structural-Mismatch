# Process Guide: KG Retrieval Update

Date and time: 2026-04-11 23:00 America/Phoenix

## Basic Summary

This task upgraded PRISM’s KG backend from a placeholder token-overlap retriever to a real graph-backed retriever. The KG now uses RDFLib as the canonical triple store and NetworkX as a traversal mirror. It supports membership, property, relation, universal counterexample, existential, and 2-hop path queries.

This matters because PRISM’s central claim is about structural mismatch: deductive questions need structured evidence and scope handling, not just similarity search.

## What Was Implemented

The KG work added:

- `rdflib` and `networkx` dependencies
- a real `KGRetriever`
- curated local demo KG build
- JSONL and Turtle KG artifacts
- optional local extra triples from JSON or CSV
- deductive 20-query evaluation slice
- KG verification CLI
- KG-vs-Dense and KG-vs-BM25 comparison
- tests for graph build, traversal, templates, persistence, and verification

The main command for KG verification is:

```bash
.venv/bin/python3 -m prism.eval.verify_kg
```

The final result was:

```text
kg_hit@3=20/20 kg_top1=19/20 dense_hit@3=0/20 bm25_hit@3=0/20 kg_beats_dense=20/20 triples=99 passed=True
```

## How RDFLib Is Used

RDFLib stores the canonical RDF graph.

Each triple becomes:

```text
subject predicate object
```

Example:

```text
bat is_a mammal
```

In RDFLib, these are stored as RDF resources using PRISM-local URIs.

Why RDFLib is useful:

- it gives the project a real RDF graph representation
- it can serialize to Turtle
- it provides a standard path toward SPARQL and richer KG tooling later

The current Turtle artifact is:

```text
data/processed/kg.ttl
```

## How NetworkX Is Used

NetworkX stores a mirror graph for traversal.

The RDFLib graph is good as a canonical triple store.

NetworkX is convenient for graph algorithms and path traversal.

For example, the query:

```text
What two-hop path connects bat to vertebrate?
```

can be answered by finding:

```text
bat -> mammal -> vertebrate
```

That path corresponds to two KG triples:

```text
bat is_a mammal
mammal is_a vertebrate
```

## What The Closed-World Demo Assumption Means

In the real world, absence of a fact does not automatically mean the fact is false.

Example:

If a real KG does not say:

```text
cat capable_of fly
```

that does not prove cats cannot fly unless the KG is known to be complete for that domain.

For this project’s demo slice, we use a closed-world demo assumption.

That means:

- the curated KG is treated as complete only for the narrow demo facts
- universal claims are judged using explicit facts inside this local KG
- this assumption is documented and should not be generalized to the real world

This lets PRISM demonstrate scope and counterexample behavior without pretending to build a universal world model.

## Existential vs Universal Handling

An existential query asks whether at least one example exists.

Example:

```text
Can a mammal fly?
```

The KG can answer yes if it finds:

```text
bat is_a mammal
bat capable_of fly
```

A universal query asks whether all known members satisfy a property.

Example:

```text
Are all mammals able to fly?
```

The KG should not answer yes just because bats can fly.

It must check for counterexamples.

The curated KG contains facts like:

```text
whale is_a mammal
whale not_capable_of fly
```

That counterexample disproves the universal claim under the closed-world demo assumption.

## Query Modes Used

The KG retriever records a `query_mode` in result metadata.

Examples:

- `membership`
- `property`
- `relation`
- `inverse_relation`
- `existential`
- `universal_counterexample`
- `universal_support`
- `two_hop`
- `fallback`

This is useful for later tracing because the UI or answer system can explain how evidence was retrieved.

## Why KG Beats Dense And BM25 Here

Dense retrieval compares vector similarity.

BM25 compares lexical term overlap.

KG retrieval can use explicit structure.

For deductive queries, explicit structure matters.

Example:

```text
Are all mammals able to fly?
```

Dense may retrieve text about mammals and flight.

BM25 may retrieve documents with overlapping terms.

But the KG can retrieve both support and counterexamples:

```text
bat is_a mammal
bat capable_of fly
whale is_a mammal
whale not_capable_of fly
```

That is why KG is the correct backend for this slice.

## What Provenance Is Stored

Each KG `RetrievedItem` includes metadata for tracing:

- triple id or path id
- source doc id
- subject
- predicate
- object
- hop count
- backend type
- query mode

This supports PRISM’s later soundness requirement: answers should cite retrieved evidence ids.

## KG Size

The current KG build produced:

- `99` JSONL triples
- `98` RDFLib graph triples
- `52` NetworkX nodes
- `99` NetworkX edges

RDFLib has one fewer triple because it stores unique `(subject, predicate, object)` RDF triples. JSONL preserves each curated triple id. NetworkX stores keyed multi-edges, so it preserves all 99 edges.

## Remaining Limitations

The KG backend is now real, but still intentionally small.

Limitations:

- not a general KG extractor
- not a full ontology
- no deep multi-hop reasoning beyond the current 2-hop groundwork
- simple rule-based query templates rather than a full parser
- universal handling only works when explicit counterexample facts exist
- closed-world assumption only applies to this demo KG

This is still the correct next step because PRISM now has three distinct retrieval backends with verified behavior:

- BM25 for lexical exact-match queries
- Dense for semantic paraphrase queries
- KG for deductive and scope-sensitive queries
