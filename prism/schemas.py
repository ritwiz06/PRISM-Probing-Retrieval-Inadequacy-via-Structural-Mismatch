from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str


@dataclass(slots=True)
class Triple:
    triple_id: str
    subject: str
    predicate: str
    object: str
    source_doc_id: str


@dataclass(slots=True)
class RetrievedItem:
    item_id: str
    content: str
    score: float
    source_type: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class QueryFeatures:
    query: str
    lexical: bool = False
    semantic: bool = False
    deductive: bool = False
    relational: bool = False


@dataclass(slots=True)
class RouteDecision:
    selected_backend: str
    ras_scores: dict[str, float]
    features: QueryFeatures


@dataclass(slots=True)
class AnswerTrace:
    query: str
    backend: str
    evidence_ids: list[str]
    ras_scores: dict[str, float]
