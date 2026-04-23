from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from prism.answering.generator import StructuredAnswer
from prism.llm_experiments.local_llm_client import LocalLLMClient
from prism.schemas import RetrievedItem


@dataclass(frozen=True, slots=True)
class RefinedAnswer:
    final_answer: str
    reasoning_trace_steps: list[dict[str, object]]
    available: bool
    model: str
    provider: str
    evidence_ids: list[str]
    preserved_backend: str
    refinement_notes: str
    raw_text: str = ""
    error: str = ""


def refine_answer_with_llm(
    query: str,
    answer: StructuredAnswer,
    evidence: list[RetrievedItem],
    *,
    client: LocalLLMClient | None = None,
) -> RefinedAnswer:
    active_client = client or LocalLLMClient()
    prompt = _prompt(query, answer, evidence)
    response = active_client.complete(
        prompt,
        system="Rewrite only from supplied evidence. Do not add outside facts. Return JSON only.",
        temperature=0.0,
        max_tokens=320,
    )
    if not response.available:
        return RefinedAnswer(
            final_answer=answer.final_answer,
            reasoning_trace_steps=answer.reasoning_trace_steps,
            available=False,
            model=response.model,
            provider=response.provider,
            evidence_ids=answer.evidence_ids,
            preserved_backend=answer.selected_backend,
            refinement_notes="Local LLM unavailable; deterministic answer preserved.",
            raw_text=response.text,
            error=response.error,
        )
    parsed = _parse_refinement(response.text)
    return RefinedAnswer(
        final_answer=str(parsed.get("final_answer") or answer.final_answer),
        reasoning_trace_steps=_trace(parsed.get("reasoning_trace_steps"), answer.reasoning_trace_steps),
        available=True,
        model=response.model,
        provider=response.provider,
        evidence_ids=answer.evidence_ids,
        preserved_backend=answer.selected_backend,
        refinement_notes=str(parsed.get("refinement_notes") or "Evidence-grounded wording refinement."),
        raw_text=response.text,
        error="",
    )


def _prompt(query: str, answer: StructuredAnswer, evidence: list[RetrievedItem]) -> str:
    payload = {
        "task": "Improve readability of the answer and reasoning trace without changing evidence or backend.",
        "query": query,
        "selected_backend": answer.selected_backend,
        "route_rationale": answer.route_rationale,
        "current_answer": asdict(answer),
        "evidence": [
            {
                "item_id": item.item_id,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in evidence
        ],
        "constraints": [
            "Use only the supplied evidence.",
            "Preserve evidence ids.",
            "Do not add facts not present in evidence.",
            "If evidence is insufficient, say insufficient evidence.",
        ],
        "output_schema": {
            "final_answer": "refined answer text",
            "reasoning_trace_steps": [{"step": "short label", "detail": "evidence-grounded detail"}],
            "refinement_notes": "short note on what changed",
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _parse_refinement(text: str) -> dict[str, object]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _trace(value: object, fallback: list[dict[str, object]]) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return fallback
    clean = [item for item in value if isinstance(item, dict)]
    return clean or fallback

