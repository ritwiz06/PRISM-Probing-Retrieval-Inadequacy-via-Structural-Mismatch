from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from prism.adversarial.verify_adversarial import JSON_PATH as ADVERSARIAL_JSON
from prism.adversarial.verify_adversarial import verify_adversarial
from prism.utils import read_json, write_json

JSON_PATH = Path("data/eval/adversarial_failure_analysis.json")
MARKDOWN_PATH = Path("data/eval/adversarial_failure_analysis_summary.md")


def analyze_adversarial_failures() -> dict[str, object]:
    if not ADVERSARIAL_JSON.exists():
        verify_adversarial()
    payload = read_json(ADVERSARIAL_JSON)
    computed = payload["systems"]["combined"]["computed_ras"]
    all_systems = payload["systems"]["combined"]
    rows = []
    bucket_counts: Counter[str] = Counter()
    system_failures_by_id = _system_failures_by_id(all_systems)
    for row in computed["results"]:
        buckets = _buckets(row)
        if row["answer_correct"] and row["route_correct"] and row["evidence_hit"] and not row["top1_topk_gap"]:
            continue
        bucket_counts.update(buckets)
        rows.append(
            {
                "id": row["id"],
                "query": row["query"],
                "split": row["split"],
                "intended_route_family": row["intended_route_family"],
                "predicted_backend": row["predicted_backend"],
                "ambiguity_tags": row["ambiguity_tags"],
                "answer_correct": row["answer_correct"],
                "route_correct": row["route_correct"],
                "evidence_hit": row["evidence_hit"],
                "top1_evidence_hit": row["top1_evidence_hit"],
                "buckets": buckets,
                "systems_failed": system_failures_by_id.get(row["id"], []),
                "failure_count_across_systems": len(system_failures_by_id.get(row["id"], [])),
                "top_evidence_ids": row["top_evidence_ids"][:5],
                "remediation_note": _remediation_note(buckets),
            }
        )
    hardest = sorted(rows, key=lambda item: item["failure_count_across_systems"], reverse=True)[:12]
    tag_summary = _tag_summary(computed["results"])
    payload_out = {
        "source": str(ADVERSARIAL_JSON),
        "computed_ras": {
            "total": computed["total"],
            "route_accuracy": computed["route_accuracy"],
            "answer_accuracy": computed["answer_accuracy"],
            "evidence_hit_at_k": computed["evidence_hit_at_k"],
            "top1_evidence_hit": computed["top1_evidence_hit"],
        },
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "failure_rows": rows,
        "hardest_examples": hardest,
        "tag_summary": tag_summary,
        "baseline_subtype_wins": _baseline_subtype_wins(payload),
        "known_limitations": [
            "Hard cases are hand-constructed and intentionally route-boundary-heavy.",
            "Failure buckets are rule-assisted and inspectable, not learned labels.",
            "Answer correctness still uses normalized exact/soft string matching.",
        ],
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload_out)
    MARKDOWN_PATH.write_text(_markdown(payload_out), encoding="utf-8")
    return payload_out


def _system_failures_by_id(systems: dict[str, dict[str, object]]) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = defaultdict(list)
    for system, result in systems.items():
        for row in result["results"]:
            if not row["answer_correct"] or not row["route_correct"] or not row["evidence_hit"]:
                failures[row["id"]].append(system)
    return dict(failures)


def _buckets(row: dict[str, object]) -> list[str]:
    buckets: list[str] = []
    tags = set(row["ambiguity_tags"])
    if not row["route_correct"]:
        buckets.append("route boundary confusion")
    if row["predicted_backend"] == "bm25" and row["intended_route_family"] != "bm25":
        buckets.append("lexical over-trigger")
    if row["predicted_backend"] == "dense" and row["intended_route_family"] != "dense":
        buckets.append("semantic over-generalization")
    if row["intended_route_family"] == "kg" and (not row["evidence_hit"] or not row["answer_correct"]):
        buckets.append("KG incompleteness")
    if "public_document_noise" in tags:
        buckets.append("public-document noise")
    if "wrong_bridge_distractor" in tags and (not row["evidence_hit"] or not row["answer_correct"]):
        buckets.append("relational bridge confusion")
    if "identifier_ambiguity" in tags:
        buckets.append("identifier ambiguity")
    if row["evidence_hit"] and not row["top1_evidence_hit"]:
        buckets.append("evidence present in top-k but not top-1")
    if row["evidence_hit"] and not row["answer_correct"]:
        buckets.append("answer synthesis miss")
    if not row["evidence_hit"]:
        buckets.append("retrieval miss")
    return buckets or ["hard-case near miss without current failure"]


def _remediation_note(buckets: list[str]) -> str:
    if "route boundary confusion" in buckets:
        return "Inspect feature parser/RAS margin and consider an analysis-only arbitration rule before changing production routing."
    if "evidence present in top-k but not top-1" in buckets:
        return "Reranking or metadata-aware tie-breaking may help without changing benchmark labels."
    if "relational bridge confusion" in buckets:
        return "Inspect Hybrid fusion contribution order and KG path evidence."
    if "KG incompleteness" in buckets:
        return "Check whether the needed triple/path exists in demo, public, or mixed graph mode."
    if "answer synthesis miss" in buckets:
        return "Adjust deterministic answer templates only if retrieved evidence is correct."
    return "Keep as an observed hard-case limitation unless a grounded fix is clear."


def _tag_summary(results: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    counters = defaultdict(lambda: Counter(total=0, route_misses=0, answer_misses=0, evidence_misses=0, top1_topk_gaps=0))
    for row in results:
        for tag in row["ambiguity_tags"]:
            counter = counters[tag]
            counter["total"] += 1
            counter["route_misses"] += int(not row["route_correct"])
            counter["answer_misses"] += int(not row["answer_correct"])
            counter["evidence_misses"] += int(not row["evidence_hit"])
            counter["top1_topk_gaps"] += int(row["top1_topk_gap"])
    return {
        tag: {
            "total": counter["total"],
            "route_miss_rate": counter["route_misses"] / counter["total"] if counter["total"] else 0.0,
            "answer_miss_rate": counter["answer_misses"] / counter["total"] if counter["total"] else 0.0,
            "evidence_miss_rate": counter["evidence_misses"] / counter["total"] if counter["total"] else 0.0,
            "top1_topk_gap_rate": counter["top1_topk_gaps"] / counter["total"] if counter["total"] else 0.0,
        }
        for tag, counter in sorted(counters.items())
    }


def _baseline_subtype_wins(payload: dict[str, object]) -> list[str]:
    computed = payload["systems"]["combined"]["computed_ras"]["per_ambiguity_tag"]
    systems = payload["systems"]["combined"]
    rows: list[str] = []
    for tag, computed_row in computed.items():
        best_system = "computed_ras"
        best_score = computed_row["answer_accuracy"]
        for system, result in systems.items():
            score = result["per_ambiguity_tag"].get(tag, {"answer_accuracy": 0.0})["answer_accuracy"]
            if score > best_score:
                best_system = system
                best_score = score
        if best_system != "computed_ras":
            rows.append(f"{best_system} beats computed_ras on {tag}: {best_score:.3f} vs {computed_row['answer_accuracy']:.3f}.")
    return rows or ["No baseline beats computed_ras on an ambiguity tag by answer accuracy."]


def _markdown(payload: dict[str, object]) -> str:
    metrics = payload["computed_ras"]
    lines = [
        "# Adversarial Failure Analysis",
        "",
        f"Source: `{payload['source']}`.",
        f"Computed RAS answer accuracy: {metrics['answer_accuracy']:.3f}.",
        f"Computed RAS route accuracy: {metrics['route_accuracy']:.3f}.",
        f"Computed RAS evidence hit@k: {metrics['evidence_hit_at_k']:.3f}.",
        f"Computed RAS top-1 evidence hit: {metrics['top1_evidence_hit']:.3f}.",
        "",
        "## Bucket Counts",
        "",
        *[f"- {bucket}: {count}" for bucket, count in payload["bucket_counts"].items()],
        "",
        "## Hardest Examples",
        "",
    ]
    for row in payload["hardest_examples"]:
        lines.append(
            f"- `{row['id']}` failed_by={row['systems_failed']} buckets={row['buckets']} query={row['query']}"
        )
    lines.extend(
        [
            "",
            "## Baseline Subtype Wins",
            "",
            *[f"- {item}" for item in payload["baseline_subtype_wins"]],
            "",
            "## Tag Summary",
            "",
        ]
    )
    for tag, row in payload["tag_summary"].items():
        lines.append(
            f"- {tag}: route_miss={row['route_miss_rate']:.3f}, answer_miss={row['answer_miss_rate']:.3f}, "
            f"evidence_miss={row['evidence_miss_rate']:.3f}, top1_topk_gap={row['top1_topk_gap_rate']:.3f}."
        )
    lines.extend(
        [
            "",
            "## Known Limitations",
            "",
            *[f"- {item}" for item in payload["known_limitations"]],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{JSON_PATH}`",
            f"- Markdown: `{MARKDOWN_PATH}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze PRISM failures on hard ambiguity/adversarial benchmark.")
    parser.parse_args()
    payload = analyze_adversarial_failures()
    metrics = payload["computed_ras"]
    print(
        "adversarial_failure_analysis "
        f"answer_accuracy={metrics['answer_accuracy']:.3f} "
        f"route_accuracy={metrics['route_accuracy']:.3f} "
        f"failures={len(payload['failure_rows'])} "
        f"json={JSON_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["baseline_subtype_wins"]:
        print(item)


if __name__ == "__main__":
    main()
