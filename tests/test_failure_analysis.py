from __future__ import annotations

from pathlib import Path

from prism.analysis import failure_analysis as fa


def test_failure_bucket_structure() -> None:
    row = {
        "slice": "semantic",
        "route_correct": True,
        "evidence_hit": False,
        "top1_hit": False,
        "answer_match": False,
        "retrieved_evidence_ids": ["lex_hipaa_164_510"],
    }

    buckets = fa.assign_error_buckets(row)

    assert "retrieval_miss" in buckets
    assert "semantic_drift" in buckets
    assert "lexical_confusion" in buckets


def test_failure_analysis_cli_output_shape(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(fa, "EVAL_DIR", tmp_path)
    monkeypatch.setattr(fa, "FAILURE_JSON", tmp_path / "failure_analysis.json")
    monkeypatch.setattr(fa, "FAILURE_CSV", tmp_path / "failure_analysis.csv")
    monkeypatch.setattr(fa, "FAILURE_MD", tmp_path / "failure_analysis_summary.md")
    monkeypatch.setattr(fa, "DENSE_COMPARE_JSON", tmp_path / "dense_before_after.json")
    monkeypatch.setattr(fa, "DENSE_COMPARE_MD", tmp_path / "dense_before_after_summary.md")
    monkeypatch.setattr(fa, "ROBUSTNESS_MD", tmp_path / "robustness_summary.md")
    monkeypatch.setattr(fa, "_load_artifacts", lambda: ([], []))

    class FakeDense:
        backend_status = {
            "active_backend": "sentence_transformers+faiss",
            "semantic_rerank": True,
            "model_name": "fake",
        }

    monkeypatch.setattr(fa, "_build_retrievers", lambda documents, triples, variant: {"dense": FakeDense()})
    monkeypatch.setattr(fa, "_evaluate_semantic", lambda retrievers: _semantic_payload())
    monkeypatch.setattr(fa, "_evaluate_external", lambda retrievers: _external_payload())
    monkeypatch.setattr(fa, "evaluate_system", lambda *args, **kwargs: _e2e_payload())

    payload = fa.run_failure_analysis()

    assert payload["failure_count"] >= 1
    assert (tmp_path / "failure_analysis.json").exists()
    assert (tmp_path / "dense_before_after.json").exists()
    assert (tmp_path / "robustness_summary.md").exists()
    assert "sentence_transformers_faiss_robust" in payload["semantic_runs"]


def test_dense_before_after_summary_shape() -> None:
    dense = type("Dense", (), {"backend_status": {"active_backend": "numpy_fallback", "semantic_rerank": True}})()
    retrievers = {name: {"dense": dense} for name in fa.DENSE_VARIANTS}
    semantic_runs = {name: _semantic_payload() for name in fa.DENSE_VARIANTS}
    e2e_runs = {name: _e2e_payload() for name in fa.DENSE_VARIANTS}
    external_runs = {name: _external_payload() for name in fa.DENSE_VARIANTS}

    payload = fa._dense_before_after(retrievers, semantic_runs, e2e_runs, external_runs)

    assert set(payload["runs"]) == set(fa.DENSE_VARIANTS)
    assert "claim_validation_note" in payload
    assert payload["runs"]["numpy_fallback"]["curated_semantic"]["total"] == 1


def _semantic_payload() -> dict[str, object]:
    return {
        "total": 1,
        "top1": 0,
        "hit_at_3": 1,
        "top1_accuracy": 0.0,
        "hit_at_3_accuracy": 1.0,
        "dense_backend_status": {"active_backend": "sentence_transformers+faiss", "semantic_rerank": True},
        "rows": [
            {
                "query": "Which idea is daylight carbohydrate alchemy?",
                "gold_answer": "Photosynthesis.",
                "gold_evidence_id": "sem_photosynthesis",
                "top1_hit": False,
                "hit_at_3": True,
                "top_evidence": [
                    {
                        "item_id": "sem_circadian_rhythm::chunk_0",
                        "parent_doc_id": "sem_circadian_rhythm",
                        "score": 0.9,
                        "title": "Circadian rhythm",
                        "snippet": "Wrong competing semantic neighbor.",
                    }
                ],
            }
        ],
    }


def _e2e_payload() -> dict[str, object]:
    return {
        "total": 1,
        "route_accuracy": 1.0,
        "evidence_hit_at_k": 1.0,
        "answer_accuracy": 0.0,
        "answer_matches": 0,
        "evidence_hits": 1,
        "per_slice": {
            "semantic": {
                "answer_matches": 0,
                "evidence_hits": 1,
                "total": 1,
            }
        },
        "results": [
            {
                "slice": "semantic",
                "query": "Which idea is daylight carbohydrate alchemy?",
                "gold_answer": "Photosynthesis.",
                "answer": "Circadian rhythm.",
                "answer_match": False,
                "gold_evidence_ids": ["sem_photosynthesis"],
                "retrieved_evidence_ids": ["sem_circadian_rhythm", "sem_photosynthesis"],
                "evidence_hit": True,
                "route_correct": True,
            }
        ],
    }


def _external_payload() -> dict[str, object]:
    return {
        "total": 1,
        "answer_matches": 1,
        "answer_accuracy": 1.0,
        "per_family": {"dense": {"answer_matches": 1, "total": 1, "answer_accuracy": 1.0}},
        "rows": [
            {
                "id": "external_sem_photosynthesis",
                "query": "What concept turns daylight into carbohydrates?",
                "route_family": "dense",
                "source_dataset": "NaturalQuestions-style",
                "gold_answer": "Photosynthesis.",
                "answer": "Photosynthesis.",
                "answer_match": True,
                "selected_backend": "dense",
                "top_evidence_ids": ["sem_photosynthesis::chunk_0"],
            }
        ],
    }
