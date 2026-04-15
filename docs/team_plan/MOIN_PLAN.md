# Moin Plan: Claims, Failure Analysis, And Research Evidence

## Objective

Own optional research-support artifacts: claim validation, trace-validity review, multi-seed baselines, failure-analysis expansion, limitations, and appendix material. The goal is to make the final report more credible without weakening honest claim reporting.

## Main Areas To Work In

- `prism/analysis/*`
- `data/eval/*`
- `data/submission/*`
- new Markdown, CSV, JSON, or PNG artifacts
- tests for analysis output shape

## Files And Modules To Avoid

Do not edit without Ritik's approval:

- `prism/app/*`
- `prism/demo/*`
- `prism/answering/*`
- `prism/ras/*`
- final benchmark gold labels
- production retriever defaults
- final report narrative and presentation flow

## Deliverables

Choose one or more, ordered by priority:

1. Trace-validity rubric: a small Markdown/CSV rubric for judging whether reasoning traces are faithful to retrieved evidence.
2. Multi-seed random-router baseline artifact showing variance across several fixed seeds.
3. Expanded failure-analysis appendix with representative misses, buckets, and remediation notes.
4. Threats-to-validity document for the final report.
5. Human-eval style labeling sheet for a small sample of answers/traces.

## Starting Checklist

- Run `.venv/bin/python3 -m pip install -e .`.
- Run `.venv/bin/python3 -m prism.analysis.claim_validation`.
- Run `.venv/bin/python3 -m prism.analysis.failure_analysis`.
- Run `.venv/bin/python3 -m prism.analysis.report_artifacts`.
- Read:
  - `prism/analysis/evaluation.py`
  - `prism/analysis/claim_validation.py`
  - `prism/analysis/failure_analysis.py`
  - `data/eval/claim_validation.json`
  - `data/eval/failure_analysis_summary.md`
  - `data/eval/robustness_summary.md`

## Step-By-Step Work Plan

1. Start from existing claim and failure-analysis outputs.
2. Choose one report-support artifact to add first.
3. Keep new analysis in a separate module or separate output file.
4. Do not change claim thresholds to force support.
5. If a claim is unsupported, report it clearly and explain why.
6. Add a lightweight test for artifact shape.
7. Run relevant analysis CLIs before handoff.

## Definition Of Done

- Artifacts are readable and report-ready.
- Unsupported claims remain visible.
- Random baselines use fixed seeds and are reproducible.
- Trace rubric references evidence ids and route rationale.
- New files do not alter demo behavior.

## Failure-Safe Note

If this track is unfinished, PRISM keeps the current analysis layer. Ritik can still present claim validation, report artifacts, and the Dense failure-analysis story already in the repo.

## Handoff Checklist

Submit:

- Files changed.
- Commands run.
- Test results.
- Artifact paths.
- One-paragraph summary.
- Known limitations.
