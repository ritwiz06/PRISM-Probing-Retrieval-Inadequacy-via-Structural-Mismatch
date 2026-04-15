# Process Guide: Prompt 11 External Mini-Benchmark and Generalization Evaluation

## Basic Summary

This step added a small external mini-benchmark layer. It is separate from the curated 80-query PRISM benchmark and is meant to test whether PRISM’s routing idea still works on examples shaped like public benchmark tasks.

## How The External Mini-Benchmark Is Built

The builder is:

```bash
.venv/bin/python3 -m prism.external_benchmarks.mini_benchmark
```

It writes:

```text
data/processed/external_mini_benchmark.jsonl
```

Each row uses the normalized `ExternalBenchmarkItem` schema:

- `id`
- `query`
- `source_dataset`
- `route_family`
- `gold_answer`
- `gold_evidence_text`
- `difficulty`
- `tag`
- `notes`

The file is small and cached locally, so the verifier does not need internet access after the normalized subset exists.

## Which Source Datasets Were Used

The external mini-benchmark uses public benchmark provenance labels and task styles from:

- BEIR for lexical/exact-match retrieval examples.
- Natural Questions for semantic question answering examples.
- WebQSP for structured/deductive question examples.
- HotpotQA for relational and bridge-style question examples.

This is not a full dataset download. It is a small normalized subset designed to be practical for this repo and laptop execution.

## How Examples Were Mapped To PRISM Route Families

Examples were included only when they mapped cleanly to one PRISM route family.

BM25 examples are exact identifier or formal lookup questions, such as `RFC-7231`, `ICD-10 J18.9`, and API identifiers.

Dense examples are semantic paraphrase questions where the wording is conceptual rather than exact-match, such as climate anxiety or reinforcement learning.

KG examples are deductive or structured questions involving membership, properties, universal counterexamples, and simple two-hop facts.

Hybrid examples are relational or bridge questions, such as asking what connects one entity to another.

Ambiguous examples were not added. The goal is a clean mini-benchmark, not a large noisy benchmark.

## How Generalization Evaluation Works

The verifier is:

```bash
.venv/bin/python3 -m prism.external_benchmarks.verify_generalization
```

It evaluates:

- Computed RAS.
- Always BM25.
- Always Dense.
- Always KG.
- Always Hybrid.
- Random router with a fixed seed.

The verifier reuses the normal PRISM path:

- Feature parsing.
- RAS routing.
- Retrieval.
- Answer synthesis.
- Reasoning trace generation.

For fixed-backend baselines, the verifier uses the same `answer_query()` pipeline with a backend override. That keeps the code path consistent while allowing baseline comparison.

## Generated Artifacts

The verifier writes:

```text
data/eval/external_generalization.json
data/eval/external_generalization.csv
data/eval/external_generalization_summary.md
```

The JSON file contains detailed per-system and per-example results.

The CSV file contains compact system-level metrics.

The Markdown summary is report-friendly and includes benchmark size, source datasets, route-family counts, PRISM performance, fixed-backend comparison, per-family results, takeaways, and caveats.

## Current Results

The external mini-benchmark has 32 examples:

- 8 BM25.
- 8 Dense.
- 8 KG.
- 8 Hybrid.

Computed RAS achieved route accuracy 1.000 and answer accuracy 0.969.

The strongest fixed-backend baselines were always BM25 and always Hybrid at answer accuracy 0.5625.

The one computed RAS miss was in the Dense family: a photosynthesis-style semantic paraphrase retrieved a PostgreSQL JSONB chunk under the local Dense fallback.

## What Remains Limited About This External Benchmark Layer

The benchmark is intentionally small. It is a generalization smoke test, not a substitute for running a full public benchmark suite.

The examples are normalized and cached, not downloaded dynamically from full public datasets.

The local Dense backend is still the numpy/hash fallback on this machine, so some semantic paraphrases may fail.

The answer accuracy metric is deterministic normalized matching, not human assessment.

The source dataset labels describe benchmark provenance/task style, but this layer does not claim to reproduce official BEIR, Natural Questions, WebQSP, or HotpotQA scores.

## Concepts And Topics Used

External validity means checking whether results generalize beyond the original curated benchmark.

Mini-benchmark means a small benchmark designed to run quickly and reproducibly.

Provenance means recording where the example style or source label came from.

Route family means the intended PRISM backend: BM25, Dense, KG, or Hybrid.

Fixed-backend baseline means forcing every query through one backend for comparison.

Random router means choosing a backend randomly with a fixed seed for reproducibility.

Normalized answer accuracy means comparing simplified answer text rather than exact raw strings.

Cached benchmark means the normalized benchmark is saved locally and can be reused without internet access.
