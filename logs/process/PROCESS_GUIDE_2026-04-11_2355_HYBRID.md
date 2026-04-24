# Process Guide: Hybrid Retrieval Update

Date and time: 2026-04-11 23:55 America/Phoenix

## Basic Summary

This task added PRISM’s real Hybrid retrieval backend. Hybrid now combines BM25, Dense, and KG evidence instead of acting as a simple placeholder. It uses Reciprocal Rank Fusion and can create relational bundles that include both structured KG evidence and text evidence.

Hybrid matters because relational questions often need more than one representation. A KG path can show structure, while a text snippet can explain the relation in natural language.

## What Hybrid Is Doing Internally

Hybrid does not reimplement BM25, Dense, or KG.

Instead, it calls the existing retrievers:

- BM25 returns lexical document hits
- Dense returns semantic text chunks
- KG returns triples or paths

Hybrid then fuses those results.

For normal fusion, it creates RRF-scored fused items.

For relational queries, it can create a relational bundle:

```text
KG path/triple + BM25 or Dense text evidence
```

Example:

```text
What bridge connects bat and vertebrate?
```

Hybrid can combine:

```text
path:kg_bat_is_mammal->kg_mammal_is_vertebrate
rel_bat_vertebrate
```

The first part is structured graph evidence. The second part is text evidence.

## How RRF Works In This Repo

RRF means Reciprocal Rank Fusion.

It combines rankings rather than trying to compare raw scores directly.

The basic formula used here is:

```text
backend_weight * (1 / (rrf_k + rank))
```

Where:

- `rank` is the result position from one backend
- `rrf_k` is a smoothing constant
- `backend_weight` lets KG, Dense, or BM25 contribute more or less

The default `rrf_k` is:

```text
60
```

Why RRF is useful:

- BM25 scores and Dense cosine scores are not directly comparable
- KG path scores are different again
- ranks are easier to combine across different retrieval systems

## What Evidence Types Are Fused

Hybrid can fuse:

- Dense text chunks
- BM25 text document hits
- KG triples
- KG paths
- relational bundles made from KG plus text evidence

The fused result metadata includes:

- contributing backends
- component ids
- raw ranks
- raw scores
- fusion method
- evidence type
- parent doc id
- chunk id
- triple id
- path id

This is important because PRISM needs to explain why evidence was retrieved.

## Why Relational Queries Benefit From Hybrid

Relational queries often ask about a connection.

Example:

```text
What bridge connects penguin and vertebrate?
```

KG can provide:

```text
penguin is_a bird
bird is_a vertebrate
```

Text can provide:

```text
A penguin connects to vertebrate through bird.
```

Neither representation alone is ideal for the full explanation:

- KG gives precise structure
- text gives readable context
- Hybrid gives both together

This is the reason the relational benchmark defines gold evidence as fused evidence: the correct result should include both structure and text.

## What Changed In The Corpus

The corpus now includes 20 small relational snippets.

Examples:

- `rel_bat_vertebrate`
- `rel_penguin_vertebrate`
- `rel_whale_swim`
- `rel_cat_mouse`

These snippets are small and local. They exist to make relational evaluation possible without building a large external data pipeline.

The corpus now builds to:

```text
148 documents
```

## What The Verification Measures

The Hybrid verifier runs 20 relational queries.

It checks:

- whether Hybrid finds the fused gold evidence in top-k
- whether Hybrid top-1 is correct
- whether Dense alone finds the complete fused evidence
- whether KG alone finds the complete fused evidence
- whether BM25 alone finds the complete fused evidence
- which backends contribute to top Hybrid results

Final result:

```text
hybrid_hit@5=20/20
hybrid_top1=17/20
dense_hit@5=0/20
kg_hit@5=0/20
bm25_hit@5=0/20
hybrid_beats_dense=20/20
hybrid_beats_kg=20/20
passed=True
```

## Concepts And Topics Used

Hybrid retrieval:

- a retrieval approach that combines multiple backends

RRF:

- rank-based fusion method that avoids comparing incompatible raw scores directly

Heterogeneous evidence:

- evidence from different representation types, such as text chunks and KG paths

Relational query:

- a query asking how entities connect or what relation bridges them

Provenance:

- metadata that tracks where each piece of fused evidence came from

Deduplication:

- grouping overlapping text evidence by parent document and KG evidence by triple or path identity

Structural mismatch:

- failure caused by using a retrieval representation that does not match the query structure

## Remaining Limitations

Hybrid is now real, but still intentionally small.

Limitations:

- no persisted Hybrid index yet
- relational bundles are rule-based
- relational snippets are curated
- Dense still uses the numpy fallback on this machine
- answer generation still echoes evidence rather than using a final local LLM

The important milestone is that PRISM now has verified behavior across all four retrieval families:

- BM25 for lexical exact-match
- Dense for semantic paraphrase
- KG for deductive structure
- Hybrid for relational fused evidence
