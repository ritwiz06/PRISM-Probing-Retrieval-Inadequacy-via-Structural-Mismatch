# Process Guide: Comparative Human Evaluation and Adjudication

## Basic Summary

This update adds side-by-side human evaluation for PRISM. The earlier human-eval layer asks evaluators to score one PRISM output at a time. The comparative layer asks a more targeted question: when two system variants answer the same query, which one is better supported, clearer, and more faithful?

The production PRISM path is unchanged. Computed RAS remains the default router. Calibrated rescue, classifier routing, and fixed-backend outputs are used only as analysis variants inside the comparative packet.

## How Comparative Sampling Works

The comparative packet samples from four benchmark sources:

- adversarial hard-case benchmark
- public raw-document benchmark
- generalization_v2 benchmark
- curated benchmark

The current packet has `28` side-by-side items. It is balanced across route families:

- `bm25`: 7 examples
- `dense`: 7 examples
- `kg`: 7 examples
- `hybrid`: 7 examples

Each item compares:

- System A: normal `computed_ras`
- System B: one of `calibrated_rescue`, `classifier_router`, `always_dense`, or `always_bm25`

The packet prioritizes cases that are useful for human comparison:

- route disagreements
- hard adversarial cases
- public raw-document cases
- computed RAS vs calibrated rescue
- computed RAS vs classifier router
- computed RAS vs strongest fixed-backend baselines
- trace/evidence audit cases even when automatic correctness is the same

Each comparative item contains:

- stable comparative item id
- source benchmark
- query
- route family and difficulty
- ambiguity tags
- System A label, route, answer, evidence, trace, and automatic correctness
- System B label, route, answer, evidence, trace, and automatic correctness
- gold answer and gold route for context
- comparison tag
- selection reason

## How Pairwise Rubrics Are Defined

The comparative rubric uses forced-choice judgments. For each field, evaluators choose:

- `A`
- `B`
- `Tie`

Fields:

- `better_supported_answer`: which answer is better supported by evidence.
- `more_faithful_trace`: which reasoning trace better matches the shown route and evidence.
- `clearer_trace`: which trace is easier to understand.
- `more_appropriate_route`: which selected route/backend better fits the query.
- `overall_preference`: which output is better overall.

Additional fields:

- `judgment_confidence`: 1 to 3.
- `major_difference_type`: route choice, evidence support, answer faithfulness, trace faithfulness, trace clarity, retrieval quality, or other.
- `needs_adjudication`: yes/no.
- `notes`: free text.

This format keeps annotation lightweight while still capturing why one system is preferred.

## How Adjudication Support Works

The adjudication layer reads comparative annotation CSV files from:

- `data/human_eval/comparative_annotations/`

It groups annotations by comparative item id. Once annotations exist, it identifies:

- unanimous preferences
- split decisions
- ties
- low-confidence judgments
- explicit adjudication requests

Items needing review are written to:

- `data/human_eval/adjudication_queue.json`

The queue includes the item id, query, compared systems, vote pattern, evaluator notes, and suggested reason for adjudication.

If no annotations exist yet, the queue is empty and the summary clearly says judgments are pending.

## How Comparative Analysis Works

The analyzer produces win/loss/tie summaries once annotation CSVs are present.

It reports:

- preference counts by system pair
- win rates by benchmark source
- win rates by route family
- win rates by comparison tag
- trace-faithfulness preference rates
- evidence-support preference rates
- adjudication-needed cases

For example, it can answer:

- Do evaluators prefer calibrated rescue over computed RAS on adversarial cases?
- Does classifier routing produce clearer traces or just different routes?
- Does a fixed backend win on public raw lexical cases?
- Are disagreements concentrated in one route family?

No human preferences are fabricated. Until annotations are added, generated summaries are placeholders.

## Artifacts Generated

Comparative packet:

- `data/human_eval/comparative_packet.json`
- `data/human_eval/comparative_packet.csv`
- `data/human_eval/comparative_packet.md`

Comparative rubric and template:

- `data/human_eval/comparative_rubric.md`
- `data/human_eval/comparative_annotation_template.csv`

Comparative summaries:

- `data/human_eval/comparative_summary.json`
- `data/human_eval/comparative_summary.csv`
- `data/human_eval/comparative_summary.md`
- `data/human_eval/comparative_results_for_report.md`
- `data/human_eval/human_eval_workflow.md`

Adjudication:

- `data/human_eval/adjudication_queue.json`

## Workflow For Teammates

1. Run `.venv/bin/python3 -m prism.human_eval.export_comparative_packets`.
2. Open `data/human_eval/comparative_packet.md`.
3. Open `data/human_eval/comparative_rubric.md`.
4. Copy `data/human_eval/comparative_annotation_template.csv` to `data/human_eval/comparative_annotations/<your_name>.csv`.
5. Fill A/B/Tie choices, confidence, major difference type, adjudication flag, and notes.
6. Rerun `.venv/bin/python3 -m prism.human_eval.compare_annotations`.
7. Review `data/human_eval/comparative_summary.md` and `data/human_eval/adjudication_queue.json`.

Do not edit benchmark gold labels or production routing as part of annotation.

## Concepts And Terms Used

- Pairwise evaluation: comparing two outputs for the same query.
- System variant: a non-production alternative such as calibrated rescue or classifier routing.
- Forced choice: asking evaluators to choose A, B, or Tie.
- Adjudication: a review step for cases where evaluators disagree or mark uncertainty.
- Win rate: the fraction of judgments preferring one system.
- Trace faithfulness: whether reasoning trace statements accurately reflect retrieved evidence and route behavior.
- Evidence support: whether answer claims are justified by the shown snippets or triples.
- Route appropriateness: whether the selected backend fits the structure of the query.
- Disagreement type: why the item was selected, such as route disagreement or trace/evidence audit.

## What Remains Unresolved

- Human comparative annotations have not been collected yet.
- The current packet is targeted and balanced, not statistically large.
- A/B/Tie labels simplify nuanced preferences.
- Human evaluator familiarity with PRISM could bias judgments.
- If future annotations prefer a non-production variant for some subset, that should be reported honestly before changing production behavior.
