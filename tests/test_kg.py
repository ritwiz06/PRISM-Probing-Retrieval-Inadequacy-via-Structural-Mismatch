from __future__ import annotations

from prism.eval.deductive_slice import load_deductive_queries
from prism.eval.verify_kg import verify_kg
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.retrievers.kg_retriever import KGRetriever


def test_kg_retriever_returns_matching_triple(sample_triples) -> None:
    retriever = KGRetriever(sample_triples)
    results = retriever.retrieve("Can a bat fly?", top_k=1)
    assert results[0].item_id == "kg_bat_capable_fly"


def test_kg_builds_rdflib_graph(sample_triples) -> None:
    retriever = KGRetriever.build(sample_triples)
    assert len(retriever.graph) == len(sample_triples)


def test_kg_builds_networkx_mirror(sample_triples) -> None:
    retriever = KGRetriever.build(sample_triples)
    assert retriever.nx_graph.number_of_edges() == len(sample_triples)
    assert "bat" in retriever.nx_graph


def test_kg_membership_query_correctness(sample_triples) -> None:
    retriever = KGRetriever.build(sample_triples)
    results = retriever.retrieve("Is a bat a mammal?", top_k=1)
    assert results[0].item_id == "kg_bat_is_mammal"
    assert results[0].metadata["query_mode"] == "membership"


def test_kg_property_query_correctness(sample_triples) -> None:
    retriever = KGRetriever.build(sample_triples)
    results = retriever.retrieve("What property allows a bat to fly?", top_k=2)
    assert any(result.item_id == "kg_bat_has_wings" for result in results)


def test_kg_two_hop_traversal_correctness(sample_triples) -> None:
    retriever = KGRetriever.build(sample_triples)
    results = retriever.retrieve("What two-hop path connects bat to vertebrate?", top_k=1)
    assert results[0].item_id == "path:kg_bat_is_mammal->kg_mammal_is_vertebrate"
    assert results[0].metadata["hop_count"] == "2"


def test_kg_save_load_round_trip(sample_triples, tmp_path) -> None:
    path = tmp_path / "kg.pkl"
    KGRetriever.build(sample_triples).save(path)
    loaded = KGRetriever.load(path)
    assert loaded.retrieve("Is a bat a mammal?", top_k=1)[0].item_id == "kg_bat_is_mammal"


def test_kg_retrieve_returns_sorted_results(sample_triples) -> None:
    retriever = KGRetriever.build(sample_triples)
    results = retriever.retrieve("Are all mammals able to fly?", top_k=3)
    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)


def test_deductive_slice_loads_correctly() -> None:
    queries = load_deductive_queries()
    assert len(queries) == 20
    assert all(query.gold_route == "kg" for query in queries)
    assert all(query.gold_evidence_ids for query in queries)


def test_kg_verification_thresholds(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PRISM_DATA_DIR", str(data_dir))
    monkeypatch.delenv("PRISM_CONFIG", raising=False)
    build_corpus()
    build_kg()

    payload = verify_kg()

    assert payload["total"] == 20
    assert payload["triple_count"] >= 80
    assert payload["kg_hit_at_k"] >= 16
    assert payload["kg_beats_dense"] >= 12
    assert payload["passed"] is True
