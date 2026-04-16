from __future__ import annotations

import argparse
import csv
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from prism.analysis.evaluation import BACKENDS, answer_matches_gold
from prism.app.pipeline import answer_query
from prism.ingest.build_kg import build_kg
from prism.public_corpus.benchmark_builder import build_public_benchmark
from prism.public_corpus.build_public_corpus import PUBLIC_CORPUS_SUMMARY_PATH, build_public_corpus
from prism.public_corpus.lexical_retriever import PublicAwareBM25Retriever, is_identifier_heavy_query
from prism.public_corpus.loaders import PublicBenchmarkItem, load_public_benchmark, public_benchmark_counts
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.utils import read_json, read_jsonl_documents, read_jsonl_triples, write_json

SYSTEMS = ("computed_ras", "always_bm25", "always_dense", "always_kg", "always_hybrid", "random_router")
ROBUST_SYSTEMS = ("computed_ras_public_lexical", "computed_ras_public_arbitrated", "always_bm25_public_lexical")
PREVIOUS_PUBLIC_TEST_REFERENCE = {
    "source": "Prompt 17 public_corpus_eval before public robustness work",
    "computed_ras_answer_accuracy": 0.917,
    "computed_ras_answer_correct": 22,
    "computed_ras_total": 24,
    "computed_ras_route_accuracy": 0.875,
    "computed_ras_evidence_hit_at_k": 0.917,
    "strongest_fixed_backend": "always_bm25",
    "strongest_fixed_answer_accuracy": 0.958,
}
SPLITS = ("dev", "test")
JSON_PATH = Path("data/eval/public_corpus_eval.json")
CSV_PATH = Path("data/eval/public_corpus_eval.csv")
MARKDOWN_PATH = Path("data/eval/public_corpus_eval_summary.md")
BASELINE_PLOT = Path("data/eval/public_corpus_baselines.png")
FAMILY_PLOT = Path("data/eval/public_corpus_family_accuracy.png")


def verify_public_corpus(seed: int = 31) -> dict[str, object]:
    corpus_path = build_public_corpus()
    benchmark_path = build_public_benchmark()
    kg_path = Path("data/processed/kg_triples.jsonl")
    if not kg_path.exists():
        build_kg()

    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    retrievers = _build_public_retrievers(documents, triples)
    robust_retrievers = _build_public_retrievers(documents, triples, public_lexical=True)
    items = load_public_benchmark(benchmark_path)

    runs: dict[str, dict[str, object]] = {}
    robust_runs: dict[str, dict[str, object]] = {}
    for split in SPLITS:
        split_items = [item for item in items if item.split == split]
        runs[split] = {system: _evaluate_system(system, split_items, retrievers, seed) for system in SYSTEMS}
        robust_runs[split] = {
            system: _evaluate_system(system, split_items, robust_retrievers, seed) for system in ROBUST_SYSTEMS
        }

    corpus_summary = read_json(PUBLIC_CORPUS_SUMMARY_PATH) if PUBLIC_CORPUS_SUMMARY_PATH.exists() else {}
    grounding = _grounding_coverage(items, {document.doc_id for document in documents})
    payload = {
        "seed": seed,
        "corpus": corpus_summary,
        "benchmark": {
            "path": str(benchmark_path),
            "total": len(items),
            "counts": public_benchmark_counts(items),
            "note": "Public raw-document benchmark kept separate from curated, external mini, and generalization_v2 suites.",
        },
        "systems": runs,
        "public_robustness_systems": robust_runs,
        "before_after": _before_after(runs, robust_runs),
        "previous_public_test_reference": PREVIOUS_PUBLIC_TEST_REFERENCE,
        "grounding_coverage": grounding,
        "takeaways": _takeaways(runs),
        "threats_to_validity": _threats_to_validity(),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    _plot_baselines(payload, BASELINE_PLOT)
    _plot_family_accuracy(payload, FAMILY_PLOT)
    return payload


def _build_public_retrievers(documents, triples, public_lexical: bool = False):
    bm25 = PublicAwareBM25Retriever.build(documents) if public_lexical else BM25Retriever.build(documents)
    dense = DenseRetriever.build(documents)
    kg = KGRetriever.build(triples)
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def _evaluate_system(
    system_name: str,
    items: list[PublicBenchmarkItem],
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
        backend = _select_backend(system_name, item, rng, retrievers)
        payload = answer_query(
            item.query,
            top_k=5 if backend == "hybrid" else 3,
            retrievers=retrievers,
            backend_override=backend,
        )
        evidence_rows = list(payload["top_evidence"])
        evidence_ok = _evidence_hit(item, evidence_rows)
        final_answer = str(payload["answer"]["final_answer"])
        answer_ok = answer_matches_gold(final_answer, item.gold_answer)
        route_ok = backend == item.route_family

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
                "source_dataset_style": item.source_dataset_style,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": item.gold_answer,
                "answer": final_answer,
                "answer_correct": answer_ok,
                "gold_source_doc_ids": item.gold_source_doc_ids,
                "top_evidence_ids": [row["item_id"] for row in evidence_rows],
                "evidence_hit": evidence_ok,
                "route_arbitration": _route_arbitration_metadata(system_name, item, retrievers),
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


def _select_backend(
    system_name: str,
    item: PublicBenchmarkItem,
    rng: random.Random,
    retrievers: dict[str, object] | None = None,
) -> str:
    if system_name in {"computed_ras", "computed_ras_public_lexical"}:
        return route_query(item.query).selected_backend
    if system_name == "computed_ras_public_arbitrated":
        decision = route_query(item.query)
        confidence = _lexical_confidence(item.query, retrievers or {})
        if confidence.get("should_arbitrate") and is_identifier_heavy_query(item.query):
            return "bm25"
        return decision.selected_backend
    if system_name == "random_router":
        return rng.choice(BACKENDS)
    if system_name == "always_bm25_public_lexical":
        return "bm25"
    if system_name.startswith("always_"):
        return system_name.removeprefix("always_")
    raise ValueError(f"Unknown public-corpus system: {system_name}")


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


def _evidence_hit(item: PublicBenchmarkItem, evidence_rows: list[dict[str, object]]) -> bool:
    gold_docs = set(item.gold_source_doc_ids)
    evidence_ids: set[str] = set()
    text = ""
    for row in evidence_rows:
        evidence_ids.add(str(row.get("item_id", "")))
        metadata = row.get("metadata", {}) or {}
        if isinstance(metadata, dict):
            for key in ("component_ids", "parent_doc_id", "chunk_id", "source_doc_id", "kg_source_doc_id"):
                for part in str(metadata.get(key, "")).split(","):
                    if part:
                        evidence_ids.add(part)
        text += " " + str(row.get("content", ""))
    if gold_docs & evidence_ids:
        return True
    gold_phrase = item.gold_evidence_text or item.gold_answer
    return _soft_text_hit(gold_phrase, text)


def _soft_text_hit(gold_phrase: str, evidence_text: str) -> bool:
    gold_tokens = {
        token
        for token in re.findall(r"[a-z0-9._:/-]+", gold_phrase.lower())
        if token not in {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "what"}
    }
    if not gold_tokens:
        return False
    evidence = evidence_text.lower()
    overlap = sum(1 for token in gold_tokens if token in evidence)
    return overlap / len(gold_tokens) >= 0.5


def _grounding_coverage(items: list[PublicBenchmarkItem], doc_ids: set[str]) -> dict[str, object]:
    grounded = [item for item in items if set(item.gold_source_doc_ids).issubset(doc_ids)]
    by_family: dict[str, dict[str, int]] = {}
    for item in items:
        row = by_family.setdefault(item.route_family, {"total": 0, "grounded": 0})
        row["total"] += 1
        row["grounded"] += int(set(item.gold_source_doc_ids).issubset(doc_ids))
    return {
        "total": len(items),
        "grounded": len(grounded),
        "coverage": len(grounded) / len(items) if items else 0.0,
        "by_family": by_family,
    }


def _best_fixed_backend(systems: dict[str, dict[str, object]]) -> tuple[str, dict[str, object]]:
    fixed = {name: row for name, row in systems.items() if name.startswith("always_")}
    name = max(fixed, key=lambda key: fixed[key]["answer_accuracy"])
    return name, fixed[name]


def _lexical_confidence(query: str, retrievers: dict[str, object]) -> dict[str, object]:
    bm25 = retrievers.get("bm25")
    if hasattr(bm25, "lexical_confidence"):
        return bm25.lexical_confidence(query)  # type: ignore[no-any-return]
    return {"confidence": 0.0, "should_arbitrate": False, "matched_fields": [], "top_doc_id": "", "boost": 0.0}


def _route_arbitration_metadata(
    system_name: str,
    item: PublicBenchmarkItem,
    retrievers: dict[str, object],
) -> dict[str, object]:
    if system_name != "computed_ras_public_arbitrated":
        return {}
    normal_backend = route_query(item.query).selected_backend
    confidence = _lexical_confidence(item.query, retrievers)
    selected_backend = _select_backend(system_name, item, random.Random(31), retrievers)
    return {
        "normal_backend": normal_backend,
        "selected_backend": selected_backend,
        "overrode_to_bm25": selected_backend == "bm25" and normal_backend != "bm25",
        "lexical_confidence": confidence,
        "identifier_heavy": is_identifier_heavy_query(item.query),
    }


def _before_after(
    runs: dict[str, dict[str, object]],
    robust_runs: dict[str, dict[str, object]],
) -> dict[str, object]:
    rows: dict[str, object] = {}
    for split in sorted(set(runs) & set(robust_runs)):
        baseline = runs[split]["computed_ras"]
        public_lexical = robust_runs[split]["computed_ras_public_lexical"]
        arbitrated = robust_runs[split]["computed_ras_public_arbitrated"]
        best_name, best = _best_fixed_backend(runs[split])
        rows[split] = {
            "baseline_answer_accuracy": baseline["answer_accuracy"],
            "public_lexical_answer_accuracy": public_lexical["answer_accuracy"],
            "public_arbitrated_answer_accuracy": arbitrated["answer_accuracy"],
            "public_lexical_delta": public_lexical["answer_accuracy"] - baseline["answer_accuracy"],
            "public_arbitrated_delta": arbitrated["answer_accuracy"] - baseline["answer_accuracy"],
            "baseline_route_accuracy": baseline["route_accuracy"],
            "public_arbitrated_route_accuracy": arbitrated["route_accuracy"],
            "public_arbitrated_route_delta": arbitrated["route_accuracy"] - baseline["route_accuracy"],
            "strongest_fixed_backend": best_name,
            "strongest_fixed_answer_accuracy": best["answer_accuracy"],
            "fixed_gap_after_arbitration": arbitrated["answer_accuracy"] - best["answer_accuracy"],
            "per_family": _per_family_before_after(baseline["per_family"], arbitrated["per_family"]),
        }
    return rows


def _per_family_before_after(
    baseline: dict[str, dict[str, object]],
    improved: dict[str, dict[str, object]],
) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for family in sorted(set(baseline) | set(improved)):
        base_answer = float(baseline.get(family, {}).get("answer_accuracy", 0.0))
        improved_answer = float(improved.get(family, {}).get("answer_accuracy", 0.0))
        rows[family] = {
            "baseline_answer_accuracy": base_answer,
            "public_arbitrated_answer_accuracy": improved_answer,
            "answer_delta": improved_answer - base_answer,
        }
    return rows


def _takeaways(runs: dict[str, dict[str, object]]) -> list[str]:
    rows: list[str] = []
    for split, systems in runs.items():
        ras = systems["computed_ras"]
        best_name, best = _best_fixed_backend(systems)
        verdict = "beats or matches" if ras["answer_accuracy"] >= best["answer_accuracy"] else "trails"
        weakest_family = _weakest_family(ras["per_family"])
        rows.append(
            f"{split}: computed RAS answer accuracy {ras['answer_accuracy']:.3f} {verdict} "
            f"strongest fixed backend {best_name} at {best['answer_accuracy']:.3f}; weakest family is {weakest_family}."
        )
    return rows


def _weakest_family(per_family: dict[str, dict[str, object]]) -> str:
    if not per_family:
        return "none"
    return min(per_family, key=lambda family: float(per_family[family]["answer_accuracy"]))


def _threats_to_validity() -> list[str]:
    return [
        "The public raw corpus is small and source-selected, so results are not a web-scale claim.",
        "Network failures can cause fallback public snapshots to be used; fetch status is reported in artifacts.",
        "Fetched pages may include formatting noise, navigation text, and boilerplate not present in normalized local corpora.",
        "Deductive and relational public queries still rely partly on the compact demo KG, which can mismatch public-page wording.",
        "Answer matching is normalized string matching, not human grading.",
    ]


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
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
        for split, systems in payload["systems"].items():
            for system, row in systems.items():
                writer.writerow(
                    {
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
    corpus = payload["corpus"]
    benchmark = payload["benchmark"]
    lines = [
        "# Public Raw-Document Corpus Evaluation",
        "",
        f"Public corpus path: `{corpus.get('path')}`.",
        f"Public documents available: {corpus.get('document_count')} of {corpus.get('target_source_count')} registry sources.",
        f"Fetch summary: {corpus.get('fetch_summary')}.",
        f"Cached content status counts: {corpus.get('content_status_counts')}.",
        f"Corpus counts by route family: {corpus.get('counts_by_route_family')}.",
        f"Enriched metadata path: `{corpus.get('enriched_metadata_path')}` with {corpus.get('identifier_document_count')} identifier-bearing documents.",
        "",
        f"Benchmark path: `{benchmark['path']}`.",
        f"Benchmark size: {benchmark['total']} examples.",
        f"Benchmark counts: {benchmark['counts']}.",
        f"Public-doc grounding coverage: {payload['grounding_coverage']}.",
        "",
        "## Results",
        "",
    ]
    for split, systems in payload["systems"].items():
        ras = systems["computed_ras"]
        best_name, best = _best_fixed_backend(systems)
        lines.extend(
            [
                f"### {split.title()} Split",
                "",
                f"- Computed RAS route accuracy: {ras['route_accuracy']:.3f}.",
                f"- Computed RAS answer accuracy: {ras['answer_accuracy']:.3f} ({ras['answer_correct']}/{ras['total']}).",
                f"- Computed RAS evidence hit@k: {ras['evidence_hit_at_k']:.3f} ({ras['evidence_hits']}/{ras['total']}).",
                f"- Strongest fixed-backend baseline: `{best_name}` at answer accuracy {best['answer_accuracy']:.3f}.",
                f"- Predicted backend distribution: {ras['predicted_backend_distribution']}.",
                "- Per-family computed RAS:",
                *[
                    f"  - {family}: answer={row['answer_accuracy']:.3f}, evidence_hit@k={row['evidence_hit_at_k']:.3f}, total={row['total']}"
                    for family, row in ras["per_family"].items()
                ],
                "",
            ]
        )
    previous = payload["previous_public_test_reference"]
    lines.extend(
        [
            "## Public Robustness Before/After",
            "",
            f"- Previous public test reference: computed RAS answer={previous['computed_ras_answer_accuracy']:.3f} ({previous['computed_ras_answer_correct']}/{previous['computed_ras_total']}), route={previous['computed_ras_route_accuracy']:.3f}, strongest fixed={previous['strongest_fixed_backend']} at {previous['strongest_fixed_answer_accuracy']:.3f}.",
        ]
    )
    for split, row in payload.get("before_after", {}).items():
        lines.extend(
            [
                f"- {split}: baseline answer={row['baseline_answer_accuracy']:.3f}; public lexical={row['public_lexical_answer_accuracy']:.3f}; public arbitrated={row['public_arbitrated_answer_accuracy']:.3f}.",
                f"- {split}: public arbitrated route delta={row['public_arbitrated_route_delta']:.3f}; gap vs strongest fixed backend after arbitration={row['fixed_gap_after_arbitration']:.3f}.",
            ]
        )
    lines.append("")
    lines.extend(
        [
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
            f"- Plot: `{BASELINE_PLOT}`",
            f"- Plot: `{FAMILY_PLOT}`",
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


def _plot_baselines(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    split = "test" if "test" in payload["systems"] else next(iter(payload["systems"]))
    systems = payload["systems"][split]
    names = list(SYSTEMS)
    values = [systems[name]["answer_accuracy"] for name in names]
    _, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(names, values, color=["#2b6cb0" if name == "computed_ras" else "#a0aec0" for name in names])
    ax.set_title(f"Public raw corpus: PRISM vs baselines on {split}")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_family_accuracy(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    split = "test" if "test" in payload["systems"] else next(iter(payload["systems"]))
    per_family = payload["systems"][split]["computed_ras"]["per_family"]
    families = sorted(per_family)
    values = [per_family[family]["answer_accuracy"] for family in families]
    _, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(families, values, color="#38a169")
    ax.set_title(f"Public raw corpus per-family answer accuracy ({split})")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRISM on public raw-document corpus benchmark.")
    parser.add_argument("--seed", type=int, default=31)
    args = parser.parse_args()
    payload = verify_public_corpus(seed=args.seed)
    test = payload["systems"]["test"]["computed_ras"]
    print(
        "public_corpus_eval "
        f"benchmark_total={payload['benchmark']['total']} "
        f"splits={payload['benchmark']['counts']['split']} "
        f"families={payload['benchmark']['counts']['route_family']} "
        f"test_answer_accuracy={test['answer_accuracy']:.3f} "
        f"test_evidence_hit_at_k={test['evidence_hit_at_k']:.3f} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
