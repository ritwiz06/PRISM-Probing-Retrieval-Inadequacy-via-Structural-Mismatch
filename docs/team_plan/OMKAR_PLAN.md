# Omkar Plan: Dense, Semantic, And External Generalization Extensions

## Objective

Own optional Dense and semantic retrieval extensions. The goal is to strengthen the evidence around semantic retrieval and external generalization without risking the production demo.

## Main Areas To Work In

- `prism/retrievers/dense_retriever.py`
- `prism/external_benchmarks/*`
- `prism/analysis/dense_*`
- new files under `prism/analysis/` for Dense experiments
- semantic support data and optional benchmark files
- Dense and external benchmark tests

## Files And Modules To Avoid

Do not edit without Ritik's approval:

- `prism/app/*`
- `prism/demo/*`
- `prism/answering/*`
- `prism/ras/*`
- final benchmark gold labels
- final report narrative and presentation flow

## Deliverables

Choose one or more, ordered by priority:

1. Dense model comparison artifact comparing MiniLM against one or two other local sentence-transformer models if already cached or lightweight to install.
2. Semantic robustness report showing which semantic queries are sensitive to reranking.
3. External mini-benchmark expansion proposal with new examples kept separate from the existing 32-query benchmark.
4. Optional reranking experiment behind a config flag, not enabled by default.
5. Dense diagnostics Markdown/CSV artifact with sample query top hits and backend status.

## Starting Checklist

- Run `.venv/bin/python3 -m pip install -e .`.
- Run `.venv/bin/python3 -m prism.eval.verify_semantic`.
- Run `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`.
- Run `.venv/bin/python3 -m prism.analysis.dense_diagnostics`.
- Read:
  - `prism/retrievers/dense_retriever.py`
  - `prism/eval/semantic_slice.py`
  - `prism/external_benchmarks/mini_benchmark.py`
  - `data/eval/dense_before_after_summary.md`
  - `data/eval/robustness_summary.md`

## Step-By-Step Work Plan

1. Start with a read-only diagnostic run and record current Dense status.
2. Pick exactly one experiment to implement first.
3. Put new experiment code in a separate module or behind an explicit config flag.
4. Write outputs to a new path such as `data/eval/dense_model_comparison.*` or `data/eval/semantic_robustness.*`.
5. Do not replace the current production Dense default unless Ritik approves it.
6. Add tests for output shape or config behavior.
7. Run the relevant verifier before handing off.

## Definition Of Done

- Work is additive and optional.
- Current semantic verifier still passes.
- Current external verifier still passes or any regression is explicitly reported.
- Artifacts include model/backend status, commands run, and limitations.
- Any new benchmark examples are separate from final gold labels unless approved.

## Failure-Safe Note

If this track is unfinished, PRISM keeps the current MiniLM + FAISS + robustness rerank path. Ritik can demo without any Omkar deliverables.

## Handoff Checklist

Submit:

- Files changed.
- Commands run.
- Test results.
- Artifact paths.
- One-paragraph summary.
- Known limitations.
