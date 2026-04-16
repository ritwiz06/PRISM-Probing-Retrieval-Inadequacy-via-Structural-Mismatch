from __future__ import annotations

from pathlib import Path

from prism.kg_extraction.build_extracted_kg import build_extracted_kg, merge_triples
from prism.kg_extraction.extract_triples import ExtractedTriple, extract_triples_from_documents
from prism.kg_extraction import verify_structure_shift as vss
from prism.schemas import Document, Triple
from prism.utils import write_jsonl_documents


def test_extracted_triple_schema() -> None:
    item = ExtractedTriple(
        triple_id="xkg_bat_is_mammal",
        subject="bat",
        predicate="is_a",
        object="mammal",
        source_doc_id="doc_bat",
        confidence=0.8,
        pattern="demo",
        snippet="bat is a mammal",
    )

    triple = item.to_triple()

    assert triple.subject == "bat"
    assert triple.predicate == "is_a"
    assert item.metadata()["confidence"] == 0.8


def test_extracted_kg_build_and_load(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    output_path = tmp_path / "kg_extracted.jsonl"
    write_jsonl_documents(
        corpus_path,
        [
            Document("rel_bat", "Bat bridge", "A bat connects to vertebrate through mammal. bat is capable of fly.", "test"),
            Document("rel_food", "Food", "bat eats mosquito. mammal produces milk.", "test"),
        ],
    )

    payload = build_extracted_kg(corpus_path, output_path)

    assert output_path.exists()
    assert payload["total"] >= 3
    assert "bridge_through" in payload["patterns"] or "capable_of" in payload["patterns"]


def test_extract_triples_normalizes_known_entities() -> None:
    triples = extract_triples_from_documents(
        [Document("doc", "Demo", "A penguin connects to vertebrate through bird. dolphin has property echolocation.", "test")]
    )
    keys = {(triple.subject, triple.predicate, triple.object) for triple in triples}

    assert ("penguin", "is_a", "bird") in keys
    assert ("bird", "is_a", "vertebrate") in keys
    assert ("dolphin", "has_property", "echolocation") in keys


def test_mixed_mode_provenance_behavior() -> None:
    curated = [Triple("kg_bat_is_mammal", "bat", "is_a", "mammal", "curated_doc")]
    extracted = [
        Triple("xkg_bat_is_mammal", "bat", "is_a", "mammal", "extracted_doc"),
        Triple("xkg_bat_eats_mosquito", "bat", "eats", "mosquito", "rel_doc"),
    ]

    merged, metadata = merge_triples(curated, extracted)

    assert len(merged) == 2
    assert metadata["overlap"] == 1
    assert metadata["extracted_only"] == 1
    assert any(triple.triple_id == "kg_bat_is_mammal" and "extracted:" in triple.source_doc_id for triple in merged)


def test_structure_shift_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(vss, "JSON_PATH", tmp_path / "structure_shift.json")
    monkeypatch.setattr(vss, "CSV_PATH", tmp_path / "structure_shift.csv")
    monkeypatch.setattr(vss, "MARKDOWN_PATH", tmp_path / "structure_shift.md")
    monkeypatch.setattr(vss, "MODE_PLOT", tmp_path / "mode.png")
    monkeypatch.setattr(vss, "DEGRADATION_PLOT", tmp_path / "degradation.png")
    monkeypatch.setattr(vss, "build_corpus", lambda *args, **kwargs: tmp_path / "corpus.jsonl")
    monkeypatch.setattr(vss, "build_kg", lambda *args, **kwargs: tmp_path / "kg.jsonl")
    monkeypatch.setattr(vss, "build_generalization_benchmark", lambda *args, **kwargs: {"total": 4})
    monkeypatch.setattr(vss, "build_extracted_kg", lambda *args, **kwargs: {"path": "xkg", "total": 2, "patterns": {"demo": 2}, "average_confidence": 0.8})
    monkeypatch.setattr(vss, "read_jsonl_documents", lambda *args, **kwargs: [Document("doc", "Doc", "gold", "test")])
    monkeypatch.setattr(vss, "load_kg_triples_for_mode", lambda mode: [Triple(f"{mode}_t", "bat", "is_a", "mammal", "doc")])
    monkeypatch.setattr(vss, "_build_retrievers_for_kg_mode", lambda *args, **kwargs: {"bm25": object(), "dense": object(), "kg": object(), "hybrid": object()})
    monkeypatch.setattr(vss, "_structure_items", _small_structure_items)
    monkeypatch.setattr(
        vss,
        "answer_query",
        lambda query, top_k, retrievers, backend_override: {
            "answer": {"final_answer": "gold"},
            "top_evidence": [{"item_id": "e1", "content": "gold", "score": 1.0, "source_type": "triple", "metadata": {"kg_mode": "test"}}],
            "reasoning_trace": [{"step": "demo"}],
        },
    )
    monkeypatch.setattr(vss, "answer_matches_gold", lambda answer, gold: True)
    monkeypatch.setattr(vss, "_plot_mode_performance", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vss, "_plot_degradation", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))

    payload = vss.verify_structure_shift()

    assert set(payload["kg_modes"]) == {"curated", "extracted", "mixed"}
    assert "curated_deductive" in payload["runs"]["curated"]
    assert "mode_deltas" in payload
    assert (tmp_path / "structure_shift.json").exists()
    assert (tmp_path / "structure_shift.csv").exists()
    assert (tmp_path / "structure_shift.md").exists()
    assert (tmp_path / "mode.png").exists()
    assert (tmp_path / "degradation.png").exists()


def _small_structure_items() -> dict[str, list[dict[str, object]]]:
    return {
        "curated_deductive": [
            {
                "id": "d1",
                "dataset": "curated_deductive",
                "family": "deductive",
                "query": "Can a mammal fly?",
                "gold_route": "kg",
                "gold_answer": "gold",
                "gold_evidence_ids": [],
            }
        ],
        "curated_relational": [
            {
                "id": "r1",
                "dataset": "curated_relational",
                "family": "relational",
                "query": "What bridge connects bat and vertebrate?",
                "gold_route": "hybrid",
                "gold_answer": "gold",
                "gold_evidence_ids": [],
            }
        ],
    }
