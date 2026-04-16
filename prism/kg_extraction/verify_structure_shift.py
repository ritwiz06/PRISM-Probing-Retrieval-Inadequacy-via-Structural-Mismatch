from __future__ import annotations

import argparse
import csv
import os
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from prism.analysis.evaluation import answer_matches_gold, evidence_id_set
from prism.app.pipeline import answer_query
from prism.config import load_config
from prism.eval.deductive_slice import load_deductive_queries
from prism.eval.relational_slice import load_relational_queries
from prism.generalization.benchmark_builder import build_generalization_benchmark
from prism.generalization.loaders import load_generalization_benchmark
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.kg_extraction.build_extracted_kg import (
    KGMode,
    build_extracted_kg,
    load_kg_triples_for_mode,
)
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_jsonl_documents, write_json

KG_MODES: tuple[KGMode, ...] = ("curated", "extracted", "mixed")
SYSTEMS = ("computed_ras", "always_kg", "always_hybrid")
JSON_PATH = Path("data/eval/structure_shift.json")
CSV_PATH = Path("data/eval/structure_shift.csv")
MARKDOWN_PATH = Path("data/eval/structure_shift_summary.md")
MODE_PLOT = Path("data/eval/structure_shift_kg_modes.png")
DEGRADATION_PLOT = Path("data/eval/structure_shift_degradation.png")


def verify_structure_shift() -> dict[str, object]:
    corpus_path = build_corpus()
    build_kg(corpus_path=str(corpus_path))
    extracted_summary = build_extracted_kg(corpus_path)
    build_generalization_benchmark()
    documents = read_jsonl_documents(corpus_path)
    datasets = _structure_items()
    retrievers_by_mode = {mode: _build_retrievers_for_kg_mode(documents, mode) for mode in KG_MODES}

    runs: dict[str, dict[str, dict[str, object]]] = {}
    for mode in KG_MODES:
        runs[mode] = {}
        for dataset_name, items in datasets.items():
            runs[mode][dataset_name] = {
                system: _evaluate_system(system, items, retrievers_by_mode[mode])
                for system in SYSTEMS
            }

    deltas = _mode_deltas(runs)
    payload = {
        "kg_modes": list(KG_MODES),
        "systems_evaluated": list(SYSTEMS),
        "kg_artifacts": {
            "curated": {"path": "data/processed/kg_triples.jsonl", "triple_count": len(load_kg_triples_for_mode("curated"))},
            "extracted": extracted_summary,
            "mixed": {"triple_count": len(load_kg_triples_for_mode("mixed")), "metadata_path": "data/processed/kg_mixed_metadata.json"},
        },
        "datasets": {name: {"total": len(items), "families": dict(Counter(item["family"] for item in items))} for name, items in datasets.items()},
        "runs": runs,
        "mode_deltas": deltas,
        "error_analysis": _error_analysis(runs),
        "takeaways": _takeaways(runs, deltas),
        "threats_to_validity": _threats_to_validity(),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    _plot_mode_performance(payload, MODE_PLOT)
    _plot_degradation(payload, DEGRADATION_PLOT)
    return payload


def _build_retrievers_for_kg_mode(documents: list[Document], mode: KGMode) -> dict[str, object]:
    config = load_config()
    triples = load_kg_triples_for_mode(mode)
    bm25 = BM25Retriever.build(documents)
    dense = DenseRetriever.build(documents, config=config.retrieval)
    kg = KGRetriever.build(triples, kg_mode=mode)
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def _structure_items() -> dict[str, list[dict[str, object]]]:
    datasets: dict[str, list[dict[str, object]]] = {
        "curated_deductive": [],
        "curated_relational": [],
        "generalization_v2_deductive": [],
        "generalization_v2_relational": [],
    }
    for index, item in enumerate(load_deductive_queries()):
        row = asdict(item)
        row.update({"id": f"curated_deductive_{index:03d}", "dataset": "curated_deductive", "family": "deductive"})
        datasets["curated_deductive"].append(row)
    for index, item in enumerate(load_relational_queries()):
        row = asdict(item)
        row.update({"id": f"curated_relational_{index:03d}", "dataset": "curated_relational", "family": "relational"})
        datasets["curated_relational"].append(row)
    for item in load_generalization_benchmark():
        if item.route_family == "kg":
            datasets["generalization_v2_deductive"].append(
                {
                    "id": item.id,
                    "dataset": "generalization_v2_deductive",
                    "family": "deductive",
                    "query": item.query,
                    "gold_route": item.route_family,
                    "gold_answer": item.gold_answer,
                    "gold_evidence_ids": [],
                    "gold_evidence_text": item.gold_evidence_text,
                    "split": item.split,
                }
            )
        if item.route_family == "hybrid":
            datasets["generalization_v2_relational"].append(
                {
                    "id": item.id,
                    "dataset": "generalization_v2_relational",
                    "family": "relational",
                    "query": item.query,
                    "gold_route": item.route_family,
                    "gold_answer": item.gold_answer,
                    "gold_evidence_ids": [],
                    "gold_evidence_text": item.gold_evidence_text,
                    "split": item.split,
                }
            )
    return datasets


def _evaluate_system(system: str, items: list[dict[str, object]], retrievers: dict[str, object]) -> dict[str, object]:
    route_correct = 0
    answer_correct = 0
    evidence_hits = 0
    predicted_distribution: Counter[str] = Counter()
    rows: list[dict[str, object]] = []
    for item in items:
        backend = _select_backend(system, str(item["query"]))
        payload = answer_query(
            str(item["query"]),
            top_k=5 if backend == "hybrid" else 3,
            retrievers=retrievers,
            backend_override=backend,
        )
        evidence = _payload_evidence(payload)
        evidence_ids = evidence_id_set(evidence)
        route_ok = backend == item["gold_route"]
        answer_ok = answer_matches_gold(str(payload["answer"]["final_answer"]), str(item["gold_answer"]))
        evidence_ok = _evidence_hit(item, evidence, evidence_ids)
        route_correct += int(route_ok)
        answer_correct += int(answer_ok)
        evidence_hits += int(evidence_ok)
        predicted_distribution[backend] += 1
        rows.append(
            {
                "id": item["id"],
                "dataset": item["dataset"],
                "family": item["family"],
                "query": item["query"],
                "gold_route": item["gold_route"],
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": item["gold_answer"],
                "answer": payload["answer"]["final_answer"],
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "top_evidence_ids": [row["item_id"] for row in payload["top_evidence"]],
                "top_evidence_modes": [row["metadata"].get("kg_mode") or row["metadata"].get("contributing_backends") for row in payload["top_evidence"]],
            }
        )
    total = len(items)
    return {
        "system": system,
        "total": total,
        "route_accuracy": route_correct / total if total else 0.0,
        "answer_accuracy": answer_correct / total if total else 0.0,
        "evidence_hit_at_k": evidence_hits / total if total else 0.0,
        "route_correct": route_correct,
        "answer_correct": answer_correct,
        "evidence_hits": evidence_hits,
        "predicted_backend_distribution": dict(predicted_distribution),
        "results": rows,
    }


def _select_backend(system: str, query: str) -> str:
    if system == "computed_ras":
        return route_query(query).selected_backend
    if system == "always_kg":
        return "kg"
    if system == "always_hybrid":
        return "hybrid"
    raise ValueError(f"Unknown structure-shift system: {system}")


def _payload_evidence(payload: dict[str, object]) -> list[RetrievedItem]:
    items: list[RetrievedItem] = []
    for row in payload["top_evidence"]:
        items.append(
            RetrievedItem(
                item_id=row["item_id"],
                content=row["content"],
                score=float(row["score"]),
                source_type=row["source_type"],
                metadata=row["metadata"],
            )
        )
    return items


def _evidence_hit(item: dict[str, object], evidence: list[RetrievedItem], evidence_ids: set[str]) -> bool:
    gold_ids = {str(value) for value in item.get("gold_evidence_ids", [])}
    if gold_ids and bool(gold_ids & evidence_ids):
        return True
    evidence_text = " ".join([entry.content for entry in evidence] + sorted(evidence_ids))
    gold_text = f"{item.get('gold_evidence_text', '')} {item.get('gold_answer', '')}"
    return _token_overlap(gold_text, evidence_text) >= 0.45


def _token_overlap(gold: str, observed: str) -> float:
    stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "yes", "no", "through", "plus"}
    gold_tokens = {token for token in _tokens(gold) if token not in stopwords}
    observed_tokens = set(_tokens(observed))
    if not gold_tokens:
        return 0.0
    return len(gold_tokens & observed_tokens) / len(gold_tokens)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _mode_deltas(runs: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    deltas: dict[str, object] = {}
    for dataset in runs["curated"]:
        curated = runs["curated"][dataset]["computed_ras"]
        deltas[dataset] = {}
        for mode in ("extracted", "mixed"):
            row = runs[mode][dataset]["computed_ras"]
            deltas[dataset][mode] = {
                "answer_delta": row["answer_accuracy"] - curated["answer_accuracy"],
                "evidence_delta": row["evidence_hit_at_k"] - curated["evidence_hit_at_k"],
                "curated_answer_accuracy": curated["answer_accuracy"],
                "mode_answer_accuracy": row["answer_accuracy"],
            }
    return deltas


def _error_analysis(runs: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    buckets: Counter[str] = Counter()
    examples: list[dict[str, object]] = []
    for mode in ("extracted", "mixed"):
        for dataset, systems in runs[mode].items():
            for row in systems["computed_ras"]["results"]:
                if row["answer_correct"] and row["evidence_hit"]:
                    continue
                assigned = _error_buckets(row, mode)
                buckets.update(assigned)
                examples.append(
                    {
                        "kg_mode": mode,
                        "dataset": dataset,
                        "id": row["id"],
                        "query": row["query"],
                        "buckets": assigned,
                        "answer_correct": row["answer_correct"],
                        "evidence_hit": row["evidence_hit"],
                        "top_evidence_ids": row["top_evidence_ids"][:3],
                    }
                )
    return {"bucket_counts": dict(sorted(buckets.items())), "examples": examples[:20]}


def _error_buckets(row: dict[str, object], mode: str) -> list[str]:
    buckets: list[str] = []
    if not row["evidence_hit"]:
        buckets.append("KG incompleteness" if mode == "extracted" else "relational path degradation")
    if not row["answer_correct"]:
        buckets.append("extraction noise" if mode == "extracted" else "answer mismatch under mixed evidence")
    query = str(row["query"]).lower()
    if any(term in query for term in ("all ", "able to", "not", "counterexample")):
        buckets.append("relation normalization failures")
    if any(term in query for term in ("sparrow", "mosquito", "amphibian", "vertebrate")):
        buckets.append("alias normalization failures")
    return buckets or ["unclassified structure-shift miss"]


def _takeaways(runs: dict[str, dict[str, dict[str, object]]], deltas: dict[str, object]) -> list[str]:
    rows: list[str] = []
    for dataset in runs["curated"]:
        curated = runs["curated"][dataset]["computed_ras"]
        extracted = runs["extracted"][dataset]["computed_ras"]
        mixed = runs["mixed"][dataset]["computed_ras"]
        rows.append(
            f"{dataset}: curated={curated['answer_accuracy']:.3f}, "
            f"extracted={extracted['answer_accuracy']:.3f}, mixed={mixed['answer_accuracy']:.3f} answer accuracy."
        )
    worst = min(
        ((dataset, mode, row["answer_delta"]) for dataset, modes in deltas.items() for mode, row in modes.items()),
        key=lambda item: item[2],
    )
    rows.append(f"Largest answer degradation is {worst[2]:.3f} for {worst[1]} on {worst[0]}.")
    rows.append("Curated KG remains the production default; extracted and mixed KG modes are analysis-only.")
    return rows


def _threats_to_validity() -> list[str]:
    return [
        "The extracted KG is rule-based and intentionally lightweight, not a full information-extraction system.",
        "Extraction is limited to patterns visible in the local corpus, so missing text causes missing triples.",
        "Relation normalization uses a small controlled predicate set and can miss paraphrases.",
        "Alias normalization is heuristic and handles only common demo entities.",
        "Curated and held-out benchmarks are grounded in local artifacts, not arbitrary web-scale evidence.",
    ]


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "kg_mode",
                "dataset",
                "system",
                "total",
                "route_accuracy",
                "answer_accuracy",
                "evidence_hit_at_k",
                "route_correct",
                "answer_correct",
                "evidence_hits",
            ],
        )
        writer.writeheader()
        for mode, datasets in payload["runs"].items():
            for dataset, systems in datasets.items():
                for system, row in systems.items():
                    writer.writerow(
                        {
                            "kg_mode": mode,
                            "dataset": dataset,
                            "system": system,
                            "total": row["total"],
                            "route_accuracy": row["route_accuracy"],
                            "answer_accuracy": row["answer_accuracy"],
                            "evidence_hit_at_k": row["evidence_hit_at_k"],
                            "route_correct": row["route_correct"],
                            "answer_correct": row["answer_correct"],
                            "evidence_hits": row["evidence_hits"],
                        }
                    )


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Structure-Shift Evaluation Summary",
        "",
        "This evaluation compares curated, extracted, and mixed KG modes without changing the production curated KG default.",
        "",
        "## KG Artifacts",
        "",
        f"- Curated KG: `{payload['kg_artifacts']['curated']['path']}` with {payload['kg_artifacts']['curated']['triple_count']} triples.",
        f"- Extracted KG: `{payload['kg_artifacts']['extracted']['path']}` with {payload['kg_artifacts']['extracted']['total']} triples.",
        f"- Mixed KG: {payload['kg_artifacts']['mixed']['triple_count']} triples with provenance at `{payload['kg_artifacts']['mixed']['metadata_path']}`.",
        "",
        "## Computed RAS By KG Mode",
        "",
    ]
    for mode, datasets in payload["runs"].items():
        lines.extend([f"### {mode.title()} KG", ""])
        for dataset, systems in datasets.items():
            row = systems["computed_ras"]
            lines.append(
                f"- {dataset}: answer_accuracy={row['answer_accuracy']:.3f} ({row['answer_correct']}/{row['total']}), "
                f"evidence_hit@k={row['evidence_hit_at_k']:.3f}, route_accuracy={row['route_accuracy']:.3f}."
            )
        lines.append("")
    lines.extend(["## Curated Vs Extracted Vs Mixed Delta", ""])
    for dataset, modes in payload["mode_deltas"].items():
        for mode, row in modes.items():
            lines.append(
                f"- {dataset}/{mode}: answer_delta={row['answer_delta']:.3f}, evidence_delta={row['evidence_delta']:.3f}."
            )
    lines.extend(
        [
            "",
            "## Error Analysis",
            "",
            f"- Error buckets: {payload['error_analysis']['bucket_counts']}.",
            "- Common failure modes include KG incompleteness, extraction noise, alias normalization failures, relation normalization failures, and relational path degradation.",
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
            f"- Plot: `{DEGRADATION_PLOT}`",
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
    datasets = list(payload["runs"]["curated"])
    modes = list(KG_MODES)
    x_positions = list(range(len(datasets)))
    width = 0.24
    _, ax = plt.subplots(figsize=(10, 4.8))
    for index, mode in enumerate(modes):
        values = [payload["runs"][mode][dataset]["computed_ras"]["answer_accuracy"] for dataset in datasets]
        offsets = [x + (index - 1) * width for x in x_positions]
        ax.bar(offsets, values, width, label=mode)
    ax.set_title("Computed RAS answer accuracy by KG mode")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x_positions, datasets, rotation=20, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_degradation(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    labels: list[str] = []
    values: list[float] = []
    for dataset, modes in payload["mode_deltas"].items():
        for mode, row in modes.items():
            labels.append(f"{dataset}\n{mode}")
            values.append(row["answer_delta"])
    _, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(labels, values, color=["#d95f02" if value < 0 else "#1b9e77" for value in values])
    ax.set_title("Answer accuracy delta vs curated KG")
    ax.set_ylabel("Delta")
    ax.tick_params(axis="x", rotation=25)
    ax.axhline(0.0, color="#333333", linewidth=1)
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRISM under curated/extracted/mixed KG structure shift.")
    parser.parse_args()
    payload = verify_structure_shift()
    print(
        f"structure_shift_modes={payload['kg_modes']} "
        f"extracted_triples={payload['kg_artifacts']['extracted']['total']} "
        f"mixed_triples={payload['kg_artifacts']['mixed']['triple_count']} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
