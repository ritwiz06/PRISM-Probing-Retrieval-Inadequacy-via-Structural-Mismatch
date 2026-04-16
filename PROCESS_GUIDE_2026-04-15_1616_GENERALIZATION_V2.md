# Process Guide: Generalization V2 And Noisy Corpus

## Basic Summary

This task added a broader held-out evaluation layer for PRISM. It does not change the demo, production router, curated benchmark, external mini-benchmark, or any retrieval backend. The new layer asks a harder question:

Can PRISM still work when evaluated on a larger held-out suite and when the text corpus contains realistic distractors?

The answer from this local run is: mostly yes, with honest degradation under noise. Clean held-out answers were `40/40` on test. Noisy held-out answers were `39/40` on test. The main weakness under noise was lexical retrieval, because near-match identifier distractors can confuse exact-code lookup.

## How The Held-Out Benchmark Is Built

The held-out benchmark builder lives in:

- `prism/generalization/benchmark_builder.py`

It writes:

- `data/processed/generalization_v2_benchmark.jsonl`

The benchmark has `80` examples:

- `20` BM25 / lexical examples,
- `20` Dense / semantic examples,
- `20` KG / deductive examples,
- `20` Hybrid / relational examples.

The examples are public-source-style rather than full public dataset downloads. This means they imitate common benchmark formats while staying small, local, and reproducible:

- BEIR-style exact identifier and lexical retrieval examples,
- Natural Questions / TriviaQA / MS MARCO-style semantic QA examples,
- WebQSP / CWQ / GrailQA-style structured QA examples,
- HotpotQA / 2WikiMultihopQA-style bridge and relational examples.

Each item uses a normalized schema with:

- `id`
- `query`
- `source_dataset`
- `split`
- `route_family`
- `gold_answer`
- `gold_evidence_text`
- `difficulty`
- `tag`
- `notes`

## How The Splits Are Defined

The benchmark has two splits:

- `dev`: `40` examples
- `test`: `40` examples

Each split has `10` examples per route family. The intended use is:

- use `dev` for diagnosis and future improvements,
- use `test` for report-facing held-out results.

The task intentionally does not tune the benchmark after seeing test failures. If future changes are needed, they should be justified using dev cases first and documented clearly.

## How The Noisy Corpus Is Built

The noisy corpus builder lives in:

- `prism/generalization/noisy_corpus.py`

It reads the clean corpus:

- `data/processed/corpus.jsonl`

and writes a separate artifact:

- `data/processed/corpus_noisy.jsonl`

The clean corpus remains unchanged. The noisy corpus contains the clean documents plus `60` extra distractors, for `208` total documents in this run.

The added distractors include:

- lexical near matches such as nearby RFCs, HIPAA sections, ICD codes, and API names,
- semantic distractors such as concepts related to but not identical to the gold concept,
- relational clutter around KG entities and predicates,
- mixed-quality background snippets that add retrieval noise.

This helps test whether retrieval still works when the corpus contains plausible non-gold evidence.

## How Clean Vs Noisy Evaluation Works

The verifier lives in:

- `prism/generalization/verify_generalization_v2.py`

Run it with:

```bash
.venv/bin/python3 -m prism.generalization.verify_generalization_v2
```

It evaluates:

- clean corpus / dev split,
- clean corpus / test split,
- noisy corpus / dev split,
- noisy corpus / test split.

For each condition it compares:

- computed RAS,
- always BM25,
- always Dense,
- always KG,
- always Hybrid,
- fixed-seed random router.

Metrics include:

- route accuracy,
- answer accuracy,
- per-family answer accuracy,
- predicted backend distribution,
- strongest fixed-backend baseline,
- clean-vs-noisy delta.

The verifier builds retrievers from the requested corpus path, but it does not change the production app path. Computed RAS remains the production router.

## What Artifacts Are Generated

The verifier writes:

- `data/eval/generalization_v2.json`
- `data/eval/generalization_v2.csv`
- `data/eval/generalization_v2_summary.md`
- `data/eval/generalization_v2_clean_vs_noisy.png`
- `data/eval/generalization_v2_baseline_comparison.png`

The Markdown summary is designed for reports and slides. It includes:

- benchmark size,
- counts by split and route family,
- clean corpus performance,
- noisy corpus performance,
- strongest fixed-backend baselines,
- noisy-corpus degradation,
- threats to validity.

## What The Results Mean

On the held-out v2 benchmark:

- Clean dev answer accuracy: `1.000`
- Clean test answer accuracy: `1.000`
- Noisy dev answer accuracy: `0.975`
- Noisy test answer accuracy: `0.975`

PRISM still beats the strongest fixed-backend baseline in all four clean/noisy and dev/test conditions.

The main degradation is lexical. Under noise, BM25-style exact identifier examples dropped from `1.000` to `0.900` answer accuracy on both dev and test. This is plausible because near-match identifiers are exactly the kind of distractor that can hurt lexical retrieval.

## Concepts And Topics Used

- Held-out benchmark: examples kept separate from the main curated benchmark to test generalization.
- Dev split: examples used for diagnosis and possible improvement.
- Test split: examples reserved for report-facing evaluation.
- Public-source-style benchmark: small local examples modeled after public QA/retrieval datasets without downloading full datasets.
- Noisy corpus: a retrieval corpus with distractor documents added to make retrieval harder.
- Distractor: a non-gold document that looks relevant enough to confuse a retriever.
- Clean-vs-noisy delta: the performance change when moving from the clean corpus to the noisy corpus.
- Fixed-backend baseline: a system that always uses one backend, such as always BM25 or always Dense.
- Route accuracy: whether the router selected the expected backend family.
- Answer accuracy: whether the generated local deterministic answer matches the normalized gold answer.

## What Remains Unresolved

- The benchmark is still local and normalized; it is not a full official public benchmark run.
- The noisy corpus is synthetic and controlled, not a real web-scale index.
- Answer accuracy is based on string normalization, not human grading.
- KG and Hybrid remain robust in this suite partly because their supporting KG is compact and curated.
- Future work should add more genuinely ambiguous held-out queries and human-labeled answer/trace judgments.
