from __future__ import annotations

from pathlib import Path

from prism.generalization.benchmark_builder import build_generalization_benchmark
from prism.generalization.loaders import GeneralizationItem, benchmark_counts, load_generalization_benchmark
from prism.generalization.noisy_corpus import build_noisy_corpus, load_noisy_corpus
from prism.generalization import verify_generalization_v2 as gv2
from prism.schemas import Document
from prism.utils import write_jsonl_documents


def test_generalization_item_schema() -> None:
    item = GeneralizationItem(
        id="demo",
        query="Which concept describes worry about climate futures?",
        source_dataset="NaturalQuestions-style",
        split="dev",
        route_family="dense",
        gold_answer="Climate anxiety",
    )

    assert item.id == "demo"
    assert item.split == "dev"
    assert item.route_family == "dense"


def test_generalization_benchmark_build_and_load(tmp_path: Path) -> None:
    path = tmp_path / "generalization_v2.jsonl"
    summary = build_generalization_benchmark(path)
    items = load_generalization_benchmark(path)
    counts = benchmark_counts(items)

    assert summary["total"] == 80
    assert len(items) == 80
    assert counts["split"] == {"dev": 40, "test": 40}
    assert counts["route_family"] == {"bm25": 20, "dense": 20, "hybrid": 20, "kg": 20}
    assert len(counts["source_dataset"]) >= 4


def test_noisy_corpus_build_and_load(tmp_path: Path) -> None:
    clean_path = tmp_path / "corpus.jsonl"
    noisy_path = tmp_path / "corpus_noisy.jsonl"
    write_jsonl_documents(
        clean_path,
        [
            Document("doc_a", "Alpha", "RFC-7231 defines HTTP semantics.", "test"),
            Document("doc_b", "Beta", "Climate anxiety describes ecological worry.", "test"),
        ],
    )

    summary = build_noisy_corpus(clean_path, noisy_path)
    loaded = load_noisy_corpus(noisy_path)

    assert summary["clean_count"] == 2
    assert summary["noise_count"] > 0
    assert summary["total"] == len(loaded)
    assert noisy_path.exists()


def test_generalization_v2_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    clean_path = tmp_path / "clean.jsonl"
    noisy_path = tmp_path / "noisy.jsonl"
    write_jsonl_documents(clean_path, [Document("doc_a", "Alpha", "gold", "test")])
    write_jsonl_documents(noisy_path, [Document("doc_a", "Alpha", "gold", "test"), Document("noise", "Noise", "noise", "test")])

    monkeypatch.setattr(gv2, "JSON_PATH", tmp_path / "generalization_v2.json")
    monkeypatch.setattr(gv2, "CSV_PATH", tmp_path / "generalization_v2.csv")
    monkeypatch.setattr(gv2, "MARKDOWN_PATH", tmp_path / "generalization_v2.md")
    monkeypatch.setattr(gv2, "CLEAN_NOISY_PLOT", tmp_path / "clean_noisy.png")
    monkeypatch.setattr(gv2, "BASELINE_PLOT", tmp_path / "baselines.png")
    monkeypatch.setattr(gv2, "build_generalization_benchmark", lambda *args, **kwargs: {"total": 8})
    monkeypatch.setattr(gv2, "build_corpus", lambda *args, **kwargs: clean_path)
    monkeypatch.setattr(
        gv2,
        "build_noisy_corpus",
        lambda *args, **kwargs: {"clean_path": str(clean_path), "path": str(noisy_path), "clean_count": 1, "noise_count": 1, "total": 2},
    )
    monkeypatch.setattr(gv2, "build_kg", lambda *args, **kwargs: Path("kg.jsonl"))
    monkeypatch.setattr(gv2, "_load_retrievers_for_mode", lambda *args, **kwargs: {"bm25": object(), "dense": object(), "kg": object(), "hybrid": object()})
    monkeypatch.setattr(gv2, "load_generalization_benchmark", lambda: _small_generalization_items())
    monkeypatch.setattr(
        gv2,
        "answer_query",
        lambda query, top_k, retrievers, backend_override: {
            "answer": {"final_answer": "gold"},
            "top_evidence": [{"item_id": "evidence"}],
            "reasoning_trace": [{"step": "demo"}],
        },
    )
    monkeypatch.setattr(gv2, "answer_matches_gold", lambda answer, gold: True)
    monkeypatch.setattr(gv2, "_plot_clean_vs_noisy", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(gv2, "_plot_baselines", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))

    payload = gv2.verify_generalization_v2(seed=3)

    assert payload["benchmark"]["total"] == 8
    assert {"clean", "noisy"} == set(payload["systems"])
    assert {"dev", "test"} == set(payload["systems"]["clean"])
    assert {"computed_ras", "always_bm25", "always_dense", "always_kg", "always_hybrid", "random_router"} <= set(payload["systems"]["clean"]["dev"])
    assert "clean_vs_noisy_deltas" in payload
    assert (tmp_path / "generalization_v2.json").exists()
    assert (tmp_path / "generalization_v2.csv").exists()
    assert (tmp_path / "generalization_v2.md").exists()
    assert (tmp_path / "clean_noisy.png").exists()
    assert (tmp_path / "baselines.png").exists()


def _small_generalization_items() -> list[GeneralizationItem]:
    rows = [
        ("dev_bm25", "RFC-7231", "dev", "bm25"),
        ("dev_dense", "Which concept means climate worry?", "dev", "dense"),
        ("dev_kg", "Can a mammal fly?", "dev", "kg"),
        ("dev_hybrid", "What bridge connects bat and vertebrate?", "dev", "hybrid"),
        ("test_bm25", "HIPAA 164.512", "test", "bm25"),
        ("test_dense", "Which concept describes memory during sleep?", "test", "dense"),
        ("test_kg", "Is a bat a mammal?", "test", "kg"),
        ("test_hybrid", "What relation connects owl and mouse?", "test", "hybrid"),
    ]
    return [
        GeneralizationItem(
            id=item_id,
            query=query,
            source_dataset="unit-test",
            split=split,
            route_family=family,
            gold_answer="gold",
        )
        for item_id, query, split, family in rows
    ]
