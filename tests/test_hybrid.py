from __future__ import annotations

from prism.eval.relational_slice import load_relational_queries
from prism.eval.verify_hybrid import verify_hybrid
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridConfig, HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever


def test_rrf_fusion_produces_hybrid_items(sample_documents, sample_triples) -> None:
    bm25 = BM25Retriever.build(sample_documents)
    dense = DenseRetriever.build(sample_documents)
    kg = KGRetriever.build(sample_triples)
    hybrid = HybridRetriever([dense, kg, bm25], config=HybridConfig(rrf_k=10))

    results = hybrid.retrieve("What relation connects bat and fly?", top_k=3)

    assert results
    assert all(result.item_id.startswith("hybrid:") for result in results)
    assert all("fusion_method" in result.metadata for result in results)


def test_hybrid_returns_sorted_top_k(sample_documents, sample_triples) -> None:
    hybrid = HybridRetriever(
        [DenseRetriever.build(sample_documents), KGRetriever.build(sample_triples), BM25Retriever.build(sample_documents)]
    )
    results = hybrid.retrieve("What relation connects bat and fly?", top_k=3)
    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)


def test_hybrid_relational_bundle_preserves_provenance(sample_documents, sample_triples) -> None:
    hybrid = HybridRetriever(
        [DenseRetriever.build(sample_documents), KGRetriever.build(sample_triples), BM25Retriever.build(sample_documents)]
    )
    results = hybrid.retrieve("What relation connects bat and fly?", top_k=5)
    bundled = [result for result in results if result.metadata["fusion_method"] == "rrf+relational_bundle"]
    assert bundled
    assert "kg" in bundled[0].metadata["contributing_backends"]
    assert "kg_bat_capable_fly" in bundled[0].metadata["component_ids"]


def test_relational_slice_loads_correctly() -> None:
    queries = load_relational_queries()
    assert len(queries) == 20
    assert all(query.gold_route == "hybrid" for query in queries)
    assert all(len(query.gold_evidence_ids) == 2 for query in queries)


def test_relational_queries_route_to_hybrid() -> None:
    decision = route_query("What bridge connects bat and vertebrate?")
    assert decision.selected_backend == "hybrid"


def test_hybrid_verification_thresholds(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PRISM_DATA_DIR", str(data_dir))
    monkeypatch.delenv("PRISM_CONFIG", raising=False)
    build_corpus()
    build_kg()

    payload = verify_hybrid()

    assert payload["total"] == 20
    assert payload["hybrid_hit_at_k"] >= 15
    assert payload["hybrid_beats_dense"] >= 12
    assert payload["hybrid_beats_kg"] >= 10
    assert payload["passed"] is True
