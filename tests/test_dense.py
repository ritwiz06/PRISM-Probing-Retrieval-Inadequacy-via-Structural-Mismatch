from __future__ import annotations

from prism.eval.verify_semantic import verify_semantic
from prism.ingest.build_corpus import build_corpus
from prism.analysis.dense_diagnostics import run_dense_diagnostics
from prism.config import RetrievalConfig
from prism.retrievers.dense_retriever import DenseRetriever, HashingEmbeddingModel, build_embedding_model, chunk_documents
from prism.eval.semantic_slice import load_semantic_queries


def test_dense_returns_semanticish_match(sample_documents) -> None:
    retriever = DenseRetriever(sample_documents)
    results = retriever.retrieve("eco grief and planetary worry", top_k=1)
    assert results[0].metadata["parent_doc_id"] == "sem_climate_anxiety"


def test_dense_chunking_behavior(sample_documents) -> None:
    chunks = chunk_documents(sample_documents, chunk_size=4, chunk_overlap=1)
    assert chunks
    assert all("::chunk_" in chunk.chunk_id for chunk in chunks)
    assert all(chunk.parent_doc_id for chunk in chunks)


def test_dense_index_build(sample_documents) -> None:
    retriever = DenseRetriever.build(sample_documents)
    assert retriever.chunks
    assert retriever.embeddings.shape[0] == len(retriever.chunks)
    assert retriever.index_backend in {"numpy", "faiss"}
    assert retriever.active_backend in {"sentence_transformers+numpy", "sentence_transformers+faiss", "numpy_fallback"}


def test_dense_save_load_round_trip(sample_documents, tmp_path) -> None:
    index_path = tmp_path / "dense.pkl"
    DenseRetriever.build(sample_documents).save(index_path)
    loaded = DenseRetriever.load(index_path)
    results = loaded.retrieve("secretly unqualified fraud despite skill", top_k=1)
    assert index_path.exists()
    assert results[0].metadata["parent_doc_id"] == "sem_impostor_syndrome"


def test_dense_retrieve_returns_sorted_results(sample_documents) -> None:
    retriever = DenseRetriever.build(sample_documents)
    results = retriever.retrieve("eco grief and warming future", top_k=3)
    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)


def test_dense_metadata_includes_backend_and_model(sample_documents) -> None:
    retriever = DenseRetriever(sample_documents, embedding_model=HashingEmbeddingModel(fallback_reason="test fallback"))
    result = retriever.retrieve("eco grief and warming future", top_k=1)[0]
    assert result.metadata["active_dense_backend"] == "numpy_fallback"
    assert result.metadata["embedding_model_name"] == "hashing-semantic-fallback"
    assert result.metadata["fallback_reason"] == "test fallback"


def test_dense_backend_selection_fallback() -> None:
    model = build_embedding_model(RetrievalConfig(dense_backend="numpy"))
    assert model.backend_name == "numpy_fallback"
    assert model.fallback_reason


def test_dense_diagnostics_output_shape() -> None:
    payload = run_dense_diagnostics(top_k=1)
    assert "dense_backend_status" in payload
    assert payload["dense_backend_status"]["active_backend"] in {"sentence_transformers+numpy", "sentence_transformers+faiss", "numpy_fallback"}
    assert payload["sample_queries"]


def test_semantic_slice_loads_correctly() -> None:
    queries = load_semantic_queries()
    assert len(queries) == 20
    assert all(query.gold_route == "dense" for query in queries)
    assert all(query.gold_evidence_doc_id for query in queries)


def test_semantic_verification_thresholds(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PRISM_DATA_DIR", str(data_dir))
    monkeypatch.delenv("PRISM_CONFIG", raising=False)
    build_corpus()

    payload = verify_semantic()

    assert payload["total"] == 20
    assert payload["dense_hit_at_k"] >= 14
    assert payload["dense_beats_bm25"] >= 12
    assert payload["passed"] is True
