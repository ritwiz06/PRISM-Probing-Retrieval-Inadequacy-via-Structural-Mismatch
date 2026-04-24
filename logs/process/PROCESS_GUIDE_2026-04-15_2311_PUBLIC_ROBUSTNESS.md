# Process Guide: Public Raw Robustness

## Basic Summary

This task added a robustness layer for PRISM's public raw-document benchmark. The focus was not to rewrite the public benchmark to make scores look better. The focus was to diagnose why public raw documents caused misses, improve public-document metadata and lexical grounding, and keep every improvement transparent.

The production demo path is still unchanged. Computed RAS remains the production router. Public-aware lexical retrieval and route arbitration are analysis-only unless explicitly used by the public-corpus verifier.

## How Public Raw Failure Analysis Works

The failure-analysis module is:

- `prism/public_corpus/failure_analysis.py`

Run it with:

```bash
.venv/bin/python3 -m prism.public_corpus.failure_analysis
```

It loads or regenerates the public-corpus evaluation and compares:

- normal computed RAS,
- always BM25,
- public-aware lexical mode,
- public-aware lexical arbitration.

For each public test item, it records:

- route family,
- predicted backend,
- whether the route was correct,
- whether the answer matched,
- whether evidence hit@k succeeded,
- source style,
- source type,
- whether the query is identifier-heavy,
- whether always BM25 answered correctly when computed RAS missed,
- error buckets,
- a short remediation note.

The current bucket labels include:

- route error,
- retrieval miss,
- ranking error,
- answer synthesis miss,
- KG incompleteness,
- lexical confusion,
- semantic drift,
- hybrid fusion miss,
- public identifier arbitration candidate.

## How Public Document Enrichment Works

The enrichment module is:

- `prism/public_corpus/enrich_documents.py`

The public corpus builder now writes a companion metadata file:

- `data/processed/public_corpus_enriched_metadata.json`

The raw cached public pages are not changed.

For each public document, enrichment records:

- title,
- source type,
- route family,
- source URL,
- fetch status,
- canonical identifiers,
- aliases,
- section-heading candidates,
- lead summary,
- body character count.

This keeps the public corpus inspectable while giving lexical retrieval structured fields that are useful for messy public pages.

## How Identifier Extraction And Lexical Boosting Work

Identifier extraction handles patterns such as:

- `RFC-7231`
- `RFC 7231`
- `ICD-10 J18.9`
- `J18.9`
- `HIPAA 164.512`
- `45 CFR 164.512`
- dotted API names such as `torch.nn.CrossEntropyLoss`
- class-like API names such as `TfidfVectorizer`

The public-aware lexical retriever is:

- `prism/public_corpus/lexical_retriever.py`

It wraps BM25 for public-corpus analysis. It builds a BM25 index over enriched text fields:

- title,
- canonical identifiers,
- aliases,
- lead summary,
- cleaned body.

It then reranks results with transparent boosts for:

- identifier matches,
- alias matches,
- title matches.

Retrieved metadata exposes:

- whether public identifier matching was used,
- matched fields,
- matched identifiers,
- matched aliases,
- public lexical boost,
- whether reranking was enabled.

The normal curated/local BM25 path is not replaced.

## How Public Route Arbitration Works

Public route arbitration is intentionally narrow.

It only overrides normal computed RAS to BM25 when:

- the query is identifier-heavy, and
- the public-aware lexical retriever has high title/identifier/alias confidence.

It does not override broad semantic, KG, or Hybrid questions just because BM25 has a strong text hit.

Current public test overrides:

- `pub_bm25_11`: `Python dataclasses generated special methods`
- `pub_bm25_12`: `TfidfVectorizer raw documents matrix TF-IDF features`

The route arbitration artifacts are:

- `data/eval/public_route_arbitration.json`
- `data/eval/public_route_arbitration_summary.md`

## How Before/After Public Evaluation Works

The public verifier is still:

```bash
.venv/bin/python3 -m prism.public_corpus.verify_public_corpus
```

It now reports:

- normal computed RAS,
- fixed-backend baselines,
- computed RAS with public lexical retriever,
- computed RAS with public lexical arbitration,
- before/after comparison against the Prompt 17 public test reference.

The current public raw test results are:

- Prompt 17 reference computed RAS answer accuracy: `0.917`
- Current computed RAS answer accuracy: `1.000`
- Public-arbitrated answer accuracy: `1.000`
- Current computed RAS route accuracy: `0.917`
- Public-arbitrated route accuracy: `1.000`

The biggest actual fix was the feature-parser marker bug. Public lexical arbitration mainly improves route-label correctness for identifier-heavy public examples.

## What Artifacts Are Generated

Public enrichment:

- `data/processed/public_corpus_enriched_metadata.json`

Public failure analysis:

- `data/eval/public_failure_analysis.json`
- `data/eval/public_failure_analysis.csv`
- `data/eval/public_failure_analysis_summary.md`

Route arbitration:

- `data/eval/public_route_arbitration.json`
- `data/eval/public_route_arbitration_summary.md`

Robustness summary and plots:

- `data/eval/public_robustness_summary.md`
- `data/eval/public_robustness_before_after.png`
- `data/eval/public_identifier_subgroup.png`

Updated public evaluation:

- `data/eval/public_corpus_eval.json`
- `data/eval/public_corpus_eval.csv`
- `data/eval/public_corpus_eval_summary.md`

Updated local-vs-public comparison:

- `data/eval/public_vs_local_grounding.json`
- `data/eval/public_vs_local_grounding_summary.md`

## Concepts And Topics Used

- Public raw-document robustness: making retrieval and routing less brittle when source pages contain boilerplate, formatting noise, and long text.
- Field-aware lexical retrieval: treating title, identifiers, aliases, lead summary, and body as useful fields instead of one undifferentiated blob.
- Identifier extraction: recognizing formal strings that should strongly anchor lexical retrieval.
- Lexical boost: increasing the score of documents whose identifiers, aliases, or titles match the query.
- Route arbitration: an optional analysis-time override when a specialized signal is much more reliable than the default route.
- Error buckets: structured labels explaining whether a miss came from routing, retrieval, ranking, answer synthesis, or representation mismatch.
- Before/after comparison: comparing current metrics against a stored reference from the previous prompt.

## What Remains Unresolved

- The public benchmark is still small and source-selected.
- Public-aware arbitration is not enabled in the production demo path.
- The public-aware lexical retriever is designed for this public corpus, not yet a general web retriever.
- Deductive and relational public cases still use the compact demo KG.
- One public document still uses a fallback snapshot.
- Evaluation still uses normalized exact/string matching rather than human grading.
