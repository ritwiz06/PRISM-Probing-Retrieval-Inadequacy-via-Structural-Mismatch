# Process Guide: Human Evaluation and Trace Validity Layer

## Basic Summary

This update adds a human-evaluation workflow to PRISM. Until now, most evaluation was automatic: route accuracy, evidence hit@k, and normalized answer matching. Those metrics are useful, but they do not fully answer whether a person would judge the answer as supported, the evidence as sufficient, or the reasoning trace as faithful. The new human-eval layer creates evaluator packets, a scoring rubric, annotation templates, and analysis summaries without changing PRISM's production behavior.

## What Was Implemented

The new package is `prism/human_eval/`.

- `sample_builder.py` builds a deterministic packet of examples from existing benchmark layers.
- `export_packets.py` is the CLI for writing JSON, CSV, Markdown packet files, rubric, and annotation template.
- `rubric.py` defines the human scoring dimensions and writes the rubric/template files.
- `load_annotations.py` loads completed evaluator CSV files.
- `analyze_annotations.py` summarizes human scores, agreement, trace validity, and disagreement cases.

The production answer path is unchanged. Computed RAS remains the default router, and calibrated routing is only included as an audit variant in a few packet items.

## How Packet Sampling Works

The packet builder samples from four benchmark layers:

- curated benchmark
- generalization_v2 benchmark
- public raw-document benchmark
- adversarial hard-case benchmark

The current packet has `36` examples. It is balanced across all four route families:

- `bm25`: lexical and exact-identifier examples
- `dense`: semantic/paraphrase examples
- `kg`: deductive/structured examples
- `hybrid`: relational/multi-evidence examples

The packet also includes easy and hard cases. Most items use normal computed RAS, while a small number use the calibrated adversarial variant so evaluators can inspect whether the rescue path improves trace and answer quality.

Each packet item contains:

- stable item id
- benchmark source
- query
- predicted route and selected backend
- gold route and gold answer
- final answer
- evidence ids and evidence snippets
- reasoning trace
- route rationale
- automatic correctness label
- system variant label

## How The Rubric Is Defined

The rubric uses a 1 to 3 scale so evaluators can score quickly and consistently.

Dimensions:

- `route_appropriateness`: whether the selected backend fits the query type.
- `evidence_sufficiency`: whether retrieved evidence is enough to answer the query.
- `answer_faithfulness`: whether the final answer is supported by evidence.
- `trace_faithfulness`: whether reasoning trace steps accurately reflect the evidence and routing.
- `trace_clarity`: whether the trace is understandable to a reader.
- `overall_usefulness`: whether the answer and trace would be useful in practice.

The template also includes:

- `major_error_type`
- `is_usable`
- `notes`

This makes the annotation useful for both quantitative summaries and qualitative failure analysis.

## How Annotation Ingestion Works

Evaluators should not edit the packet files directly. The workflow is:

1. Run `.venv/bin/python3 -m prism.human_eval.export_packets`.
2. Copy `data/human_eval/annotation_template.csv` to `data/human_eval/annotations/<evaluator_id>.csv`.
3. Fill one row per packet item.
4. Run `.venv/bin/python3 -m prism.human_eval.analyze_annotations`.

The loader reads all CSV files from `data/human_eval/annotations/`. It supports multiple annotators and keeps the source file name for traceability.

If no annotation files exist, the analyzer does not fail. It writes a placeholder summary explaining that annotation files are still needed.

## How Agreement Analysis Works

When annotations are present, the analyzer computes:

- mean score by rubric dimension
- mean score by benchmark source
- mean score by route family
- trace-faithfulness and trace-clarity summaries
- major error type counts
- disagreement cases
- percent agreement for categorical fields
- Cohen's kappa where there are two annotators with overlapping labels

Agreement metrics are intentionally lightweight. They are meant to support a small class/team evaluation, not a large-scale human-subjects study.

## Trace-Validity Analysis

Trace validity is important because PRISM's demo claim is not only "the answer is correct." The system also needs to show why a backend was selected and how evidence supports the answer.

The trace-validity summary answers questions like:

- Did the trace cite the evidence it actually used?
- Did the trace explain the selected backend?
- Did the trace avoid claiming support that was not in the evidence?
- Were traces clear enough for a non-author evaluator?

Before human annotations exist, this file is a placeholder. After annotations are collected, it becomes a report-ready trace-validity artifact.

## Artifacts Generated

Packet artifacts:

- `data/human_eval/eval_packet.json`
- `data/human_eval/eval_packet.csv`
- `data/human_eval/eval_packet.md`

Rubric/template artifacts:

- `data/human_eval/rubric.md`
- `data/human_eval/annotation_template.csv`

Analysis artifacts:

- `data/human_eval/human_eval_summary.json`
- `data/human_eval/human_eval_summary.csv`
- `data/human_eval/human_eval_summary.md`
- `data/human_eval/trace_validity_summary.md`
- `data/human_eval/disagreement_cases.json`

If annotations are later added, the analysis can also generate plots for score breakdowns.

## Concepts And Terms Used

- Human evaluation: manual scoring by people instead of only automatic metrics.
- Evaluation packet: a curated set of examples shown to annotators.
- Rubric: a written scoring guide that defines what each score means.
- Ordinal scale: a small ordered scale, here 1 to 3, where higher is better.
- Trace faithfulness: whether the reasoning trace accurately reflects evidence and system behavior.
- Evidence sufficiency: whether the retrieved snippets or triples are enough to justify the answer.
- Answer faithfulness: whether the answer stays grounded in the shown evidence.
- Inter-annotator agreement: how consistently different evaluators label the same item.
- Cohen's kappa: a simple agreement statistic that adjusts for chance agreement.
- Disagreement case: an item where annotators produce meaningfully different scores.

## What Remains Unresolved

- No real human annotations have been collected yet.
- The packet is intentionally small and practical, so it cannot support broad population-level claims.
- The scoring rubric reduces ambiguity but cannot remove all subjectivity.
- Automatic correctness can disagree with human support judgments.
- Stronger agreement analysis would require more annotators and more overlapping labels.
- The layer currently audits PRISM behavior; it does not automatically train or change the router based on human feedback.
