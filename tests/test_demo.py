from __future__ import annotations

from pathlib import Path

from prism.demo.data import build_demo_view_model, export_demo_examples, load_benchmark_queries
from prism.demo.report_summary import format_report
from prism.schemas import RetrievedItem


class _FakeRetriever:
    def __init__(self, item_id: str, content: str) -> None:
        self.item_id = item_id
        self.content = content

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        return [
            RetrievedItem(
                item_id=self.item_id,
                content=self.content,
                score=1.0,
                source_type="document",
                metadata={"title": self.item_id, "rank": "1"},
            )
        ][:top_k]


def _fake_retrievers() -> dict[str, object]:
    return {
        "bm25": _FakeRetriever("lex_rfc_7231", "RFC-7231 defines HTTP semantics."),
        "dense": _FakeRetriever("sem_climate_anxiety::chunk_0", "Climate anxiety describes distress."),
        "kg": _FakeRetriever("path:kg_bat_is_mammal->kg_bat_capable_fly", "bat is_a mammal ; bat capable_of fly"),
        "hybrid": _FakeRetriever("hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate", "bat connects to vertebrate through mammal."),
    }


def test_demo_view_model_shape() -> None:
    view_model = build_demo_view_model("RFC-7231", retrievers=_fake_retrievers())
    assert view_model["payload"]["selected_backend"] == "bm25"
    assert view_model["score_rows"]
    assert view_model["evidence_rows"][0]["id"] == "lex_rfc_7231"
    assert view_model["backend_detail_rows"]


def test_benchmark_query_loading_covers_four_slices() -> None:
    benchmarks = load_benchmark_queries()
    assert sorted(benchmarks) == ["deductive", "lexical", "relational", "semantic"]
    assert all(benchmarks[name] for name in benchmarks)
    assert {benchmarks[name][0]["gold_route"] for name in benchmarks} == {"bm25", "dense", "kg", "hybrid"}


def test_export_examples_output_shape(tmp_path: Path) -> None:
    output_path = tmp_path / "demo_examples.json"
    payload = export_demo_examples(output_path)
    assert payload["example_count"] >= 8
    assert {"bm25", "dense", "kg", "hybrid"}.issubset(set(payload["route_families"]))
    assert output_path.exists()
    first = payload["examples"][0]
    assert {"query", "parsed_features", "ras_scores", "selected_backend", "answer", "evidence", "reasoning_trace"} <= set(first)


def test_report_summary_format_includes_counts() -> None:
    text = format_report(
        {
            "corpus_size": 148,
            "kg_size": 99,
            "verification": {
                "lexical": {"top1_correct": 20, "total": 20, "passed": True},
                "semantic": {"top_k": 3, "dense_hit_at_k": 20, "total": 20, "passed": True},
                "kg": {"top_k": 3, "kg_hit_at_k": 20, "total": 20, "passed": True},
                "hybrid": {"top_k": 5, "hybrid_hit_at_k": 20, "total": 20, "passed": True},
                "end_to_end": {"total": 80, "route_accuracy": 1.0, "evidence_hit_at_k": 1.0, "trace_count": 80, "passed": True},
            },
            "examples": [{"label": "Lexical: RFC-7231", "query": "RFC-7231"}],
        }
    )
    assert "Corpus documents: 148" in text
    assert "End-to-end: total=80" in text
