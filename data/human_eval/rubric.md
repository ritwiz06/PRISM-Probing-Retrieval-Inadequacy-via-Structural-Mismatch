# PRISM Human Evaluation Rubric

Use this rubric to judge whether PRISM's route choice, evidence, answer, and reasoning trace are useful and faithful. Score each dimension from 1 to 3.

## Score Scale

- 1 = poor or incorrect.
- 2 = partially correct, incomplete, or unclear.
- 3 = correct, sufficient, and clear.

## Dimensions

### Route Appropriateness

Score whether the selected backend fits the query.

- 1: clearly wrong representation family.
- 2: defensible but not ideal.
- 3: correct or best available route.

### Evidence Sufficiency

Score whether retrieved evidence is enough to support the answer.

- 1: missing or irrelevant evidence.
- 2: partially relevant but incomplete.
- 3: sufficient evidence is shown.

### Answer Support / Faithfulness

Score whether the final answer follows from the shown evidence.

- 1: unsupported, contradicted, or hallucinated.
- 2: mostly related but overclaims or misses nuance.
- 3: faithful to evidence.

### Reasoning Trace Faithfulness

Score whether the trace accurately describes what the system did and what evidence supports the answer.

- 1: trace claims steps or support not present in evidence.
- 2: trace is partly faithful but omits important caveats.
- 3: trace is faithful to route/evidence/answer.

### Reasoning Trace Clarity

Score whether a reader can understand the route decision and synthesis.

- 1: unclear or confusing.
- 2: understandable but too vague or verbose.
- 3: concise and inspectable.

### Overall Answer Usefulness

Score whether the system output would help a user.

- 1: not useful.
- 2: somewhat useful but needs correction.
- 3: useful as-is for a demo or report audit.

## Yes/No Field

`is_usable` should be `yes` if the item is acceptable for demo/report evidence after minor wording polish, otherwise `no`.

## Major Error Type

Use one label: `none`, `wrong_route`, `insufficient_evidence`, `unsupported_answer`, `unfaithful_trace`, `unclear_trace`, `missing_counterexample`, `wrong_bridge`, or `other`.

## Annotation Guidance

Judge only what is visible in the packet. Do not assume hidden evidence exists. If the answer is correct but the trace explains it poorly, give high answer faithfulness and lower trace clarity or faithfulness. If the route is imperfect but the answer is well supported, score route lower and answer/evidence higher. Use notes for ambiguous cases.
