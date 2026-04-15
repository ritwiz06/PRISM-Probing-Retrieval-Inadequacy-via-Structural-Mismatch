from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
import random
import re
from pathlib import Path
from typing import Callable

from prism.answering.generator import synthesize_answer
from prism.config import load_config
from prism.eval.deductive_slice import load_deductive_queries
from prism.eval.lexical_slice import load_lexical_queries
from prism.eval.relational_slice import load_relational_queries
from prism.eval.semantic_slice import load_semantic_queries
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridConfig, HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_jsonl_documents, read_jsonl_triples

BACKENDS = ("bm25", "dense", "kg", "hybrid")


def load_analysis_retrievers() -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    if not corpus_path.exists():
        build_corpus()
    if not kg_path.exists():
        build_kg(corpus_path=str(corpus_path))
    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    return build_retrievers(documents, triples)


def build_retrievers(documents: list[Document], triples: list[Triple]) -> dict[str, object]:
    bm25 = BM25Retriever.build(documents)
    dense = DenseRetriever.build(documents, config=load_config().retrieval)
    kg = KGRetriever.build(triples)
    hybrid = HybridRetriever([dense, kg, bm25])
    return {
        "bm25": bm25,
        "dense": dense,
        "kg": kg,
        "hybrid": hybrid,
        "hybrid_no_kg": HybridRetriever([dense, bm25], config=HybridConfig(enabled_backends=("dense", "bm25"))),
        "hybrid_no_bm25": HybridRetriever([dense, kg], config=HybridConfig(enabled_backends=("dense", "kg"))),
        "hybrid_no_dense": HybridRetriever([kg, bm25], config=HybridConfig(enabled_backends=("kg", "bm25"))),
    }


def load_combined_benchmark() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for slice_name, items in (
        ("lexical", load_lexical_queries()),
        ("semantic", load_semantic_queries()),
        ("deductive", load_deductive_queries()),
        ("relational", load_relational_queries()),
    ):
        for item in items:
            row = asdict(item)
            row["slice"] = slice_name
            row["gold_evidence_ids"] = _gold_evidence_ids(row)
            rows.append(row)
    return rows


def evaluate_systems(
    system_names: list[str] | None = None,
    retrievers: dict[str, object] | None = None,
    seed: int = 7,
) -> dict[str, object]:
    retrievers = retrievers or load_analysis_retrievers()
    benchmark = load_combined_benchmark()
    names = system_names or ["computed_ras", "always_bm25", "always_dense", "always_kg", "always_hybrid", "random_router", "oracle_route"]
    payload = {
        "seed": seed,
        "benchmark_total": len(benchmark),
        "systems": {name: evaluate_system(name, benchmark, retrievers, seed=seed) for name in names},
    }
    return payload


def evaluate_system(
    system_name: str,
    benchmark: list[dict[str, object]] | None = None,
    retrievers: dict[str, object] | None = None,
    seed: int = 7,
) -> dict[str, object]:
    benchmark = benchmark or load_combined_benchmark()
    retrievers = retrievers or load_analysis_retrievers()
    rng = random.Random(seed)
    route_correct = 0
    evidence_hits = 0
    answer_matches = 0
    per_slice = defaultdict(lambda: Counter(total=0, route_correct=0, evidence_hits=0, answer_matches=0))
    predicted_distribution: Counter[str] = Counter()
    confusion: Counter[str] = Counter()
    rows: list[dict[str, object]] = []

    for item in benchmark:
        predicted = _select_backend(system_name, item, rng)
        retriever_key = _retriever_key(system_name, predicted)
        top_k = 5 if item["slice"] == "relational" else 3
        decision = route_query(str(item["query"]))
        evidence = retrievers[retriever_key].retrieve(str(item["query"]), top_k=top_k)
        answer = synthesize_answer(str(item["query"]), decision.features, decision.ras_scores, predicted, evidence)
        evidence_ids = evidence_id_set(evidence)
        gold_evidence = set(item["gold_evidence_ids"])
        evidence_ok = _evidence_hit(str(item["slice"]), gold_evidence, evidence_ids)
        answer_ok = answer_matches_gold(answer.final_answer, str(item["gold_answer"]))
        route_ok = predicted == item["gold_route"]

        route_correct += int(route_ok)
        evidence_hits += int(evidence_ok)
        answer_matches += int(answer_ok)
        predicted_distribution[predicted] += 1
        confusion[f"{item['gold_route']}->{predicted}"] += 1
        slice_counter = per_slice[str(item["slice"])]
        slice_counter["total"] += 1
        slice_counter["route_correct"] += int(route_ok)
        slice_counter["evidence_hits"] += int(evidence_ok)
        slice_counter["answer_matches"] += int(answer_ok)
        rows.append(
            {
                "system": system_name,
                "slice": item["slice"],
                "query": item["query"],
                "gold_route": item["gold_route"],
                "predicted_backend": predicted,
                "route_correct": route_ok,
                "gold_answer": item["gold_answer"],
                "answer": answer.final_answer,
                "answer_match": answer_ok,
                "gold_evidence_ids": sorted(gold_evidence),
                "retrieved_evidence_ids": sorted(evidence_ids),
                "evidence_hit": evidence_ok,
            }
        )

    total = len(benchmark)
    return {
        "system": system_name,
        "total": total,
        "route_accuracy": route_correct / total if total else 0.0,
        "evidence_hit_at_k": evidence_hits / total if total else 0.0,
        "answer_accuracy": answer_matches / total if total else 0.0,
        "route_correct": route_correct,
        "evidence_hits": evidence_hits,
        "answer_matches": answer_matches,
        "per_slice": {
            name: {
                "total": counts["total"],
                "route_accuracy": counts["route_correct"] / counts["total"] if counts["total"] else 0.0,
                "evidence_hit_at_k": counts["evidence_hits"] / counts["total"] if counts["total"] else 0.0,
                "answer_accuracy": counts["answer_matches"] / counts["total"] if counts["total"] else 0.0,
                "route_correct": counts["route_correct"],
                "evidence_hits": counts["evidence_hits"],
                "answer_matches": counts["answer_matches"],
            }
            for name, counts in sorted(per_slice.items())
        },
        "predicted_distribution": dict(predicted_distribution),
        "confusion": dict(confusion),
        "results": rows,
    }


def answer_matches_gold(answer: str, gold: str) -> bool:
    answer_norm = _normalize(answer)
    gold_norm = _normalize(gold)
    if not gold_norm:
        return False
    if gold_norm in answer_norm:
        return True
    gold_tokens = [token for token in gold_norm.split() if token not in {"the", "a", "an", "and", "or", "to", "of", "in"}]
    if not gold_tokens:
        return False
    overlap = sum(1 for token in gold_tokens if token in answer_norm)
    return overlap / len(gold_tokens) >= 0.5


def evidence_id_set(evidence: list[RetrievedItem]) -> set[str]:
    ids: set[str] = set()
    for item in evidence:
        ids.add(item.item_id)
        for key in ("component_ids", "triple_id", "path_id", "parent_doc_id", "chunk_id"):
            for part in str(item.metadata.get(key, "")).split(","):
                if part:
                    ids.add(part)
    return ids


def _select_backend(system_name: str, item: dict[str, object], rng: random.Random) -> str:
    if system_name == "computed_ras":
        return route_query(str(item["query"])).selected_backend
    if system_name == "oracle_route":
        return str(item["gold_route"])
    if system_name == "random_router":
        return rng.choice(BACKENDS)
    if system_name.startswith("always_"):
        return system_name.removeprefix("always_")
    if system_name.startswith("hybrid_no_"):
        return "hybrid"
    raise ValueError(f"Unknown system: {system_name}")


def _retriever_key(system_name: str, predicted_backend: str) -> str:
    if system_name in {"hybrid_no_kg", "hybrid_no_bm25", "hybrid_no_dense"}:
        return system_name
    return predicted_backend


def _gold_evidence_ids(row: dict[str, object]) -> list[str]:
    if "gold_evidence_doc_id" in row:
        return [str(row["gold_evidence_doc_id"])]
    return [str(value) for value in row.get("gold_evidence_ids", [])]


def _evidence_hit(slice_name: str, gold_evidence: set[str], evidence_ids: set[str]) -> bool:
    if slice_name == "relational":
        return gold_evidence.issubset(evidence_ids)
    return bool(gold_evidence & evidence_ids)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9§._:/ -]+", " ", text.lower())).strip()
