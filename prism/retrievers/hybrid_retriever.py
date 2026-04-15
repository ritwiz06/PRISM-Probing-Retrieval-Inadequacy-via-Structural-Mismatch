from __future__ import annotations

import json
from dataclasses import dataclass

from prism.retrievers.base import BaseRetriever
from prism.schemas import RetrievedItem


@dataclass(slots=True)
class HybridConfig:
    rrf_k: int = 60
    enabled_backends: tuple[str, ...] = ("dense", "kg", "bm25")
    backend_weights: dict[str, float] | None = None
    candidate_multiplier: int = 5


class HybridRetriever(BaseRetriever):
    backend_name = "hybrid"

    def __init__(self, retrievers: list[BaseRetriever], config: HybridConfig | None = None) -> None:
        self.retrievers = {retriever.backend_name: retriever for retriever in retrievers}
        self.config = config or HybridConfig()
        self.backend_weights = self.config.backend_weights or {"dense": 1.0, "kg": 1.2, "bm25": 0.9}

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        per_backend = self._retrieve_candidates(query, top_k=max(top_k * self.config.candidate_multiplier, top_k))
        fused = self._rrf_fuse(per_backend)
        if _is_relational_query(query) and "kg" in per_backend:
            fused.update(self._relational_bundles(per_backend))
        return sorted(fused.values(), key=lambda item: (item.score, item.item_id), reverse=True)[:top_k]

    def _retrieve_candidates(self, query: str, top_k: int) -> dict[str, list[RetrievedItem]]:
        candidates: dict[str, list[RetrievedItem]] = {}
        for backend_name in self.config.enabled_backends:
            retriever = self.retrievers.get(backend_name)
            if retriever is None:
                continue
            candidates[backend_name] = retriever.retrieve(query, top_k=top_k)
        return candidates

    def _rrf_fuse(self, per_backend: dict[str, list[RetrievedItem]]) -> dict[str, RetrievedItem]:
        merged: dict[str, RetrievedItem] = {}
        components: dict[str, list[tuple[str, int, RetrievedItem]]] = {}
        scores: dict[str, float] = {}

        for backend_name, items in per_backend.items():
            weight = self.backend_weights.get(backend_name, 1.0)
            for rank, item in enumerate(items, start=1):
                key = _canonical_key(backend_name, item)
                scores[key] = scores.get(key, 0.0) + weight * (1.0 / (self.config.rrf_k + rank))
                components.setdefault(key, []).append((backend_name, rank, item))

        for key, component_rows in components.items():
            representative = component_rows[0][2]
            merged[f"hybrid:{key}"] = _build_fused_item(
                fused_id=f"hybrid:{key}",
                score=scores[key],
                components=component_rows,
                fusion_method="rrf",
                evidence_type=_evidence_type(representative),
            )
        return merged

    def _relational_bundles(self, per_backend: dict[str, list[RetrievedItem]]) -> dict[str, RetrievedItem]:
        bundles: dict[str, RetrievedItem] = {}
        kg_items = [item for item in per_backend.get("kg", []) if item.source_type in {"path", "triple"}]
        text_items = per_backend.get("bm25", []) + per_backend.get("dense", [])
        for kg_rank, kg_item in enumerate(kg_items[:3], start=1):
            for text_rank, text_item in enumerate(text_items[:6], start=1):
                if not _text_relevant_to_kg(text_item, kg_item):
                    continue
                text_backend = text_item.metadata.get("embedding_backend") and "dense" or "bm25"
                component_rows = [("kg", kg_rank, kg_item), (text_backend, text_rank, text_item)]
                fused_id = f"hybrid:bundle:{kg_item.item_id}+{_component_id(text_item)}"
                score = (
                    self.backend_weights.get("kg", 1.0) * (1.0 / (self.config.rrf_k + kg_rank))
                    + self.backend_weights.get(text_backend, 1.0) * (1.0 / (self.config.rrf_k + text_rank))
                    + 0.05
                )
                bundles[fused_id] = _build_fused_item(
                    fused_id=fused_id,
                    score=score,
                    components=component_rows,
                    fusion_method="rrf+relational_bundle",
                    evidence_type="hybrid_relational",
                )
        return bundles


def _build_fused_item(
    fused_id: str,
    score: float,
    components: list[tuple[str, int, RetrievedItem]],
    fusion_method: str,
    evidence_type: str,
) -> RetrievedItem:
    component_ids = [_component_id(item) for _, _, item in components]
    contributing_backends = [backend for backend, _, _ in components]
    raw_ranks = {backend: rank for backend, rank, _ in components}
    raw_scores = {backend: item.score for backend, _, item in components}
    content = "\n".join(f"[{backend}:{_component_id(item)}] {item.content}" for backend, _, item in components)
    metadata = {
        "contributing_backends": ",".join(sorted(set(contributing_backends))),
        "component_ids": ",".join(component_ids),
        "raw_ranks": json.dumps(raw_ranks, sort_keys=True),
        "raw_scores": json.dumps(raw_scores, sort_keys=True),
        "fusion_method": fusion_method,
        "evidence_type": evidence_type,
    }

    for _, _, item in components:
        if "parent_doc_id" in item.metadata:
            metadata.setdefault("parent_doc_id", item.metadata["parent_doc_id"])
        if "chunk_id" in item.metadata:
            metadata.setdefault("chunk_id", item.metadata["chunk_id"])
        if item.source_type == "document":
            metadata.setdefault("parent_doc_id", item.item_id)
        if "triple_id" in item.metadata:
            metadata.setdefault("triple_id", item.metadata["triple_id"])
        if "path_id" in item.metadata:
            metadata.setdefault("path_id", item.metadata["path_id"])
        if "source_doc_id" in item.metadata:
            metadata.setdefault("kg_source_doc_id", item.metadata["source_doc_id"])

    return RetrievedItem(
        item_id=fused_id,
        content=content or "No renderable evidence.",
        score=score,
        source_type="hybrid",
        metadata=metadata,
    )


def _canonical_key(backend_name: str, item: RetrievedItem) -> str:
    if backend_name == "kg":
        return f"kg:{item.item_id}"
    if "parent_doc_id" in item.metadata:
        return f"text:{item.metadata['parent_doc_id']}"
    return f"text:{item.item_id}"


def _component_id(item: RetrievedItem) -> str:
    return item.metadata.get("path_id") or item.metadata.get("triple_id") or item.metadata.get("chunk_id") or item.item_id


def _evidence_type(item: RetrievedItem) -> str:
    if item.source_type == "path":
        return "kg_path"
    if item.source_type == "triple":
        return "kg_triple"
    if item.source_type == "chunk":
        return "text_chunk"
    return "text_document"


def _is_relational_query(query: str) -> bool:
    lowered = query.lower()
    return any(marker in lowered for marker in ("connect", "bridge", "between", "relation", "path", "multi-hop", "links"))


def _text_relevant_to_kg(text_item: RetrievedItem, kg_item: RetrievedItem) -> bool:
    text = f"{text_item.content} {text_item.metadata.get('title', '')}".lower()
    subject = kg_item.metadata.get("subject", "").replace("_", " ").lower()
    object_ = kg_item.metadata.get("object", "").replace("_", " ").lower()
    predicate = kg_item.metadata.get("predicate", "").replace("_", " ").lower()
    kg_terms = [term for term in [subject, object_, *predicate.split(" -> ")] if term]
    return sum(1 for term in kg_terms if term and term in text) >= 1
