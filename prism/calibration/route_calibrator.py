from __future__ import annotations

from dataclasses import dataclass, field
import re

from prism.analysis.evaluation import BACKENDS
from prism.public_corpus.lexical_retriever import is_identifier_heavy_query
from prism.ras.compute_ras import route_query
from prism.router_baselines.classifier_router import ClassifierRouter
from prism.router_baselines.route_confidence import compute_route_confidence
from prism.router_baselines.rule_router import RouterPrediction, keyword_rule_route


@dataclass(frozen=True, slots=True)
class CalibratorConfig:
    name: str = "dev_balanced"
    classifier_probability_threshold: float = 0.42
    classifier_margin_threshold: float = 0.08
    allow_classifier_override: bool = True
    allow_semantic_bait_override: bool = True
    allow_structural_override: bool = True
    allow_identifier_kg_suppression: bool = True


@dataclass(frozen=True, slots=True)
class CalibratedDecision:
    selected_backend: str
    original_backend: str
    calibrated: bool
    confidence_label: str
    confidence_score: float
    top_competing_backend: str
    rationale: str
    signals: dict[str, object] = field(default_factory=dict)
    ras_scores: dict[str, float] = field(default_factory=dict)
    auxiliary_routes: dict[str, str] = field(default_factory=dict)


class RouteCalibrator:
    """Small deterministic overlay for hard route-boundary cases.

    This class is intentionally not used by the production app path. It is an
    analysis-time router that starts from computed RAS, then applies a narrow
    set of inspectable overrides tuned on adversarial dev only.
    """

    def __init__(self, config: CalibratorConfig | None = None, classifier: ClassifierRouter | None = None) -> None:
        self.config = config or CalibratorConfig()
        self.classifier = classifier

    def predict(self, query: str) -> CalibratedDecision:
        decision = route_query(query)
        keyword = keyword_rule_route(query)
        classifier_prediction = self.classifier.predict(query) if self.classifier is not None else None
        confidence = compute_route_confidence(query, classifier=self.classifier)
        signals = detect_route_signals(query)
        selected = decision.selected_backend
        rationale_parts = [f"Started from computed RAS={selected}."]

        override = self._structural_override(selected, signals)
        if override:
            selected, reason = override
            rationale_parts.append(reason)
        else:
            override = self._semantic_bait_override(selected, signals, classifier_prediction)
            if override:
                selected, reason = override
                rationale_parts.append(reason)
            else:
                override = self._identifier_kg_suppression(selected, signals)
                if override:
                    selected, reason = override
                    rationale_parts.append(reason)
                else:
                    override = self._classifier_override(selected, classifier_prediction, confidence, signals)
                    if override:
                        selected, reason = override
                        rationale_parts.append(reason)

        if selected == decision.selected_backend:
            rationale_parts.append("No calibration override fired.")
        return CalibratedDecision(
            selected_backend=selected,
            original_backend=decision.selected_backend,
            calibrated=selected != decision.selected_backend,
            confidence_label=str(confidence["confidence_label"]),
            confidence_score=float(confidence["confidence_score"]),
            top_competing_backend=str(confidence["top_competing_backend"]),
            rationale=" ".join(rationale_parts),
            signals=signals,
            ras_scores=decision.ras_scores,
            auxiliary_routes={
                "keyword": keyword.route,
                "classifier": classifier_prediction.route if classifier_prediction else "",
            },
        )

    def _structural_override(self, selected: str, signals: dict[str, object]) -> tuple[str, str] | None:
        if not self.config.allow_structural_override:
            return None
        if signals["relational_cue"] and selected != "hybrid":
            return "hybrid", "Relational bridge/connect cue overrode route to Hybrid."
        if signals["deductive_cue"] and not signals["explicit_kg_negation"] and selected != "kg":
            return "kg", "Closed-world or membership/property cue overrode route to KG."
        return None

    def _semantic_bait_override(
        self,
        selected: str,
        signals: dict[str, object],
        classifier_prediction: RouterPrediction | None,
    ) -> tuple[str, str] | None:
        if not self.config.allow_semantic_bait_override or selected != "bm25":
            return None
        classifier_dense = classifier_prediction is not None and classifier_prediction.route == "dense"
        if signals["semantic_cue"] and signals["misleading_exact_cue"] and classifier_dense:
            return "dense", "Semantic cue plus misleading exact-term bait overrode BM25 to Dense."
        if signals["semantic_cue"] and signals["misleading_exact_cue"] and not signals["primary_identifier_query"]:
            return "dense", "Semantic wording with negated/distractor identifier overrode BM25 to Dense."
        return None

    def _identifier_kg_suppression(self, selected: str, signals: dict[str, object]) -> tuple[str, str] | None:
        if not self.config.allow_identifier_kg_suppression:
            return None
        if selected == "kg" and signals["explicit_kg_negation"] and (signals["identifier_heavy"] or signals["api_cue"]):
            return "bm25", "Explicit instruction not to route class/KG substring overrode KG to BM25."
        return None

    def _classifier_override(
        self,
        selected: str,
        classifier_prediction: RouterPrediction | None,
        confidence: dict[str, object],
        signals: dict[str, object],
    ) -> tuple[str, str] | None:
        if not self.config.allow_classifier_override or classifier_prediction is None:
            return None
        if classifier_prediction.route == selected or confidence["confidence_label"] == "high":
            return None
        hard_boundary_signal = (
            signals["misleading_exact_cue"]
            or signals["explicit_kg_negation"]
            or (signals["semantic_cue"] and signals["identifier_heavy"])
            or (signals["relational_cue"] and signals["identifier_heavy"])
        )
        if not hard_boundary_signal:
            return None
        scores = classifier_prediction.scores
        classifier_score = float(scores.get(classifier_prediction.route, 0.0))
        selected_score = float(scores.get(selected, 0.0))
        if (
            classifier_score >= self.config.classifier_probability_threshold
            and classifier_score - selected_score >= self.config.classifier_margin_threshold
        ):
            return classifier_prediction.route, (
                f"Low/medium confidence RAS disagreed with classifier; classifier margin "
                f"{classifier_score - selected_score:.3f} overrode to {classifier_prediction.route}."
            )
        return None


def detect_route_signals(query: str) -> dict[str, object]:
    lowered = query.lower()
    identifiers = _identifiers(query)
    semantic_terms = {
        "concept",
        "idea",
        "process",
        "model",
        "condition",
        "explains",
        "feels",
        "meaning",
        "view",
        "why",
        "how",
        "rather than",
    }
    semantic_cue = any(term in lowered for term in semantic_terms)
    misleading_exact_cue = any(term in lowered for term in (" not ", "despite", "although", "even if", "rather than", "instead of"))
    relational_cue = any(term in lowered for term in ("bridge", "connects", "connection", "relation connects", "what relation"))
    deductive_cue = (
        "closed-world" in lowered
        or "closed world" in lowered
        or lowered.startswith(("can a ", "can an ", "are all ", "is a ", "is an "))
        or " what property" in lowered
        or lowered.startswith("what property")
    )
    explicit_kg_negation = "do not route" in lowered or "not route" in lowered or "substring to kg" in lowered
    primary_identifier_query = bool(identifiers) and not semantic_cue and not relational_cue and not deductive_cue
    return {
        "identifier_heavy": is_identifier_heavy_query(query),
        "identifiers": identifiers,
        "semantic_cue": semantic_cue,
        "misleading_exact_cue": misleading_exact_cue,
        "relational_cue": relational_cue,
        "deductive_cue": deductive_cue,
        "explicit_kg_negation": explicit_kg_negation,
        "api_cue": bool(re.search(r"\b[a-zA-Z_][\w]*\.[\w.]+\b|\bsklearn\b|\bdataclasses\b", query)),
        "primary_identifier_query": primary_identifier_query,
    }


def _identifiers(query: str) -> list[str]:
    patterns = [
        r"\bRFC-?\d+\b",
        r"\bICD-10\s+[A-Z]\d{2}\.\d\b",
        r"\b\d{3}\.\d{3}\b",
        r"§\d+",
        r"\b[a-zA-Z_][\w]*\.[\w.]+\b",
    ]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, query))
    return matches
