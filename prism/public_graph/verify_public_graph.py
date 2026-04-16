from __future__ import annotations

import argparse
import csv
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from prism.analysis.evaluation import answer_matches_gold
from prism.app.pipeline import answer_query
from prism.ingest.build_kg import build_kg
from prism.public_corpus.build_public_corpus import build_public_corpus
from prism.public_graph.benchmark_builder import build_public_structure_benchmark
from prism.public_graph.build_public_graph import (
    PUBLIC_GRAPH_METADATA_PATH,
    PUBLIC_GRAPH_PATH,
    PUBLIC_GRAPH_TTL_PATH,
    PUBLIC_MIXED_METADATA_PATH,
    StructureMode,
    build_public_graph,
    load_public_structure_triples,
)
from prism.public_graph.loaders import PublicStructureItem, load_public_structure_benchmark, public_structure_counts
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_json, read_jsonl_documents, write_json

STRUCTURE_MODES: tuple[StructureMode, ...] = ("demo_kg", "public_graph", "mixed_public_demo")
SYSTEMS = ("computed_ras", "always_kg", "always_hybrid")
SPLITS = ("dev", "test")
JSON_PATH = Path("data/eval/public_graph_eval.json")
CSV_PATH = Path("data/eval/public_graph_eval.csv")
MARKDOWN_PATH = Path("data/eval/public_graph_eval_summary.md")
MODE_PLOT = Path("data/eval/public_graph_mode_performance.png")
SPLIT_PLOT = Path("data/eval/public_graph_dev_test_modes.png")


def verify_public_graph(seed: int = 41) -> dict[str, object]:
    corpus_path = build_public_corpus()
    build_kg()
    public_graph_summary = build_public_graph(corpus_path)
    benchmark_path = build_public_structure_benchmark()

    documents = read_jsonl_documents(corpus_path)
    items = load_public_structure_benchmark(benchmark_path)
    retrievers_by_mode = {mode: _build_retrievers(documents, load_public_structure_triples(mode), mode) for mode in STRUCTURE_MODES}

    runs: dict[str, dict[str, dict[str, object]]] = {}
    for mode in STRUCTURE_MODES:
        runs[mode] = {}
        for split in SPLITS:
            split_items = [item for item in items if item.split == split]
            runs[mode][split] = {
                system: _evaluate_system(system, split_items, retrievers_by_mode[mode], seed=seed)
                for system in SYSTEMS
            }

    public_triples = load_public_structure_triples("public_graph")
    mixed_triples = load_public_structure_triples("mixed_public_demo")
    payload = {
        "seed": seed,
        "structure_modes": list(STRUCTURE_MODES),
        "systems": list(SYSTEMS),
        "public_graph": {
            **public_graph_summary,
            "triple_artifact": str(PUBLIC_GRAPH_PATH),
            "ttl_artifact": str(PUBLIC_GRAPH_TTL_PATH),
            "metadata_artifact": str(PUBLIC_GRAPH_METADATA_PATH),
        },
        "structure_artifacts": {
            "demo_kg": {"path": "data/processed/kg_triples.jsonl", "triple_count": len(load_public_structure_triples("demo_kg"))},
            "public_graph": {"path": str(PUBLIC_GRAPH_PATH), "triple_count": len(public_triples)},
            "mixed_public_demo": {
                "triple_count": len(mixed_triples),
                "metadata_path": str(PUBLIC_MIXED_METADATA_PATH),
            },
        },
        "benchmark": {
            "path": str(benchmark_path),
            "total": len(items),
            "counts": public_structure_counts(items),
            "note": "Public-structure benchmark is separate from curated, external, generalization_v2, and public raw-document benchmarks.",
        },
        "public_structure_grounding_coverage": _grounding_coverage(items, public_triples),
        "runs": runs,
        "mode_comparison": _mode_comparison(runs),
        "error_analysis": _error_analysis(runs),
        "takeaways": _takeaways(runs),
        "threats_to_validity": _threats_to_validity(),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    _plot_mode_performance(payload, MODE_PLOT)
    _plot_split_performance(payload, SPLIT_PLOT)
    return payload


def _build_retrievers(documents: list[Document], triples: list[Triple], mode: StructureMode) -> dict[str, object]:
    bm25 = BM25Retriever.build(documents)
    dense = DenseRetriever.build(documents)
    kg = KGRetriever.build(triples, kg_mode=mode)
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def _evaluate_system(
    system_name: str,
    items: list[PublicStructureItem],
    retrievers: dict[str, object],
    seed: int,
) -> dict[str, object]:
    rng = random.Random(seed)
    route_correct = 0
    answer_correct = 0
    evidence_hits = 0
    predicted_distribution: Counter[str] = Counter()
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0))
    rows: list[dict[str, object]] = []

    for item in items:
        backend = _select_backend(system_name, item.query, rng)
        payload = answer_query(
            item.query,
            top_k=5 if backend == "hybrid" else 3,
            retrievers=retrievers,
            backend_override=backend,
        )
        evidence = _payload_evidence(payload)
        evidence_ids = _evidence_id_set(evidence)
        route_ok = backend == item.route_family
        final_answer = str(payload["answer"]["final_answer"])
        answer_ok = answer_matches_gold(final_answer, item.gold_answer)
        evidence_ok = _evidence_hit(item, evidence, evidence_ids)

        route_correct += int(route_ok)
        answer_correct += int(answer_ok)
        evidence_hits += int(evidence_ok)
        predicted_distribution[backend] += 1
        family_counter = per_family[item.route_family]
        family_counter["total"] += 1
        family_counter["route_correct"] += int(route_ok)
        family_counter["answer_correct"] += int(answer_ok)
        family_counter["evidence_hits"] += int(evidence_ok)
        rows.append(
            {
                "id": item.id,
                "query": item.query,
                "split": item.split,
                "route_family": item.route_family,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": item.gold_answer,
                "answer": final_answer,
                "answer_correct": answer_ok,
                "gold_source_doc_ids": item.gold_source_doc_ids,
                "gold_triple_ids": item.gold_triple_ids,
                "gold_path_ids": item.gold_path_ids,
                "evidence_hit": evidence_ok,
                "top_evidence_ids": [row["item_id"] for row in payload["top_evidence"]],
                "top_evidence_modes": [
                    row.get("metadata", {}).get("kg_mode") or row.get("metadata", {}).get("fusion_method") or row.get("source_type")
                    for row in payload["top_evidence"]
                ],
                "top_evidence_sources": [
                    row.get("metadata", {}).get("source_doc_id")
                    or row.get("metadata", {}).get("kg_source_doc_id")
                    or row.get("metadata", {}).get("parent_doc_id")
                    for row in payload["top_evidence"]
                ],
            }
        )

    total = len(items)
    return {
        "system": system_name,
        "total": total,
        "route_accuracy": route_correct / total if total else 0.0,
        "answer_accuracy": answer_correct / total if total else 0.0,
        "evidence_hit_at_k": evidence_hits / total if total else 0.0,
        "route_correct": route_correct,
        "answer_correct": answer_correct,
        "evidence_hits": evidence_hits,
        "predicted_backend_distribution": dict(predicted_distribution),
        "per_family": _counter_breakdown(per_family),
        "results": rows,
    }


def _select_backend(system_name: str, query: str, rng: random.Random) -> str:
    if system_name == "computed_ras":
        return route_query(query).selected_backend
    if system_name == "always_kg":
        return "kg"
    if system_name == "always_hybrid":
        return "hybrid"
    if system_name == "random_router":
        return rng.choice(["kg", "hybrid"])
    raise ValueError(f"Unknown public-graph system: {system_name}")


def _payload_evidence(payload: dict[str, object]) -> list[RetrievedItem]:
    items: list[RetrievedItem] = []
    for row in payload["top_evidence"]:
        items.append(
            RetrievedItem(
                item_id=str(row["item_id"]),
                content=str(row["content"]),
                score=float(row["score"]),
                source_type=str(row["source_type"]),
                metadata=dict(row["metadata"]),
            )
        )
    return items


def _evidence_id_set(evidence: list[RetrievedItem]) -> set[str]:
    ids: set[str] = set()
    for item in evidence:
        ids.add(item.item_id)
        for key in (
            "component_ids",
            "triple_id",
            "path_id",
            "parent_doc_id",
            "chunk_id",
            "source_doc_id",
            "kg_source_doc_id",
        ):
            value = item.metadata.get(key, "")
            for part in str(value).split(","):
                if part:
                    ids.add(part)
    return ids


def _evidence_hit(item: PublicStructureItem, evidence: list[RetrievedItem], evidence_ids: set[str]) -> bool:
    gold_ids = set(item.gold_source_doc_ids) | set(item.gold_triple_ids) | set(item.gold_path_ids)
    if gold_ids & evidence_ids:
        return True
    text = " ".join([entry.content for entry in evidence] + sorted(evidence_ids))
    return _token_overlap(item.gold_evidence_text or item.gold_answer, text) >= 0.45


def _token_overlap(gold: str, observed: str) -> float:
    stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "yes", "no", "what"}
    gold_tokens = {token for token in re.findall(r"[a-z0-9_./:-]+", gold.lower()) if token not in stopwords}
    observed_tokens = set(re.findall(r"[a-z0-9_./:-]+", observed.lower()))
    if not gold_tokens:
        return 0.0
    return len(gold_tokens & observed_tokens) / len(gold_tokens)


def _counter_breakdown(counters: dict[str, Counter[str]]) -> dict[str, dict[str, object]]:
    return {
        family: {
            "total": counter["total"],
            "route_accuracy": counter["route_correct"] / counter["total"] if counter["total"] else 0.0,
            "answer_accuracy": counter["answer_correct"] / counter["total"] if counter["total"] else 0.0,
            "evidence_hit_at_k": counter["evidence_hits"] / counter["total"] if counter["total"] else 0.0,
            "route_correct": counter["route_correct"],
            "answer_correct": counter["answer_correct"],
            "evidence_hits": counter["evidence_hits"],
        }
        for family, counter in sorted(counters.items())
    }


def _grounding_coverage(items: list[PublicStructureItem], public_triples: list[Triple]) -> dict[str, object]:
    triple_ids = {triple.triple_id for triple in public_triples}
    source_doc_ids = {triple.source_doc_id for triple in public_triples}
    grounded = [
        item
        for item in items
        if set(item.gold_triple_ids).issubset(triple_ids) and set(item.gold_source_doc_ids).issubset(source_doc_ids)
    ]
    by_family: dict[str, dict[str, int]] = {}
    for item in items:
        row = by_family.setdefault(item.route_family, {"total": 0, "grounded": 0})
        row["total"] += 1
        row["grounded"] += int(item in grounded)
    return {
        "total": len(items),
        "grounded": len(grounded),
        "coverage": len(grounded) / len(items) if items else 0.0,
        "by_family": by_family,
    }


def _mode_comparison(runs: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    comparison: dict[str, object] = {}
    for split in SPLITS:
        demo = runs["demo_kg"][split]["computed_ras"]
        public = runs["public_graph"][split]["computed_ras"]
        mixed = runs["mixed_public_demo"][split]["computed_ras"]
        comparison[split] = {
            "demo_kg_answer_accuracy": demo["answer_accuracy"],
            "public_graph_answer_accuracy": public["answer_accuracy"],
            "mixed_public_demo_answer_accuracy": mixed["answer_accuracy"],
            "public_graph_answer_delta_vs_demo": public["answer_accuracy"] - demo["answer_accuracy"],
            "mixed_answer_delta_vs_demo": mixed["answer_accuracy"] - demo["answer_accuracy"],
            "public_graph_evidence_delta_vs_demo": public["evidence_hit_at_k"] - demo["evidence_hit_at_k"],
            "mixed_evidence_delta_vs_demo": mixed["evidence_hit_at_k"] - demo["evidence_hit_at_k"],
            "per_family": _family_mode_delta(demo["per_family"], public["per_family"], mixed["per_family"]),
        }
    return comparison


def _family_mode_delta(
    demo: dict[str, dict[str, object]],
    public: dict[str, dict[str, object]],
    mixed: dict[str, dict[str, object]],
) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for family in sorted(set(demo) | set(public) | set(mixed)):
        demo_answer = float(demo.get(family, {}).get("answer_accuracy", 0.0))
        public_answer = float(public.get(family, {}).get("answer_accuracy", 0.0))
        mixed_answer = float(mixed.get(family, {}).get("answer_accuracy", 0.0))
        rows[family] = {
            "demo_answer_accuracy": demo_answer,
            "public_graph_answer_accuracy": public_answer,
            "mixed_public_demo_answer_accuracy": mixed_answer,
            "public_graph_delta_vs_demo": public_answer - demo_answer,
            "mixed_delta_vs_demo": mixed_answer - demo_answer,
        }
    return rows


def _error_analysis(runs: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    bucket_counts: Counter[str] = Counter()
    examples: list[dict[str, object]] = []
    for mode in STRUCTURE_MODES:
        for split in SPLITS:
            for row in runs[mode][split]["computed_ras"]["results"]:
                if row["answer_correct"] and row["evidence_hit"]:
                    continue
                buckets = _error_buckets(mode, row)
                bucket_counts.update(buckets)
                examples.append(
                    {
                        "structure_mode": mode,
                        "split": split,
                        "id": row["id"],
                        "query": row["query"],
                        "route_family": row["route_family"],
                        "answer_correct": row["answer_correct"],
                        "evidence_hit": row["evidence_hit"],
                        "buckets": buckets,
                        "top_evidence_ids": row["top_evidence_ids"][:3],
                    }
                )
    return {"bucket_counts": dict(sorted(bucket_counts.items())), "examples": examples[:30]}


def _error_buckets(mode: StructureMode, row: dict[str, object]) -> list[str]:
    buckets: list[str] = []
    if not row["evidence_hit"]:
        buckets.append("public graph incompleteness" if mode == "public_graph" else "structure evidence miss")
    if not row["answer_correct"]:
        buckets.append("answer mismatch under public structure")
    query = str(row["query"]).lower()
    if any(term in query for term in ("bridge", "connect", "through", "relation")):
        buckets.append("relational path degradation")
    if any(term in query for term in ("all ", "able to", "not", "counterexample")):
        buckets.append("quantifier or negation handling")
    if any(term in query for term in ("vertebrate", "mammal", "bird", "animal")):
        buckets.append("alias or class normalization")
    return buckets or ["unclassified public-structure miss"]


def _takeaways(runs: dict[str, dict[str, dict[str, object]]]) -> list[str]:
    rows: list[str] = []
    for split in SPLITS:
        demo = runs["demo_kg"][split]["computed_ras"]
        public = runs["public_graph"][split]["computed_ras"]
        mixed = runs["mixed_public_demo"][split]["computed_ras"]
        if public["answer_accuracy"] < demo["answer_accuracy"]:
            verdict = "degrades versus demo KG"
        elif public["answer_accuracy"] > demo["answer_accuracy"]:
            verdict = "improves versus demo KG on this public-structure suite"
        else:
            verdict = "matches demo KG"
        recovery = mixed["answer_accuracy"] - public["answer_accuracy"]
        rows.append(
            f"{split}: demo_kg={demo['answer_accuracy']:.3f}, public_graph={public['answer_accuracy']:.3f}, "
            f"mixed_public_demo={mixed['answer_accuracy']:.3f}; public graph {verdict}, mixed-minus-public={recovery:.3f}."
        )
    rows.append("Curated demo KG remains the production default; public_graph and mixed_public_demo are analysis modes.")
    return rows


def _threats_to_validity() -> list[str]:
    return [
        "The public graph is produced by lightweight rule/profile extraction, not a full information-extraction system.",
        "The public graph is small and source-selected, so it tests structure shift but not web-scale graph construction.",
        "Entity and relation normalization use controlled aliases and predicates that can miss public-text paraphrases.",
        "Public raw text is noisier than compact benchmark facts, and some facts may be absent after cleaning.",
        "Mixed public+demo performance should be interpreted as robustness with curated support still present, not solved public graph extraction.",
        "Answer matching is normalized string matching rather than human grading.",
    ]


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "structure_mode",
                "split",
                "system",
                "total",
                "route_accuracy",
                "answer_accuracy",
                "evidence_hit_at_k",
                "route_correct",
                "answer_correct",
                "evidence_hits",
                "predicted_backend_distribution",
            ],
        )
        writer.writeheader()
        for mode, splits in payload["runs"].items():
            for split, systems in splits.items():
                for system, row in systems.items():
                    writer.writerow(
                        {
                            "structure_mode": mode,
                            "split": split,
                            "system": system,
                            "total": row["total"],
                            "route_accuracy": row["route_accuracy"],
                            "answer_accuracy": row["answer_accuracy"],
                            "evidence_hit_at_k": row["evidence_hit_at_k"],
                            "route_correct": row["route_correct"],
                            "answer_correct": row["answer_correct"],
                            "evidence_hits": row["evidence_hits"],
                            "predicted_backend_distribution": row["predicted_backend_distribution"],
                        }
                    )


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Public Graph Structural Grounding Evaluation",
        "",
        "This evaluation compares PRISM's current demo KG with a graph extracted from public raw-document text and a mixed public+demo mode. The production demo default is unchanged.",
        "",
        "## Public Graph",
        "",
        f"- Public graph triples: {payload['public_graph']['total']}.",
        f"- Source documents represented: {payload['public_graph']['source_doc_count']}.",
        f"- Triple artifact: `{payload['public_graph']['triple_artifact']}`.",
        f"- Turtle artifact: `{payload['public_graph']['ttl_artifact']}`.",
        f"- Metadata artifact: `{payload['public_graph']['metadata_artifact']}`.",
        f"- Extraction patterns: {payload['public_graph']['patterns']}.",
        "",
        "## Benchmark",
        "",
        f"- Benchmark path: `{payload['benchmark']['path']}`.",
        f"- Benchmark total: {payload['benchmark']['total']}.",
        f"- Benchmark counts: {payload['benchmark']['counts']}.",
        f"- Public-structure grounding coverage: {payload['public_structure_grounding_coverage']}.",
        "",
        "## Computed RAS Results By Structure Mode",
        "",
    ]
    for split in SPLITS:
        lines.extend([f"### {split.title()} Split", ""])
        for mode in STRUCTURE_MODES:
            row = payload["runs"][mode][split]["computed_ras"]
            lines.append(
                f"- {mode}: answer_accuracy={row['answer_accuracy']:.3f} ({row['answer_correct']}/{row['total']}), "
                f"evidence_hit@k={row['evidence_hit_at_k']:.3f}, route_accuracy={row['route_accuracy']:.3f}, "
                f"distribution={row['predicted_backend_distribution']}."
            )
        lines.append("")
    lines.extend(["## Demo KG Vs Public Graph Vs Mixed", ""])
    for split, row in payload["mode_comparison"].items():
        lines.append(
            f"- {split}: public_graph answer delta vs demo={row['public_graph_answer_delta_vs_demo']:.3f}; "
            f"mixed answer delta vs demo={row['mixed_answer_delta_vs_demo']:.3f}; "
            f"public evidence delta={row['public_graph_evidence_delta_vs_demo']:.3f}."
        )
        for family, family_row in row["per_family"].items():
            lines.append(
                f"- {split}/{family}: demo={family_row['demo_answer_accuracy']:.3f}, "
                f"public={family_row['public_graph_answer_accuracy']:.3f}, "
                f"mixed={family_row['mixed_public_demo_answer_accuracy']:.3f}."
            )
    lines.extend(
        [
            "",
            "## Error Analysis",
            "",
            f"- Error buckets: {payload['error_analysis']['bucket_counts']}.",
            "- Public-graph-only errors, if present, are interpreted as structural brittleness rather than hidden by benchmark edits.",
            "",
            "## Main Takeaways",
            "",
            *[f"- {item}" for item in payload["takeaways"]],
            "",
            "## Threats To Validity",
            "",
            *[f"- {item}" for item in payload["threats_to_validity"]],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{JSON_PATH}`",
            f"- CSV: `{CSV_PATH}`",
            f"- Markdown: `{MARKDOWN_PATH}`",
            f"- Plot: `{MODE_PLOT}`",
            f"- Plot: `{SPLIT_PLOT}`",
            "",
        ]
    )
    return "\n".join(lines)


def _matplotlib_pyplot():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib_cache")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_mode_performance(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    split = "test"
    modes = list(STRUCTURE_MODES)
    families = ["overall", "kg", "hybrid"]
    x_positions = list(range(len(families)))
    width = 0.24
    _, ax = plt.subplots(figsize=(8.5, 4.6))
    for index, mode in enumerate(modes):
        row = payload["runs"][mode][split]["computed_ras"]
        values = [row["answer_accuracy"]] + [
            row["per_family"].get(family, {"answer_accuracy": 0.0})["answer_accuracy"] for family in families[1:]
        ]
        offsets = [x + (index - 1) * width for x in x_positions]
        ax.bar(offsets, values, width, label=mode)
    ax.set_title("Public-structure test answer accuracy by structure mode")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x_positions, families)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_split_performance(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    labels = [f"{mode}\n{split}" for mode in STRUCTURE_MODES for split in SPLITS]
    values = [payload["runs"][mode][split]["computed_ras"]["answer_accuracy"] for mode in STRUCTURE_MODES for split in SPLITS]
    _, ax = plt.subplots(figsize=(9, 4.6))
    ax.bar(labels, values, color=["#2b6cb0", "#63b3ed"] * len(STRUCTURE_MODES))
    ax.set_title("Public-structure dev/test answer accuracy")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate public graph structure grounding modes.")
    parser.add_argument("--seed", type=int, default=41)
    args = parser.parse_args()
    payload = verify_public_graph(seed=args.seed)
    test = payload["runs"]["public_graph"]["test"]["computed_ras"]
    print(
        "public_graph_eval "
        f"triples={payload['public_graph']['total']} "
        f"benchmark_total={payload['benchmark']['total']} "
        f"test_public_graph_answer_accuracy={test['answer_accuracy']:.3f} "
        f"test_public_graph_evidence_hit_at_k={test['evidence_hit_at_k']:.3f} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
