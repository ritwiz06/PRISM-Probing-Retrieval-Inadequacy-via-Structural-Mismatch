# Process Guide: Prompt 12 Dense Backend Upgrade

## Basic Summary

This step upgraded Dense retrieval from a deterministic hash-based fallback to a real local embedding backend. PRISM now prefers `sentence-transformers/all-MiniLM-L6-v2` and uses FAISS when available. If either the model or FAISS is unavailable, the system still falls back cleanly.

## How Dense Backend Selection Now Works

The Dense retriever reads `dense_backend` from config.

The default config now uses:

```yaml
dense_backend: sentence-transformers
dense_model_name: sentence-transformers/all-MiniLM-L6-v2
```

When Dense starts, it tries to load the sentence-transformers model. The loader first attempts local cached loading. If the model is not cached, it can download the model once if network access is available. If loading fails, the retriever falls back to the existing numpy/hash embedding model.

The active backend is reported as one of:

- `sentence_transformers+faiss`
- `sentence_transformers+numpy`
- `numpy_fallback`

## Whether Sentence-Transformers And FAISS Are Active

On this machine after the upgrade:

- sentence-transformers is active.
- Model: `sentence-transformers/all-MiniLM-L6-v2`.
- FAISS is active.
- Active Dense backend: `sentence_transformers+faiss`.
- Fallback reason: none.

`faiss-cpu` installed successfully in the project venv, so Dense now uses FAISS for vector search.

## How Fallback Behavior Is Handled

Fallback behavior is still explicit and deterministic.

If sentence-transformers cannot load, PRISM uses `HashingEmbeddingModel` and reports:

```text
active_backend = numpy_fallback
```

If sentence-transformers loads but FAISS cannot import, PRISM keeps the real embeddings and uses numpy similarity search:

```text
active_backend = sentence_transformers+numpy
```

This separation matters. A FAISS failure does not mean the model failed; it only means vector search uses numpy.

## FAISS Bug Fix

The previous FAISS path had a score/index mapping issue. FAISS returns scores and original vector indices, but the retriever was treating returned score order as if it were the original chunk order. That caused wrong chunks to be selected.

The fix maps FAISS search results back into a full score array indexed by original chunk id before sorting. After this fix, the photosynthesis paraphrase retrieves the photosynthesis chunk instead of an unrelated JSONB chunk.

## How Diagnostics Work

The diagnostics command is:

```bash
.venv/bin/python3 -m prism.analysis.dense_diagnostics
```

It reports:

- Active Dense backend.
- Model name.
- Whether FAISS is active.
- Corpus chunk count.
- Fallback reason.
- Sample semantic queries and top hits.
- External semantic result if the external generalization artifact exists.

It writes:

```text
data/eval/dense_diagnostics.json
data/eval/dense_upgrade_summary.md
```

## What Changed In Semantic And Generalization Results

Curated semantic slice:

- Old fallback result: 20/20 Dense hit@3.
- New sentence-transformers+FAISS result: 19/20 Dense hit@3.
- The curated semantic verifier still passes.

External mini-benchmark:

- Old fallback result: 31/32 overall and 7/8 Dense-family answers.
- New sentence-transformers+FAISS result: 32/32 overall and 8/8 Dense-family answers.
- The previous photosynthesis miss is fixed.

Claim validation changed honestly:

- The old lexical claim that BM25 beats Dense is no longer supported under the strict check because Dense ties BM25 on lexical evidence hit@k.
- Semantic, deductive, relational, and computed-RAS-over-fixed-backend claims remain supported.

## Concepts And Topics Used

Dense retrieval means retrieving text by embedding query and document chunks into a vector space.

Embedding model means a model that converts text into numeric vectors.

Sentence-transformers is a local embedding library for producing semantic sentence/document vectors.

FAISS is a vector index used for fast similarity search.

Numpy fallback means PRISM computes deterministic hash embeddings and similarity locally without a neural model.

Local cache means the MiniLM model is stored on disk after download and can be reused without internet access.

Top-k retrieval means returning the highest-scoring k evidence chunks.

Backend status means a structured report of which Dense path is active and why.
