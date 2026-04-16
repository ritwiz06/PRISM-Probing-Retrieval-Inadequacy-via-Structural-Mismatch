from __future__ import annotations

import argparse
from pathlib import Path

from prism.public_graph.verify_public_graph import JSON_PATH as PUBLIC_GRAPH_JSON
from prism.public_graph.verify_public_graph import verify_public_graph
from prism.utils import read_json, write_json

JSON_PATH = Path("data/eval/public_structure_comparison.json")
MARKDOWN_PATH = Path("data/eval/public_structure_comparison_summary.md")


def compare_structure_grounding() -> dict[str, object]:
    if not PUBLIC_GRAPH_JSON.exists():
        verify_public_graph()
    public_graph = read_json(PUBLIC_GRAPH_JSON)
    comparison = {
        split: _compare_split(public_graph["runs"], split)
        for split in ("dev", "test")
    }
    payload = {
        "source": str(PUBLIC_GRAPH_JSON),
        "structure_modes": public_graph["structure_modes"],
        "benchmark_total": public_graph["benchmark"]["total"],
        "public_graph_triples": public_graph["public_graph"]["total"],
        "comparison": comparison,
        "interpretation": _interpretation(comparison),
        "threats_to_validity": public_graph["threats_to_validity"],
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    return payload


def _compare_split(runs: dict[str, object], split: str) -> dict[str, object]:
    demo = runs["demo_kg"][split]["computed_ras"]
    public = runs["public_graph"][split]["computed_ras"]
    mixed = runs["mixed_public_demo"][split]["computed_ras"]
    return {
        "demo_kg_answer_accuracy": demo["answer_accuracy"],
        "public_graph_answer_accuracy": public["answer_accuracy"],
        "mixed_public_demo_answer_accuracy": mixed["answer_accuracy"],
        "public_graph_delta_vs_demo": public["answer_accuracy"] - demo["answer_accuracy"],
        "mixed_public_demo_delta_vs_demo": mixed["answer_accuracy"] - demo["answer_accuracy"],
        "mixed_public_demo_delta_vs_public_graph": mixed["answer_accuracy"] - public["answer_accuracy"],
        "demo_kg_evidence_hit_at_k": demo["evidence_hit_at_k"],
        "public_graph_evidence_hit_at_k": public["evidence_hit_at_k"],
        "mixed_public_demo_evidence_hit_at_k": mixed["evidence_hit_at_k"],
        "public_graph_evidence_delta_vs_demo": public["evidence_hit_at_k"] - demo["evidence_hit_at_k"],
        "mixed_evidence_delta_vs_public_graph": mixed["evidence_hit_at_k"] - public["evidence_hit_at_k"],
        "per_family": _per_family_delta(demo["per_family"], public["per_family"], mixed["per_family"]),
    }


def _per_family_delta(
    demo: dict[str, dict[str, object]],
    public: dict[str, dict[str, object]],
    mixed: dict[str, dict[str, object]],
) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for family in sorted(set(demo) | set(public) | set(mixed)):
        demo_answer = float(demo.get(family, {}).get("answer_accuracy", 0.0))
        public_answer = float(public.get(family, {}).get("answer_accuracy", 0.0))
        mixed_answer = float(mixed.get(family, {}).get("answer_accuracy", 0.0))
        demo_evidence = float(demo.get(family, {}).get("evidence_hit_at_k", 0.0))
        public_evidence = float(public.get(family, {}).get("evidence_hit_at_k", 0.0))
        mixed_evidence = float(mixed.get(family, {}).get("evidence_hit_at_k", 0.0))
        rows[family] = {
            "demo_answer_accuracy": demo_answer,
            "public_graph_answer_accuracy": public_answer,
            "mixed_public_demo_answer_accuracy": mixed_answer,
            "public_graph_answer_delta_vs_demo": public_answer - demo_answer,
            "mixed_answer_delta_vs_demo": mixed_answer - demo_answer,
            "mixed_answer_delta_vs_public_graph": mixed_answer - public_answer,
            "demo_evidence_hit_at_k": demo_evidence,
            "public_graph_evidence_hit_at_k": public_evidence,
            "mixed_public_demo_evidence_hit_at_k": mixed_evidence,
        }
    return rows


def _interpretation(comparison: dict[str, dict[str, object]]) -> list[str]:
    rows: list[str] = []
    for split, row in comparison.items():
        public_delta = row["public_graph_delta_vs_demo"]
        mixed_delta = row["mixed_public_demo_delta_vs_public_graph"]
        if public_delta < 0:
            public_statement = f"public_graph-only degrades by {public_delta:.3f} answer accuracy versus demo_kg"
        elif public_delta > 0:
            public_statement = f"public_graph-only improves by {public_delta:.3f} answer accuracy versus demo_kg"
        else:
            public_statement = "public_graph-only matches demo_kg answer accuracy"
        if mixed_delta > 0:
            mixed_statement = f"mixed_public_demo recovers {mixed_delta:.3f} over public_graph-only"
        elif mixed_delta < 0:
            mixed_statement = f"mixed_public_demo drops {mixed_delta:.3f} versus public_graph-only"
        else:
            mixed_statement = "mixed_public_demo matches public_graph-only"
        rows.append(f"{split}: {public_statement}; {mixed_statement}.")
    rows.append("These deltas compare structure modes on a public-graph-grounded suite; they are not a claim that rule-based extraction solves arbitrary public KG construction.")
    return rows


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Public Structure Grounding Comparison",
        "",
        f"Source evaluation: `{payload['source']}`.",
        f"Public graph triples: {payload['public_graph_triples']}.",
        f"Benchmark total: {payload['benchmark_total']}.",
        "",
        "## Structure-Mode Comparison",
        "",
    ]
    for split, row in payload["comparison"].items():
        lines.extend(
            [
                f"### {split.title()} Split",
                "",
                f"- Demo KG answer accuracy: {row['demo_kg_answer_accuracy']:.3f}.",
                f"- Public graph answer accuracy: {row['public_graph_answer_accuracy']:.3f}.",
                f"- Mixed public+demo answer accuracy: {row['mixed_public_demo_answer_accuracy']:.3f}.",
                f"- Public graph delta vs demo: {row['public_graph_delta_vs_demo']:.3f}.",
                f"- Mixed delta vs public graph: {row['mixed_public_demo_delta_vs_public_graph']:.3f}.",
                "",
            ]
        )
        for family, family_row in row["per_family"].items():
            lines.append(
                f"- {split}/{family}: demo={family_row['demo_answer_accuracy']:.3f}, "
                f"public={family_row['public_graph_answer_accuracy']:.3f}, "
                f"mixed={family_row['mixed_public_demo_answer_accuracy']:.3f}."
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            *[f"- {item}" for item in payload["interpretation"]],
            "",
            "## Threats To Validity",
            "",
            *[f"- {item}" for item in payload["threats_to_validity"]],
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
    parser = argparse.ArgumentParser(description="Compare demo KG, public graph, and mixed public+demo structure modes.")
    parser.parse_args()
    payload = compare_structure_grounding()
    test = payload["comparison"]["test"]
    print(
        "public_structure_comparison "
        f"test_public_delta_vs_demo={test['public_graph_delta_vs_demo']:.3f} "
        f"test_mixed_delta_vs_public={test['mixed_public_demo_delta_vs_public_graph']:.3f} "
        f"json={JSON_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["interpretation"]:
        print(item)


if __name__ == "__main__":
    main()
