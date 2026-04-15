from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from prism.answering.generator import StructuredAnswer, synthesize_answer
from prism.config import load_config
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.schemas import RetrievedItem, RouteDecision
from prism.utils import read_jsonl_documents, read_jsonl_triples


def load_retrievers() -> dict[str, object]:
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
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def answer_query(
    query: str,
    top_k: int | None = None,
    retrievers: dict[str, object] | None = None,
    backend_override: str | None = None,
) -> dict[str, object]:
    config = load_config()
    decision = route_query(query)
    active_retrievers = retrievers or load_retrievers()
    limit = top_k or config.retrieval.default_top_k
    selected_backend = backend_override or decision.selected_backend
    evidence = active_retrievers[selected_backend].retrieve(query, top_k=limit)
    answer = synthesize_answer(query, decision.features, decision.ras_scores, selected_backend, evidence)
    return _payload(query, decision, evidence, answer, selected_backend=selected_backend)


def _payload(
    query: str,
    decision: RouteDecision,
    evidence: list[RetrievedItem],
    answer: StructuredAnswer,
    selected_backend: str | None = None,
) -> dict[str, object]:
    return {
        "query": query,
        "parsed_features": asdict(decision.features),
        "ras_scores": decision.ras_scores,
        "selected_backend": selected_backend or decision.selected_backend,
        "top_evidence": [
            {
                "item_id": item.item_id,
                "score": item.score,
                "source_type": item.source_type,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in evidence
        ],
        "answer": asdict(answer),
        "reasoning_trace": answer.reasoning_trace_steps,
    }
