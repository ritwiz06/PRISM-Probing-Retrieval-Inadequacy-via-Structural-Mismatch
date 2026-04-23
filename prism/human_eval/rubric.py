from __future__ import annotations

import csv
from pathlib import Path

from prism.utils import read_json

HUMAN_EVAL_DIR = Path("data/human_eval")
RUBRIC_PATH = HUMAN_EVAL_DIR / "rubric.md"
ANNOTATION_TEMPLATE_PATH = HUMAN_EVAL_DIR / "annotation_template.csv"
COMPARATIVE_RUBRIC_PATH = HUMAN_EVAL_DIR / "comparative_rubric.md"
COMPARATIVE_ANNOTATION_TEMPLATE_PATH = HUMAN_EVAL_DIR / "comparative_annotation_template.csv"

RUBRIC_FIELDS = (
    "route_appropriateness",
    "evidence_sufficiency",
    "answer_faithfulness",
    "trace_faithfulness",
    "trace_clarity",
    "overall_usefulness",
)

MAJOR_ERROR_TYPES = (
    "none",
    "wrong_route",
    "insufficient_evidence",
    "unsupported_answer",
    "unfaithful_trace",
    "unclear_trace",
    "missing_counterexample",
    "wrong_bridge",
    "other",
)

COMPARATIVE_FIELDS = (
    "better_supported_answer",
    "more_faithful_trace",
    "clearer_trace",
    "more_appropriate_route",
    "overall_preference",
)

COMPARATIVE_DIFFERENCE_TYPES = (
    "none",
    "route_choice",
    "evidence_support",
    "answer_faithfulness",
    "trace_faithfulness",
    "trace_clarity",
    "retrieval_quality",
    "other",
)


def export_rubric_and_template(packet_path: str | Path = HUMAN_EVAL_DIR / "eval_packet.json") -> dict[str, object]:
    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    RUBRIC_PATH.write_text(rubric_markdown(), encoding="utf-8")
    packet = read_json(packet_path) if Path(packet_path).exists() else {"items": []}
    with ANNOTATION_TEMPLATE_PATH.open("w", newline="", encoding="utf-8") as file:
        fieldnames = ["evaluator_id", "item_id", *RUBRIC_FIELDS, "major_error_type", "is_usable", "notes"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in packet.get("items", []):
            writer.writerow(
                {
                    "evaluator_id": "",
                    "item_id": item["item_id"],
                    **{field: "" for field in RUBRIC_FIELDS},
                    "major_error_type": "",
                    "is_usable": "",
                    "notes": "",
                }
            )
    return {
        "rubric_path": str(RUBRIC_PATH),
        "annotation_template_path": str(ANNOTATION_TEMPLATE_PATH),
        "fields": list(RUBRIC_FIELDS),
        "major_error_types": list(MAJOR_ERROR_TYPES),
        "template_rows": len(packet.get("items", [])),
    }


def rubric_markdown() -> str:
    return """# PRISM Human Evaluation Rubric

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
"""


def export_comparative_rubric_and_template(
    packet_path: str | Path = HUMAN_EVAL_DIR / "comparative_packet.json",
) -> dict[str, object]:
    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    COMPARATIVE_RUBRIC_PATH.write_text(comparative_rubric_markdown(), encoding="utf-8")
    packet = read_json(packet_path) if Path(packet_path).exists() else {"items": []}
    with COMPARATIVE_ANNOTATION_TEMPLATE_PATH.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "evaluator_id",
            "comparative_item_id",
            *COMPARATIVE_FIELDS,
            "judgment_confidence",
            "major_difference_type",
            "needs_adjudication",
            "notes",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in packet.get("items", []):
            writer.writerow(
                {
                    "evaluator_id": "",
                    "comparative_item_id": item["comparative_item_id"],
                    **{field: "" for field in COMPARATIVE_FIELDS},
                    "judgment_confidence": "",
                    "major_difference_type": "",
                    "needs_adjudication": "",
                    "notes": "",
                }
            )
    return {
        "comparative_rubric_path": str(COMPARATIVE_RUBRIC_PATH),
        "comparative_annotation_template_path": str(COMPARATIVE_ANNOTATION_TEMPLATE_PATH),
        "fields": list(COMPARATIVE_FIELDS),
        "major_difference_types": list(COMPARATIVE_DIFFERENCE_TYPES),
        "template_rows": len(packet.get("items", [])),
    }


def comparative_rubric_markdown() -> str:
    return """# PRISM Comparative Human Evaluation Rubric

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
"""
