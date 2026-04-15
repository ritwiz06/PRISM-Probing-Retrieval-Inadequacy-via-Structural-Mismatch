from __future__ import annotations

import argparse
from pathlib import Path

from prism.config import load_config
from prism.eval.relational_slice import load_relational_queries
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json


def verify_hybrid(top_k: int = 5) -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    if not corpus_path.exists():
        build_corpus()
    if not kg_path.exists():
        build_kg(corpus_path=str(corpus_path))

    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    bm25 = BM25Retriever.build(documents)
    dense = DenseRetriever.build(documents, config=config.retrieval)
    kg = KGRetriever.build(triples)
    hybrid = HybridRetriever([dense, kg, bm25])

    rows: list[dict[str, object]] = []
    hybrid_top1 = 0
    hybrid_hit_at_k = 0
    dense_hit_at_k = 0
    kg_hit_at_k = 0
    bm25_hit_at_k = 0
    hybrid_beats_dense = 0
    hybrid_beats_kg = 0
    hybrid_beats_bm25 = 0
    contributing_backend_counts: dict[str, int] = {}

    for item in load_relational_queries():
        hybrid_results = hybrid.retrieve(item.query, top_k=top_k)
        dense_results = dense.retrieve(item.query, top_k=top_k)
        kg_results = kg.retrieve(item.query, top_k=top_k)
        bm25_results = bm25.retrieve(item.query, top_k=top_k)
        gold = set(item.gold_evidence_ids)
        hybrid_hits = [_contains_all_gold(result, gold) for result in hybrid_results]
        dense_hits = [_contains_all_gold(result, gold) for result in dense_results]
        kg_hits = [_contains_all_gold(result, gold) for result in kg_results]
        bm25_hits = [_contains_all_gold(result, gold) for result in bm25_results]
        hybrid_hit = any(hybrid_hits)
        dense_hit = any(dense_hits)
        kg_hit = any(kg_hits)
        bm25_hit = any(bm25_hits)
        hybrid_top1_hit = bool(hybrid_hits and hybrid_hits[0])
        hybrid_hit_at_k += int(hybrid_hit)
        dense_hit_at_k += int(dense_hit)
        kg_hit_at_k += int(kg_hit)
        bm25_hit_at_k += int(bm25_hit)
        hybrid_top1 += int(hybrid_top1_hit)
        hybrid_beats_dense += int(hybrid_hit and not dense_hit)
        hybrid_beats_kg += int(hybrid_hit and not kg_hit)
        hybrid_beats_bm25 += int(hybrid_hit and not bm25_hit)
        for result in hybrid_results[:1]:
            for backend in result.metadata.get("contributing_backends", "").split(","):
                if backend:
                    contributing_backend_counts[backend] = contributing_backend_counts.get(backend, 0) + 1
        rows.append(
            {
                "query": item.query,
                "gold_evidence_ids": item.gold_evidence_ids,
                "hybrid_top_ids": [result.item_id for result in hybrid_results],
                "hybrid_component_ids": [result.metadata.get("component_ids", "") for result in hybrid_results],
                "dense_top_ids": [result.item_id for result in dense_results],
                "kg_top_ids": [result.item_id for result in kg_results],
                "bm25_top_ids": [result.item_id for result in bm25_results],
                "hybrid_hit_at_k": hybrid_hit,
                "hybrid_top1": hybrid_top1_hit,
                "dense_hit_at_k": dense_hit,
                "kg_hit_at_k": kg_hit,
                "bm25_hit_at_k": bm25_hit,
                "hybrid_beats_dense": hybrid_hit and not dense_hit,
                "hybrid_beats_kg": hybrid_hit and not kg_hit,
                "hybrid_beats_bm25": hybrid_hit and not bm25_hit,
                "top_contributing_backends": hybrid_results[0].metadata.get("contributing_backends") if hybrid_results else "",
            }
        )

    total = len(rows)
    payload = {
        "total": total,
        "top_k": top_k,
        "hybrid_top1": hybrid_top1,
        "hybrid_hit_at_k": hybrid_hit_at_k,
        "dense_hit_at_k": dense_hit_at_k,
        "kg_hit_at_k": kg_hit_at_k,
        "bm25_hit_at_k": bm25_hit_at_k,
        "hybrid_beats_dense": hybrid_beats_dense,
        "hybrid_beats_kg": hybrid_beats_kg,
        "hybrid_beats_bm25": hybrid_beats_bm25,
        "required_hybrid_hit_at_k": 15,
        "required_hybrid_beats_dense": 12,
        "required_hybrid_beats_kg": 10,
        "passed": hybrid_hit_at_k >= 15 and hybrid_beats_dense >= 12 and hybrid_beats_kg >= 10,
        "fusion_method": "rrf+relational_bundle",
        "contributing_backend_counts": contributing_backend_counts,
        "results": rows,
    }
    output_path = Path(config.paths.eval_dir) / "hybrid_verification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def _contains_all_gold(result, gold: set[str]) -> bool:
    ids = {result.item_id}
    ids.update(part for part in result.metadata.get("component_ids", "").split(",") if part)
    ids.update(part for part in result.metadata.get("triple_id", "").split(",") if part)
    ids.update(part for part in result.metadata.get("path_id", "").split(",") if part)
    ids.update(part for part in result.metadata.get("parent_doc_id", "").split(",") if part)
    ids.update(part for part in result.metadata.get("chunk_id", "").split(",") if part)
    return gold.issubset(ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Hybrid relational retrieval.")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    payload = verify_hybrid(top_k=args.top_k)
    print(
        f"hybrid_hit@{payload['top_k']}={payload['hybrid_hit_at_k']}/{payload['total']} "
        f"hybrid_top1={payload['hybrid_top1']}/{payload['total']} "
        f"dense_hit@{payload['top_k']}={payload['dense_hit_at_k']}/{payload['total']} "
        f"kg_hit@{payload['top_k']}={payload['kg_hit_at_k']}/{payload['total']} "
        f"bm25_hit@{payload['top_k']}={payload['bm25_hit_at_k']}/{payload['total']} "
        f"hybrid_beats_dense={payload['hybrid_beats_dense']}/{payload['total']} "
        f"hybrid_beats_kg={payload['hybrid_beats_kg']}/{payload['total']} "
        f"passed={payload['passed']}"
    )


if __name__ == "__main__":
    main()
