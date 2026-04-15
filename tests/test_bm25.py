from __future__ import annotations

from prism.retrievers.bm25_retriever import BM25Retriever
from prism.eval.verify_lexical import verify_lexical
from prism.ingest.build_corpus import build_corpus


def test_bm25_prefers_lexical_match(sample_documents) -> None:
    retriever = BM25Retriever(sample_documents)
    results = retriever.retrieve("exact identifier", top_k=1)
    assert results[0].item_id == "doc1"


def test_bm25_exact_match_outranks_near_match(sample_documents) -> None:
    retriever = BM25Retriever.build(sample_documents)
    results = retriever.retrieve("What does HIPAA 164.512 cover?", top_k=2)
    assert results[0].item_id == "hipaa_164_512"
    assert results[1].item_id == "hipaa_164_510"


def test_bm25_preserves_dotted_api_identifier(sample_documents) -> None:
    retriever = BM25Retriever.build(sample_documents)
    results = retriever.retrieve("torch.nn.CrossEntropyLoss", top_k=2)
    assert results[0].item_id == "torch_ce"


def test_bm25_save_load_round_trip(sample_documents, tmp_path) -> None:
    index_path = tmp_path / "bm25.pkl"
    BM25Retriever.build(sample_documents).save(index_path)
    loaded = BM25Retriever.load(index_path)

    assert index_path.exists()
    assert loaded.retrieve("HIPAA 164.512", top_k=1)[0].item_id == "hipaa_164_512"


def test_bm25_retrieve_returns_sorted_results(sample_documents) -> None:
    retriever = BM25Retriever.build(sample_documents)
    results = retriever.retrieve("HIPAA 164.512", top_k=3)
    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)


def test_lexical_verification_hits_threshold(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PRISM_DATA_DIR", str(data_dir))
    monkeypatch.delenv("PRISM_CONFIG", raising=False)
    build_corpus()

    payload = verify_lexical()

    assert payload["total"] == 20
    assert payload["top1_correct"] >= 16
    assert payload["passed"] is True
