from __future__ import annotations

from prism.schemas import RetrievedItem


def generate_answer(query: str, evidence: list[RetrievedItem]) -> str:
    if not evidence:
        return "insufficient evidence"
    lead = evidence[0]
    return f"{lead.content} [evidence: {', '.join(item.item_id for item in evidence)}]"
