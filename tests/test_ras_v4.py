from __future__ import annotations

from pathlib import Path

from prism.ras_v4.explain import explanation_payload
from prism.ras_v4.features import FEATURE_NAMES, extract_joint_features
from prism.ras_v4.model import RASV4Model
from prism.ras_v4.scoring import route_query_v4
from prism.ras_v4.verify_ras_v4 import _human_alignment, _write_csv
from prism.schemas import RetrievedItem


def _evidence(content: str = "RFC-7231 defines HTTP semantics.") -> list[RetrievedItem]:
    return [
        RetrievedItem(
            item_id="doc_rfc_7231",
            content=content,
            score=2.0,
            source_type="document",
            metadata={"title": "RFC-7231", "parent_doc_id": "doc_rfc_7231"},
        ),
        RetrievedItem(
            item_id="doc_rfc_7230",
            content="RFC-7230 defines message syntax.",
            score=0.8,
            source_type="document",
            metadata={"title": "RFC-7230", "parent_doc_id": "doc_rfc_7230"},
        ),
    ]


def _tiny_model() -> RASV4Model:
    queries = [
        ("RFC-7231", "bm25", _evidence()),
        ("What feels like climate anxiety?", "dense", _evidence("Climate anxiety describes distress about climate change.")),
        ("Can a bat fly?", "kg", _evidence("A bat is a mammal and has wings.")),
        ("What bridge connects bat and vertebrate?", "hybrid", _evidence("Bat connects to vertebrate through mammal.")),
    ]
    features = []
    labels = []
    for query, gold, evidence in queries:
        for backend in ("bm25", "dense", "kg", "hybrid"):
            features.append(extract_joint_features(query, backend, evidence, source_type="unit"))
            labels.append(int(backend == gold))
    return RASV4Model.fit(features, labels, seed=5, c_value=0.5)


def test_ras_v4_evidence_feature_vector_shape() -> None:
    vector = extract_joint_features("RFC-7231 exact target", "bm25", _evidence(), source_type="unit")
    assert set(FEATURE_NAMES).issubset(vector.values)
    assert len(vector.ordered_values()) == len(FEATURE_NAMES)
    assert vector.evidence_feature_values["identifier_exact_match"] > 0
    assert "evidence_metadata" in vector.metadata


def test_ras_v4_model_save_load_roundtrip(tmp_path: Path) -> None:
    model = _tiny_model()
    path = model.save(tmp_path / "ras_v4_model.json")
    loaded = RASV4Model.load(path)
    vector = extract_joint_features("RFC-7231", "bm25", _evidence(), source_type="unit")
    assert isinstance(loaded.score(vector), float)
    assert loaded.contribution_groups(vector).keys() >= {"route_contribution", "evidence_contribution"}


def test_ras_v4_score_and_explanation_output_structure() -> None:
    model = _tiny_model()
    evidence_by_backend = {backend: _evidence() for backend in ("bm25", "dense", "kg", "hybrid")}
    decision = route_query_v4("RFC-7231", evidence_by_backend, model=model, source_type="unit")
    payload = explanation_payload(decision)
    assert decision.selected_backend in {"bm25", "dense", "kg", "hybrid"}
    assert payload["candidate_scores"][decision.selected_backend]["top_contributions"]


def test_ras_v4_eval_csv_artifact_structure(tmp_path: Path) -> None:
    payload = {
        "systems": {
            "adversarial_test": {
                "ras_v4": {
                    "total": 1,
                    "route_accuracy": 1.0,
                    "answer_accuracy": 1.0,
                    "evidence_hit_at_k": 1.0,
                    "top1_evidence_hit": 1.0,
                    "mean_route_margin": 0.1,
                    "mean_route_contribution": 0.2,
                    "mean_evidence_contribution": 0.3,
                }
            }
        }
    }
    path = tmp_path / "ras_v4_eval.csv"
    _write_csv(path, payload)
    text = path.read_text(encoding="utf-8")
    assert "dataset,system,total" in text
    assert "adversarial_test,ras_v4" in text


def test_ras_v4_human_comparison_shape() -> None:
    payload = _human_alignment(_tiny_model(), {backend: type("R", (), {"retrieve": lambda self, query, top_k=3: _evidence()})() for backend in ("bm25", "dense", "kg", "hybrid")})
    assert "status" in payload
    if payload["status"] == "evaluated":
        assert "ras_v4_human_preferred_route_alignment" in payload
