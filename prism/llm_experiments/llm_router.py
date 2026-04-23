from __future__ import annotations

from dataclasses import dataclass

from prism.ras.compute_ras import route_query
from prism.router_baselines.rule_router import RouterPrediction

from prism.llm_experiments.local_llm_client import LocalLLMClient
from prism.llm_experiments.router_prompt import build_router_prompt, parse_router_response


@dataclass(frozen=True, slots=True)
class LLMRouterPrediction:
    route: str
    confidence: float
    rationale: str
    alternatives: list[dict[str, object]]
    available: bool
    model: str
    provider: str
    raw_text: str
    error: str = ""

    def as_router_prediction(self) -> RouterPrediction:
        scores = {backend: 0.0 for backend in ("bm25", "dense", "kg", "hybrid")}
        if self.route in scores:
            scores[self.route] = self.confidence
        for alternative in self.alternatives:
            route = str(alternative.get("route", ""))
            if route in scores:
                scores[route] = max(scores[route], float(alternative.get("score", 0.0)))
        return RouterPrediction(route=self.route, scores=scores, rationale=self.rationale)


class LLMRouter:
    def __init__(self, client: LocalLLMClient | None = None) -> None:
        self.client = client or LocalLLMClient()

    def predict(self, query: str, evidence_hints: dict[str, object] | None = None) -> LLMRouterPrediction:
        decision = route_query(query)
        prompt = build_router_prompt(
            query,
            parsed_features={
                "lexical": decision.features.lexical,
                "semantic": decision.features.semantic,
                "deductive": decision.features.deductive,
                "relational": decision.features.relational,
            },
            ras_scores=decision.ras_scores,
            evidence_hints=evidence_hints,
        )
        response = self.client.complete(
            prompt,
            system="You are a local, analysis-only PRISM route classifier. Return compact valid JSON only.",
            temperature=0.0,
            max_tokens=192,
        )
        if not response.available:
            return LLMRouterPrediction(
                route="",
                confidence=0.0,
                rationale="Local LLM router unavailable.",
                alternatives=[],
                available=False,
                model=response.model,
                provider=response.provider,
                raw_text=response.text,
                error=response.error,
            )
        parsed = parse_router_response(response.text)
        return LLMRouterPrediction(
            route=str(parsed["route"]),
            confidence=float(parsed["confidence"]),
            rationale=str(parsed["rationale"]),
            alternatives=list(parsed["alternatives"]),
            available=bool(parsed["route"]),
            model=response.model,
            provider=response.provider,
            raw_text=response.text,
            error="" if parsed["route"] else "LLM response did not contain a valid PRISM backend.",
        )

    def diagnostics(self) -> dict[str, object]:
        return self.client.diagnostics()

