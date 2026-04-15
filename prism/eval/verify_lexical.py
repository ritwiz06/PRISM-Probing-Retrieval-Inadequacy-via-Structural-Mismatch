from __future__ import annotations

import argparse
from pathlib import Path

from prism.config import load_config
from prism.eval.lexical_slice import load_lexical_queries
from prism.ingest.build_corpus import build_corpus
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.utils import read_jsonl_documents, write_json


def verify_lexical(top_k: int = 3) -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    if not corpus_path.exists():
        build_corpus()

    retriever = BM25Retriever.build(read_jsonl_documents(corpus_path))
    rows: list[dict[str, object]] = []
    top1_correct = 0
    for item in load_lexical_queries():
        results = retriever.retrieve(item.query, top_k=top_k)
        top_ids = [result.item_id for result in results]
        correct = bool(top_ids and top_ids[0] == item.gold_evidence_doc_id)
        top1_correct += int(correct)
        rows.append(
            {
                "query": item.query,
                "gold_evidence_doc_id": item.gold_evidence_doc_id,
                "top_ids": top_ids,
                "top1_correct": correct,
            }
        )

    payload = {
        "total": len(rows),
        "top1_correct": top1_correct,
        "top1_accuracy": top1_correct / len(rows) if rows else 0.0,
        "required_top1_correct": 16,
        "passed": top1_correct >= 16,
        "results": rows,
    }
    output_path = Path(config.paths.eval_dir) / "lexical_verification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify BM25 lexical exact-match retrieval.")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    payload = verify_lexical(top_k=args.top_k)
    print(
        f"lexical_top1={payload['top1_correct']}/{payload['total']} "
        f"accuracy={payload['top1_accuracy']:.2f} passed={payload['passed']}"
    )


if __name__ == "__main__":
    main()
