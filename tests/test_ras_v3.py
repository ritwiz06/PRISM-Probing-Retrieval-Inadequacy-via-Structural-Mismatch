from __future__ import annotations

from pathlib import Path

from prism.ras_v3.explain import explanation_payload
from prism.ras_v3.features import FEATURE_NAMES, extract_features
from prism.ras_v3.model import RASV3Model, RASV3TrainingExample
from prism.ras_v3.scoring import route_query_v3
from prism.ras_v3.verify_ras_v3 import _human_alignment, _write_csv


def _tiny_model() -> RASV3Model:
    examples = [
        RASV3TrainingExample("RFC-7231 exact identifier", "bm25", source_type="curated_train"),
        RASV3TrainingExample("What feels like climate anxiety?", "dense", source_type="curated_train"),
        RASV3TrainingExample("Can a bat fly?", "kg", source_type="curated_train"),
        RASV3TrainingExample("What bridge connects bat and vertebrate?", "hybrid", source_type="curated_train"),
        RASV3TrainingExample("ICD-10 J18.9 exact code", "bm25", source_type="public_raw_dev"),
        RASV3TrainingExample("Which concept describes circular economy?", "dense", source_type="adversarial_dev"),
        RASV3TrainingExample("Are all mammals vertebrates?", "kg", source_type="adversarial_dev"),
        RASV3TrainingExample("What relation connects eagle and fish?", "hybrid", source_type="adversarial_dev"),
    ]
    return RASV3Model.fit(examples, seed=3, c_value=0.5)


def test_ras_v3_feature_vector_shape() -> None:
    features = extract_features("Which concept feels like RFC-7231 but means worry?", source_type="adversarial_dev")
    assert set(FEATURE_NAMES).issubset(features.values)
    assert len(features.ordered_values()) == len(FEATURE_NAMES)
    assert "computed_route" in features.metadata


def test_ras_v3_model_save_load_roundtrip(tmp_path: Path) -> None:
    model = _tiny_model()
    path = model.save(tmp_path / "ras_v3_model.json")
    loaded = RASV3Model.load(path)
    features = extract_features("RFC-7231", source_type="curated")
    assert loaded.predict(features) in {"bm25", "dense", "kg", "hybrid"}
    assert loaded.predict_scores(features).keys() == model.predict_scores(features).keys()


def test_ras_v3_decision_and_explanation_shape() -> None:
    model = _tiny_model()
    decision = route_query_v3("What bridge connects bat and vertebrate?", model=model, source_type="adversarial_test")
    payload = explanation_payload(decision)
    assert decision.selected_backend in {"bm25", "dense", "kg", "hybrid"}
    assert payload["selected_backend"] == decision.selected_backend
    assert payload["top_selected_route_contributions"]


def test_ras_v3_eval_csv_artifact_structure(tmp_path: Path) -> None:
    payload = {
        "systems": {
            "adversarial_test": {
                "ras_v3": {
                    "total": 1,
                    "route_accuracy": 1.0,
                    "answer_accuracy": 1.0,
                    "evidence_hit_at_k": 1.0,
                    "top1_evidence_hit": 1.0,
                    "mean_route_margin": 0.4,
                    "low_margin_count": 0,
                }
            }
        }
    }
    path = tmp_path / "ras_v3_eval.csv"
    _write_csv(path, payload)
    text = path.read_text(encoding="utf-8")
    assert "dataset,system,total" in text
    assert "adversarial_test,ras_v3" in text


def test_ras_v3_human_alignment_shape() -> None:
    model = _tiny_model()
    payload = _human_alignment(model)
    assert "status" in payload
    if payload["status"] == "evaluated":
        assert "ras_v3_human_preferred_route_alignment" in payload
