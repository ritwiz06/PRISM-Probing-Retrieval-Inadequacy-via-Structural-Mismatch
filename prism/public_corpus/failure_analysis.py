from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

from prism.public_corpus.enrich_documents import load_enriched_metadata
from prism.public_corpus.lexical_retriever import is_identifier_heavy_query
from prism.public_corpus.loaders import load_public_benchmark
from prism.public_corpus.verify_public_corpus import JSON_PATH as PUBLIC_EVAL_JSON
from prism.public_corpus.verify_public_corpus import PREVIOUS_PUBLIC_TEST_REFERENCE, verify_public_corpus
from prism.utils import read_json, write_json

FAILURE_JSON = Path("data/eval/public_failure_analysis.json")
FAILURE_CSV = Path("data/eval/public_failure_analysis.csv")
FAILURE_MD = Path("data/eval/public_failure_analysis_summary.md")
ARBITRATION_JSON = Path("data/eval/public_route_arbitration.json")
ARBITRATION_MD = Path("data/eval/public_route_arbitration_summary.md")
ROBUSTNESS_MD = Path("data/eval/public_robustness_summary.md")
BEFORE_AFTER_PLOT = Path("data/eval/public_robustness_before_after.png")
IDENTIFIER_PLOT = Path("data/eval/public_identifier_subgroup.png")

PREVIOUS_PROMPT17_MISSES = [
    {
        "id": "pub_bm25_11",
        "query": "Python dataclasses generated special methods",
        "route_family": "bm25",
        "previous_predicted_backend": "kg",
        "previous_buckets": ["route_error", "retrieval_miss", "answer_synthesis_miss", "lexical_confusion"],
        "remediation": "Fixed substring marker matching so dataclasses no longer triggers the deductive class marker; public lexical arbitration also recognizes dataclasses as a public-doc alias.",
    },
    {
        "id": "pub_bm25_12",
        "query": "TfidfVectorizer raw documents matrix TF-IDF features",
        "route_family": "bm25",
        "previous_predicted_backend": "dense",
        "previous_buckets": ["route_error", "lexical_confusion"],
        "remediation": "Public lexical arbitration recognizes TfidfVectorizer and TF-IDF aliases and routes this identifier-heavy case to BM25 in analysis mode.",
    },
    {
        "id": "pub_dense_10",
        "query": "What immune response mistakes harmless substances for threats?",
        "route_family": "dense",
        "previous_predicted_backend": "kg",
        "previous_buckets": ["route_error", "retrieval_miss", "answer_synthesis_miss", "semantic_drift"],
        "remediation": "Fixed substring marker matching so threats no longer triggers the KG eats marker; the query now routes to Dense.",
    },
]


def analyze_public_failures() -> dict[str, object]:
    payload = verify_public_corpus()
    items = {item.id: item for item in load_public_benchmark()}
    metadata = load_enriched_metadata()
    analysis_rows = _analysis_rows(payload, items, metadata)
    bucket_counts = Counter(bucket for row in analysis_rows for bucket in row["buckets"])
    current_test = payload["systems"]["test"]["computed_ras"]
    arbitrated_test = payload["public_robustness_systems"]["test"]["computed_ras_public_arbitrated"]
    before_after = payload["before_after"]["test"]
    result = {
        "public_eval_source": str(PUBLIC_EVAL_JSON),
        "previous_public_test_reference": PREVIOUS_PUBLIC_TEST_REFERENCE,
        "previous_prompt17_misses": PREVIOUS_PROMPT17_MISSES,
        "current_test_metrics": {
            "answer_accuracy": current_test["answer_accuracy"],
            "route_accuracy": current_test["route_accuracy"],
            "evidence_hit_at_k": current_test["evidence_hit_at_k"],
            "answer_correct": current_test["answer_correct"],
            "total": current_test["total"],
        },
        "public_arbitrated_test_metrics": {
            "answer_accuracy": arbitrated_test["answer_accuracy"],
            "route_accuracy": arbitrated_test["route_accuracy"],
            "evidence_hit_at_k": arbitrated_test["evidence_hit_at_k"],
            "answer_correct": arbitrated_test["answer_correct"],
            "total": arbitrated_test["total"],
        },
        "before_after": before_after,
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "identifier_subgroups": _identifier_subgroups(analysis_rows),
        "fixed_bm25_rescues": _fixed_bm25_rescues(payload),
        "rows": analysis_rows,
        "tradeoffs": _tradeoffs(payload),
    }
    FAILURE_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json(FAILURE_JSON, result)
    _write_failure_csv(FAILURE_CSV, analysis_rows)
    FAILURE_MD.write_text(_failure_markdown(result), encoding="utf-8")
    route_payload = _route_arbitration_payload(payload)
    write_json(ARBITRATION_JSON, route_payload)
    ARBITRATION_MD.write_text(_route_arbitration_markdown(route_payload), encoding="utf-8")
    ROBUSTNESS_MD.write_text(_robustness_markdown(result), encoding="utf-8")
    _plot_before_after(result, BEFORE_AFTER_PLOT)
    _plot_identifier_subgroups(result, IDENTIFIER_PLOT)
    return result


def _analysis_rows(payload: dict[str, object], items: dict[str, object], metadata: dict[str, object]) -> list[dict[str, object]]:
    baseline = payload["systems"]["test"]["computed_ras"]["results"]
    always_bm25 = {row["id"]: row for row in payload["systems"]["test"]["always_bm25"]["results"]}
    arbitrated = {row["id"]: row for row in payload["public_robustness_systems"]["test"]["computed_ras_public_arbitrated"]["results"]}
    rows: list[dict[str, object]] = []
    for row in baseline:
        item = items[row["id"]]
        doc_ids = row["gold_source_doc_ids"]
        source_types = sorted({metadata[doc_id].source_type for doc_id in doc_ids if doc_id in metadata})
        identifier_heavy = is_identifier_heavy_query(row["query"])
        buckets = _buckets(row, identifier_heavy)
        bm25_row = always_bm25[row["id"]]
        arbitrated_row = arbitrated[row["id"]]
        rows.append(
            {
                "id": row["id"],
                "query": row["query"],
                "route_family": row["route_family"],
                "source_dataset_style": row["source_dataset_style"],
                "source_types": ",".join(source_types),
                "identifier_heavy": identifier_heavy,
                "predicted_backend": row["predicted_backend"],
                "route_correct": row["route_correct"],
                "answer_correct": row["answer_correct"],
                "evidence_hit": row["evidence_hit"],
                "always_bm25_answer_correct": bm25_row["answer_correct"],
                "bm25_gets_right_when_computed_wrong": (not row["answer_correct"] or not row["route_correct"]) and bm25_row["answer_correct"],
                "arbitrated_backend": arbitrated_row["predicted_backend"],
                "arbitrated_route_correct": arbitrated_row["route_correct"],
                "arbitrated_answer_correct": arbitrated_row["answer_correct"],
                "buckets": buckets,
                "suggested_remediation": _remediation(row, buckets, identifier_heavy),
            }
        )
    return rows


def _buckets(row: dict[str, object], identifier_heavy: bool) -> list[str]:
    buckets: list[str] = []
    if not row["route_correct"]:
        buckets.append("route_error")
    if not row["evidence_hit"]:
        buckets.append("retrieval_miss")
    if not row["answer_correct"] and row["evidence_hit"]:
        buckets.append("answer_synthesis_miss")
    if not row["answer_correct"] and row["evidence_hit"] and row["route_correct"]:
        buckets.append("ranking_error")
    if row["route_family"] == "bm25" and (not row["route_correct"] or not row["evidence_hit"]):
        buckets.append("lexical_confusion")
    if row["route_family"] == "dense" and (not row["route_correct"] or not row["evidence_hit"]):
        buckets.append("semantic_drift")
    if row["route_family"] == "hybrid" and (not row["route_correct"] or not row["evidence_hit"]):
        buckets.append("hybrid_fusion_miss")
    if row["route_family"] == "kg" and (not row["route_correct"] or not row["evidence_hit"]):
        buckets.append("kg_incompleteness")
    if identifier_heavy and row["predicted_backend"] != "bm25":
        buckets.append("public_identifier_arbitration_candidate")
    return buckets or ["correct"]


def _remediation(row: dict[str, object], buckets: list[str], identifier_heavy: bool) -> str:
    if "public_identifier_arbitration_candidate" in buckets:
        return "Use public-only lexical arbitration when enriched title/identifier/alias confidence is high."
    if "route_error" in buckets:
        return "Inspect feature parsing and RAS marker match behavior before changing benchmark labels."
    if "retrieval_miss" in buckets:
        return "Inspect public-page cleaning and field-aware lexical metadata for this source."
    if "answer_synthesis_miss" in buckets:
        return "Inspect answer template extraction from the retrieved evidence."
    if identifier_heavy:
        return "Keep enriched identifier metadata for regression coverage."
    return "No change needed for this current run."


def _identifier_subgroups(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = {
        "identifier_heavy": [row for row in rows if row["identifier_heavy"]],
        "non_identifier": [row for row in rows if not row["identifier_heavy"]],
    }
    return {
        name: {
            "total": len(group),
            "answer_accuracy": sum(1 for row in group if row["answer_correct"]) / len(group) if group else 0.0,
            "route_accuracy": sum(1 for row in group if row["route_correct"]) / len(group) if group else 0.0,
            "arbitrated_route_accuracy": sum(1 for row in group if row["arbitrated_route_correct"]) / len(group) if group else 0.0,
        }
        for name, group in groups.items()
    }


def _fixed_bm25_rescues(payload: dict[str, object]) -> list[dict[str, object]]:
    computed = payload["systems"]["test"]["computed_ras"]["results"]
    bm25 = {row["id"]: row for row in payload["systems"]["test"]["always_bm25"]["results"]}
    rescues = []
    for row in computed:
        bm25_row = bm25[row["id"]]
        if (not row["answer_correct"] or not row["route_correct"]) and bm25_row["answer_correct"]:
            rescues.append(
                {
                    "id": row["id"],
                    "query": row["query"],
                    "route_family": row["route_family"],
                    "computed_predicted_backend": row["predicted_backend"],
                    "bm25_answer_correct": bm25_row["answer_correct"],
                    "computed_answer_correct": row["answer_correct"],
                    "computed_route_correct": row["route_correct"],
                }
            )
    return rescues


def _route_arbitration_payload(payload: dict[str, object]) -> dict[str, object]:
    rows = []
    for split, result in payload["public_robustness_systems"].items():
        for row in result["computed_ras_public_arbitrated"]["results"]:
            metadata = row.get("route_arbitration", {})
            if metadata.get("overrode_to_bm25"):
                rows.append(
                    {
                        "split": split,
                        "id": row["id"],
                        "query": row["query"],
                        "route_family": row["route_family"],
                        "normal_backend": metadata["normal_backend"],
                        "arbitrated_backend": metadata["selected_backend"],
                        "identifier_heavy": metadata["identifier_heavy"],
                        "lexical_confidence": metadata["lexical_confidence"],
                    }
                )
    return {
        "normal_computed_ras": {
            split: payload["systems"][split]["computed_ras"] for split in payload["systems"]
        },
        "public_arbitrated": {
            split: payload["public_robustness_systems"][split]["computed_ras_public_arbitrated"]
            for split in payload["public_robustness_systems"]
        },
        "overrides": rows,
        "policy": "Analysis-only override to BM25 only when the query is identifier-heavy and public lexical confidence is high.",
    }


def _tradeoffs(payload: dict[str, object]) -> list[str]:
    test_before_after = payload["before_after"]["test"]
    rows = [
        f"Public test answer accuracy improved from the Prompt 17 reference {PREVIOUS_PUBLIC_TEST_REFERENCE['computed_ras_answer_accuracy']:.3f} to current computed RAS {payload['systems']['test']['computed_ras']['answer_accuracy']:.3f}.",
        f"Public lexical arbitration improves test route accuracy from {test_before_after['baseline_route_accuracy']:.3f} to {test_before_after['public_arbitrated_route_accuracy']:.3f}.",
        "The main production-safe change is fixing substring marker false positives in feature parsing.",
        "The public lexical retriever and arbitration mode remain analysis-only and do not change the demo path by default.",
    ]
    return rows


def _write_failure_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "query",
                "route_family",
                "source_dataset_style",
                "source_types",
                "identifier_heavy",
                "predicted_backend",
                "route_correct",
                "answer_correct",
                "evidence_hit",
                "always_bm25_answer_correct",
                "bm25_gets_right_when_computed_wrong",
                "arbitrated_backend",
                "arbitrated_route_correct",
                "arbitrated_answer_correct",
                "buckets",
                "suggested_remediation",
            ],
        )
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            serialized["buckets"] = ",".join(row["buckets"])
            writer.writerow(serialized)


def _failure_markdown(payload: dict[str, object]) -> str:
    current_misses = [row for row in payload["rows"] if row["buckets"] != ["correct"]]
    lines = [
        "# Public Raw Failure Analysis",
        "",
        "## Current Test Metrics",
        "",
        f"- Current computed RAS answer accuracy: {payload['current_test_metrics']['answer_accuracy']:.3f} ({payload['current_test_metrics']['answer_correct']}/{payload['current_test_metrics']['total']}).",
        f"- Current computed RAS route accuracy: {payload['current_test_metrics']['route_accuracy']:.3f}.",
        f"- Current computed RAS evidence hit@k: {payload['current_test_metrics']['evidence_hit_at_k']:.3f}.",
        f"- Public arbitrated route accuracy: {payload['public_arbitrated_test_metrics']['route_accuracy']:.3f}.",
        "",
        "## Previous Prompt 17 Misses",
        "",
        *[
            f"- {row['id']}: `{row['query']}` previously predicted `{row['previous_predicted_backend']}`; buckets={row['previous_buckets']}; remediation={row['remediation']}"
            for row in payload["previous_prompt17_misses"]
        ],
        "",
        "## Current Non-Correct Buckets",
        "",
        *[
            f"- {row['id']}: family={row['route_family']}, predicted={row['predicted_backend']}, buckets={row['buckets']}, remediation={row['suggested_remediation']}"
            for row in current_misses
        ],
        "",
        "## Fixed BM25 Rescue Cases",
        "",
        *[
            f"- {row['id']}: computed predicted `{row['computed_predicted_backend']}`, always BM25 answered correctly."
            for row in payload["fixed_bm25_rescues"]
        ],
        "",
        "## Bucket Counts",
        "",
        *[f"- {bucket}: {count}" for bucket, count in payload["bucket_counts"].items()],
        "",
        "## Identifier Subgroups",
        "",
        *[
            f"- {name}: total={row['total']}, answer={row['answer_accuracy']:.3f}, route={row['route_accuracy']:.3f}, arbitrated_route={row['arbitrated_route_accuracy']:.3f}"
            for name, row in payload["identifier_subgroups"].items()
        ],
        "",
        "## Tradeoffs",
        "",
        *[f"- {item}" for item in payload["tradeoffs"]],
        "",
        "## Artifacts",
        "",
        f"- JSON: `{FAILURE_JSON}`",
        f"- CSV: `{FAILURE_CSV}`",
        f"- Markdown: `{FAILURE_MD}`",
        f"- Route arbitration: `{ARBITRATION_JSON}` and `{ARBITRATION_MD}`",
        f"- Robustness summary: `{ROBUSTNESS_MD}`",
        f"- Plot: `{BEFORE_AFTER_PLOT}`",
        f"- Plot: `{IDENTIFIER_PLOT}`",
        "",
    ]
    return "\n".join(lines)


def _route_arbitration_markdown(payload: dict[str, object]) -> str:
    test_normal = payload["normal_computed_ras"]["test"]
    test_arbitrated = payload["public_arbitrated"]["test"]
    lines = [
        "# Public Route Arbitration",
        "",
        f"Policy: {payload['policy']}",
        "",
        f"- Normal computed RAS test route accuracy: {test_normal['route_accuracy']:.3f}.",
        f"- Public-arbitrated test route accuracy: {test_arbitrated['route_accuracy']:.3f}.",
        f"- Normal computed RAS test answer accuracy: {test_normal['answer_accuracy']:.3f}.",
        f"- Public-arbitrated test answer accuracy: {test_arbitrated['answer_accuracy']:.3f}.",
        "",
        "## Overrides",
        "",
        *[
            f"- {row['split']} / {row['id']}: `{row['query']}` {row['normal_backend']} -> {row['arbitrated_backend']} with confidence {row['lexical_confidence'].get('confidence', 0.0):.3f}."
            for row in payload["overrides"]
        ],
        "",
    ]
    return "\n".join(lines)


def _robustness_markdown(payload: dict[str, object]) -> str:
    before = PREVIOUS_PUBLIC_TEST_REFERENCE
    current = payload["current_test_metrics"]
    arbitrated = payload["public_arbitrated_test_metrics"]
    verdict = "improved" if current["answer_accuracy"] > before["computed_ras_answer_accuracy"] else "stayed flat or worsened"
    lines = [
        "# Public Robustness Summary",
        "",
        f"- Previous public raw test answer accuracy: {before['computed_ras_answer_accuracy']:.3f}.",
        f"- Current computed RAS public raw test answer accuracy: {current['answer_accuracy']:.3f}.",
        f"- Public-arbitrated public raw test answer accuracy: {arbitrated['answer_accuracy']:.3f}.",
        f"- Before/after answer result: {verdict}.",
        f"- Previous public raw test route accuracy: {before['computed_ras_route_accuracy']:.3f}.",
        f"- Current computed RAS public raw test route accuracy: {current['route_accuracy']:.3f}.",
        f"- Public-arbitrated route accuracy: {arbitrated['route_accuracy']:.3f}.",
        "",
        "## What Changed",
        "",
        "- Feature parser marker matching now uses token boundaries to avoid accidental KG routing from substrings like `class` inside `dataclasses` or `eats` inside `threats`.",
        "- Public documents now have companion enriched metadata with identifiers, aliases, lead summaries, headings, source URLs, and fetch status.",
        "- Public-aware BM25 can boost title, alias, and identifier matches in public-corpus analysis mode.",
        "- Public route arbitration is analysis-only and only overrides to BM25 for identifier-heavy queries with high public lexical confidence.",
        "",
        "## Tradeoffs",
        "",
        *[f"- {item}" for item in payload["tradeoffs"]],
        "",
    ]
    return "\n".join(lines)


def _matplotlib_pyplot():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib_cache")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_before_after(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    labels = ["Prompt 17", "Current RAS", "Public Arbitrated", "Fixed BM25"]
    values = [
        PREVIOUS_PUBLIC_TEST_REFERENCE["computed_ras_answer_accuracy"],
        payload["current_test_metrics"]["answer_accuracy"],
        payload["public_arbitrated_test_metrics"]["answer_accuracy"],
        PREVIOUS_PUBLIC_TEST_REFERENCE["strongest_fixed_answer_accuracy"],
    ]
    _, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(labels, values, color=["#a0aec0", "#2b6cb0", "#38a169", "#d69e2e"])
    ax.set_title("Public raw test answer accuracy before/after")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_identifier_subgroups(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    groups = payload["identifier_subgroups"]
    labels = list(groups)
    route = [groups[label]["route_accuracy"] for label in labels]
    arbitrated = [groups[label]["arbitrated_route_accuracy"] for label in labels]
    x_positions = list(range(len(labels)))
    width = 0.36
    _, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar([x - width / 2 for x in x_positions], route, width, label="normal route")
    ax.bar([x + width / 2 for x in x_positions], arbitrated, width, label="public arbitrated route")
    ax.set_title("Identifier-heavy subgroup route accuracy")
    ax.set_ylabel("Route accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x_positions, labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze public raw-document benchmark failures and robustness.")
    parser.parse_args()
    payload = analyze_public_failures()
    current = payload["current_test_metrics"]
    arbitrated = payload["public_arbitrated_test_metrics"]
    print(
        "public_failure_analysis "
        f"current_answer_accuracy={current['answer_accuracy']:.3f} "
        f"current_route_accuracy={current['route_accuracy']:.3f} "
        f"arbitrated_route_accuracy={arbitrated['route_accuracy']:.3f} "
        f"json={FAILURE_JSON} csv={FAILURE_CSV} markdown={FAILURE_MD}"
    )
    for item in payload["tradeoffs"]:
        print(item)


if __name__ == "__main__":
    main()
