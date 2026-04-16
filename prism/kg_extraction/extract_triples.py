from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re

from prism.kg_extraction.entity_normalization import is_known_entity, normalize_predicate, triple_key
from prism.schemas import Document, Triple


@dataclass(frozen=True, slots=True)
class ExtractedTriple:
    triple_id: str
    subject: str
    predicate: str
    object: str
    source_doc_id: str
    confidence: float
    pattern: str
    snippet: str

    def to_triple(self) -> Triple:
        return Triple(self.triple_id, self.subject, self.predicate, self.object, self.source_doc_id)

    def metadata(self) -> dict[str, object]:
        return asdict(self)


PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    ("is_a_singular", re.compile(r"\b(?:a|the)?\s*([a-z]+)\s+is\s+(?:a|an)\s+([a-z_ -]+?)(?:[.;,]| and|$)", re.IGNORECASE), 0.82),
    ("are_plural", re.compile(r"\b([a-z]+)s\s+are\s+([a-z]+)s?\b", re.IGNORECASE), 0.72),
    ("capable_of", re.compile(r"\b([a-z]+)\s+is\s+capable\s+of\s+([a-z]+)\b", re.IGNORECASE), 0.86),
    ("can_capability", re.compile(r"\b([a-z]+)s?\s+(?:can|could)\s+([a-z]+)\b", re.IGNORECASE), 0.64),
    ("not_capable_of", re.compile(r"\b([a-z]+)\s+(?:is\s+)?not\s+capable\s+of\s+([a-z]+)\b", re.IGNORECASE), 0.86),
    ("eats", re.compile(r"\b([a-z]+)\s+eats\s+([a-z]+)\b", re.IGNORECASE), 0.90),
    ("has_property", re.compile(r"\b([a-z]+)\s+has\s+(?:property\s+)?([a-z]+)\b", re.IGNORECASE), 0.84),
    ("produces", re.compile(r"\b([a-z]+)\s+produces\s+([a-z]+)\b", re.IGNORECASE), 0.88),
    ("bridge_through", re.compile(r"\b([a-z]+)\s+connects\s+to\s+([a-z]+)\s+through\s+([a-z]+)\b", re.IGNORECASE), 0.78),
)


def extract_triples_from_documents(documents: list[Document]) -> list[ExtractedTriple]:
    extracted: dict[tuple[str, str, str], ExtractedTriple] = {}
    for document in documents:
        for sentence in _sentences(document.text):
            for item in _extract_from_sentence(sentence, document.doc_id):
                key = (item.subject, item.predicate, item.object)
                existing = extracted.get(key)
                if existing is None or item.confidence > existing.confidence:
                    extracted[key] = item
    return sorted(extracted.values(), key=lambda item: item.triple_id)


def _extract_from_sentence(sentence: str, source_doc_id: str) -> list[ExtractedTriple]:
    items: list[ExtractedTriple] = []
    for pattern_name, pattern, confidence in PATTERNS:
        for match in pattern.finditer(sentence):
            if pattern_name == "bridge_through":
                source, target, middle = match.groups()
                items.extend(
                    item
                    for item in (
                        _make_item(source, "is_a", middle, source_doc_id, confidence, pattern_name, sentence),
                        _make_item(middle, "is_a", target, source_doc_id, confidence, pattern_name, sentence),
                    )
                    if item is not None
                )
                continue
            subject, object_ = match.groups()
            predicate = _predicate_for_pattern(pattern_name)
            if pattern_name == "can_capability" and object_.lower() not in {"fly", "swim"}:
                continue
            if pattern_name == "is_a_singular" and object_.lower().strip() in {"capable", "supported"}:
                continue
            item = _make_item(subject, predicate, object_, source_doc_id, confidence, pattern_name, sentence)
            if item is not None:
                items.append(item)
    return items


def _make_item(
    subject: str,
    predicate: str,
    object_: str,
    source_doc_id: str,
    confidence: float,
    pattern: str,
    snippet: str,
) -> ExtractedTriple | None:
    if not is_known_entity(subject) or not is_known_entity(object_):
        return None
    normalized_subject, normalized_predicate, normalized_object = triple_key(subject, predicate, object_)
    triple_id = "xkg_" + _stable_id(normalized_subject, normalized_predicate, normalized_object)
    return ExtractedTriple(
        triple_id=triple_id,
        subject=normalized_subject,
        predicate=normalized_predicate,
        object=normalized_object,
        source_doc_id=source_doc_id,
        confidence=confidence,
        pattern=pattern,
        snippet=snippet.strip(),
    )


def _predicate_for_pattern(pattern_name: str) -> str:
    if pattern_name in {"is_a_singular", "are_plural"}:
        return "is_a"
    if pattern_name in {"capable_of", "can_capability"}:
        return "capable_of"
    if pattern_name == "not_capable_of":
        return "not_capable_of"
    return normalize_predicate(pattern_name)


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.;])\s+", text) if sentence.strip()]


def _stable_id(subject: str, predicate: str, object_: str) -> str:
    digest = hashlib.blake2b(f"{subject}|{predicate}|{object_}".encode("utf-8"), digest_size=6).hexdigest()
    return f"{subject}_{predicate}_{object_}_{digest}".replace("-", "_")
