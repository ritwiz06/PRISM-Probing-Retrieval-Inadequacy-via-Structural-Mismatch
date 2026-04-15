from __future__ import annotations

from prism.schemas import AnswerTrace, RouteDecision


def validate_trace(decision: RouteDecision, trace: AnswerTrace, answer: str) -> list[str]:
    issues: list[str] = []
    if decision.selected_backend != min(decision.ras_scores, key=decision.ras_scores.get):
        issues.append("Selected backend is not the minimum-RAS backend.")
    if not trace.evidence_ids:
        issues.append("Answer trace is missing evidence ids.")
    if "all " in answer.lower() and not trace.evidence_ids:
        issues.append("Universal claim missing evidence support.")
    return issues
