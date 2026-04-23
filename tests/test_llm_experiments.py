from __future__ import annotations

from pathlib import Path

from prism.answering.generator import StructuredAnswer
from prism.llm_experiments.answer_refiner import refine_answer_with_llm
from prism.llm_experiments.llm_router import LLMRouter
from prism.llm_experiments.local_llm_client import LLMResponse
from prism.llm_experiments.router_prompt import parse_router_response
from prism.llm_experiments.verify_llm_router import _write_csv
from prism.schemas import RetrievedItem


class StubClient:
    provider = "stub"
    model = "stub-model"

    def __init__(self, text: str = "", available: bool = True) -> None:
        self.text = text
        self.available = available

    def complete(self, *args, **kwargs) -> LLMResponse:
        return LLMResponse(
            text=self.text,
            available=self.available,
            model=self.model,
            provider=self.provider,
            raw={},
            error="" if self.available else "stub unavailable",
        )

    def diagnostics(self) -> dict[str, object]:
        return {"provider": self.provider, "model": self.model, "available": self.available, "error": "" if self.available else "stub unavailable"}


def test_llm_router_response_parsing_structure() -> None:
    parsed = parse_router_response('{"route":"kg","confidence":0.82,"rationale":"membership query","alternatives":[{"route":"dense","score":0.2}]}')
    assert parsed["route"] == "kg"
    assert parsed["confidence"] == 0.82
    assert parsed["alternatives"][0]["route"] == "dense"


def test_llm_router_output_shape() -> None:
    router = LLMRouter(client=StubClient('{"route":"bm25","confidence":0.91,"rationale":"identifier","alternatives":[]}'))  # type: ignore[arg-type]
    prediction = router.predict("RFC-7231")
    assert prediction.available is True
    assert prediction.route == "bm25"
    assert prediction.as_router_prediction().route == "bm25"


def test_llm_router_unavailable_shape() -> None:
    router = LLMRouter(client=StubClient(available=False))  # type: ignore[arg-type]
    prediction = router.predict("What feels like climate anxiety?")
    assert prediction.available is False
    assert prediction.route == ""
    assert "unavailable" in prediction.rationale.lower()


def test_evidence_grounded_refiner_preserves_metadata_when_unavailable() -> None:
    answer = StructuredAnswer(
        final_answer="RFC-7231: HTTP semantics [evidence: lex_rfc_7231]",
        answer_type="lexical_exact_match",
        selected_backend="bm25",
        route_rationale="Identifier query.",
        evidence_ids=["lex_rfc_7231"],
        evidence_snippets=["RFC-7231 defines HTTP semantics."],
        reasoning_trace_steps=[{"step": "route", "detail": "BM25 selected."}],
        support_score=0.9,
        backend_metadata={},
    )
    evidence = [RetrievedItem("lex_rfc_7231", "RFC-7231 defines HTTP semantics.", 1.0, "document", {})]
    refined = refine_answer_with_llm("RFC-7231", answer, evidence, client=StubClient(available=False))  # type: ignore[arg-type]
    assert refined.available is False
    assert refined.final_answer == answer.final_answer
    assert refined.evidence_ids == ["lex_rfc_7231"]
    assert refined.preserved_backend == "bm25"


def test_llm_eval_csv_artifact_structure(tmp_path: Path) -> None:
    payload = {
        "status": "llm_unavailable",
        "baseline_results": {
            "datasets": {
                "adversarial_test": {
                    "computed_ras": {
                        "route_accuracy": 1.0,
                        "answer_accuracy": 0.9,
                        "evidence_hit_at_k": 1.0,
                    }
                }
            }
        },
        "llm_results": {
            "datasets": {
                "adversarial_test": {
                    "route_accuracy": None,
                    "answer_accuracy": None,
                    "evidence_hit_at_k": None,
                }
            }
        },
    }
    path = tmp_path / "llm_router_eval.csv"
    _write_csv(path, payload)
    assert path.exists()
    assert "llm_runtime_status" in path.read_text(encoding="utf-8")
