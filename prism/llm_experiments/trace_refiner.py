from __future__ import annotations

from prism.answering.generator import StructuredAnswer
from prism.llm_experiments.answer_refiner import RefinedAnswer, refine_answer_with_llm
from prism.llm_experiments.local_llm_client import LocalLLMClient
from prism.schemas import RetrievedItem


def refine_trace_with_llm(
    query: str,
    answer: StructuredAnswer,
    evidence: list[RetrievedItem],
    *,
    client: LocalLLMClient | None = None,
) -> RefinedAnswer:
    """Evidence-grounded trace refinement wrapper.

    The implementation delegates to the answer refiner so answer and trace stay
    synchronized. This remains analysis-only and preserves evidence ids/backend.
    """

    return refine_answer_with_llm(query, answer, evidence, client=client or LocalLLMClient())

