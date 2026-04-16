from __future__ import annotations

from pathlib import Path

from prism.public_corpus.benchmark_builder import build_public_benchmark
from prism.public_corpus.build_public_corpus import build_public_corpus
from prism.public_corpus.enrich_documents import enrich_public_documents, extract_identifiers
from prism.public_corpus.failure_analysis import analyze_public_failures
from prism.public_corpus.lexical_retriever import PublicAwareBM25Retriever
from prism.public_corpus.loaders import load_public_benchmark, public_benchmark_counts
from prism.public_corpus.source_registry import public_sources
from prism.public_corpus.verify_public_corpus import verify_public_corpus
from prism.public_corpus.compare_grounding import compare_grounding
from prism.utils import read_jsonl_documents


def test_public_source_registry_shape() -> None:
    sources = public_sources()
    assert len(sources) >= 40
    assert {"bm25", "dense", "kg", "hybrid"}.issubset({source.route_family for source in sources})
    assert all(source.source_id.startswith("pub_") for source in sources)
    assert all(source.url.startswith("https://") for source in sources)


def test_public_corpus_build_and_load(tmp_path: Path) -> None:
    output_path = tmp_path / "public_corpus.jsonl"
    path = build_public_corpus(output_path=output_path)
    assert path.exists()
    rows = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) >= 40


def test_public_benchmark_schema_and_counts(tmp_path: Path) -> None:
    output_path = tmp_path / "public_benchmark.jsonl"
    path = build_public_benchmark(output_path)
    items = load_public_benchmark(path)
    counts = public_benchmark_counts(items)
    assert len(items) >= 40
    assert counts["split"]["dev"] > 0
    assert counts["split"]["test"] > 0
    assert set(counts["route_family"]) == {"bm25", "dense", "hybrid", "kg"}
    assert all(item.gold_source_doc_ids for item in items)


def test_public_corpus_eval_artifact_structure() -> None:
    payload = verify_public_corpus(seed=31)
    assert payload["benchmark"]["total"] >= 40
    assert "dev" in payload["systems"]
    assert "test" in payload["systems"]
    assert "computed_ras" in payload["systems"]["test"]
    assert "evidence_hit_at_k" in payload["systems"]["test"]["computed_ras"]
    assert "public_robustness_systems" in payload
    assert "computed_ras_public_arbitrated" in payload["public_robustness_systems"]["test"]


def test_public_vs_local_comparison_artifact_structure() -> None:
    payload = compare_grounding()
    assert "overall_answer_accuracy_delta" in payload
    assert set(payload["per_family_delta"]) == {"bm25", "dense", "hybrid", "kg"}
    assert payload["diagnosis"]


def test_public_identifier_extraction() -> None:
    identifiers = extract_identifiers("RFC 7231, ICD-10 J18.9, HIPAA 164.512, torch.nn.CrossEntropyLoss")
    assert "RFC-7231" in identifiers
    assert "ICD-10 J18.9" in identifiers
    assert "HIPAA 164.512" in identifiers
    assert "torch.nn.CrossEntropyLoss" in identifiers


def test_public_document_enrichment_structure() -> None:
    build_public_corpus()
    metadata = enrich_public_documents()
    assert "pub_rfc_7231" in metadata
    assert metadata["pub_rfc_7231"].canonical_identifiers
    assert metadata["pub_rfc_7231"].lead_summary


def test_public_aware_lexical_retrieval_metadata_shape() -> None:
    corpus_path = build_public_corpus()
    retriever = PublicAwareBM25Retriever.build(read_jsonl_documents(corpus_path))
    results = retriever.retrieve("TfidfVectorizer raw documents matrix TF-IDF features", top_k=1)
    assert results
    assert results[0].item_id == "pub_sklearn_tfidf"
    assert results[0].metadata["public_rerank_enabled"] == "true"
    assert results[0].metadata["public_matched_fields"]


def test_public_failure_analysis_artifact_structure() -> None:
    payload = analyze_public_failures()
    assert "previous_prompt17_misses" in payload
    assert "bucket_counts" in payload
    assert "identifier_subgroups" in payload
    assert payload["public_arbitrated_test_metrics"]["route_accuracy"] >= payload["current_test_metrics"]["route_accuracy"]
