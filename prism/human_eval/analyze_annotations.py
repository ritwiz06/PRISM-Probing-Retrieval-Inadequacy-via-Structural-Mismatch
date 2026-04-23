from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

from prism.human_eval.load_annotations import AnnotationRecord, load_annotations
from prism.human_eval.rubric import RUBRIC_FIELDS, export_rubric_and_template
from prism.human_eval.sample_builder import PACKET_JSON, build_eval_packet
from prism.human_eval.validation import validate_all_annotations
from prism.utils import read_json, write_json

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

HUMAN_EVAL_DIR = Path("data/human_eval")
SUMMARY_JSON = HUMAN_EVAL_DIR / "human_eval_summary.json"
SUMMARY_CSV = HUMAN_EVAL_DIR / "human_eval_summary.csv"
SUMMARY_MD = HUMAN_EVAL_DIR / "human_eval_summary.md"
TRACE_VALIDITY_MD = HUMAN_EVAL_DIR / "trace_validity_summary.md"
DISAGREEMENT_JSON = HUMAN_EVAL_DIR / "disagreement_cases.json"
DIMENSION_PLOT = HUMAN_EVAL_DIR / "human_scores_by_dimension.png"
SOURCE_PLOT = HUMAN_EVAL_DIR / "human_scores_by_source.png"
FAMILY_PLOT = HUMAN_EVAL_DIR / "human_scores_by_route_family.png"
HUMAN_VS_AUTOMATIC_MD = HUMAN_EVAL_DIR / "human_vs_automatic_summary.md"
HUMAN_EVAL_PAPER_MD = HUMAN_EVAL_DIR / "human_eval_results_for_paper.md"


def analyze_human_annotations() -> dict[str, object]:
    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    if not PACKET_JSON.exists():
        build_eval_packet()
    export_rubric_and_template(PACKET_JSON)
    validation = validate_all_annotations()
    packet = read_json(PACKET_JSON)
    annotations = load_annotations()
    if not annotations:
        payload = _empty_payload(packet)
    else:
        payload = _analysis_payload(packet, annotations)
        payload["validation"] = validation.get("standard", {})
        _plot_dimension_scores(payload, DIMENSION_PLOT)
        _plot_source_scores(payload, SOURCE_PLOT)
        _plot_family_scores(payload, FAMILY_PLOT)
    write_json(SUMMARY_JSON, payload)
    _write_summary_csv(SUMMARY_CSV, payload)
    SUMMARY_MD.write_text(_summary_markdown(payload), encoding="utf-8")
    TRACE_VALIDITY_MD.write_text(_trace_markdown(payload), encoding="utf-8")
    write_json(DISAGREEMENT_JSON, payload.get("disagreement_cases", []))
    HUMAN_VS_AUTOMATIC_MD.write_text(_human_vs_automatic_markdown(payload), encoding="utf-8")
    HUMAN_EVAL_PAPER_MD.write_text(_paper_markdown(payload), encoding="utf-8")
    return payload


def _empty_payload(packet: dict[str, object]) -> dict[str, object]:
    return {
        "status": "no_annotations",
        "message": "No annotation CSV files were found under data/human_eval/annotations/. Packet and template are ready for evaluators.",
        "packet_size": packet.get("packet_size", 0),
        "packet_counts": packet.get("counts", {}),
        "annotation_dir": "data/human_eval/annotations",
        "expected_template": "data/human_eval/annotation_template.csv",
        "rubric": "data/human_eval/rubric.md",
        "dimension_means": {},
        "dimension_medians": {},
        "score_distributions": {},
        "by_benchmark_source": {},
        "by_route_family": {},
        "by_system_variant": {},
        "agreement": {},
        "trace_validity": {
            "trace_faithfulness_mean": None,
            "trace_clarity_mean": None,
            "supported_answer_when_route_imperfect": None,
        },
        "disagreement_cases": [],
        "threats_to_validity": _threats(),
    }


def _analysis_payload(packet: dict[str, object], annotations: list[AnnotationRecord]) -> dict[str, object]:
    item_meta = {item["item_id"]: item for item in packet.get("items", [])}
    complete = [row for row in annotations if row.item_id in item_meta]
    dimension_means = {
        field: _mean([row.scores[field] for row in complete if row.scores[field] > 0])
        for field in RUBRIC_FIELDS
    }
    dimension_medians = {
        field: _median([row.scores[field] for row in complete if row.scores[field] > 0])
        for field in RUBRIC_FIELDS
    }
    distributions = {
        field: dict(Counter(str(row.scores[field]) for row in complete if row.scores[field] > 0))
        for field in RUBRIC_FIELDS
    }
    by_source = _group_means(complete, item_meta, "benchmark_source")
    by_family = _group_means(complete, item_meta, "route_family")
    by_variant = _group_means(complete, item_meta, "system_variant")
    agreement = _agreement(complete)
    disagreement_cases = _disagreement_cases(complete, item_meta)
    trace_validity = _trace_validity(complete, item_meta)
    human_vs_auto = _human_vs_automatic(complete, item_meta)
    return {
        "status": "annotations_loaded",
        "packet_size": packet.get("packet_size", 0),
        "annotation_count": len(complete),
        "evaluator_count": len({row.evaluator_id for row in complete}),
        "packet_counts": packet.get("counts", {}),
        "dimension_means": dimension_means,
        "dimension_medians": dimension_medians,
        "score_distributions": distributions,
        "by_benchmark_source": by_source,
        "by_route_family": by_family,
        "by_system_variant": by_variant,
        "agreement": agreement,
        "trace_validity": trace_validity,
        "human_vs_automatic": human_vs_auto,
        "disagreement_cases": disagreement_cases,
        "major_error_type_counts": dict(Counter(row.major_error_type for row in complete)),
        "threats_to_validity": _threats(),
    }


def _group_means(records: list[AnnotationRecord], item_meta: dict[str, dict[str, object]], key: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[AnnotationRecord]] = defaultdict(list)
    for record in records:
        grouped[str(item_meta[record.item_id].get(key, "unknown"))].append(record)
    return {
        group: {field: _mean([row.scores[field] for row in rows if row.scores[field] > 0]) for field in RUBRIC_FIELDS}
        for group, rows in sorted(grouped.items())
    }


def _agreement(records: list[AnnotationRecord]) -> dict[str, object]:
    by_item: dict[str, list[AnnotationRecord]] = defaultdict(list)
    for record in records:
        by_item[record.item_id].append(record)
    comparable = {item: rows for item, rows in by_item.items() if len(rows) >= 2}
    percent_by_field = {}
    kappa_by_field = {}
    weighted_kappa_by_field = {}
    for field in RUBRIC_FIELDS:
        pairs = []
        for rows in comparable.values():
            first, second = rows[0], rows[1]
            if first.scores[field] and second.scores[field]:
                pairs.append((first.scores[field], second.scores[field]))
        percent_by_field[field] = _percent_agreement(pairs)
        kappa_by_field[field] = _cohen_kappa(pairs)
        weighted_kappa_by_field[field] = _weighted_kappa(pairs)
    error_pairs = []
    for rows in comparable.values():
        first, second = rows[0], rows[1]
        error_pairs.append((first.major_error_type, second.major_error_type))
    return {
        "items_with_multiple_annotations": len(comparable),
        "percent_agreement": percent_by_field,
        "cohen_kappa": kappa_by_field,
        "weighted_kappa": weighted_kappa_by_field,
        "major_error_type_percent_agreement": _percent_agreement(error_pairs),
        "major_error_type_kappa": _cohen_kappa(error_pairs),
        "protocol": "Agreement uses the first two annotators per item; additional annotators are included in means but not pairwise kappa.",
    }


def _trace_validity(records: list[AnnotationRecord], item_meta: dict[str, dict[str, object]]) -> dict[str, object]:
    trace_faith = [row.scores["trace_faithfulness"] for row in records if row.scores["trace_faithfulness"] > 0]
    trace_clarity = [row.scores["trace_clarity"] for row in records if row.scores["trace_clarity"] > 0]
    supported_route_imperfect = []
    for row in records:
        meta = item_meta[row.item_id]
        if meta.get("predicted_route") != meta.get("gold_route") and row.scores["answer_faithfulness"] > 0:
            supported_route_imperfect.append(row.scores["answer_faithfulness"] >= 2)
    weak_auto_correct = [
        {
            "item_id": row.item_id,
            "benchmark_source": item_meta[row.item_id].get("benchmark_source"),
            "automatic_correct": item_meta[row.item_id].get("automatic_correct"),
            "answer_faithfulness": row.scores["answer_faithfulness"],
            "trace_faithfulness": row.scores["trace_faithfulness"],
        }
        for row in records
        if item_meta[row.item_id].get("automatic_correct") and row.scores["answer_faithfulness"] in {1, 2}
    ]
    return {
        "trace_faithfulness_mean": _mean(trace_faith),
        "trace_clarity_mean": _mean(trace_clarity),
        "trace_faithfulness_ge_2_rate": _rate([score >= 2 for score in trace_faith]),
        "trace_clarity_ge_2_rate": _rate([score >= 2 for score in trace_clarity]),
        "supported_answer_when_route_imperfect": _rate(supported_route_imperfect),
        "automatic_correct_but_human_support_weak": weak_auto_correct[:20],
        "weak_trace_support_cases": [
            {
                "item_id": row.item_id,
                "benchmark_source": item_meta[row.item_id].get("benchmark_source"),
                "route_family": item_meta[row.item_id].get("route_family"),
                "trace_faithfulness": row.scores["trace_faithfulness"],
                "trace_clarity": row.scores["trace_clarity"],
                "evaluator_id": row.evaluator_id,
                "notes": row.notes,
            }
            for row in records
            if row.scores["trace_faithfulness"] in {1, 2} or row.scores["trace_clarity"] in {1, 2}
        ][:25],
    }


def _human_vs_automatic(records: list[AnnotationRecord], item_meta: dict[str, dict[str, object]]) -> dict[str, object]:
    weak_auto_correct = []
    strong_auto_incorrect = []
    for row in records:
        meta = item_meta[row.item_id]
        auto_correct = bool(meta.get("automatic_correct"))
        answer_score = row.scores["answer_faithfulness"]
        evidence_score = row.scores["evidence_sufficiency"]
        trace_score = row.scores["trace_faithfulness"]
        if auto_correct and (answer_score <= 2 or evidence_score <= 2 or trace_score <= 2):
            weak_auto_correct.append(
                {
                    "item_id": row.item_id,
                    "benchmark_source": meta.get("benchmark_source"),
                    "route_family": meta.get("route_family"),
                    "system_variant": meta.get("system_variant"),
                    "answer_faithfulness": answer_score,
                    "evidence_sufficiency": evidence_score,
                    "trace_faithfulness": trace_score,
                    "evaluator_id": row.evaluator_id,
                    "notes": row.notes,
                }
            )
        if not auto_correct and answer_score >= 3 and evidence_score >= 3:
            strong_auto_incorrect.append(
                {
                    "item_id": row.item_id,
                    "benchmark_source": meta.get("benchmark_source"),
                    "route_family": meta.get("route_family"),
                    "system_variant": meta.get("system_variant"),
                    "answer_faithfulness": answer_score,
                    "evidence_sufficiency": evidence_score,
                    "evaluator_id": row.evaluator_id,
                    "notes": row.notes,
                }
            )
    return {
        "automatic_correct_but_human_support_weak_count": len(weak_auto_correct),
        "automatic_incorrect_but_human_support_strong_count": len(strong_auto_incorrect),
        "automatic_correct_but_human_support_weak": weak_auto_correct[:30],
        "automatic_incorrect_but_human_support_strong": strong_auto_incorrect[:30],
    }


def _disagreement_cases(records: list[AnnotationRecord], item_meta: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    by_item: dict[str, list[AnnotationRecord]] = defaultdict(list)
    for record in records:
        by_item[record.item_id].append(record)
    cases = []
    for item_id, rows in by_item.items():
        if len(rows) < 2:
            continue
        max_gap = 0
        for field in RUBRIC_FIELDS:
            scores = [row.scores[field] for row in rows if row.scores[field] > 0]
            if scores:
                max_gap = max(max_gap, max(scores) - min(scores))
        if max_gap > 0:
            cases.append(
                {
                    "item_id": item_id,
                    "query": item_meta[item_id].get("query"),
                    "benchmark_source": item_meta[item_id].get("benchmark_source"),
                    "route_family": item_meta[item_id].get("route_family"),
                    "max_score_gap": max_gap,
                    "annotators": [row.evaluator_id for row in rows],
                    "scores": [{**row.scores, "major_error_type": row.major_error_type} for row in rows],
                }
            )
    return sorted(cases, key=lambda row: int(row["max_score_gap"]), reverse=True)[:20]


def _write_summary_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["scope", "name", "dimension", "mean_score"])
        writer.writeheader()
        for dimension, value in payload.get("dimension_means", {}).items():
            writer.writerow({"scope": "overall", "name": "all", "dimension": dimension, "mean_score": value})
        for scope, groups in (("benchmark_source", payload.get("by_benchmark_source", {})), ("route_family", payload.get("by_route_family", {}))):
            for name, dimensions in groups.items():
                for dimension, value in dimensions.items():
                    writer.writerow({"scope": scope, "name": name, "dimension": dimension, "mean_score": value})
        if not payload.get("dimension_means"):
            writer.writerow({"scope": "status", "name": payload.get("status"), "dimension": "none", "mean_score": ""})


def _summary_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# PRISM Human Evaluation Summary",
        "",
        f"Status: `{payload['status']}`.",
        f"Packet size: {payload.get('packet_size', 0)}.",
    ]
    if payload["status"] == "no_annotations":
        lines.extend(
            [
                "",
                payload["message"],
                "",
                "## Next Steps",
                "",
                "- Give evaluators `data/human_eval/eval_packet.md` and `data/human_eval/rubric.md`.",
                "- Copy `data/human_eval/annotation_template.csv` into `data/human_eval/annotations/<evaluator_id>.csv`.",
                "- Fill scores from 1 to 3, then rerun `python -m prism.human_eval.analyze_annotations`.",
            ]
        )
    else:
        lines.extend(
            [
                f"Annotation count: {payload['annotation_count']}.",
                f"Evaluator count: {payload['evaluator_count']}.",
                "",
                "## Dimension Means",
                "",
                *[f"- {field}: {value:.3f}" for field, value in payload["dimension_means"].items()],
                "",
                "## Agreement",
                "",
                f"- Items with multiple annotations: {payload['agreement']['items_with_multiple_annotations']}",
                f"- Major error type percent agreement: {payload['agreement']['major_error_type_percent_agreement']}",
                f"- Major error type kappa: {payload['agreement']['major_error_type_kappa']}",
                "",
                "## Medians",
                "",
                *[f"- {field}: {value}" for field, value in payload["dimension_medians"].items()],
                "",
                "## Human Vs Automatic",
                "",
                f"- Automatic-correct but weak human support annotations: {payload['human_vs_automatic']['automatic_correct_but_human_support_weak_count']}",
                f"- Automatic-incorrect but strong human support annotations: {payload['human_vs_automatic']['automatic_incorrect_but_human_support_strong_count']}",
            ]
        )
    lines.extend(["", "## Threats To Validity", "", *[f"- {item}" for item in payload["threats_to_validity"]], ""])
    return "\n".join(lines)


def _trace_markdown(payload: dict[str, object]) -> str:
    trace = payload.get("trace_validity", {})
    lines = [
        "# Trace Validity Summary",
        "",
        f"Status: `{payload['status']}`.",
    ]
    if payload["status"] == "no_annotations":
        lines.append("No human trace-validity judgments are available yet. Use the annotation template to collect them.")
    else:
        lines.extend(
            [
                f"Trace faithfulness mean: {trace.get('trace_faithfulness_mean')}",
                f"Trace clarity mean: {trace.get('trace_clarity_mean')}",
                f"Trace faithfulness >=2 rate: {trace.get('trace_faithfulness_ge_2_rate')}",
                f"Trace clarity >=2 rate: {trace.get('trace_clarity_ge_2_rate')}",
                f"Supported answer when route imperfect: {trace.get('supported_answer_when_route_imperfect')}",
                f"Automatic-correct but weak human support count: {len(trace.get('automatic_correct_but_human_support_weak', []))}",
                f"Weak trace support case count: {len(trace.get('weak_trace_support_cases', []))}",
            ]
        )
    return "\n".join(lines) + "\n"


def _human_vs_automatic_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Human Vs Automatic Summary",
        "",
        f"Standard human-eval status: `{payload['status']}`.",
    ]
    if payload["status"] == "no_annotations":
        lines.append("Standard human judgments are not available yet.")
        return "\n".join(lines) + "\n"
    human_auto = payload.get("human_vs_automatic", {})
    lines.extend(
        [
            "",
            "## Standard Packet",
            "",
            f"- Automatic-correct but weak human support annotations: {human_auto.get('automatic_correct_but_human_support_weak_count', 0)}.",
            f"- Automatic-incorrect but strong human support annotations: {human_auto.get('automatic_incorrect_but_human_support_strong_count', 0)}.",
            "",
            "## Interpretation",
            "",
            "These cases identify where normalized answer matching and human support judgments diverge. They are useful for report caveats and adjudication discussion.",
        ]
    )
    return "\n".join(lines) + "\n"


def _paper_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# PRISM Human-Evaluation Results For Paper",
        "",
        "## Study Setup",
        "",
        f"- Standard packet size: {payload.get('packet_size', 0)}.",
        f"- Standard evaluator count: {payload.get('evaluator_count', 0) if payload['status'] != 'no_annotations' else 'pending'}.",
        "",
        "## Standard Human-Eval Results",
        "",
    ]
    if payload["status"] == "annotations_loaded":
        for field, value in payload["dimension_means"].items():
            lines.append(f"- {field}: mean {value:.3f}, median {payload['dimension_medians'][field]}.")
        trace = payload["trace_validity"]
        lines.extend(
            [
                "",
                "## Trace Validity",
                "",
                f"- Trace faithfulness mean: {trace.get('trace_faithfulness_mean')}.",
                f"- Trace clarity mean: {trace.get('trace_clarity_mean')}.",
                f"- Weak trace support annotations: {len(trace.get('weak_trace_support_cases', []))}.",
                "",
                "## Agreement",
                "",
                f"- Items with multiple annotations: {payload['agreement']['items_with_multiple_annotations']}.",
                f"- Major error type percent agreement: {payload['agreement']['major_error_type_percent_agreement']}.",
                "",
                "## Human Vs Automatic",
                "",
                f"- Automatic-correct but weak support annotations: {payload['human_vs_automatic']['automatic_correct_but_human_support_weak_count']}.",
            ]
        )
    else:
        lines.append("- Standard annotations are pending.")
    lines.extend(["", "## Threats To Validity", "", *[f"- {item}" for item in _threats()], ""])
    return "\n".join(lines)


def _plot_dimension_scores(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dimensions = list(payload["dimension_means"].keys())
    values = [payload["dimension_means"][dimension] for dimension in dimensions]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(range(len(dimensions)), values, color="#3a6ea5")
    ax.set_xticks(range(len(dimensions)), dimensions, rotation=30, ha="right")
    ax.set_ylim(0, 3)
    ax.set_ylabel("Mean score")
    ax.set_title("Human Scores By Dimension")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_source_scores(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sources = list(payload["by_benchmark_source"].keys())
    values = [
        _mean([score for score in payload["by_benchmark_source"][source].values() if score is not None])
        for source in sources
    ]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(sources)), values, color="#5f8d4e")
    ax.set_xticks(range(len(sources)), sources, rotation=25, ha="right")
    ax.set_ylim(0, 3)
    ax.set_ylabel("Mean score")
    ax.set_title("Human Scores By Benchmark Source")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_family_scores(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    families = list(payload["by_route_family"].keys())
    values = [
        _mean([score for score in payload["by_route_family"][family].values() if score is not None])
        for family in families
    ]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(families)), values, color="#8b5e34")
    ax.set_xticks(range(len(families)), families)
    ax.set_ylim(0, 3)
    ax.set_ylabel("Mean score")
    ax.set_title("Human Scores By Route Family")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _percent_agreement(pairs: list[tuple[object, object]]) -> float | None:
    if not pairs:
        return None
    return sum(1 for first, second in pairs if first == second) / len(pairs)


def _cohen_kappa(pairs: list[tuple[object, object]]) -> float | None:
    if not pairs:
        return None
    labels = sorted({label for pair in pairs for label in pair})
    observed = _percent_agreement(pairs) or 0.0
    total = len(pairs)
    first_counts = Counter(first for first, _second in pairs)
    second_counts = Counter(second for _first, second in pairs)
    expected = sum((first_counts[label] / total) * (second_counts[label] / total) for label in labels)
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1.0 - expected)


def _weighted_kappa(pairs: list[tuple[int, int]]) -> float | None:
    clean = [(int(first), int(second)) for first, second in pairs if first in {1, 2, 3} and second in {1, 2, 3}]
    if not clean:
        return None
    labels = [1, 2, 3]
    total = len(clean)
    observed_disagreement = sum(((first - second) ** 2) / 4 for first, second in clean) / total
    first_counts = Counter(first for first, _second in clean)
    second_counts = Counter(second for _first, second in clean)
    expected_disagreement = 0.0
    for first in labels:
        for second in labels:
            expected_disagreement += (first_counts[first] / total) * (second_counts[second] / total) * (((first - second) ** 2) / 4)
    if expected_disagreement == 0:
        return 1.0
    return 1.0 - (observed_disagreement / expected_disagreement)


def _mean(values: list[int | float]) -> float | None:
    return sum(values) / len(values) if values else None


def _median(values: list[int | float]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return float(sorted_values[mid])
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2


def _rate(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def _threats() -> list[str]:
    return [
        "Small evaluator pool can produce unstable agreement estimates.",
        "Ordinal rubric scores are subjective even with written guidance.",
        "Packet size is intentionally small for practicality.",
        "Evaluators may share expectations with benchmark designers.",
        "Human support judgments may disagree with automatic normalized string matching.",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze PRISM human-evaluation annotations.")
    parser.parse_args()
    payload = analyze_human_annotations()
    print(
        "human_eval_analysis "
        f"status={payload['status']} "
        f"packet_size={payload.get('packet_size', 0)} "
        f"annotations={payload.get('annotation_count', 0)} "
        f"summary={SUMMARY_MD} trace={TRACE_VALIDITY_MD}"
    )
    if payload["status"] == "no_annotations":
        print(payload["message"])


if __name__ == "__main__":
    main()
