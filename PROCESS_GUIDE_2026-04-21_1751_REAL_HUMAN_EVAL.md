# Process Guide: Real Human-Eval Annotation Analysis

## Basic Summary

This step converted PRISM's human-evaluation layer from placeholder-ready to real-result-ready. Four evaluators had completed standard and comparative annotation files. The new code validates those files, loads all valid rows, computes human score summaries, computes agreement, analyzes pairwise system preferences, builds an adjudication queue, connects human judgments to automatic correctness, and writes report-ready artifacts.

The production PRISM path did not change. Computed RAS remains the default router, and no retrieval, answering, demo, or benchmark-gold behavior was modified.

## How Annotation Validation Works

The validation module checks the annotation files before analysis. It reads from:

- `data/human_eval/annotations/`
- `data/human_eval/comparative_annotations/`

For standard annotations, it checks that each file has columns such as evaluator id, item id, route appropriateness, evidence sufficiency, answer faithfulness, trace faithfulness, trace clarity, overall usefulness, major error type, and notes.

For comparative annotations, it checks columns such as evaluator id, comparative item id, better supported answer, more faithful trace, clearer trace, more appropriate route, overall preference, confidence, major difference type, needs adjudication, and notes.

It also verifies that:

- item ids exist in the exported packet
- evaluator ids are present or recoverable from file names
- ordinal scores are inside the expected range
- comparative choices are valid A/B/Tie-style values
- malformed rows are reported instead of silently ignored

The main validation artifact is:

- `data/human_eval/annotation_validation_summary.md`

Machine-readable versions are also written as JSON and CSV.

## How Standard Human-Eval Analysis Works

The standard analysis uses `data/human_eval/eval_packet.json` plus all valid rows from `data/human_eval/annotations/`.

It computes:

- mean and median score by rubric dimension
- score distributions
- per-benchmark-source means
- per-route-family means
- per-system-variant means when variant metadata exists
- trace-faithfulness and trace-clarity summaries
- weak trace support cases
- automatic-correct cases that humans still rated as weak
- simple agreement metrics

The main dimensions are:

- route appropriateness
- evidence sufficiency
- answer faithfulness
- trace faithfulness
- trace clarity
- overall usefulness

The main output files are:

- `data/human_eval/human_eval_summary.json`
- `data/human_eval/human_eval_summary.csv`
- `data/human_eval/human_eval_summary.md`
- `data/human_eval/trace_validity_summary.md`
- `data/human_eval/disagreement_cases.json`

## How Comparative Analysis Works

The comparative analysis uses `data/human_eval/comparative_packet.json` plus valid rows from `data/human_eval/comparative_annotations/`.

Each comparative item shows two systems side by side. System A is normal computed RAS. System B may be calibrated rescue, classifier router, always BM25, or always Dense depending on the item.

For each pair, the analysis computes:

- A win count and rate
- B win count and rate
- tie count and rate
- preference rates by benchmark source
- preference rates by route family
- preference rates by comparison tag
- evaluator confidence summaries
- major difference type counts

The key report files are:

- `data/human_eval/comparative_summary.json`
- `data/human_eval/comparative_summary.csv`
- `data/human_eval/comparative_summary.md`
- `data/human_eval/comparative_results_for_report.md`

## How Adjudication Is Generated

The adjudication queue identifies comparative items that should be reviewed by a final judge or project lead. An item is added if:

- evaluators split on the overall preference
- an evaluator explicitly marked it for adjudication
- the confidence pattern suggests uncertainty
- tied judgments need interpretation for reporting

Each adjudication record includes:

- item id
- query
- compared systems
- vote pattern
- confidence pattern
- major difference labels
- evaluator notes
- suggested adjudication reason

The queue is written to:

- `data/human_eval/adjudication_queue.json`

In the current run, 12 comparative items require adjudication.

## How Human-Vs-Automatic Comparison Works

Automatic metrics tell whether the predicted answer matches the stored gold answer after normalization. Human judgments add a different layer: whether the evidence, route, answer, and trace are actually convincing.

The analysis flags cases such as:

- automatic answer correct but human support weak
- both systems automatically correct but humans prefer one trace or evidence set
- calibrated rescue preferred by humans even when both systems are automatically correct
- classifier router preferred on adversarial items

This matters because PRISM's paper story is not just "the answer string matched." It is also about whether the selected representation, evidence, and trace are inspectable and faithful.

The main artifact is:

- `data/human_eval/human_vs_automatic_summary.md`

## Artifacts Generated

Validation:

- `data/human_eval/annotation_validation_summary.json`
- `data/human_eval/annotation_validation_summary.csv`
- `data/human_eval/annotation_validation_summary.md`

Standard human evaluation:

- `data/human_eval/human_eval_summary.json`
- `data/human_eval/human_eval_summary.csv`
- `data/human_eval/human_eval_summary.md`
- `data/human_eval/trace_validity_summary.md`
- `data/human_eval/disagreement_cases.json`

Comparative human evaluation:

- `data/human_eval/comparative_summary.json`
- `data/human_eval/comparative_summary.csv`
- `data/human_eval/comparative_summary.md`
- `data/human_eval/comparative_results_for_report.md`
- `data/human_eval/adjudication_queue.json`

Report-facing summary:

- `data/human_eval/human_eval_results_for_paper.md`
- `data/human_eval/human_vs_automatic_summary.md`

Plots:

- `data/human_eval/human_scores_by_dimension.png`
- `data/human_eval/human_scores_by_source.png`
- `data/human_eval/human_scores_by_route_family.png`
- `data/human_eval/comparative_win_rates_by_system_pair.png`
- `data/human_eval/comparative_preferences_by_route_family.png`

## What Remains Unresolved

The current human-eval study is useful, but it is still a small pilot. The main unresolved issues are:

- only four evaluators were used
- packet sizes are practical but small
- rubric scores are clustered high, so subtle differences may be hard to detect
- forced-choice comparative judgments hide nuance
- normalized automatic correctness still does not replace human grading
- adjudication has been queued but not yet resolved by a final adjudicator

## Concepts And Topics Used

Annotation validation:

This is the process of checking annotation files before analysis. It prevents missing columns, invalid ids, malformed scores, and unknown choices from quietly corrupting results.

Rubric:

A rubric is the scoring guide evaluators use. Here, the standard rubric scores route quality, evidence quality, answer support, trace quality, and usefulness.

Ordinal score:

An ordinal score is a ranked score such as 1, 2, or 3. The values have order, but the exact distance between values is approximate.

Inter-annotator agreement:

This measures how consistently different evaluators label the same item. Percent agreement is simple overlap. Cohen kappa adjusts for agreement expected by chance.

Trace faithfulness:

A reasoning trace is faithful when it only claims what the retrieved evidence supports. A trace can be clear but unfaithful if it sounds good while relying on unsupported steps.

Comparative evaluation:

Instead of scoring one system output alone, evaluators compare two outputs side by side and choose A, B, or Tie.

Adjudication:

Adjudication is the final review step for cases where annotators disagree, tie, or mark uncertainty. It creates a clean list of examples needing human resolution.

Human-vs-automatic mismatch:

This happens when automatic string matching says an answer is correct, but human evaluators judge the support, evidence, or trace as weak.
