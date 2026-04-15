from __future__ import annotations

from prism.schemas import RetrievedItem


def build_prompt(query: str, evidence: list[RetrievedItem]) -> str:
    evidence_block = "\n".join(f"[{item.item_id}] {item.content}" for item in evidence)
    return f"Query: {query}\nEvidence:\n{evidence_block}\nAnswer using only the evidence."
