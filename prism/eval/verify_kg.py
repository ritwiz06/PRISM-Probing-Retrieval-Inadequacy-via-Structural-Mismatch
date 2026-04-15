from __future__ import annotations

import argparse
from pathlib import Path

from prism.config import load_config
from prism.eval.deductive_slice import load_deductive_queries
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json


def verify_kg(top_k: int = 3) -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    if not corpus_path.exists():
        build_corpus()
    if not kg_path.exists():
        build_kg(corpus_path=str(corpus_path))

    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    kg = KGRetriever.build(triples)
    dense = DenseRetriever.build(documents, config=config.retrieval)
    bm25 = BM25Retriever.build(documents)

    rows: list[dict[str, object]] = []
    kg_top1 = 0
    kg_hit_at_k = 0
    dense_hit_at_k = 0
    bm25_hit_at_k = 0
    kg_beats_dense = 0
    kg_beats_bm25 = 0

    for item in load_deductive_queries():
        kg_results = kg.retrieve(item.query, top_k=top_k)
        dense_results = dense.retrieve(item.query, top_k=top_k)
        bm25_results = bm25.retrieve(item.query, top_k=top_k)
        gold = set(item.gold_evidence_ids)
        kg_ids = [result.item_id for result in kg_results]
        dense_ids = [result.item_id for result in dense_results]
        bm25_ids = [result.item_id for result in bm25_results]
        kg_hit = bool(gold & set(kg_ids))
        dense_hit = bool(gold & set(dense_ids))
        bm25_hit = bool(gold & set(bm25_ids))
        kg_top1_hit = bool(kg_ids and kg_ids[0] in gold)
        kg_hit_at_k += int(kg_hit)
        dense_hit_at_k += int(dense_hit)
        bm25_hit_at_k += int(bm25_hit)
        kg_top1 += int(kg_top1_hit)
        kg_beats_dense += int(kg_hit and not dense_hit)
        kg_beats_bm25 += int(kg_hit and not bm25_hit)
        rows.append(
            {
                "query": item.query,
                "gold_evidence_ids": item.gold_evidence_ids,
                "kg_top_ids": kg_ids,
                "dense_top_ids": dense_ids,
                "bm25_top_ids": bm25_ids,
                "kg_hit_at_k": kg_hit,
                "kg_top1": kg_top1_hit,
                "dense_hit_at_k": dense_hit,
                "bm25_hit_at_k": bm25_hit,
                "kg_beats_dense": kg_hit and not dense_hit,
                "kg_beats_bm25": kg_hit and not bm25_hit,
                "query_mode": kg_results[0].metadata.get("query_mode") if kg_results else None,
            }
        )

    total = len(rows)
    payload = {
        "total": total,
        "top_k": top_k,
        "kg_top1": kg_top1,
        "kg_hit_at_k": kg_hit_at_k,
        "dense_hit_at_k": dense_hit_at_k,
        "bm25_hit_at_k": bm25_hit_at_k,
        "kg_beats_dense": kg_beats_dense,
        "kg_beats_bm25": kg_beats_bm25,
        "required_kg_hit_at_k": 16,
        "required_kg_beats_dense": 12,
        "passed": kg_hit_at_k >= 16 and kg_beats_dense >= 12,
        "triple_count": len(triples),
        "rdflib_triple_count": len(kg.graph),
        "networkx_node_count": kg.nx_graph.number_of_nodes(),
        "networkx_edge_count": kg.nx_graph.number_of_edges(),
        "results": rows,
    }
    output_path = Path(config.paths.eval_dir) / "kg_verification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify KG deductive retrieval.")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    payload = verify_kg(top_k=args.top_k)
    print(
        f"kg_hit@{payload['top_k']}={payload['kg_hit_at_k']}/{payload['total']} "
        f"kg_top1={payload['kg_top1']}/{payload['total']} "
        f"dense_hit@{payload['top_k']}={payload['dense_hit_at_k']}/{payload['total']} "
        f"bm25_hit@{payload['top_k']}={payload['bm25_hit_at_k']}/{payload['total']} "
        f"kg_beats_dense={payload['kg_beats_dense']}/{payload['total']} "
        f"triples={payload['triple_count']} passed={payload['passed']}"
    )


if __name__ == "__main__":
    main()
