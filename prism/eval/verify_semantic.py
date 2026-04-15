from __future__ import annotations

import argparse
from pathlib import Path

from prism.config import load_config
from prism.eval.semantic_slice import load_semantic_queries
from prism.ingest.build_corpus import build_corpus
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.utils import read_jsonl_documents, write_json


def verify_semantic(top_k: int = 3) -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    if not corpus_path.exists():
        build_corpus()

    documents = read_jsonl_documents(corpus_path)
    dense = DenseRetriever.build(documents, config=config.retrieval)
    bm25 = BM25Retriever.build(documents)

    rows: list[dict[str, object]] = []
    dense_top1_hits = 0
    dense_hit_at_k = 0
    bm25_hit_at_k = 0
    dense_beats_bm25 = 0

    for item in load_semantic_queries():
        dense_results = dense.retrieve(item.query, top_k=top_k)
        bm25_results = bm25.retrieve(item.query, top_k=top_k)
        dense_parent_ids = [result.metadata.get("parent_doc_id", result.item_id) for result in dense_results]
        bm25_ids = [result.item_id for result in bm25_results]
        dense_top1 = bool(dense_parent_ids and dense_parent_ids[0] == item.gold_evidence_doc_id)
        dense_hit = item.gold_evidence_doc_id in dense_parent_ids
        bm25_hit = item.gold_evidence_doc_id in bm25_ids
        dense_top1_hits += int(dense_top1)
        dense_hit_at_k += int(dense_hit)
        bm25_hit_at_k += int(bm25_hit)
        dense_beats_bm25 += int(dense_hit and not bm25_hit)
        rows.append(
            {
                "query": item.query,
                "gold_evidence_doc_id": item.gold_evidence_doc_id,
                "dense_top_ids": dense_parent_ids,
                "bm25_top_ids": bm25_ids,
                "dense_top1": dense_top1,
                "dense_hit_at_k": dense_hit,
                "bm25_hit_at_k": bm25_hit,
                "dense_beats_bm25": dense_hit and not bm25_hit,
            }
        )

    total = len(rows)
    payload = {
        "total": total,
        "top_k": top_k,
        "dense_top1": dense_top1_hits,
        "dense_hit_at_k": dense_hit_at_k,
        "bm25_hit_at_k": bm25_hit_at_k,
        "dense_beats_bm25": dense_beats_bm25,
        "required_dense_hit_at_k": 14,
        "required_dense_beats_bm25": 12,
        "passed": dense_hit_at_k >= 14 and dense_beats_bm25 >= 12,
        "dense_embedding_backend": dense.embedding_model.backend_name,
        "dense_index_backend": dense.index_backend,
        "dense_active_backend": dense.active_backend,
        "dense_model_name": dense.embedding_model.model_name,
        "dense_fallback_reason": dense.embedding_model.fallback_reason,
        "results": rows,
    }
    output_path = Path(config.paths.eval_dir) / "semantic_verification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Dense semantic retrieval against BM25.")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    payload = verify_semantic(top_k=args.top_k)
    print(
        f"semantic_dense_hit@{payload['top_k']}={payload['dense_hit_at_k']}/{payload['total']} "
        f"dense_top1={payload['dense_top1']}/{payload['total']} "
        f"bm25_hit@{payload['top_k']}={payload['bm25_hit_at_k']}/{payload['total']} "
        f"dense_beats_bm25={payload['dense_beats_bm25']}/{payload['total']} "
        f"active_backend={payload['dense_active_backend']} model={payload['dense_model_name']} "
        f"fallback_reason={payload['dense_fallback_reason'] or 'none'} "
        f"passed={payload['passed']}"
    )


if __name__ == "__main__":
    main()
