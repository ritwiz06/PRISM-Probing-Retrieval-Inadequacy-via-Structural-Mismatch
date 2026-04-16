from __future__ import annotations

from dataclasses import dataclass
import re

from prism.public_corpus.enrich_documents import (
    PublicDocumentMetadata,
    enriched_document_text,
    extract_identifiers,
    load_enriched_metadata,
)
from prism.retrievers.base import BaseRetriever
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.schemas import Document, RetrievedItem


@dataclass(frozen=True, slots=True)
class PublicLexicalConfig:
    enabled: bool = True
    identifier_boost: float = 8.0
    alias_boost: float = 4.0
    title_boost: float = 3.0
    confidence_threshold: float = 3.0


class PublicAwareBM25Retriever(BaseRetriever):
    backend_name = "bm25"

    def __init__(
        self,
        documents: list[Document],
        metadata: dict[str, PublicDocumentMetadata],
        config: PublicLexicalConfig | None = None,
    ) -> None:
        self.documents = documents
        self.metadata = metadata
        self.config = config or PublicLexicalConfig()
        enhanced_documents = [
            Document(
                doc_id=document.doc_id,
                title=document.title,
                text=enriched_document_text(document, metadata.get(document.doc_id)),
                source=document.source,
            )
            for document in documents
        ]
        self._base = BM25Retriever.build(enhanced_documents)

    @classmethod
    def build(
        cls,
        documents: list[Document],
        metadata: dict[str, PublicDocumentMetadata] | None = None,
        config: PublicLexicalConfig | None = None,
    ) -> "PublicAwareBM25Retriever":
        return cls(documents, metadata or load_enriched_metadata(), config=config)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        base_items = self._base.retrieve(query, top_k=max(top_k, len(self.documents)))
        reranked = [self._rerank_item(query, item) for item in base_items]
        return sorted(reranked, key=lambda item: (item.score, item.item_id), reverse=True)[:top_k]

    def lexical_confidence(self, query: str) -> dict[str, object]:
        top = self.retrieve(query, top_k=1)
        if not top:
            return {"confidence": 0.0, "should_arbitrate": False, "matched_fields": [], "top_doc_id": ""}
        item = top[0]
        public_boost = float(item.metadata.get("public_lexical_boost", "0") or 0.0)
        matched_fields = [field for field in item.metadata.get("public_matched_fields", "").split(",") if field]
        confidence = min(1.0, public_boost / max(1.0, self.config.identifier_boost))
        return {
            "confidence": confidence,
            "should_arbitrate": public_boost >= self.config.confidence_threshold and bool(matched_fields),
            "matched_fields": matched_fields,
            "top_doc_id": item.item_id,
            "matched_identifiers": item.metadata.get("public_matched_identifiers", ""),
            "matched_aliases": item.metadata.get("public_matched_aliases", ""),
            "boost": public_boost,
        }

    def _rerank_item(self, query: str, item: RetrievedItem) -> RetrievedItem:
        metadata = dict(item.metadata)
        doc_metadata = self.metadata.get(item.item_id)
        boost, fields, identifiers, aliases = _public_lexical_boost(query, doc_metadata, self.config)
        metadata.update(
            {
                "public_identifier_match_used": "true" if identifiers else "false",
                "public_matched_fields": ",".join(fields),
                "public_matched_identifiers": ",".join(identifiers),
                "public_matched_aliases": ",".join(aliases),
                "public_lexical_boost": f"{boost:.3f}",
                "public_rerank_enabled": str(self.config.enabled).lower(),
            }
        )
        return RetrievedItem(
            item_id=item.item_id,
            content=item.content,
            score=item.score + boost if self.config.enabled else item.score,
            source_type=item.source_type,
            metadata=metadata,
        )


def is_identifier_heavy_query(query: str) -> bool:
    if extract_identifiers(query):
        return True
    return bool(re.search(r"\b(?:rfc|icd|hipaa|cfr|tf-idf|tfidfvectorizer|dataclasses?|jsonb|torch\.nn|numpy\.linalg)\b", query, re.IGNORECASE))


def _public_lexical_boost(
    query: str,
    metadata: PublicDocumentMetadata | None,
    config: PublicLexicalConfig,
) -> tuple[float, list[str], list[str], list[str]]:
    if metadata is None:
        return 0.0, [], [], []
    lowered = query.lower()
    fields: list[str] = []
    matched_identifiers = [identifier for identifier in metadata.canonical_identifiers if identifier.lower() in lowered]
    matched_aliases = [
        alias
        for alias in metadata.aliases
        if len(alias) >= 4 and re.search(rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])", lowered)
    ]
    boost = 0.0
    if matched_identifiers:
        boost += config.identifier_boost * len(matched_identifiers)
        fields.append("identifier")
    if matched_aliases:
        boost += config.alias_boost * min(2, len(matched_aliases))
        fields.append("alias")
    title_tokens = [token for token in re.findall(r"[a-z0-9]+", metadata.title.lower()) if len(token) >= 4]
    title_hits = [token for token in title_tokens if re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", lowered)]
    if title_hits and len(title_hits) >= min(2, len(title_tokens)):
        boost += config.title_boost
        fields.append("title")
    return boost, sorted(set(fields)), matched_identifiers, sorted(set(matched_aliases))
