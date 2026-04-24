# Process Guide: Public Raw-Document Corpus Evaluation

## Basic Summary

This task added a more realistic public-document evaluation layer for PRISM. Earlier benchmarks were local, normalized, and curated. The new layer builds a small cached corpus from real public URLs, grounds a separate benchmark in those documents, evaluates PRISM on that benchmark, and compares public-raw results against the existing local-normalized generalization_v2 results.

The production demo path is unchanged. Computed RAS remains the production router. The public-corpus layer is additive and analysis-only.

## How The Public Corpus Is Built And Cached

The public corpus code lives in:

- `prism/public_corpus/source_registry.py`
- `prism/public_corpus/fetch_documents.py`
- `prism/public_corpus/clean_and_chunk.py`
- `prism/public_corpus/build_public_corpus.py`

The build command is:

```bash
.venv/bin/python3 -m prism.public_corpus.build_public_corpus
```

The registry contains explicit public URLs and metadata for `48` source documents. The sources are balanced across the four PRISM route families:

- BM25: RFCs, official docs, regulations, and identifier-heavy references.
- Dense: Wikipedia-style general knowledge pages.
- KG: public pages containing structured animal/class/property facts.
- Hybrid: public pages useful for bridge or connector questions.

Raw documents are cached under:

- `data/raw/public_corpus/`

The processed public corpus is written to:

- `data/processed/public_corpus.jsonl`

The current cached content contains:

- `47` fetched public pages,
- `1` fallback snapshot for a page that could not be fetched cleanly.

Fallback snapshots are explicit source excerpts stored in the registry. They are used only so the benchmark remains reproducible offline or under network failures. The artifact records whether each document came from a fetched page or fallback snapshot.

## How The Benchmark Is Grounded In Fetched Documents

The public benchmark code lives in:

- `prism/public_corpus/benchmark_builder.py`
- `prism/public_corpus/loaders.py`

The build command is:

```bash
.venv/bin/python3 -m prism.public_corpus.benchmark_builder
```

The benchmark is written to:

- `data/processed/public_corpus_benchmark.jsonl`

Each item includes:

- id,
- query,
- split,
- route family,
- public-source style,
- gold answer,
- gold source document ids,
- gold evidence text,
- notes/difficulty.

The benchmark contains `48` examples:

- `24` dev examples,
- `24` test examples,
- `12` lexical/BM25 examples,
- `12` semantic/Dense examples,
- `12` deductive/KG examples,
- `12` relational/Hybrid examples.

The public benchmark is intentionally separate from:

- curated 80-query benchmark,
- external 32-example mini-benchmark,
- generalization_v2 benchmark.

## How Public-Corpus Evaluation Works

The verifier lives in:

- `prism/public_corpus/verify_public_corpus.py`

Run it with:

```bash
.venv/bin/python3 -m prism.public_corpus.verify_public_corpus
```

It builds retrievers from the public raw-document corpus:

- BM25 over public documents,
- Dense over public documents,
- KG over the existing curated demo KG,
- Hybrid over BM25 + Dense + KG.

It evaluates:

- computed RAS,
- always BM25,
- always Dense,
- always KG,
- always Hybrid,
- random router with fixed seed.

Metrics include:

- route accuracy,
- answer accuracy,
- evidence hit@k,
- per-family answer accuracy,
- predicted backend distribution,
- strongest fixed-backend baseline,
- public-document grounding coverage.

Current public raw-document results:

- Dev computed RAS answer accuracy: `0.958` (`23/24`)
- Test computed RAS answer accuracy: `0.917` (`22/24`)
- Test computed RAS route accuracy: `0.875`
- Test computed RAS evidence hit@k: `0.917`
- Strongest fixed-backend baseline on public test: `always_bm25` at `0.958`

This is a useful result because it shows public raw text is harder than local-normalized benchmark data.

## How Local-Vs-Public Comparison Works

The comparison code lives in:

- `prism/public_corpus/compare_grounding.py`

Run it with:

```bash
.venv/bin/python3 -m prism.public_corpus.compare_grounding
```

It compares:

- local-normalized generalization_v2 test results,
- public raw-document test results.

The current comparison reports:

- Local normalized test answer accuracy: `1.000`
- Public raw test answer accuracy: `0.917`
- Public-minus-local answer delta: `-0.083`
- Local normalized test route accuracy: `0.950`
- Public raw test route accuracy: `0.875`
- Public-minus-local route delta: `-0.075`
- Most degraded family: `bm25`

The comparison is directional, not paired-example causal analysis, because the public raw benchmark and generalization_v2 contain different examples.

## What Artifacts Are Generated

Public corpus artifacts:

- `data/raw/public_corpus/`
- `data/processed/public_corpus.jsonl`
- `data/processed/public_corpus_summary.json`
- `data/processed/public_corpus_benchmark.jsonl`

Public evaluation artifacts:

- `data/eval/public_corpus_eval.json`
- `data/eval/public_corpus_eval.csv`
- `data/eval/public_corpus_eval_summary.md`
- `data/eval/public_corpus_baselines.png`
- `data/eval/public_corpus_family_accuracy.png`

Local-vs-public artifacts:

- `data/eval/public_vs_local_grounding.json`
- `data/eval/public_vs_local_grounding_summary.md`
- `data/eval/public_vs_local_grounding_family_delta.png`

## Concepts And Topics Used

- Public raw-document corpus: a small corpus built from real public pages rather than hand-normalized local snippets.
- Caching: saving fetched raw pages locally so future runs do not require internet.
- Fallback snapshot: a small explicit source excerpt used only when a live public source cannot be fetched.
- Grounding: linking a benchmark query to the specific source document that supports the answer.
- Evidence hit@k: whether retrieved evidence includes the gold source document or enough matching evidence text.
- Route family: the intended representation family for a query: BM25, Dense, KG, or Hybrid.
- Fixed-backend baseline: a system that always uses the same retriever regardless of query.
- Local-normalized vs public-raw comparison: a contrast between clean curated data and noisier real-page text.
- Threats to validity: reasons the evaluation may not fully support broad real-world claims.

## What Remains Unresolved

- The public corpus is still small and source-selected.
- The benchmark is public-grounded but not an official full dataset download.
- Public pages can change over time; cached copies make runs reproducible but may become stale.
- Deductive and relational evaluation still depends partly on the compact demo KG.
- HTML/page formatting noise is only lightly cleaned.
- Answer matching remains normalized string matching and should eventually be complemented by human evaluation.
