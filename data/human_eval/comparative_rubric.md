# PRISM Comparative Human Evaluation Rubric

Use this rubric for side-by-side judgments. Each row compares System A and System B on the same query. Judge only what is shown in the packet: route, answer, evidence, and reasoning trace.

## Forced-Choice Fields

For each field, enter exactly one of: `A`, `B`, or `Tie`.

- `better_supported_answer`: Which answer is better supported by the shown evidence?
- `more_faithful_trace`: Which reasoning trace more accurately reflects the evidence and route behavior?
- `clearer_trace`: Which trace is easier to understand?
- `more_appropriate_route`: Which selected route/backend better fits the query?
- `overall_preference`: Which system output is better overall for report/demo use?

## Confidence

Use `judgment_confidence` from 1 to 3:

- 1 = weak preference or high ambiguity.
- 2 = moderate confidence.
- 3 = strong confidence.

## Major Difference Type

Use one label: `none`, `route_choice`, `evidence_support`, `answer_faithfulness`, `trace_faithfulness`, `trace_clarity`, `retrieval_quality`, or `other`.

## Adjudication Flag

Use `needs_adjudication=yes` if the item is hard, ambiguous, or if neither output is clearly acceptable. Use `no` otherwise.

## Guidance

Prefer the answer that is faithful to evidence over the answer that merely sounds fluent. A system can have the right final answer but a weaker trace. A system can also choose a less ideal route but still retrieve enough evidence. Use `Tie` when the visible outputs are materially equivalent.
