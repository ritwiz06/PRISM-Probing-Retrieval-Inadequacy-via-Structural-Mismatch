from __future__ import annotations

from prism.answering.generator import synthesize_answer
from prism.app.pipeline import answer_query
from prism.ras.compute_ras import route_query
from prism.schemas import RetrievedItem


def _item(item_id: str, content: str, source_type: str = "document", **metadata) -> RetrievedItem:
    return RetrievedItem(item_id=item_id, content=content, score=1.0, source_type=source_type, metadata=metadata)


def test_structured_answer_object_shape() -> None:
    decision = route_query("RFC-7231")
    answer = synthesize_answer(
        "RFC-7231",
        decision.features,
        decision.ras_scores,
        "bm25",
        [_item("lex_rfc_7231", "RFC-7231 defines HTTP semantics.", title="RFC-7231")],
    )
    assert answer.final_answer
    assert answer.answer_type == "lexical_exact_match"
    assert answer.selected_backend == "bm25"
    assert answer.evidence_ids == ["lex_rfc_7231"]
    assert answer.reasoning_trace_steps


def test_reasoning_trace_includes_backend_evidence_and_rationale() -> None:
    decision = route_query("Can a mammal fly?")
    answer = synthesize_answer(
        "Can a mammal fly?",
        decision.features,
        decision.ras_scores,
        "kg",
        [_item("path:kg_bat_is_mammal->kg_bat_capable_fly", "bat is_a mammal ; bat capable_of fly", "path", query_mode="existential")],
    )
    trace_text = str(answer.reasoning_trace_steps)
    assert "kg" in trace_text
    assert "path:kg_bat_is_mammal->kg_bat_capable_fly" in trace_text
    assert "route_rationale" in trace_text


def test_lexical_answer_synthesis() -> None:
    decision = route_query("RFC-7231")
    answer = synthesize_answer(
        "RFC-7231",
        decision.features,
        decision.ras_scores,
        "bm25",
        [_item("lex_rfc_7231", "RFC-7231 defines HTTP/1.1 semantics and content.", title="RFC-7231")],
    )
    assert "RFC-7231" in answer.final_answer
    assert "semantics" in answer.final_answer


def test_semantic_answer_synthesis() -> None:
    decision = route_query("What feels like climate anxiety?")
    answer = synthesize_answer(
        "What feels like climate anxiety?",
        decision.features,
        decision.ras_scores,
        "dense",
        [_item("sem_climate_anxiety::chunk_0", "Climate anxiety describes distress about climate change.", "chunk", title="Climate anxiety", parent_doc_id="sem_climate_anxiety")],
    )
    assert answer.answer_type == "semantic_summary"
    assert "Climate anxiety" in answer.final_answer


def test_deductive_answer_synthesis_with_counterexample() -> None:
    decision = route_query("Are all mammals able to fly?")
    answer = synthesize_answer(
        "Are all mammals able to fly?",
        decision.features,
        decision.ras_scores,
        "kg",
        [_item("path:kg_whale_is_mammal->kg_whale_not_fly", "whale is_a mammal ; whale not_capable_of fly", "path", query_mode="universal_counterexample")],
    )
    assert answer.final_answer.startswith("No.")
    assert "Counterexample" in answer.final_answer


def test_relational_answer_synthesis_with_fused_evidence() -> None:
    decision = route_query("What bridge connects bat and vertebrate?")
    answer = synthesize_answer(
        "What bridge connects bat and vertebrate?",
        decision.features,
        decision.ras_scores,
        "hybrid",
        [
            _item(
                "hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate",
                "[kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate\n[bm25:rel_bat_vertebrate] bat connects to vertebrate through mammal",
                "hybrid",
                component_ids="path:kg_bat_is_mammal->kg_mammal_is_vertebrate,rel_bat_vertebrate",
                fusion_method="rrf+relational_bundle",
            )
        ],
    )
    assert answer.answer_type == "relational"
    assert "Hybrid connection" in answer.final_answer
    assert "rel_bat_vertebrate" in answer.final_answer


def test_end_to_end_examples_from_each_slice() -> None:
    examples = [
        ("RFC-7231", "bm25"),
        ("What feels like climate anxiety?", "dense"),
        ("Can a mammal fly?", "kg"),
        ("What bridge connects bat and vertebrate?", "hybrid"),
    ]
    for query, backend in examples:
        payload = answer_query(query)
        assert payload["selected_backend"] == backend
        assert payload["answer"]["final_answer"]
        assert payload["reasoning_trace"]
