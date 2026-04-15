from __future__ import annotations

import argparse
import logging
from pathlib import Path

from prism.answering.generator import synthesize_answer
from prism.answer.soundness import validate_trace
from prism.answer.trace import build_trace
from prism.config import load_config
from prism.eval.analyze_results import summarize_results
from prism.eval.datasets import load_smoke_queries
from prism.eval.gold_labels import smoke_gold_evidence_doc_ids, smoke_gold_routes
from prism.eval.metrics import route_accuracy
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.logging_utils import configure_logging
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.utils import ensure_directories, read_jsonl_documents, read_jsonl_triples, write_json

LOGGER = logging.getLogger(__name__)


def _load_retrievers():
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    if not corpus_path.exists():
        build_corpus()
    if not kg_path.exists():
        build_kg(corpus_path=str(corpus_path))
    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    bm25 = BM25Retriever(documents)
    dense = DenseRetriever(documents)
    kg = KGRetriever(triples)
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def run_evaluation(smoke: bool = False, backend: str | None = None) -> dict[str, object]:
    config = load_config()
    configure_logging(config.log_level)
    ensure_directories([config.paths.eval_dir, config.paths.processed_dir])

    retrievers = _load_retrievers()
    queries = load_smoke_queries(config) if smoke else load_smoke_queries(config)
    gold_routes = smoke_gold_routes()
    predicted_routes: list[str] = []
    gold: list[str] = []
    results: list[dict[str, object]] = []

    for query in queries:
        decision = route_query(query)
        selected_backend = backend or decision.selected_backend
        evidence = retrievers[selected_backend].retrieve(query, top_k=config.retrieval.default_top_k)
        structured_answer = synthesize_answer(query, decision.features, decision.ras_scores, selected_backend, evidence)
        answer = structured_answer.final_answer
        trace = build_trace(query, decision, evidence)
        issues = validate_trace(decision, trace, answer)
        predicted_routes.append(decision.selected_backend)
        if query in gold_routes:
            gold.append(gold_routes[query])
        gold_doc_id = smoke_gold_evidence_doc_ids().get(query)
        retrieved_ids = [item.metadata.get("parent_doc_id", item.item_id) for item in evidence]
        results.append(
            {
                "query": query,
                "selected_backend": selected_backend,
                "answer": answer,
                "evidence_ids": trace.evidence_ids,
                "gold_evidence_doc_id": gold_doc_id,
                "top1_correct": retrieved_ids[0] == gold_doc_id if retrieved_ids and gold_doc_id else None,
                "issues": issues,
            }
        )

    payload = {
        "route_accuracy": route_accuracy(predicted_routes, gold),
        "summary": summarize_results(results),
        "results": results,
    }
    output_path = Path(config.paths.eval_dir) / "smoke_eval.json"
    write_json(output_path, payload)
    LOGGER.info("Wrote evaluation payload to %s", output_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PRISM evaluation.")
    parser.add_argument("--smoke", action="store_true", help="Run the smoke evaluation slice.")
    parser.add_argument("--backend", default=None, choices=["bm25", "dense", "kg", "hybrid"], help="Force a backend.")
    args = parser.parse_args()
    payload = run_evaluation(smoke=args.smoke, backend=args.backend)
    print(f"route_accuracy={payload['route_accuracy']}")


if __name__ == "__main__":
    main()
