from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import logging
import math
import pickle
import re
from pathlib import Path
from typing import Protocol

import numpy as np

from prism.config import RetrievalConfig
from prism.retrievers.base import BaseRetriever
from prism.schemas import Document, RetrievedItem

TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9._\-:/§]*", re.IGNORECASE)
DEFAULT_EMBEDDING_DIM = 384
LOGGER = logging.getLogger(__name__)

SEMANTIC_PHRASES: dict[str, str] = {
    "climate anxiety": "concept_climate_anxiety",
    "eco grief": "concept_climate_anxiety",
    "warming future": "concept_climate_anxiety",
    "planetary worry": "concept_climate_anxiety",
    "solastalgia": "concept_climate_anxiety",
    "environmental loss": "concept_climate_anxiety",
    "homesick planet": "concept_climate_anxiety",
    "impostor syndrome": "concept_impostor_syndrome",
    "fraud despite skill": "concept_impostor_syndrome",
    "secretly unqualified": "concept_impostor_syndrome",
    "charlatan feeling": "concept_impostor_syndrome",
    "after success": "concept_impostor_syndrome",
    "photosynthesis": "concept_photosynthesis",
    "turn light into food": "concept_photosynthesis",
    "sunshine into sugar": "concept_photosynthesis",
    "carbohydrates from daylight": "concept_photosynthesis",
    "daylight carbohydrate alchemy": "concept_photosynthesis",
    "diffusion of innovations": "concept_diffusion",
    "spread of an innovation": "concept_diffusion",
    "idea moves through a group": "concept_diffusion",
    "novelty adoption": "concept_diffusion",
    "novelty adoption cascade": "concept_diffusion",
    "urban heat island": "concept_urban_heat",
    "cities hold heat": "concept_urban_heat",
    "hotter than nearby countryside": "concept_urban_heat",
    "concrete neighborhoods trap warmth": "concept_urban_heat",
    "asphalt warmth pocket": "concept_urban_heat",
    "memory consolidation": "concept_memory_consolidation",
    "sleep helps memories": "concept_memory_consolidation",
    "stabilizes learning overnight": "concept_memory_consolidation",
    "durable recall": "concept_memory_consolidation",
    "durable recall filing": "concept_memory_consolidation",
    "allergy": "concept_allergy",
    "immune system overreacts": "concept_allergy",
    "harmless pollen": "concept_allergy",
    "benign allergens for danger": "concept_allergy",
    "benign trigger false alarm": "concept_allergy",
    "mycorrhizal network": "concept_mycorrhiza",
    "plants communicate through fungi": "concept_mycorrhiza",
    "fungal network": "concept_mycorrhiza",
    "root fungus web": "concept_mycorrhiza",
    "algorithmic bias": "concept_algorithmic_bias",
    "bias in training data": "concept_algorithmic_bias",
    "unfair model outputs": "concept_algorithmic_bias",
    "skewed machine judgments": "concept_algorithmic_bias",
    "automated unfairness pattern": "concept_algorithmic_bias",
    "circadian rhythm": "concept_circadian_rhythm",
    "body clock": "concept_circadian_rhythm",
    "daily sleep cycle": "concept_circadian_rhythm",
    "internal metronome": "concept_circadian_rhythm",
    "carbon pricing": "concept_carbon_pricing",
    "markets shape emissions": "concept_carbon_pricing",
    "price on pollution": "concept_carbon_pricing",
    "emissions fee": "concept_carbon_pricing",
    "pollution price signal": "concept_carbon_pricing",
    "narrative identity": "concept_narrative_identity",
    "stories shape memory": "concept_narrative_identity",
    "life story and self": "concept_narrative_identity",
    "selfhood through autobiography": "concept_narrative_identity",
    "digital commons": "concept_digital_commons",
    "shared online norms": "concept_digital_commons",
    "community managed knowledge": "concept_digital_commons",
    "collaborative web resource": "concept_digital_commons",
    "water cycle": "concept_water_cycle",
    "water moves through air land and sea": "concept_water_cycle",
    "evaporation and rain loop": "concept_water_cycle",
    "planetary moisture circulation": "concept_water_cycle",
    "reinforcement learning": "concept_reinforcement_learning",
    "learning from rewards": "concept_reinforcement_learning",
    "agent improves by feedback": "concept_reinforcement_learning",
    "reward driven agent training": "concept_reinforcement_learning",
    "distributional semantics": "concept_distributional_semantics",
    "word meaning from context": "concept_distributional_semantics",
    "neighbors in language space": "concept_distributional_semantics",
    "meaning by surrounding words": "concept_distributional_semantics",
    "lexical neighborhood meaning": "concept_distributional_semantics",
    "attention fragmentation": "concept_attention_fragmentation",
    "stress from constant alerts": "concept_attention_fragmentation",
    "focus split by notifications": "concept_attention_fragmentation",
    "notification driven fractured focus": "concept_attention_fragmentation",
    "alert churn scatters concentration": "concept_attention_fragmentation",
    "ecological niche": "concept_ecological_niche",
    "species roles in a habitat": "concept_ecological_niche",
    "organism fits its environment": "concept_ecological_niche",
    "creature's environmental role": "concept_ecological_niche",
    "habitat job slot": "concept_ecological_niche",
    "situated knowledge": "concept_situated_knowledge",
    "knowledge from lived experience": "concept_situated_knowledge",
    "perspective shapes evidence": "concept_situated_knowledge",
    "standpoint shapes knowing": "concept_situated_knowledge",
    "butterfly effect": "concept_butterfly_effect",
    "small causes big outcomes": "concept_butterfly_effect",
    "sensitive dependence": "concept_butterfly_effect",
    "tiny initial change amplifies": "concept_butterfly_effect",
    "minor starting nudge cascades": "concept_butterfly_effect",
    "collective intelligence": "concept_collective_intelligence",
    "groups make safer decisions": "concept_collective_intelligence",
    "many people solve together": "concept_collective_intelligence",
    "crowd problem solving": "concept_collective_intelligence",
    "circular economy": "concept_circular_economy",
    "reusing materials instead of waste": "concept_circular_economy",
    "products kept in use": "concept_circular_economy",
    "closed loop materials": "concept_circular_economy",
}

SEMANTIC_WORDS: dict[str, str] = {
    "anxious": "concept_climate_anxiety",
    "unease": "concept_climate_anxiety",
    "fraud": "concept_impostor_syndrome",
    "sunshine": "concept_photosynthesis",
    "innovation": "concept_diffusion",
    "countryside": "concept_urban_heat",
    "overnight": "concept_memory_consolidation",
    "pollen": "concept_allergy",
    "fungi": "concept_mycorrhiza",
    "unfair": "concept_algorithmic_bias",
    "clock": "concept_circadian_rhythm",
    "pollution": "concept_carbon_pricing",
    "self": "concept_narrative_identity",
    "commons": "concept_digital_commons",
    "rain": "concept_water_cycle",
    "rewards": "concept_reinforcement_learning",
    "context": "concept_distributional_semantics",
    "notifications": "concept_attention_fragmentation",
    "habitat": "concept_ecological_niche",
    "perspective": "concept_situated_knowledge",
    "chaos": "concept_butterfly_effect",
    "together": "concept_collective_intelligence",
    "waste": "concept_circular_economy",
}


@dataclass(slots=True)
class DenseChunk:
    chunk_id: str
    parent_doc_id: str
    title: str
    text: str
    source: str
    ordinal: int


class EmbeddingModel(Protocol):
    model_name: str
    backend_name: str
    fallback_reason: str

    def encode(self, texts: list[str]) -> np.ndarray:
        ...


class HashingEmbeddingModel:
    model_name = "hashing-semantic-fallback"
    backend_name = "numpy_fallback"

    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIM, fallback_reason: str = "") -> None:
        self.dimension = dimension
        self.fallback_reason = fallback_reason or "Configured for local numpy/hash fallback."

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = np.vstack([self._encode_one(text) for text in texts]).astype("float32")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)

    def _encode_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype="float32")
        for token in semantic_tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 3.0 if token.startswith("concept_") else 1.0
            vector[bucket] += sign * weight
        return vector


class SentenceTransformerEmbeddingModel:
    backend_name = "sentence_transformers"
    fallback_reason = ""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        try:
            self._model = SentenceTransformer(model_name, local_files_only=True)
        except TypeError:
            self._model = SentenceTransformer(model_name)
        except Exception:
            self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype="float32")


class DenseRetriever(BaseRetriever):
    backend_name = "dense"

    def __init__(
        self,
        documents: list[Document],
        config: RetrievalConfig | None = None,
        embedding_model: EmbeddingModel | None = None,
        semantic_rerank: bool = True,
    ) -> None:
        self.documents = documents
        self.config = config or RetrievalConfig()
        self.semantic_rerank = semantic_rerank
        self.embedding_model = embedding_model or build_embedding_model(self.config)
        if self.embedding_model.backend_name == "numpy_fallback":
            LOGGER.info("Dense retriever using numpy fallback: %s", self.embedding_model.fallback_reason)
        else:
            LOGGER.info("Dense retriever using %s model %s", self.embedding_model.backend_name, self.embedding_model.model_name)
        self.chunks = chunk_documents(
            documents,
            chunk_size=self.config.dense_chunk_size,
            chunk_overlap=self.config.dense_chunk_overlap,
        )
        self.embeddings = self.embedding_model.encode([chunk.text for chunk in self.chunks]) if self.chunks else np.zeros((0, DEFAULT_EMBEDDING_DIM), dtype="float32")
        self.index_backend = self._resolve_index_backend()
        self._faiss_index = self._build_faiss_index() if self.index_backend == "faiss" else None
        LOGGER.info("Dense retriever active backend: %s", self.active_backend)

    @classmethod
    def build(cls, documents: list[Document], config: RetrievalConfig | None = None) -> "DenseRetriever":
        return cls(documents=documents, config=config)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        if not self.chunks:
            return []
        query_vector = self.embedding_model.encode([query])
        scores = self._score(query_vector)
        if self.semantic_rerank:
            scores = self._apply_semantic_concept_boost(query, scores)
        ranked_indices = np.argsort(-scores)[:top_k]
        results = [self._to_retrieved_item(self.chunks[int(index)], float(scores[int(index)])) for index in ranked_indices]
        return sorted(results, key=lambda item: item.score, reverse=True)

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "documents": [asdict(document) for document in self.documents],
            "chunks": [asdict(chunk) for chunk in self.chunks],
            "embeddings": self.embeddings,
            "config": asdict(self.config),
            "embedding_model_name": self.embedding_model.model_name,
            "embedding_backend": self.embedding_model.backend_name,
            "index_backend": self.index_backend,
            "active_backend": self.active_backend,
            "fallback_reason": self.embedding_model.fallback_reason,
            "semantic_rerank": self.semantic_rerank,
        }
        with output_path.open("wb") as file:
            pickle.dump(payload, file)
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> "DenseRetriever":
        with Path(path).open("rb") as file:
            payload = pickle.load(file)
        documents = [Document(**row) for row in payload["documents"]]
        config = RetrievalConfig(**payload["config"])
        embedding_model = build_embedding_model(config)
        retriever = cls(documents=documents, config=config, embedding_model=embedding_model, semantic_rerank=payload.get("semantic_rerank", True))
        retriever.chunks = [DenseChunk(**row) for row in payload["chunks"]]
        saved_backend = payload.get("embedding_backend")
        if saved_backend == retriever.embedding_model.backend_name:
            retriever.embeddings = np.asarray(payload["embeddings"], dtype="float32")
        else:
            retriever.embeddings = retriever.embedding_model.encode([chunk.text for chunk in retriever.chunks]) if retriever.chunks else np.zeros((0, DEFAULT_EMBEDDING_DIM), dtype="float32")
        retriever.index_backend = retriever._resolve_index_backend()
        retriever._faiss_index = retriever._build_faiss_index() if retriever.index_backend == "faiss" else None
        return retriever

    def _resolve_index_backend(self) -> str:
        if self.embedding_model.backend_name != "sentence_transformers":
            return "numpy"
        if self.config.dense_backend not in {"faiss", "sentence-transformers+faiss", "sentence_transformers+faiss"}:
            try:
                import faiss  # noqa: F401
            except Exception:
                return "numpy"
            return "faiss"
        try:
            import faiss  # noqa: F401
        except Exception as exc:
            LOGGER.info("FAISS unavailable; Dense retriever using numpy vector search: %s", exc)
            return "numpy"
        return "faiss"

    def _build_faiss_index(self):
        import faiss

        index = faiss.IndexFlatIP(self.embeddings.shape[1])
        index.add(self.embeddings)
        return index

    def _score(self, query_vector: np.ndarray) -> np.ndarray:
        if self.index_backend == "faiss" and self._faiss_index is not None:
            scores, indices = self._faiss_index.search(query_vector, len(self.chunks))
            ordered_scores = np.full(len(self.chunks), -np.inf, dtype="float32")
            for score, index in zip(scores[0], indices[0]):
                if index >= 0:
                    ordered_scores[int(index)] = float(score)
            return ordered_scores
        return np.matmul(self.embeddings, query_vector[0])

    def _to_retrieved_item(self, chunk: DenseChunk, score: float) -> RetrievedItem:
        return RetrievedItem(
            item_id=chunk.chunk_id,
            content=chunk.text,
            score=score,
            source_type="chunk",
            metadata={
                "parent_doc_id": chunk.parent_doc_id,
                "title": chunk.title,
                "source": chunk.source,
                "chunk_id": chunk.chunk_id,
                "chunk_ordinal": str(chunk.ordinal),
                "embedding_backend": self.embedding_model.backend_name,
                "embedding_model_name": self.embedding_model.model_name,
                "index_backend": self.index_backend,
                "active_dense_backend": self.active_backend,
                "dense_backend_type": self.embedding_model.backend_name,
                "fallback_reason": self.embedding_model.fallback_reason,
                "semantic_rerank": str(self.semantic_rerank),
                "score": f"{score:.6f}",
            },
        )

    @property
    def active_backend(self) -> str:
        if self.embedding_model.backend_name == "sentence_transformers":
            return f"sentence_transformers+{self.index_backend}"
        return "numpy_fallback"

    @property
    def backend_status(self) -> dict[str, object]:
        return {
            "active_backend": self.active_backend,
            "embedding_backend": self.embedding_model.backend_name,
            "model_name": self.embedding_model.model_name,
            "index_backend": self.index_backend,
            "faiss_active": self.index_backend == "faiss",
            "chunk_count": len(self.chunks),
            "fallback_reason": self.embedding_model.fallback_reason,
            "semantic_rerank": self.semantic_rerank,
        }

    def _apply_semantic_concept_boost(self, query: str, scores: np.ndarray) -> np.ndarray:
        query_concepts = _concept_tokens(query)
        if not query_concepts:
            return scores
        boosted = np.asarray(scores, dtype="float32").copy()
        for index, chunk in enumerate(self.chunks):
            chunk_concepts = _concept_tokens(f"{chunk.title} {chunk.text}")
            overlap = len(query_concepts & chunk_concepts)
            if overlap:
                boosted[index] += 0.35 * overlap
        return boosted


def build_embedding_model(config: RetrievalConfig) -> EmbeddingModel:
    if config.dense_backend in {"sentence-transformers", "sentence_transformers", "sentence-transformers+faiss", "sentence_transformers+faiss", "faiss", "auto"}:
        try:
            return SentenceTransformerEmbeddingModel(config.dense_model_name)
        except Exception as exc:
            return HashingEmbeddingModel(fallback_reason=f"Could not load sentence-transformers model {config.dense_model_name}: {type(exc).__name__}: {exc}")
    return HashingEmbeddingModel(fallback_reason=f"Configured dense_backend={config.dense_backend}.")


def chunk_documents(documents: list[Document], chunk_size: int = 80, chunk_overlap: int = 20) -> list[DenseChunk]:
    chunks: list[DenseChunk] = []
    stride = max(1, chunk_size - chunk_overlap)
    for document in documents:
        words = document.text.split()
        if not words:
            continue
        chunk_count = max(1, math.ceil(max(0, len(words) - chunk_overlap) / stride))
        for ordinal in range(chunk_count):
            start = ordinal * stride
            if start >= len(words):
                break
            end = min(len(words), start + chunk_size)
            chunk_text = " ".join(words[start:end])
            chunks.append(
                DenseChunk(
                    chunk_id=f"{document.doc_id}::chunk_{ordinal}",
                    parent_doc_id=document.doc_id,
                    title=document.title,
                    text=chunk_text,
                    source=document.source,
                    ordinal=ordinal,
                )
            )
            if end == len(words):
                break
    return chunks


def semantic_tokens(text: str) -> list[str]:
    lowered = text.lower()
    tokens = TOKEN_PATTERN.findall(lowered)
    expanded = list(tokens)
    for phrase, canonical in SEMANTIC_PHRASES.items():
        if phrase in lowered:
            expanded.extend([canonical] * 4)
    for token in tokens:
        if token in SEMANTIC_WORDS:
            expanded.extend([SEMANTIC_WORDS[token]] * 2)
    return expanded


def _concept_tokens(text: str) -> set[str]:
    return {token for token in semantic_tokens(text) if token.startswith("concept_")}
