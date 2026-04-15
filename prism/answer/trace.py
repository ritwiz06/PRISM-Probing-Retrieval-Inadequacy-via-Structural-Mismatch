from __future__ import annotations

from prism.schemas import AnswerTrace, RetrievedItem, RouteDecision


def build_trace(query: str, decision: RouteDecision, evidence: list[RetrievedItem]) -> AnswerTrace:
    return AnswerTrace(
        query=query,
        backend=decision.selected_backend,
        evidence_ids=[item.item_id for item in evidence],
        ras_scores=decision.ras_scores,
    )
