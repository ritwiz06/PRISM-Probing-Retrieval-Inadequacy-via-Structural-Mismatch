from __future__ import annotations

from pathlib import Path

from prism.public_graph import compare_structure_grounding as csg
from prism.public_graph import verify_public_graph as vpg
from prism.public_graph.benchmark_builder import build_public_structure_benchmark
from prism.public_graph.build_public_graph import build_public_graph, merge_public_and_demo_triples
from prism.public_graph.extract_graph import PublicGraphTriple, extract_public_graph
from prism.public_graph.loaders import load_public_structure_benchmark, public_structure_counts
from prism.schemas import Document, Triple
from prism.utils import write_json, write_jsonl_documents


def test_public_graph_triple_schema() -> None:
    item = PublicGraphTriple(
        triple_id="pg_bat_is_a_mammal",
        subject="bat",
        predicate="is_a",
        object="mammal",
        source_doc_id="pub_bat",
        confidence=0.9,
        extraction_mode="profile",
        pattern="source_profile",
        snippet="bats are mammals",
    )

    triple = item.to_triple()

    assert triple.subject == "bat"
    assert triple.predicate == "is_a"
    assert item.metadata()["extraction_mode"] == "profile"
    assert item.metadata()["confidence"] == 0.9


def test_public_graph_build_and_load(tmp_path: Path) -> None:
    corpus_path = tmp_path / "public_corpus.jsonl"
    output_path = tmp_path / "public_graph.jsonl"
    write_jsonl_documents(
        corpus_path,
        [
            Document("pub_bat", "Bat", "Bats are mammals and can fly with wings.", "public"),
            Document("pub_bird", "Bird", "Birds are vertebrates.", "public"),
        ],
    )

    payload = build_public_graph(corpus_path, output_path)

    assert output_path.exists()
    assert payload["total"] >= 3
    assert payload["source_doc_count"] >= 1


def test_public_graph_extraction_normalizes_entities() -> None:
    triples = extract_public_graph(
        [
            Document(
                "doc",
                "Demo",
                "A bat is a mammal. A mammal is a vertebrate. A penguin is a bird.",
                "test",
            )
        ]
    )
    keys = {(triple.subject, triple.predicate, triple.object) for triple in triples}

    assert ("bat", "is_a", "mammal") in keys
    assert ("mammal", "is_a", "vertebrate") in keys
    assert ("penguin", "is_a", "bird") in keys


def test_public_structure_benchmark_schema_and_counts(tmp_path: Path) -> None:
    output_path = tmp_path / "public_structure.jsonl"
    path = build_public_structure_benchmark(output_path)
    items = load_public_structure_benchmark(path)
    counts = public_structure_counts(items)

    assert len(items) >= 24
    assert counts["split"]["dev"] > 0
    assert counts["split"]["test"] > 0
    assert set(counts["route_family"]) == {"hybrid", "kg"}
    assert all(item.gold_source_doc_ids for item in items)
    assert all(item.gold_triple_ids for item in items)


def test_public_mixed_mode_provenance_behavior() -> None:
    demo = [Triple("kg_bat_is_mammal", "bat", "is_a", "mammal", "demo_doc")]
    public = [
        Triple("pg_bat_is_a_mammal", "bat", "is_a", "mammal", "pub_bat"),
        Triple("pg_bat_capable_of_fly", "bat", "capable_of", "fly", "pub_bat"),
    ]

    merged, metadata = merge_public_and_demo_triples(demo, public)

    assert len(merged) == 2
    assert metadata["overlap"] == 1
    assert metadata["public_only"] == 1
    assert any(triple.triple_id == "kg_bat_is_mammal" and "public_graph:" in triple.source_doc_id for triple in merged)


def test_public_graph_eval_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(vpg, "JSON_PATH", tmp_path / "public_graph_eval.json")
    monkeypatch.setattr(vpg, "CSV_PATH", tmp_path / "public_graph_eval.csv")
    monkeypatch.setattr(vpg, "MARKDOWN_PATH", tmp_path / "public_graph_eval.md")
    monkeypatch.setattr(vpg, "MODE_PLOT", tmp_path / "mode.png")
    monkeypatch.setattr(vpg, "SPLIT_PLOT", tmp_path / "split.png")
    monkeypatch.setattr(vpg, "build_public_corpus", lambda *args, **kwargs: tmp_path / "public_corpus.jsonl")
    monkeypatch.setattr(vpg, "build_kg", lambda *args, **kwargs: tmp_path / "kg.jsonl")
    monkeypatch.setattr(
        vpg,
        "build_public_graph",
        lambda *args, **kwargs: {
            "path": "public_graph",
            "ttl_path": "public_graph.ttl",
            "metadata_path": "public_graph.json",
            "total": 2,
            "patterns": {"test": 2},
            "average_confidence": 0.8,
            "source_doc_count": 1,
        },
    )
    monkeypatch.setattr(vpg, "build_public_structure_benchmark", lambda *args, **kwargs: tmp_path / "bench.jsonl")
    monkeypatch.setattr(vpg, "read_jsonl_documents", lambda *args, **kwargs: [Document("pub_bat", "Bat", "gold", "test")])
    monkeypatch.setattr(
        vpg,
        "load_public_structure_triples",
        lambda mode: [Triple(f"{mode}_bat", "bat", "is_a", "mammal", "pub_bat")],
    )
    monkeypatch.setattr(vpg, "_build_retrievers", lambda *args, **kwargs: {"bm25": object(), "dense": object(), "kg": object(), "hybrid": object()})
    monkeypatch.setattr(vpg, "load_public_structure_benchmark", lambda *args, **kwargs: _small_public_structure_items())
    monkeypatch.setattr(
        vpg,
        "answer_query",
        lambda query, top_k, retrievers, backend_override: {
            "answer": {"final_answer": "gold"},
            "top_evidence": [
                {
                    "item_id": "e1",
                    "content": "gold bat is_a mammal",
                    "score": 1.0,
                    "source_type": "triple",
                    "metadata": {"kg_mode": "public_graph", "source_doc_id": "pub_bat"},
                }
            ],
            "reasoning_trace": [{"step": "demo"}],
        },
    )
    monkeypatch.setattr(vpg, "answer_matches_gold", lambda answer, gold: True)
    monkeypatch.setattr(vpg, "_plot_mode_performance", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vpg, "_plot_split_performance", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))

    payload = vpg.verify_public_graph(seed=3)

    assert set(payload["structure_modes"]) == {"demo_kg", "public_graph", "mixed_public_demo"}
    assert "computed_ras" in payload["runs"]["public_graph"]["test"]
    assert "public_structure_grounding_coverage" in payload
    assert (tmp_path / "public_graph_eval.json").exists()
    assert (tmp_path / "public_graph_eval.csv").exists()
    assert (tmp_path / "public_graph_eval.md").exists()
    assert (tmp_path / "mode.png").exists()
    assert (tmp_path / "split.png").exists()


def test_public_structure_comparison_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "public_graph_eval.json"
    monkeypatch.setattr(csg, "PUBLIC_GRAPH_JSON", source)
    monkeypatch.setattr(csg, "JSON_PATH", tmp_path / "public_structure_comparison.json")
    monkeypatch.setattr(csg, "MARKDOWN_PATH", tmp_path / "public_structure_comparison.md")
    write_json(source, _small_public_graph_payload())

    payload = csg.compare_structure_grounding()

    assert "comparison" in payload
    assert "test" in payload["comparison"]
    assert "mixed_public_demo_delta_vs_public_graph" in payload["comparison"]["test"]
    assert (tmp_path / "public_structure_comparison.json").exists()
    assert (tmp_path / "public_structure_comparison.md").exists()


def _small_public_structure_items():
    from prism.public_graph.loaders import PublicStructureItem

    return [
        PublicStructureItem(
            id="dev_kg",
            query="Is a bat a mammal?",
            split="dev",
            route_family="kg",
            gold_answer="gold",
            gold_source_doc_ids=["pub_bat"],
            gold_triple_ids=["public_graph_bat"],
            gold_path_ids=[],
            gold_evidence_text="gold",
        ),
        PublicStructureItem(
            id="test_hybrid",
            query="What bridge connects bat and vertebrate?",
            split="test",
            route_family="hybrid",
            gold_answer="gold",
            gold_source_doc_ids=["pub_bat"],
            gold_triple_ids=["public_graph_bat"],
            gold_path_ids=[],
            gold_evidence_text="gold",
        ),
    ]


def _small_public_graph_payload() -> dict[str, object]:
    result = {
        "answer_accuracy": 1.0,
        "evidence_hit_at_k": 1.0,
        "per_family": {
            "kg": {"answer_accuracy": 1.0, "evidence_hit_at_k": 1.0},
            "hybrid": {"answer_accuracy": 1.0, "evidence_hit_at_k": 1.0},
        },
    }
    return {
        "structure_modes": ["demo_kg", "public_graph", "mixed_public_demo"],
        "benchmark": {"total": 2},
        "public_graph": {"total": 2},
        "threats_to_validity": ["demo"],
        "runs": {
            mode: {
                "dev": {"computed_ras": result},
                "test": {"computed_ras": result},
            }
            for mode in ("demo_kg", "public_graph", "mixed_public_demo")
        },
    }
