from __future__ import annotations

from pathlib import Path

from prism.human_eval.analyze_annotations import analyze_human_annotations
from prism.human_eval.compare_annotations import analyze_comparative_annotations, load_comparative_annotations
from prism.human_eval.comparative_sample_builder import ComparativeItem, SystemOutput, comparative_counts
from prism.human_eval.load_annotations import load_annotations
from prism.human_eval.rubric import RUBRIC_FIELDS, export_comparative_rubric_and_template, export_rubric_and_template
from prism.human_eval.sample_builder import HumanEvalItem, packet_counts
from prism.human_eval.validation import validate_all_annotations
from prism.utils import write_json


def test_human_eval_item_schema_and_counts() -> None:
    item = HumanEvalItem(
        item_id="he_test",
        benchmark_source="curated",
        system_variant="computed_ras",
        query="RFC-7231",
        gold_route="bm25",
        predicted_route="bm25",
        selected_backend="bm25",
        final_answer="HTTP semantics",
        automatic_correct=True,
        gold_answer="HTTP semantics",
        evidence_ids=["lex_rfc_7231"],
        evidence_snippets=["RFC-7231 defines HTTP semantics."],
        reasoning_trace=[{"step": "route", "detail": "BM25"}],
        route_rationale="Identifier query.",
        route_family="bm25",
        difficulty="easy_curated",
        packet_notes="unit test",
    )
    counts = packet_counts([item])
    assert counts["benchmark_source"]["curated"] == 1
    assert counts["route_family"]["bm25"] == 1
    assert item.reasoning_trace[0]["step"] == "route"


def test_rubric_and_template_export(tmp_path: Path, monkeypatch) -> None:
    packet_path = tmp_path / "packet.json"
    write_json(
        packet_path,
        {
            "items": [
                {
                    "item_id": "he_001",
                    "query": "RFC-7231",
                }
            ]
        },
    )
    monkeypatch.setattr("prism.human_eval.rubric.HUMAN_EVAL_DIR", tmp_path)
    monkeypatch.setattr("prism.human_eval.rubric.RUBRIC_PATH", tmp_path / "rubric.md")
    monkeypatch.setattr("prism.human_eval.rubric.ANNOTATION_TEMPLATE_PATH", tmp_path / "annotation_template.csv")
    payload = export_rubric_and_template(packet_path)
    assert Path(payload["rubric_path"]).exists()
    assert Path(payload["annotation_template_path"]).exists()
    template_text = Path(payload["annotation_template_path"]).read_text(encoding="utf-8")
    assert "trace_faithfulness" in template_text
    assert "he_001" in template_text


def test_annotation_loader_structure(tmp_path: Path) -> None:
    annotations_dir = tmp_path / "annotations"
    annotations_dir.mkdir()
    (annotations_dir / "eval_a.csv").write_text(
        "evaluator_id,item_id,route_appropriateness,evidence_sufficiency,answer_faithfulness,"
        "trace_faithfulness,trace_clarity,overall_usefulness,major_error_type,is_usable,notes\n"
        "ann1,he_001,3,3,2,2,3,3,none,yes,ok\n",
        encoding="utf-8",
    )
    rows = load_annotations(annotations_dir)
    assert len(rows) == 1
    assert rows[0].scores["answer_faithfulness"] == 2
    assert rows[0].major_error_type == "none"


def test_analyze_annotations_no_annotations(tmp_path: Path, monkeypatch) -> None:
    packet_path = tmp_path / "eval_packet.json"
    write_json(
        packet_path,
        {
            "packet_size": 1,
            "counts": {"route_family": {"bm25": 1}},
            "items": [
                {
                    "item_id": "he_001",
                    "benchmark_source": "curated",
                    "route_family": "bm25",
                    "automatic_correct": True,
                    "predicted_route": "bm25",
                    "gold_route": "bm25",
                }
            ],
        },
    )
    monkeypatch.setattr("prism.human_eval.analyze_annotations.PACKET_JSON", packet_path)
    monkeypatch.setattr("prism.human_eval.analyze_annotations.HUMAN_EVAL_DIR", tmp_path)
    monkeypatch.setattr("prism.human_eval.analyze_annotations.SUMMARY_JSON", tmp_path / "human_eval_summary.json")
    monkeypatch.setattr("prism.human_eval.analyze_annotations.SUMMARY_CSV", tmp_path / "human_eval_summary.csv")
    monkeypatch.setattr("prism.human_eval.analyze_annotations.SUMMARY_MD", tmp_path / "human_eval_summary.md")
    monkeypatch.setattr("prism.human_eval.analyze_annotations.TRACE_VALIDITY_MD", tmp_path / "trace_validity_summary.md")
    monkeypatch.setattr("prism.human_eval.analyze_annotations.DISAGREEMENT_JSON", tmp_path / "disagreement_cases.json")
    monkeypatch.setattr("prism.human_eval.analyze_annotations.load_annotations", lambda: [])
    monkeypatch.setattr("prism.human_eval.analyze_annotations.export_rubric_and_template", lambda _path: {})
    payload = analyze_human_annotations()
    assert payload["status"] == "no_annotations"
    assert (tmp_path / "human_eval_summary.md").exists()
    assert (tmp_path / "trace_validity_summary.md").exists()


def test_rubric_fields_include_trace_dimensions() -> None:
    assert "trace_faithfulness" in RUBRIC_FIELDS
    assert "trace_clarity" in RUBRIC_FIELDS


def test_comparative_packet_item_schema_and_counts() -> None:
    output = SystemOutput(
        system_label="computed_ras",
        route="bm25",
        selected_backend="bm25",
        final_answer="HTTP semantics",
        automatic_correct=True,
        evidence_ids=["lex_rfc_7231"],
        evidence_snippets=["RFC-7231 defines HTTP semantics."],
        reasoning_trace=[{"step": "route", "detail": "BM25"}],
        route_rationale="Identifier query.",
        rescue_metadata={"applied": False},
    )
    item = ComparativeItem(
        comparative_item_id="che_001",
        source_benchmark="adversarial",
        query="RFC-7231",
        route_family="bm25",
        difficulty="hard",
        ambiguity_tags=["identifier_ambiguity"],
        system_a_label="computed_ras",
        system_b_label="classifier_router",
        system_a=output,
        system_b=output,
        gold_answer="HTTP semantics",
        gold_route="bm25",
        comparison_tag="computed_vs_classifier_router:trace_evidence_audit",
        selection_reason="unit test",
    )
    counts = comparative_counts([item])
    assert counts["source_benchmark"]["adversarial"] == 1
    assert counts["route_family"]["bm25"] == 1
    assert counts["system_pair"]["computed_ras_vs_classifier_router"] == 1


def test_comparative_rubric_and_template_export(tmp_path: Path, monkeypatch) -> None:
    packet_path = tmp_path / "comparative_packet.json"
    write_json(
        packet_path,
        {
            "items": [
                {
                    "comparative_item_id": "che_001",
                    "query": "RFC-7231",
                }
            ]
        },
    )
    monkeypatch.setattr("prism.human_eval.rubric.HUMAN_EVAL_DIR", tmp_path)
    monkeypatch.setattr("prism.human_eval.rubric.COMPARATIVE_RUBRIC_PATH", tmp_path / "comparative_rubric.md")
    monkeypatch.setattr(
        "prism.human_eval.rubric.COMPARATIVE_ANNOTATION_TEMPLATE_PATH",
        tmp_path / "comparative_annotation_template.csv",
    )
    payload = export_comparative_rubric_and_template(packet_path)
    assert Path(payload["comparative_rubric_path"]).exists()
    assert Path(payload["comparative_annotation_template_path"]).exists()
    template_text = Path(payload["comparative_annotation_template_path"]).read_text(encoding="utf-8")
    assert "overall_preference" in template_text
    assert "che_001" in template_text


def test_comparative_annotation_loader_structure(tmp_path: Path) -> None:
    annotations_dir = tmp_path / "comparative_annotations"
    annotations_dir.mkdir()
    (annotations_dir / "eval_a.csv").write_text(
        "evaluator_id,comparative_item_id,better_supported_answer,more_faithful_trace,clearer_trace,"
        "more_appropriate_route,overall_preference,judgment_confidence,major_difference_type,"
        "needs_adjudication,notes\n"
        "ann1,che_001,A,B,Tie,A,B,2,route_choice,yes,hard case\n",
        encoding="utf-8",
    )
    rows = load_comparative_annotations(annotations_dir)
    assert len(rows) == 1
    assert rows[0].choices["overall_preference"] == "B"
    assert rows[0].needs_adjudication is True


def test_analyze_comparative_annotations_no_annotations(tmp_path: Path, monkeypatch) -> None:
    packet_path = tmp_path / "comparative_packet.json"
    write_json(
        packet_path,
        {
            "packet_size": 1,
            "counts": {"route_family": {"bm25": 1}},
            "items": [
                {
                    "comparative_item_id": "che_001",
                    "source_benchmark": "curated",
                    "route_family": "bm25",
                    "system_a_label": "computed_ras",
                    "system_b_label": "classifier_router",
                    "query": "RFC-7231",
                }
            ],
        },
    )
    monkeypatch.setattr("prism.human_eval.compare_annotations.HUMAN_EVAL_DIR", tmp_path)
    monkeypatch.setattr("prism.human_eval.compare_annotations.COMPARATIVE_PACKET_JSON", packet_path)
    monkeypatch.setattr("prism.human_eval.compare_annotations.COMPARATIVE_ANNOTATION_DIR", tmp_path / "comparative_annotations")
    monkeypatch.setattr("prism.human_eval.compare_annotations.COMPARATIVE_SUMMARY_JSON", tmp_path / "comparative_summary.json")
    monkeypatch.setattr("prism.human_eval.compare_annotations.COMPARATIVE_SUMMARY_CSV", tmp_path / "comparative_summary.csv")
    monkeypatch.setattr("prism.human_eval.compare_annotations.COMPARATIVE_SUMMARY_MD", tmp_path / "comparative_summary.md")
    monkeypatch.setattr("prism.human_eval.compare_annotations.ADJUDICATION_QUEUE_JSON", tmp_path / "adjudication_queue.json")
    monkeypatch.setattr("prism.human_eval.compare_annotations.COMPARATIVE_RESULTS_MD", tmp_path / "comparative_results_for_report.md")
    monkeypatch.setattr("prism.human_eval.compare_annotations.HUMAN_EVAL_WORKFLOW_MD", tmp_path / "human_eval_workflow.md")
    monkeypatch.setattr("prism.human_eval.compare_annotations.load_comparative_annotations", lambda: [])
    monkeypatch.setattr("prism.human_eval.compare_annotations.export_comparative_rubric_and_template", lambda _path: {})
    payload = analyze_comparative_annotations()
    assert payload["status"] == "no_comparative_annotations"
    assert (tmp_path / "comparative_summary.md").exists()
    assert (tmp_path / "adjudication_queue.json").exists()


def test_annotation_validation_structure(tmp_path: Path) -> None:
    standard_packet = tmp_path / "eval_packet.json"
    comparative_packet = tmp_path / "comparative_packet.json"
    standard_dir = tmp_path / "annotations"
    comparative_dir = tmp_path / "comparative_annotations"
    standard_dir.mkdir()
    comparative_dir.mkdir()
    write_json(standard_packet, {"items": [{"item_id": "he_001"}]})
    write_json(comparative_packet, {"items": [{"comparative_item_id": "che_001"}]})
    (standard_dir / "ann.csv").write_text(
        "evaluator_id,item_id,route_appropriateness,evidence_sufficiency,answer_faithfulness,"
        "trace_faithfulness,trace_clarity,overall_usefulness,major_error_type,is_usable,notes\n"
        "ann,he_001,3,3,3,3,3,3,none,yes,\n",
        encoding="utf-8",
    )
    (comparative_dir / "ann.csv").write_text(
        "evaluator_id,comparative_item_id,better_supported_answer,more_faithful_trace,clearer_trace,"
        "more_appropriate_route,overall_preference,judgment_confidence,major_difference_type,"
        "needs_adjudication,notes\n"
        "ann,che_001,A,Tie,Tie,A,A,3,route_choice,no,\n",
        encoding="utf-8",
    )
    payload = validate_all_annotations(
        standard_dir=standard_dir,
        comparative_dir=comparative_dir,
        standard_packet_path=standard_packet,
        comparative_packet_path=comparative_packet,
    )
    assert payload["status"] == "valid"
    assert payload["standard"]["valid_rows"] == 1
    assert payload["comparative"]["valid_rows"] == 1
