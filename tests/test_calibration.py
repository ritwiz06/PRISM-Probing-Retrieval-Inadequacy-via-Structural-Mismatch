from __future__ import annotations

from pathlib import Path

from prism.adversarial.loaders import AdversarialItem
from prism.calibration.dev_tuning import tune_calibrator_on_adversarial_dev
from prism.calibration.route_calibrator import RouteCalibrator
from prism.calibration.topk_rescue import rescue_topk_evidence
from prism.calibration.verify_calibrated_router import _failure_delta, _write_csv
from prism.router_baselines.rule_router import RouterPrediction
from prism.schemas import RetrievedItem


class StubClassifier:
    def __init__(self, route: str = "dense") -> None:
        self.route = route

    def predict(self, query: str) -> RouterPrediction:
        return RouterPrediction(
            route=self.route,
            scores={"bm25": 0.1, "dense": 0.7, "kg": 0.1, "hybrid": 0.1},
            rationale="stub",
        )


def test_route_calibrator_output_shape() -> None:
    calibrator = RouteCalibrator(classifier=StubClassifier("kg"))  # type: ignore[arg-type]
    decision = calibrator.predict("Under the closed-world demo structure, can a mammal fly despite RFC-7231?")
    assert decision.selected_backend in {"bm25", "dense", "kg", "hybrid"}
    assert decision.original_backend in {"bm25", "dense", "kg", "hybrid"}
    assert isinstance(decision.signals, dict)
    assert "Started from computed RAS" in decision.rationale


def test_topk_rescue_promotes_non_negated_answer_evidence() -> None:
    evidence = [
        RetrievedItem("lex_numpy_linalg_svd", "numpy.linalg.svd performs singular value decomposition.", 3.0, "document", {}),
        RetrievedItem("sem_butterfly_effect", "The butterfly effect says tiny starting changes can cause large later effects.", 2.0, "chunk", {}),
    ]
    rescued, metadata = rescue_topk_evidence(
        "Which idea says tiny starting changes cause large later effects, not numpy.linalg.svd decomposition?",
        evidence,
        "bm25",
    )
    assert metadata["applied"] is True
    assert rescued[0].item_id == "sem_butterfly_effect"
    assert rescued[0].metadata["topk_rescue_checked"] is True


def test_dev_tuning_artifact_structure(tmp_path: Path) -> None:
    items = [
        AdversarialItem(
            id="a1",
            query="Which concept feels like RFC-7231 for emotions?",
            split="dev",
            intended_route_family="dense",
            difficulty="hard",
            ambiguity_tags=["misleading_exact_term"],
            gold_answer="climate anxiety",
            gold_source_doc_ids=["sem_climate_anxiety"],
            gold_triple_ids=[],
        )
    ]
    output = tmp_path / "tuning.json"
    payload = tune_calibrator_on_adversarial_dev(items, StubClassifier("dense"), output)  # type: ignore[arg-type]
    assert output.exists()
    assert payload["selected_config"]["name"]
    assert payload["candidates"]
    assert "adversarial dev" in payload["protocol"]


def test_failure_delta_structure(monkeypatch) -> None:
    def fake_analysis() -> dict[str, object]:
        return {
            "failure_rows": [
                {
                    "id": "adv_x",
                    "query": "hard query",
                    "answer_correct": False,
                    "route_correct": False,
                    "top1_evidence_hit": False,
                    "buckets": ["route boundary confusion", "answer synthesis miss"],
                }
            ]
        }

    monkeypatch.setattr("prism.calibration.verify_calibrated_router.analyze_adversarial_failures", fake_analysis)
    before = {
        "system": "computed_ras",
        "answer_accuracy": 0.0,
        "route_accuracy": 0.0,
        "results": [{"id": "adv_x"}],
    }
    after = {
        "system": "computed_ras_calibrated_topk_rescue",
        "answer_accuracy": 1.0,
        "route_accuracy": 1.0,
        "results": [{"id": "adv_x", "answer_correct": True, "route_correct": True, "top1_evidence_hit": True}],
    }
    payload = _failure_delta(before, after)
    assert payload["fixed_failures"] == 1
    assert payload["bucket_delta"]["route boundary confusion"]["after"] == 0


def test_calibrated_csv_artifact_shape(tmp_path: Path) -> None:
    payload = {
        "systems": {
            "adversarial_test": {
                "computed_ras": {
                    "total": 1,
                    "route_accuracy": 1.0,
                    "answer_accuracy": 1.0,
                    "evidence_hit_at_k": 1.0,
                    "top1_evidence_hit": 1.0,
                    "top1_topk_gap_rate": 0.0,
                    "override_count": 0,
                    "topk_rescue_applied_count": 0,
                }
            }
        }
    }
    path = tmp_path / "calibrated.csv"
    _write_csv(path, payload)
    assert path.exists()
    assert "answer_accuracy" in path.read_text(encoding="utf-8")
