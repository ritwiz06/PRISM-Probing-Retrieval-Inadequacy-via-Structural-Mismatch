from __future__ import annotations

from pathlib import Path

from prism.router_baselines.classifier_router import ClassifierRouter
from prism.router_baselines.route_confidence import compute_route_confidence
from prism.router_baselines.rule_router import keyword_rule_route
from prism.router_baselines import verify_router_baselines as vrb


def test_keyword_router_output_shape() -> None:
    prediction = keyword_rule_route("What bridge connects bat and vertebrate?")

    assert prediction.route == "hybrid"
    assert set(prediction.scores) == {"bm25", "dense", "kg", "hybrid"}
    assert prediction.rationale


def test_classifier_router_train_load_predict_shape(tmp_path: Path) -> None:
    queries = [
        "RFC-7231",
        "HIPAA 164.512",
        "What feels like climate anxiety?",
        "Which concept is internal metronome?",
        "Can a mammal fly?",
        "Is a bat a mammal?",
        "What bridge connects bat and vertebrate?",
        "What relation connects owl and mouse?",
    ]
    labels = ["bm25", "bm25", "dense", "dense", "kg", "kg", "hybrid", "hybrid"]
    model_path = tmp_path / "router.pkl"

    router = ClassifierRouter(seed=3).fit(queries, labels)
    router.save(model_path)
    loaded = ClassifierRouter.load(model_path)
    prediction = loaded.predict("Find RFC-7231")

    assert model_path.exists()
    assert prediction.route in {"bm25", "dense", "kg", "hybrid"}
    assert set(prediction.scores) == {"bm25", "dense", "kg", "hybrid"}


def test_route_confidence_shape() -> None:
    router = ClassifierRouter(seed=4).fit(
        ["RFC-7231", "climate anxiety", "Can a mammal fly?", "bridge connects bat vertebrate"],
        ["bm25", "dense", "kg", "hybrid"],
    )

    payload = compute_route_confidence("Can a mammal fly?", classifier=router)

    assert payload["selected_backend"] == "kg"
    assert payload["confidence_label"] in {"low", "medium", "high"}
    assert "ras_margin" in payload
    assert "route_rationale" in payload


def test_router_baseline_artifact_structure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(vrb, "EVAL_DIR", tmp_path)
    monkeypatch.setattr(vrb, "ROUTER_JSON", tmp_path / "router_baselines.json")
    monkeypatch.setattr(vrb, "ROUTER_CSV", tmp_path / "router_baselines.csv")
    monkeypatch.setattr(vrb, "ROUTER_MD", tmp_path / "router_baselines_summary.md")
    monkeypatch.setattr(vrb, "CONFIDENCE_JSON", tmp_path / "route_confidence.json")
    monkeypatch.setattr(vrb, "CONFIDENCE_MD", tmp_path / "route_confidence_summary.md")
    monkeypatch.setattr(vrb, "CLASSIFIER_MODEL_PATH", tmp_path / "router_classifier.pkl")
    monkeypatch.setattr(vrb, "ROUTER_COMPARISON_PLOT", tmp_path / "router_comparison.png")
    monkeypatch.setattr(vrb, "ROUTER_DISTRIBUTION_PLOT", tmp_path / "router_distribution.png")
    monkeypatch.setattr(vrb, "CONFIDENCE_PLOT", tmp_path / "confidence.png")
    monkeypatch.setattr(vrb, "load_analysis_retrievers", lambda: {"bm25": object(), "dense": object(), "kg": object(), "hybrid": object()})
    monkeypatch.setattr(vrb, "answer_query", lambda query, top_k, retrievers, backend_override: {"answer": {"final_answer": "gold"}, "reasoning_trace": []})
    monkeypatch.setattr(vrb, "answer_matches_gold", lambda answer, gold: True)
    monkeypatch.setattr(vrb, "_plot_router_comparison", lambda *args: (tmp_path / "router_comparison.png").write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vrb, "_plot_predicted_distribution", lambda *args: (tmp_path / "router_distribution.png").write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vrb, "_plot_confidence", lambda *args: (tmp_path / "confidence.png").write_text("plot", encoding="utf-8"))
    monkeypatch.setattr(vrb, "_curated_rows", _small_curated_rows)
    monkeypatch.setattr(vrb, "_external_rows", _small_external_rows)

    payload = vrb.verify_router_baselines(seed=5)

    assert (tmp_path / "router_baselines.json").exists()
    assert (tmp_path / "route_confidence.json").exists()
    assert {"computed_ras", "keyword_rule_router", "classifier_router", "random_router"} <= set(payload["router_systems"])
    assert "strongest_fixed_backend" in payload
    assert payload["route_confidence_summary"]["total"] == 20


def _small_curated_rows() -> list[dict[str, object]]:
    examples = [
        ("RFC-7231", "bm25", "lexical"),
        ("HIPAA 164.512", "bm25", "lexical"),
        ("Find numpy.linalg.svd", "bm25", "lexical"),
        ("What is torch.nn.CrossEntropyLoss?", "bm25", "lexical"),
        ("What feels like climate anxiety?", "dense", "semantic"),
        ("Which concept is internal metronome?", "dense", "semantic"),
        ("Which term means automated unfairness?", "dense", "semantic"),
        ("What is daylight carbohydrate alchemy?", "dense", "semantic"),
        ("Can a mammal fly?", "kg", "deductive"),
        ("Is a bat a mammal?", "kg", "deductive"),
        ("Are all mammals able to fly?", "kg", "deductive"),
        ("What property allows a bat to fly?", "kg", "deductive"),
        ("What bridge connects bat and vertebrate?", "hybrid", "relational"),
        ("What relation connects owl and mouse?", "hybrid", "relational"),
        ("What bridge connects salmon and vertebrate?", "hybrid", "relational"),
        ("What relation connects duck and swim?", "hybrid", "relational"),
    ]
    return [
        {"id": f"curated_{index}", "benchmark": "curated", "family": family, "query": query, "gold_route": route, "gold_answer": "gold"}
        for index, (query, route, family) in enumerate(examples)
    ]


def _small_external_rows() -> list[dict[str, object]]:
    examples = [
        ("What is ICD-10 J18.9?", "bm25"),
        ("Which term names reward driven agent training?", "dense"),
        ("Can a whale swim?", "kg"),
        ("What bridge connects penguin and vertebrate?", "hybrid"),
    ]
    return [
        {"id": f"external_{index}", "benchmark": "external", "family": route, "query": query, "gold_route": route, "gold_answer": "gold"}
        for index, (query, route) in enumerate(examples)
    ]
