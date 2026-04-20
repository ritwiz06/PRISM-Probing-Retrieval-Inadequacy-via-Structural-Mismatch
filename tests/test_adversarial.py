from __future__ import annotations

from pathlib import Path

import pytest

from prism.adversarial.benchmark_builder import build_adversarial_benchmark
from prism.adversarial.failure_analysis import analyze_adversarial_failures
from prism.adversarial import failure_analysis as afa
from prism.adversarial.loaders import AdversarialItem, load_adversarial_benchmark, adversarial_counts
from prism.adversarial import verify_adversarial as vadv
from prism.router_baselines.rule_router import RouterPrediction
from prism.schemas import Document, Triple
from prism.utils import write_json


def test_adversarial_item_schema_validates_tags() -> None:
    item = AdversarialItem(
        id="adv_test",
        query="RFC-7231 but semantic wording",
        split="dev",
        intended_route_family="bm25",
        difficulty="hard",
        ambiguity_tags=["lexical_semantic_overlap"],
        gold_answer="HTTP semantics",
        gold_source_doc_ids=["doc"],
        gold_triple_ids=[],
    )
    assert item.intended_route_family == "bm25"

    with pytest.raises(ValueError):
        AdversarialItem(
            id="bad",
            query="bad",
            split="dev",
            intended_route_family="bm25",
            difficulty="hard",
            ambiguity_tags=["unknown"],
            gold_answer="x",
            gold_source_doc_ids=["doc"],
            gold_triple_ids=[],
        )


def test_adversarial_benchmark_split_counts(tmp_path: Path) -> None:
    path = build_adversarial_benchmark(tmp_path / "adversarial.jsonl")
    items = load_adversarial_benchmark(path)
    counts = adversarial_counts(items)

    assert len(items) >= 40
    assert counts["split"]["dev"] > 0
    assert counts["split"]["test"] > 0
    assert set(counts["intended_route_family"]) == {"bm25", "dense", "hybrid", "kg"}
    assert counts["ambiguity_tags"]


def test_adversarial_verifier_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(vadv, "JSON_PATH", tmp_path / "adversarial_eval.json")
    monkeypatch.setattr(vadv, "CSV_PATH", tmp_path / "adversarial_eval.csv")
    monkeypatch.setattr(vadv, "MARKDOWN_PATH", tmp_path / "adversarial_eval.md")
    monkeypatch.setattr(vadv, "CONFIDENCE_JSON_PATH", tmp_path / "adversarial_confidence.json")
    monkeypatch.setattr(vadv, "CONFIDENCE_MARKDOWN_PATH", tmp_path / "adversarial_confidence.md")
    monkeypatch.setattr(vadv, "ABLATION_MARKDOWN_PATH", tmp_path / "adversarial_ablation.md")
    monkeypatch.setattr(vadv, "BASELINE_PLOT", tmp_path / "baseline.png")
    monkeypatch.setattr(vadv, "CONFIDENCE_PLOT", tmp_path / "confidence.png")
    monkeypatch.setattr(vadv, "TOPK_PLOT", tmp_path / "topk.png")
    monkeypatch.setattr(vadv, "build_adversarial_benchmark", lambda *args, **kwargs: tmp_path / "bench.jsonl")
    monkeypatch.setattr(vadv, "load_adversarial_benchmark", lambda *args, **kwargs: _small_items())
    monkeypatch.setattr(vadv, "_load_hard_context_documents", lambda: [Document("doc", "Doc", "gold", "test")])
    monkeypatch.setattr(vadv, "load_public_structure_triples", lambda mode: [Triple("t1", "bat", "is_a", "mammal", "doc")])
    monkeypatch.setattr(vadv, "_build_retrievers", lambda *args, **kwargs: {"bm25": object(), "dense": object(), "kg": object(), "hybrid": object()})
    monkeypatch.setattr(vadv, "_train_classifier", lambda seed: _FakeClassifier())
    monkeypatch.setattr(vadv, "answer_matches_gold", lambda answer, gold: True)
    monkeypatch.setattr(
        vadv,
        "answer_query",
        lambda query, top_k, retrievers, backend_override: {
            "answer": {"final_answer": "gold"},
            "top_evidence": [{"item_id": "doc", "content": "gold", "score": 1.0, "source_type": "chunk", "metadata": {"parent_doc_id": "doc"}}],
            "reasoning_trace": [{"step": "demo"}],
        },
    )
    monkeypatch.setattr(
        vadv,
        "compute_route_confidence",
        lambda query, classifier=None: {
            "selected_backend": "bm25",
            "confidence_score": 0.5,
            "confidence_label": "medium",
            "ras_margin": 0.2,
            "top_competing_backend": "dense",
            "best_ras_score": 1.0,
            "second_best_ras_score": 1.2,
            "keyword_route": "bm25",
            "classifier_route": "bm25",
            "router_agreement_count": 2,
            "route_rationale": "demo",
            "features": {},
            "ras_scores": {"bm25": 1.0, "dense": 1.2, "kg": 2.0, "hybrid": 2.0},
        },
    )
    monkeypatch.setattr(vadv, "_ablation_analysis", lambda *args, **kwargs: _small_ablation_payload())
    monkeypatch.setattr(vadv, "_plot_baselines_by_tag", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vadv, "_plot_confidence", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vadv, "_plot_top1_topk", lambda payload, path: Path(path).write_text("plot", encoding="utf-8"))

    payload = vadv.verify_adversarial(seed=3)

    assert payload["benchmark"]["total"] == 4
    assert "computed_ras" in payload["systems"]["combined"]
    assert "per_ambiguity_tag" in payload["systems"]["combined"]["computed_ras"]
    assert "confidence" in payload
    assert (tmp_path / "adversarial_eval.json").exists()
    assert (tmp_path / "adversarial_confidence.json").exists()
    assert (tmp_path / "adversarial_ablation.md").exists()


def test_adversarial_failure_analysis_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "adversarial_eval.json"
    monkeypatch.setattr(afa, "ADVERSARIAL_JSON", source)
    monkeypatch.setattr(afa, "JSON_PATH", tmp_path / "adversarial_failures.json")
    monkeypatch.setattr(afa, "MARKDOWN_PATH", tmp_path / "adversarial_failures.md")
    write_json(source, _small_eval_payload())

    payload = analyze_adversarial_failures()

    assert "bucket_counts" in payload
    assert "hardest_examples" in payload
    assert "baseline_subtype_wins" in payload
    assert (tmp_path / "adversarial_failures.json").exists()
    assert (tmp_path / "adversarial_failures.md").exists()


class _FakeClassifier:
    def predict(self, query: str) -> RouterPrediction:
        return RouterPrediction("bm25", {"bm25": 1.0, "dense": 0.0, "kg": 0.0, "hybrid": 0.0}, "fake")


def _small_items() -> list[AdversarialItem]:
    return [
        AdversarialItem("b1", "RFC-7231", "dev", "bm25", "hard", ["identifier_ambiguity"], "gold", ["doc"], []),
        AdversarialItem("d1", "Which concept means worry?", "dev", "dense", "hard", ["lexical_semantic_overlap"], "gold", ["doc"], []),
        AdversarialItem("k1", "Is a bat a mammal?", "test", "kg", "adversarial", ["noisy_structure"], "gold", ["doc"], ["t1"]),
        AdversarialItem("h1", "What bridge connects bat and vertebrate?", "test", "hybrid", "adversarial", ["wrong_bridge_distractor"], "gold", ["doc"], ["t1"]),
    ]


def _small_ablation_payload() -> dict[str, object]:
    row = {"total": 4, "route_accuracy": 1.0, "answer_accuracy": 1.0, "evidence_hit_at_k": 1.0, "top1_evidence_hit": 1.0}
    return {"systems": {"computed_ras": row}, "interpretation": ["demo"]}


def _small_eval_payload() -> dict[str, object]:
    result = {
        "id": "b1",
        "query": "RFC-7231",
        "split": "dev",
        "intended_route_family": "bm25",
        "ambiguity_tags": ["identifier_ambiguity"],
        "predicted_backend": "dense",
        "route_correct": False,
        "answer_correct": False,
        "evidence_hit": True,
        "top1_evidence_hit": False,
        "top1_topk_gap": True,
        "top_evidence_ids": ["doc"],
    }
    system = {
        "total": 1,
        "route_accuracy": 0.0,
        "answer_accuracy": 0.0,
        "evidence_hit_at_k": 1.0,
        "top1_evidence_hit": 0.0,
        "per_ambiguity_tag": {"identifier_ambiguity": {"answer_accuracy": 0.0}},
        "results": [result],
    }
    better_system = {
        **system,
        "answer_accuracy": 1.0,
        "per_ambiguity_tag": {"identifier_ambiguity": {"answer_accuracy": 1.0}},
        "results": [{**result, "answer_correct": True, "route_correct": True, "evidence_hit": True}],
    }
    return {
        "systems": {
            "combined": {
                "computed_ras": system,
                "always_bm25": better_system,
            }
        }
    }
