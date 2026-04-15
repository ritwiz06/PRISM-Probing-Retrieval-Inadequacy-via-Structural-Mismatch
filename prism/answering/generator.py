from __future__ import annotations

from dataclasses import dataclass

from prism.answering.reasoning_trace import build_reasoning_trace, route_rationale
from prism.schemas import QueryFeatures, RetrievedItem


@dataclass(slots=True)
class StructuredAnswer:
    final_answer: str
    answer_type: str
    selected_backend: str
    route_rationale: str
    evidence_ids: list[str]
    evidence_snippets: list[str]
    reasoning_trace_steps: list[dict[str, object]]
    support_score: float
    backend_metadata: dict[str, object]


def synthesize_answer(
    query: str,
    features: QueryFeatures,
    ras_scores: dict[str, float],
    selected_backend: str,
    evidence: list[RetrievedItem],
) -> StructuredAnswer:
    if not evidence:
        final = "insufficient evidence"
        note = "No evidence was retrieved."
        answer_type = "insufficient"
    elif selected_backend == "bm25":
        final, note = _bm25_answer(evidence)
        answer_type = "lexical_exact_match"
    elif selected_backend == "dense":
        final, note = _dense_answer(evidence)
        answer_type = "semantic_summary"
    elif selected_backend == "kg":
        final, note = _kg_answer(query, evidence)
        answer_type = "deductive"
    elif selected_backend == "hybrid":
        final, note = _hybrid_answer(evidence)
        answer_type = "relational"
    else:
        final = evidence[0].content
        note = "Used generic evidence-first synthesis."
        answer_type = "generic"

    trace = build_reasoning_trace(query, features, ras_scores, selected_backend, evidence, note)
    return StructuredAnswer(
        final_answer=final,
        answer_type=answer_type,
        selected_backend=selected_backend,
        route_rationale=route_rationale(selected_backend, features, ras_scores),
        evidence_ids=[item.item_id for item in evidence],
        evidence_snippets=[_snippet(item.content) for item in evidence],
        reasoning_trace_steps=trace,
        support_score=_support_score(evidence),
        backend_metadata=_backend_metadata(evidence),
    )


def _bm25_answer(evidence: list[RetrievedItem]) -> tuple[str, str]:
    lead = evidence[0]
    title = lead.metadata.get("title", lead.item_id)
    return f"{title}: {lead.content} [evidence: {lead.item_id}]", "Returned the highest-ranked exact-match lexical evidence."


def _dense_answer(evidence: list[RetrievedItem]) -> tuple[str, str]:
    lead = evidence[0]
    title = lead.metadata.get("title", lead.metadata.get("parent_doc_id", lead.item_id))
    return f"{title}. {lead.content} [evidence: {lead.item_id}]", "Summarized the top semantic chunk."


def _kg_answer(query: str, evidence: list[RetrievedItem]) -> tuple[str, str]:
    lowered = query.lower()
    lead = evidence[0]
    mode = lead.metadata.get("query_mode", "")
    content = lead.content
    if "universal_counterexample" in mode:
        all_counterexamples = "; ".join(item.content for item in evidence if item.metadata.get("query_mode") == "universal_counterexample")
        ids = ", ".join(item.item_id for item in evidence if item.metadata.get("query_mode") == "universal_counterexample")
        return f"No. Counterexample evidence: {all_counterexamples or content}. [evidence: {ids or lead.item_id}]", "Used KG counterexample evidence for a universal claim."
    if "existential" in mode:
        return f"Yes. Existential support in the demo KG: {content}. [evidence: {lead.item_id}]", "Used KG membership plus property support."
    if lowered.startswith("is ") or "is a " in lowered:
        if lead.source_type == "path":
            return f"Yes, indirectly: {content}. [evidence: {lead.item_id}]", "Used KG inheritance path evidence."
        return f"Yes. {content}. [evidence: {lead.item_id}]", "Used KG membership evidence."
    if "not_capable_of" in content:
        return f"No. {content}. [evidence: {lead.item_id}]", "Used explicit KG negation evidence."
    return f"{content}. [evidence: {lead.item_id}]", f"Used KG {mode or 'structured'} evidence."


def _hybrid_answer(evidence: list[RetrievedItem]) -> tuple[str, str]:
    lead = evidence[0]
    components = lead.metadata.get("component_ids", lead.item_id)
    return (
        f"Hybrid connection: {lead.content}. This combines structured evidence plus text relation evidence. [fused evidence: {components}]",
        "Combined structured KG evidence with text evidence using fused Hybrid retrieval.",
    )


def _support_score(evidence: list[RetrievedItem]) -> float:
    if not evidence:
        return 0.0
    return min(1.0, max(item.score for item in evidence) / (1.0 + max(item.score for item in evidence)))


def _backend_metadata(evidence: list[RetrievedItem]) -> dict[str, object]:
    if not evidence:
        return {}
    return {
        "top_evidence_type": evidence[0].source_type,
        "top_query_mode": evidence[0].metadata.get("query_mode"),
        "top_fusion_method": evidence[0].metadata.get("fusion_method"),
        "top_contributing_backends": evidence[0].metadata.get("contributing_backends"),
    }


def _snippet(text: str, limit: int = 240) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."
