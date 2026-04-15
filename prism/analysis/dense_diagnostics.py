from __future__ import annotations

import argparse
from pathlib import Path

from prism.config import load_config
from prism.external_benchmarks.loaders import load_external_mini_benchmark
from prism.ingest.build_corpus import build_corpus
from prism.retrievers.dense_retriever import DenseRetriever
from prism.utils import read_json, read_jsonl_documents, write_json

SAMPLE_QUERIES = (
    "What concept turns daylight into carbohydrates?",
    "What feels like climate anxiety?",
    "Which term means automated unfairness pattern?",
    "Which term names reward driven agent training?",
)


def run_dense_diagnostics(top_k: int = 3) -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    if not corpus_path.exists():
        build_corpus()
    retriever = DenseRetriever.build(read_jsonl_documents(corpus_path), config=config.retrieval)
    samples = []
    for query in SAMPLE_QUERIES:
        results = retriever.retrieve(query, top_k=top_k)
        samples.append(
            {
                "query": query,
                "top_hits": [
                    {
                        "item_id": item.item_id,
                        "parent_doc_id": item.metadata.get("parent_doc_id"),
                        "title": item.metadata.get("title"),
                        "score": item.score,
                        "active_dense_backend": item.metadata.get("active_dense_backend"),
                        "snippet": item.content,
                    }
                    for item in results
                ],
            }
        )
    external_summary_path = Path("data/eval/external_generalization.json")
    external_semantic = {}
    if external_summary_path.exists():
        external = read_json(external_summary_path)
        external_semantic = external["systems"]["computed_ras"]["per_family"].get("dense", {})
    payload = {
        "dense_backend_status": retriever.backend_status,
        "sample_queries": samples,
        "external_semantic_result": external_semantic,
        "external_semantic_query_count": sum(1 for item in load_external_mini_benchmark() if item.route_family == "dense"),
    }
    output_path = Path("data/eval/dense_diagnostics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    write_dense_upgrade_summary(payload)
    return payload


def write_dense_upgrade_summary(payload: dict[str, object]) -> Path:
    status = payload["dense_backend_status"]
    external = payload.get("external_semantic_result") or {}
    photosynthesis = next((row for row in payload["sample_queries"] if row["query"] == "What concept turns daylight into carbohydrates?"), None)
    top_hit = photosynthesis["top_hits"][0] if photosynthesis and photosynthesis["top_hits"] else {}
    path = Path("data/eval/dense_upgrade_summary.md")
    path.write_text(
        "\n".join(
            [
                "# Dense Upgrade Summary",
                "",
                "Previous Dense backend: numpy_fallback.",
                f"Current Dense backend: {status['active_backend']}.",
                f"Model name: {status['model_name']}.",
                f"FAISS active: {status['faiss_active']}.",
                f"Chunk count: {status['chunk_count']}.",
                f"Fallback reason: {status['fallback_reason'] or 'none'}.",
                "",
                "## External Semantic Result",
                "",
                f"External semantic answer accuracy: {external.get('answer_accuracy', 'not available')}.",
                f"External semantic correct: {external.get('answer_correct', 'not available')}/{external.get('total', 'not available')}.",
                "",
                "## Photosynthesis Paraphrase Check",
                "",
                f"Query: What concept turns daylight into carbohydrates?",
                f"Top hit: {top_hit.get('parent_doc_id', 'none')} ({top_hit.get('title', 'none')}).",
                f"Top hit score: {top_hit.get('score', 'none')}.",
                "",
                "## Limitations",
                "",
                "- If sentence-transformers cannot load locally, PRISM falls back to the deterministic numpy/hash backend.",
                "- If FAISS is unavailable, sentence-transformers embeddings still use numpy similarity search.",
                "- This summary reports observed local behavior; it does not hide semantic misses.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Report PRISM Dense backend capability and sample semantic retrieval results.")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    payload = run_dense_diagnostics(top_k=args.top_k)
    status = payload["dense_backend_status"]
    print(
        f"dense_active_backend={status['active_backend']} model={status['model_name']} "
        f"faiss_active={status['faiss_active']} chunks={status['chunk_count']} "
        f"fallback_reason={status['fallback_reason'] or 'none'} output=data/eval/dense_diagnostics.json"
    )
    for sample in payload["sample_queries"]:
        top = sample["top_hits"][0] if sample["top_hits"] else {}
        print(f"sample query={sample['query']!r} top={top.get('parent_doc_id')} score={top.get('score')}")


if __name__ == "__main__":
    main()
