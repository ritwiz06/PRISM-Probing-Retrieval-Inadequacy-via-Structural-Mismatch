from __future__ import annotations

from pathlib import Path

import pytest

from prism.config import AppConfig, EvaluationConfig, PathConfig, RetrievalConfig
from prism.schemas import Document, Triple


@pytest.fixture
def sample_documents() -> list[Document]:
    return [
        Document("doc1", "Exact Identifier Guide", "Exact identifiers route to BM25 retrieval.", "test"),
        Document("doc2", "Climate Concepts", "Climate anxiety is a semantic concept.", "test"),
        Document("doc3", "Mammal Facts", "Bats are mammals and can fly.", "test"),
        Document("sem_climate_anxiety", "Climate anxiety", "Climate anxiety describes distress about climate change and planetary worry.", "test"),
        Document("sem_impostor_syndrome", "Impostor syndrome", "Impostor syndrome is self-doubt where capable people feel like frauds despite competence.", "test"),
        Document("hipaa_164_512", "HIPAA 164.512", "HIPAA 164.512 covers uses and disclosures without authorization.", "test"),
        Document("hipaa_164_510", "HIPAA 164.510", "HIPAA 164.510 covers opportunity to agree or object.", "test"),
        Document("torch_ce", "torch.nn.CrossEntropyLoss", "torch.nn.CrossEntropyLoss computes cross entropy loss.", "test"),
        Document("torch_nll", "torch.nn.NLLLoss", "torch.nn.NLLLoss computes negative log likelihood loss.", "test"),
    ]


@pytest.fixture
def sample_triples() -> list[Triple]:
    return [
        Triple("kg_mammal_is_vertebrate", "mammal", "is_a", "vertebrate", "doc3"),
        Triple("kg_bat_is_mammal", "bat", "is_a", "mammal", "doc3"),
        Triple("kg_bat_capable_fly", "bat", "capable_of", "fly", "doc3"),
        Triple("kg_bat_has_wings", "bat", "has_property", "wings", "doc3"),
        Triple("kg_whale_is_mammal", "whale", "is_a", "mammal", "doc_whale"),
        Triple("kg_whale_not_fly", "whale", "not_capable_of", "fly", "doc_whale"),
    ]


@pytest.fixture
def temp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    data_dir = tmp_path / "data"
    config = AppConfig(
        data_dir=str(data_dir),
        paths=PathConfig(
            raw_dir=str(data_dir / "raw"),
            processed_dir=str(data_dir / "processed"),
            indices_dir=str(data_dir / "indices"),
            eval_dir=str(data_dir / "eval"),
        ),
        retrieval=RetrievalConfig(default_top_k=2),
        evaluation=EvaluationConfig(
            smoke_queries=["What is PRISM?", "Which backend handles exact identifiers?", "Can mammals fly?"]
        ),
    )
    monkeypatch.setenv("PRISM_DATA_DIR", str(data_dir))
    monkeypatch.delenv("PRISM_CONFIG", raising=False)
    return config
