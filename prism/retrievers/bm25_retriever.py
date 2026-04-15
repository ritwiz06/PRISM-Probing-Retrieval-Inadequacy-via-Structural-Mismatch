from __future__ import annotations

from dataclasses import asdict
import pickle
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from prism.retrievers.base import BaseRetriever
from prism.schemas import Document, RetrievedItem

TOKEN_PATTERN = re.compile(r"§?[a-z0-9]+(?:[._\-:/§][a-z0-9]+)*", re.IGNORECASE)
IDENTIFIER_PATTERN = re.compile(
    r"^(?:§\d+|\d+(?:\.\d+)+|[a-z]+\d+(?:\.\d+)*|[a-z]+(?:[._\-:/§][a-z0-9]+)+)$",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    return text.lower().replace("§ ", "§")


def tokenize(text: str) -> list[str]:
    """Tokenize text while preserving common formal identifiers."""
    normalized = normalize_text(text)
    raw_tokens = TOKEN_PATTERN.findall(normalized)
    tokens: list[str] = []
    for index, token in enumerate(raw_tokens):
        tokens.append(token)
        if "-" in token:
            tokens.append(token.replace("-", ""))
        if "." in token and not token.replace(".", "").isdigit():
            tokens.append(token.replace(".", "_"))
        if token == "rfc" and index + 1 < len(raw_tokens) and raw_tokens[index + 1].isdigit():
            tokens.append(f"rfc-{raw_tokens[index + 1]}")
        if token == "section" and index + 1 < len(raw_tokens):
            tokens.append(raw_tokens[index + 1])
    return tokens


def identifier_tokens(tokens: list[str]) -> set[str]:
    return {token for token in tokens if IDENTIFIER_PATTERN.match(token)}


class BM25Retriever(BaseRetriever):
    backend_name = "bm25"

    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        self.corpus_tokens = [self._document_tokens(document) for document in documents]
        self._index = BM25Okapi(self.corpus_tokens) if self.corpus_tokens else None

    @classmethod
    def build(cls, documents: list[Document]) -> "BM25Retriever":
        return cls(documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        if not self.documents or self._index is None:
            return []

        query_tokens = tokenize(query)
        query_identifiers = identifier_tokens(query_tokens)
        bm25_scores = self._index.get_scores(query_tokens)

        scored: list[tuple[float, float, Document]] = []
        for index, document in enumerate(self.documents):
            document_tokens = set(self.corpus_tokens[index])
            exact_overlap = len(query_identifiers & document_tokens)
            lexical_overlap = len(set(query_tokens) & document_tokens)
            score = float(bm25_scores[index]) + (exact_overlap * 5.0) + (lexical_overlap * 0.05)
            scored.append((score, float(bm25_scores[index]), document))

        ranked = sorted(scored, key=lambda item: (item[0], item[2].doc_id), reverse=True)
        return [self._to_retrieved_item(document, score, bm25_score) for score, bm25_score, document in ranked[:top_k]]

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "documents": [asdict(document) for document in self.documents],
            "corpus_tokens": self.corpus_tokens,
        }
        with output_path.open("wb") as file:
            pickle.dump(payload, file)
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> "BM25Retriever":
        with Path(path).open("rb") as file:
            payload = pickle.load(file)
        documents = [Document(**row) for row in payload["documents"]]
        retriever = cls(documents)
        retriever.corpus_tokens = payload["corpus_tokens"]
        retriever._index = BM25Okapi(retriever.corpus_tokens) if retriever.corpus_tokens else None
        return retriever

    @staticmethod
    def _document_tokens(document: Document) -> list[str]:
        return tokenize(f"{document.title} {document.text}")

    @staticmethod
    def _to_retrieved_item(document: Document, score: float, bm25_score: float) -> RetrievedItem:
        return RetrievedItem(
            item_id=document.doc_id,
            content=document.text,
            score=score,
            source_type="document",
            metadata={
                "title": document.title,
                "source": document.source,
                "bm25_score": f"{bm25_score:.6f}",
            },
        )
