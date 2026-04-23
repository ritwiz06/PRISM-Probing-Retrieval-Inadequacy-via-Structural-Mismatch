from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from prism.human_eval.comparative_sample_builder import COMPARATIVE_PACKET_JSON, build_comparative_packet
from prism.human_eval.rubric import COMPARATIVE_FIELDS, export_comparative_rubric_and_template
from prism.human_eval.validation import validate_all_annotations, discover_annotation_files
from prism.utils import read_json, write_json

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

HUMAN_EVAL_DIR = Path("data/human_eval")
COMPARATIVE_ANNOTATION_DIR = HUMAN_EVAL_DIR / "comparative_annotations"
COMPARATIVE_SUMMARY_JSON = HUMAN_EVAL_DIR / "comparative_summary.json"
COMPARATIVE_SUMMARY_CSV = HUMAN_EVAL_DIR / "comparative_summary.csv"
COMPARATIVE_SUMMARY_MD = HUMAN_EVAL_DIR / "comparative_summary.md"
ADJUDICATION_QUEUE_JSON = HUMAN_EVAL_DIR / "adjudication_queue.json"
COMPARATIVE_RESULTS_MD = HUMAN_EVAL_DIR / "comparative_results_for_report.md"
HUMAN_EVAL_WORKFLOW_MD = HUMAN_EVAL_DIR / "human_eval_workflow.md"
HUMAN_VS_AUTOMATIC_MD = HUMAN_EVAL_DIR / "human_vs_automatic_summary.md"
HUMAN_EVAL_PAPER_MD = HUMAN_EVAL_DIR / "human_eval_results_for_paper.md"
WIN_RATE_PLOT = HUMAN_EVAL_DIR / "comparative_win_rates_by_system_pair.png"
FAMILY_PLOT = HUMAN_EVAL_DIR / "comparative_preferences_by_route_family.png"


@dataclass(frozen=True, slots=True)
class ComparativeAnnotation:
    evaluator_id: str
    comparative_item_id: str
    choices: dict[str, str]
    judgment_confidence: int
    major_difference_type: str
    needs_adjudication: bool
    notes: str
    source_file: str


def load_comparative_annotations(annotation_dir: str | Path = COMPARATIVE_ANNOTATION_DIR) -> list[ComparativeAnnotation]:
    directory = Path(annotation_dir)
    directory.mkdir(parents=True, exist_ok=True)
    rows: list[ComparativeAnnotation] = []
    for path in discover_annotation_files(directory):
        with path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                item_id = (row.get("comparative_item_id") or "").strip()
                evaluator = (row.get("evaluator_id") or "").strip()
                if not item_id:
                    continue
                rows.append(
                    ComparativeAnnotation(
                        evaluator_id=evaluator or path.stem,
                        comparative_item_id=item_id,
                        choices={field: _choice(row.get(field, "")) for field in COMPARATIVE_FIELDS},
                        judgment_confidence=_confidence(row.get("judgment_confidence", "")),
                        major_difference_type=(row.get("major_difference_type") or "none").strip() or "none",
                        needs_adjudication=(row.get("needs_adjudication") or "").strip().lower() in {"yes", "true", "1"},
                        notes=(row.get("notes") or "").strip(),
                        source_file=str(path),
                    )
                )
    return rows


def analyze_comparative_annotations() -> dict[str, object]:
    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    if not COMPARATIVE_PACKET_JSON.exists():
        build_comparative_packet()
    export_comparative_rubric_and_template(COMPARATIVE_PACKET_JSON)
    validation = validate_all_annotations()
    packet = read_json(COMPARATIVE_PACKET_JSON)
    annotations = load_comparative_annotations()
    payload = _empty_payload(packet) if not annotations else _analysis_payload(packet, annotations)
    payload["validation"] = validation.get("comparative", {})
    write_json(COMPARATIVE_SUMMARY_JSON, payload)
    _write_summary_csv(COMPARATIVE_SUMMARY_CSV, payload)
    COMPARATIVE_SUMMARY_MD.write_text(_summary_markdown(payload), encoding="utf-8")
    write_json(ADJUDICATION_QUEUE_JSON, payload.get("adjudication_queue", []))
    COMPARATIVE_RESULTS_MD.write_text(_report_markdown(payload), encoding="utf-8")
    HUMAN_EVAL_WORKFLOW_MD.write_text(_workflow_markdown(), encoding="utf-8")
    HUMAN_VS_AUTOMATIC_MD.write_text(_human_vs_automatic_markdown(payload), encoding="utf-8")
    HUMAN_EVAL_PAPER_MD.write_text(_paper_markdown(payload), encoding="utf-8")
    if payload["status"] != "no_comparative_annotations":
        _plot_win_rates(payload, WIN_RATE_PLOT)
        _plot_family_preferences(payload, FAMILY_PLOT)
    return payload


def _empty_payload(packet: dict[str, object]) -> dict[str, object]:
    return {
        "status": "no_comparative_annotations",
        "message": "No comparative annotation CSV files were found under data/human_eval/comparative_annotations/.",
        "packet_size": packet.get("packet_size", 0),
        "packet_counts": packet.get("counts", {}),
        "annotation_dir": str(COMPARATIVE_ANNOTATION_DIR),
        "expected_template": "data/human_eval/comparative_annotation_template.csv",
        "rubric": "data/human_eval/comparative_rubric.md",
        "system_pair_results": {},
        "by_benchmark_source": {},
        "by_route_family": {},
        "by_comparison_tag": {},
        "adjudication_queue": [],
        "threats_to_validity": _threats(),
    }


def _analysis_payload(packet: dict[str, object], annotations: list[ComparativeAnnotation]) -> dict[str, object]:
    item_meta = {item["comparative_item_id"]: item for item in packet.get("items", [])}
    valid = [row for row in annotations if row.comparative_item_id in item_meta]
    system_pair_results = _preference_results(valid, item_meta, "system_pair")
    by_source = _preference_results(valid, item_meta, "source_benchmark")
    by_family = _preference_results(valid, item_meta, "route_family")
    by_tag = _preference_results(valid, item_meta, "comparison_tag")
    queue = _adjudication_queue(valid, item_meta)
    return {
        "status": "comparative_annotations_loaded",
        "packet_size": packet.get("packet_size", 0),
        "annotation_count": len(valid),
        "evaluator_count": len({row.evaluator_id for row in valid}),
        "packet_counts": packet.get("counts", {}),
        "system_pair_results": system_pair_results,
        "by_benchmark_source": by_source,
        "by_route_family": by_family,
        "by_comparison_tag": by_tag,
        "adjudication_queue": queue,
        "major_difference_type_counts": dict(Counter(row.major_difference_type for row in valid)),
        "confidence_summary": _confidence_summary(valid),
        "human_vs_automatic": _human_vs_automatic(valid, item_meta),
        "threats_to_validity": _threats(),
    }


def _preference_results(
    annotations: list[ComparativeAnnotation],
    item_meta: dict[str, dict[str, object]],
    group_key: str,
) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[ComparativeAnnotation]] = defaultdict(list)
    for row in annotations:
        meta = item_meta[row.comparative_item_id]
        if group_key == "system_pair":
            key = f"{meta['system_a_label']}_vs_{meta['system_b_label']}"
        else:
            key = str(meta.get(group_key, "unknown"))
        grouped[key].append(row)
    results: dict[str, dict[str, object]] = {}
    for key, rows in sorted(grouped.items()):
        counters = {field: Counter(row.choices[field] for row in rows) for field in COMPARATIVE_FIELDS}
        overall = counters["overall_preference"]
        total = sum(overall.values()) or 1
        results[key] = {
            "annotation_count": len(rows),
            "overall_preference": dict(overall),
            "a_win_rate": overall.get("A", 0) / total,
            "b_win_rate": overall.get("B", 0) / total,
            "tie_rate": overall.get("Tie", 0) / total,
            "field_preferences": {field: dict(counter) for field, counter in counters.items()},
            "mean_confidence": _mean([row.judgment_confidence for row in rows if row.judgment_confidence > 0]),
        }
    return results


def _adjudication_queue(
    annotations: list[ComparativeAnnotation],
    item_meta: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    by_item: dict[str, list[ComparativeAnnotation]] = defaultdict(list)
    for row in annotations:
        by_item[row.comparative_item_id].append(row)
    queue: list[dict[str, object]] = []
    for item_id, rows in sorted(by_item.items()):
        meta = item_meta[item_id]
        votes = Counter(row.choices["overall_preference"] for row in rows)
        confidence = Counter(str(row.judgment_confidence) for row in rows if row.judgment_confidence > 0)
        difference_types = Counter(row.major_difference_type for row in rows)
        explicit = any(row.needs_adjudication for row in rows)
        split = len([choice for choice, count in votes.items() if count > 0 and choice]) > 1
        low_confidence = any(0 < row.judgment_confidence <= 1 for row in rows)
        if explicit or split or low_confidence:
            queue.append(
                {
                    "comparative_item_id": item_id,
                    "query": meta.get("query"),
                    "compared_systems": [meta.get("system_a_label"), meta.get("system_b_label")],
                    "source_benchmark": meta.get("source_benchmark"),
                    "route_family": meta.get("route_family"),
                    "disagreement_pattern": dict(votes),
                    "confidence_pattern": dict(confidence),
                    "major_difference_types": dict(difference_types),
                    "evaluator_notes": [
                        {"evaluator_id": row.evaluator_id, "notes": row.notes}
                        for row in rows
                        if row.notes
                    ],
                    "suggested_reason": _adjudication_reason(explicit, split, low_confidence),
                }
            )
    return queue


def _write_summary_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["scope", "name", "annotation_count", "a_win_rate", "b_win_rate", "tie_rate", "mean_confidence"],
        )
        writer.writeheader()
        for scope, groups in (
            ("system_pair", payload.get("system_pair_results", {})),
            ("benchmark_source", payload.get("by_benchmark_source", {})),
            ("route_family", payload.get("by_route_family", {})),
            ("comparison_tag", payload.get("by_comparison_tag", {})),
        ):
            for name, row in groups.items():
                writer.writerow(
                    {
                        "scope": scope,
                        "name": name,
                        "annotation_count": row.get("annotation_count"),
                        "a_win_rate": row.get("a_win_rate"),
                        "b_win_rate": row.get("b_win_rate"),
                        "tie_rate": row.get("tie_rate"),
                        "mean_confidence": row.get("mean_confidence"),
                    }
                )
        if payload["status"] == "no_comparative_annotations":
            writer.writerow(
                {
                    "scope": "status",
                    "name": payload["status"],
                    "annotation_count": 0,
                    "a_win_rate": "",
                    "b_win_rate": "",
                    "tie_rate": "",
                    "mean_confidence": "",
                }
            )


def _summary_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# PRISM Comparative Human Evaluation Summary",
        "",
        f"Status: `{payload['status']}`.",
        f"Packet size: {payload.get('packet_size', 0)}.",
    ]
    if payload["status"] == "no_comparative_annotations":
        lines.extend(
            [
                "",
                payload["message"],
                "",
                "## What Is Ready",
                "",
                "- Comparative packet: `data/human_eval/comparative_packet.md`.",
                "- Comparative rubric: `data/human_eval/comparative_rubric.md`.",
                "- Annotation template: `data/human_eval/comparative_annotation_template.csv`.",
                "",
                "## Next Steps",
                "",
                "- Copy the comparative annotation template to `data/human_eval/comparative_annotations/<evaluator_id>.csv`.",
                "- Fill A/B/Tie choices and confidence scores.",
                "- Rerun `python -m prism.human_eval.compare_annotations` or `python -m prism.human_eval.export_comparative_packets`.",
            ]
        )
    else:
        lines.extend(
            [
                f"Annotation count: {payload['annotation_count']}.",
                f"Evaluator count: {payload['evaluator_count']}.",
                f"Adjudication queue size: {len(payload['adjudication_queue'])}.",
                "",
                "## System Pair Results",
                "",
            ]
        )
        for pair, row in payload["system_pair_results"].items():
            lines.append(
                f"- {pair}: A win {row['a_win_rate']:.3f}, B win {row['b_win_rate']:.3f}, Tie {row['tie_rate']:.3f}."
            )
        lines.extend(
            [
                "",
                "## Confidence",
                "",
                f"- Mean confidence: {payload.get('confidence_summary', {}).get('mean_confidence')}",
                f"- Confidence distribution: `{payload.get('confidence_summary', {}).get('distribution', {})}`",
                "",
                "## Adjudication",
                "",
                f"- Queue size: {len(payload.get('adjudication_queue', []))}",
            ]
        )
    lines.extend(["", "## Threats To Validity", "", *[f"- {item}" for item in payload["threats_to_validity"]], ""])
    return "\n".join(lines)


def _report_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Comparative Human-Eval Results For Report",
        "",
        "## What Was Compared",
        "",
        "System A is normal computed RAS. System B is one of: calibrated rescue, classifier router, or a fixed-backend baseline.",
        "",
        "## Why These Items Were Selected",
        "",
        "The packet prioritizes adversarial, public raw, held-out, and curated examples where routing, evidence, or traces are likely to differ.",
        "",
        "## What Evaluators Judge",
        "",
        "Evaluators choose A, B, or Tie for answer support, trace faithfulness, trace clarity, route appropriateness, and overall preference.",
        "",
    ]
    if payload["status"] == "no_comparative_annotations":
        lines.extend(
            [
                "## Current Status",
                "",
                "Human comparative judgments are pending. No wins/losses/ties are reported yet.",
            ]
        )
    else:
        lines.extend(["## Current Takeaways", ""])
        for pair, row in payload["system_pair_results"].items():
            lines.append(f"- {pair}: B win rate {row['b_win_rate']:.3f}; tie rate {row['tie_rate']:.3f}.")
        human_auto = payload.get("human_vs_automatic", {})
        lines.extend(
            [
                "",
                "## Human Vs Automatic",
                "",
                f"- Calibrated rescue preferred while both systems automatically correct: {human_auto.get('calibrated_preferred_when_both_auto_correct', 0)}.",
                f"- Classifier router preferred on adversarial items: {human_auto.get('classifier_preferred_on_adversarial', 0)}.",
                f"- System B preferred when System A was automatically correct: {human_auto.get('b_preferred_despite_a_auto_correct', 0)}.",
            ]
        )
    lines.extend(["", "## Threats To Validity", "", *[f"- {item}" for item in payload["threats_to_validity"]], ""])
    return "\n".join(lines)


def _workflow_markdown() -> str:
    return """# Human Evaluation Workflow

## Standard Packet

1. Run `.venv/bin/python3 -m prism.human_eval.export_packets`.
2. Give evaluators `data/human_eval/eval_packet.md` and `data/human_eval/rubric.md`.
3. Copy `data/human_eval/annotation_template.csv` to `data/human_eval/annotations/<evaluator_id>.csv`.
4. Fill scores and rerun `.venv/bin/python3 -m prism.human_eval.analyze_annotations`.

## Comparative Packet

1. Run `.venv/bin/python3 -m prism.human_eval.export_comparative_packets`.
2. Give evaluators `data/human_eval/comparative_packet.md` and `data/human_eval/comparative_rubric.md`.
3. Copy `data/human_eval/comparative_annotation_template.csv` to `data/human_eval/comparative_annotations/<evaluator_id>.csv`.
4. Fill A/B/Tie choices and confidence scores.
5. Rerun `.venv/bin/python3 -m prism.human_eval.export_comparative_packets` or `.venv/bin/python3 -m prism.human_eval.compare_annotations`.

Do not edit benchmark gold labels or production routing based on annotations without a separate reviewed change.
"""


def _confidence_summary(annotations: list[ComparativeAnnotation]) -> dict[str, object]:
    values = [row.judgment_confidence for row in annotations if row.judgment_confidence > 0]
    return {
        "mean_confidence": _mean(values),
        "distribution": dict(Counter(str(value) for value in values)),
    }


def _human_vs_automatic(
    annotations: list[ComparativeAnnotation],
    item_meta: dict[str, dict[str, object]],
) -> dict[str, object]:
    counters = Counter()
    examples: list[dict[str, object]] = []
    for row in annotations:
        if row.choices["overall_preference"] != "B":
            continue
        meta = item_meta[row.comparative_item_id]
        system_a = meta["system_a"]
        system_b = meta["system_b"]
        pair = f"{meta['system_a_label']}_vs_{meta['system_b_label']}"
        if system_a.get("automatic_correct") and system_b.get("automatic_correct"):
            counters["b_preferred_when_both_auto_correct"] += 1
            if meta["system_b_label"] == "calibrated_rescue":
                counters["calibrated_preferred_when_both_auto_correct"] += 1
        if system_a.get("automatic_correct"):
            counters["b_preferred_despite_a_auto_correct"] += 1
        if meta["source_benchmark"] == "adversarial" and meta["system_b_label"] == "classifier_router":
            counters["classifier_preferred_on_adversarial"] += 1
        examples.append(
            {
                "comparative_item_id": row.comparative_item_id,
                "pair": pair,
                "source_benchmark": meta["source_benchmark"],
                "route_family": meta["route_family"],
                "system_a_auto_correct": system_a.get("automatic_correct"),
                "system_b_auto_correct": system_b.get("automatic_correct"),
                "evaluator_id": row.evaluator_id,
                "notes": row.notes,
            }
        )
    return {**dict(counters), "b_preference_examples": examples[:25]}


def _human_vs_automatic_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Human Vs Automatic Summary",
        "",
        f"Comparative status: `{payload['status']}`.",
    ]
    if payload["status"] == "no_comparative_annotations":
        lines.append("Comparative human judgments are not available yet.")
        return "\n".join(lines) + "\n"
    human_auto = payload.get("human_vs_automatic", {})
    lines.extend(
        [
            "",
            "## Key Counts",
            "",
            f"- System B preferred when both systems were automatically correct: {human_auto.get('b_preferred_when_both_auto_correct', 0)}.",
            f"- Calibrated rescue preferred while both systems were automatically correct: {human_auto.get('calibrated_preferred_when_both_auto_correct', 0)}.",
            f"- System B preferred despite computed RAS being automatically correct: {human_auto.get('b_preferred_despite_a_auto_correct', 0)}.",
            f"- Classifier router preferred on adversarial items: {human_auto.get('classifier_preferred_on_adversarial', 0)}.",
            "",
            "## Interpretation",
            "",
            "These counts compare human preferences against automatic correctness. A human preference for System B when both outputs are automatically correct usually means trace clarity, route appropriateness, or evidence presentation mattered beyond normalized answer matching.",
        ]
    )
    return "\n".join(lines) + "\n"


def _paper_markdown(payload: dict[str, object]) -> str:
    standard = _read_optional_json(HUMAN_EVAL_DIR / "human_eval_summary.json")
    lines = [
        "# PRISM Human-Evaluation Results For Paper",
        "",
        "## Study Setup",
        "",
        f"- Standard packet size: {standard.get('packet_size', 'unknown') if standard else 'unknown'}.",
        f"- Comparative packet size: {payload.get('packet_size', 0)}.",
        f"- Standard evaluator count: {standard.get('evaluator_count', 'pending') if standard else 'pending'}.",
        f"- Comparative evaluator count: {payload.get('evaluator_count', 'pending')}.",
        "",
        "## Standard Human-Eval Findings",
        "",
    ]
    if standard and standard.get("status") == "annotations_loaded":
        for field, value in standard.get("dimension_means", {}).items():
            lines.append(f"- {field}: mean {value:.3f}.")
        trace = standard.get("trace_validity", {})
        lines.extend(
            [
                f"- Trace faithfulness mean: {trace.get('trace_faithfulness_mean')}.",
                f"- Trace clarity mean: {trace.get('trace_clarity_mean')}.",
            ]
        )
    else:
        lines.append("- Standard annotations are not available yet.")
    lines.extend(["", "## Comparative Findings", ""])
    if payload["status"] == "comparative_annotations_loaded":
        for pair, row in payload["system_pair_results"].items():
            lines.append(
                f"- {pair}: A win {row['a_win_rate']:.3f}, B win {row['b_win_rate']:.3f}, tie {row['tie_rate']:.3f}."
            )
        lines.append(f"- Adjudication queue size: {len(payload.get('adjudication_queue', []))}.")
    else:
        lines.append("- Comparative annotations are not available yet.")
    lines.extend(
        [
            "",
            "## Agreement And Caveats",
            "",
            "- Agreement should be interpreted cautiously because the evaluator pool and packet sizes are small.",
            "- Forced-choice comparative judgments can hide nuance.",
            "- Automatic correctness is normalized string matching, not a substitute for human support judgments.",
            "",
            "## Threats To Validity",
            "",
            *[f"- {item}" for item in _threats()],
            "",
        ]
    )
    return "\n".join(lines)


def _read_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    return payload if isinstance(payload, dict) else None


def _plot_win_rates(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pairs = list(payload["system_pair_results"].keys())
    a_values = [payload["system_pair_results"][pair]["a_win_rate"] for pair in pairs]
    b_values = [payload["system_pair_results"][pair]["b_win_rate"] for pair in pairs]
    tie_values = [payload["system_pair_results"][pair]["tie_rate"] for pair in pairs]
    x = list(range(len(pairs)))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x, a_values, label="A")
    ax.bar(x, b_values, bottom=a_values, label="B")
    bottoms = [a + b for a, b in zip(a_values, b_values)]
    ax.bar(x, tie_values, bottom=bottoms, label="Tie")
    ax.set_xticks(x, pairs, rotation=30, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Preference share")
    ax.set_title("Comparative Human Preferences By System Pair")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_family_preferences(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    families = list(payload["by_route_family"].keys())
    b_values = [payload["by_route_family"][family]["b_win_rate"] for family in families]
    tie_values = [payload["by_route_family"][family]["tie_rate"] for family in families]
    x = list(range(len(families)))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x, b_values, color="#3a6ea5", label="System B")
    ax.bar(x, tie_values, bottom=b_values, color="#d7a11a", label="Tie")
    ax.set_xticks(x, families)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Preference share")
    ax.set_title("System B And Tie Share By Route Family")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _choice(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "a":
        return "A"
    if normalized == "b":
        return "B"
    if normalized == "tie":
        return "Tie"
    return ""


def _confidence(value: str) -> int:
    try:
        parsed = int(str(value).strip())
    except ValueError:
        return 0
    return parsed if 1 <= parsed <= 3 else 0


def _mean(values: list[int]) -> float | None:
    return sum(values) / len(values) if values else None


def _adjudication_reason(explicit: bool, split: bool, low_confidence: bool) -> str:
    reasons = []
    if explicit:
        reasons.append("at least one evaluator requested adjudication")
    if split:
        reasons.append("overall preference votes are split")
    if low_confidence:
        reasons.append("at least one evaluator reported low confidence")
    return "; ".join(reasons) if reasons else "adjudication reason unavailable"


def _threats() -> list[str]:
    return [
        "Small annotator pool can make preference estimates unstable.",
        "Forced-choice A/B/Tie judgments can hide nuance.",
        "Comparative packet size is practical but limited.",
        "Evaluator familiarity with PRISM may bias preferences.",
        "Hard-case construction overlaps with the systems being compared.",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze PRISM comparative human-eval annotations.")
    parser.parse_args()
    payload = analyze_comparative_annotations()
    print(
        "comparative_human_eval "
        f"status={payload['status']} packet_size={payload.get('packet_size', 0)} "
        f"summary={COMPARATIVE_SUMMARY_MD} adjudication={ADJUDICATION_QUEUE_JSON}"
    )
    if payload["status"] == "no_comparative_annotations":
        print(payload["message"])


if __name__ == "__main__":
    main()
