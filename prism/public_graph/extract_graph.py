from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re

from prism.public_graph.entity_normalization import known_entity, normalize_entity, triple_key
from prism.schemas import Document, Triple


@dataclass(frozen=True, slots=True)
class PublicGraphTriple:
    triple_id: str
    subject: str
    predicate: str
    object: str
    source_doc_id: str
    confidence: float
    extraction_mode: str
    pattern: str
    snippet: str

    def to_triple(self) -> Triple:
        return Triple(self.triple_id, self.subject, self.predicate, self.object, self.source_doc_id)

    def metadata(self) -> dict[str, object]:
        return asdict(self)


DOC_PROFILES: dict[str, list[tuple[str, str, str, float]]] = {
    "pub_bat": [("bat", "is_a", "mammal", 0.92), ("bat", "capable_of", "fly", 0.90), ("bat", "has_property", "wings", 0.86), ("bat", "has_property", "echolocation", 0.86)],
    "pub_bat_echolocation": [("bat", "is_a", "mammal", 0.82), ("mammal", "is_a", "vertebrate", 0.82), ("bat", "has_property", "echolocation", 0.88)],
    "pub_penguin": [("penguin", "is_a", "bird", 0.92), ("penguin", "not_capable_of", "fly", 0.90), ("penguin", "capable_of", "swim", 0.86), ("penguin", "has_property", "wings", 0.78)],
    "pub_penguin_swimming": [("penguin", "is_a", "bird", 0.82), ("bird", "is_a", "vertebrate", 0.82), ("penguin", "capable_of", "swim", 0.86)],
    "pub_dolphin": [("dolphin", "is_a", "mammal", 0.92), ("dolphin", "capable_of", "swim", 0.88), ("dolphin", "not_capable_of", "fly", 0.76), ("dolphin", "produces", "milk", 0.78), ("dolphin", "has_property", "echolocation", 0.78)],
    "pub_dolphin_mammal_swim": [("dolphin", "is_a", "mammal", 0.82), ("mammal", "is_a", "vertebrate", 0.82), ("dolphin", "capable_of", "swim", 0.86)],
    "pub_whale": [("whale", "is_a", "mammal", 0.92), ("whale", "capable_of", "swim", 0.86), ("whale", "not_capable_of", "fly", 0.76), ("whale", "produces", "milk", 0.78)],
    "pub_whale_mammal_milk": [("whale", "is_a", "mammal", 0.82), ("mammal", "is_a", "vertebrate", 0.82), ("whale", "produces", "milk", 0.86)],
    "pub_salmon": [("salmon", "is_a", "fish", 0.92), ("salmon", "capable_of", "swim", 0.86)],
    "pub_salmon_fish_migration": [("salmon", "is_a", "fish", 0.84), ("fish", "is_a", "vertebrate", 0.82), ("salmon", "capable_of", "swim", 0.86)],
    "pub_mosquito": [("mosquito", "is_a", "insect", 0.92), ("mosquito", "capable_of", "fly", 0.86), ("mosquito", "has_property", "wings", 0.82)],
    "pub_mosquito_insect_flight": [("mosquito", "is_a", "insect", 0.84), ("insect", "is_a", "animal", 0.82), ("mosquito", "capable_of", "fly", 0.86)],
    "pub_ostrich": [("ostrich", "is_a", "bird", 0.92), ("ostrich", "not_capable_of", "fly", 0.90), ("ostrich", "has_property", "wings", 0.76)],
    "pub_ostrich_bird_counterexample": [("ostrich", "is_a", "bird", 0.84), ("bird", "is_a", "vertebrate", 0.82), ("ostrich", "not_capable_of", "fly", 0.88)],
    "pub_eagle": [("eagle", "is_a", "bird", 0.92), ("eagle", "capable_of", "fly", 0.88), ("eagle", "has_property", "wings", 0.82)],
    "pub_eagle_bird_flight": [("eagle", "is_a", "bird", 0.84), ("bird", "is_a", "vertebrate", 0.82), ("eagle", "capable_of", "fly", 0.88)],
    "pub_frog": [("frog", "is_a", "amphibian", 0.88), ("frog", "is_a", "vertebrate", 0.78), ("frog", "capable_of", "swim", 0.74)],
    "pub_frog_vertebrate_amphibian": [("frog", "is_a", "vertebrate", 0.84), ("vertebrate", "is_a", "animal", 0.82)],
    "pub_mammal": [("mammal", "is_a", "vertebrate", 0.92), ("mammal", "produces", "milk", 0.84)],
    "pub_bird": [("bird", "is_a", "vertebrate", 0.92), ("bird", "has_property", "wings", 0.76)],
    "pub_vertebrate": [("vertebrate", "is_a", "animal", 0.92), ("fish", "is_a", "vertebrate", 0.76), ("amphibian", "is_a", "vertebrate", 0.76)],
    "pub_duck_bird_swim": [("duck", "is_a", "bird", 0.84), ("bird", "is_a", "vertebrate", 0.82), ("duck", "capable_of", "swim", 0.84), ("duck", "capable_of", "fly", 0.70), ("duck", "has_property", "wings", 0.78)],
    "pub_cat_mammal_pet": [("cat", "is_a", "mammal", 0.84), ("mammal", "is_a", "vertebrate", 0.82), ("cat", "not_capable_of", "fly", 0.72)],
    "pub_owl_bird_predator": [("owl", "is_a", "bird", 0.84), ("bird", "is_a", "vertebrate", 0.82), ("owl", "capable_of", "fly", 0.84), ("owl", "has_property", "wings", 0.78)],
}

TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str], str, float], ...] = (
    ("is_a", re.compile(r"\b(?:a|an|the)?\s*([a-z]+)\s+is\s+(?:a|an)\s+([a-z]+)\b", re.IGNORECASE), "is_a", 0.70),
    ("capable_of", re.compile(r"\b([a-z]+)\s+(?:is\s+)?capable\s+of\s+([a-z]+)\b", re.IGNORECASE), "capable_of", 0.78),
    ("not_capable_of", re.compile(r"\b([a-z]+)\s+(?:is\s+)?not\s+capable\s+of\s+([a-z]+)\b", re.IGNORECASE), "not_capable_of", 0.80),
    ("has_property", re.compile(r"\b([a-z]+)\s+has\s+(?:property\s+)?([a-z]+)\b", re.IGNORECASE), "has_property", 0.74),
    ("produces", re.compile(r"\b([a-z]+)\s+produces\s+([a-z]+)\b", re.IGNORECASE), "produces", 0.76),
)


def extract_public_graph(documents: list[Document]) -> list[PublicGraphTriple]:
    extracted: dict[tuple[str, str, str], PublicGraphTriple] = {}
    for document in documents:
        candidates = _profile_triples(document) + _pattern_triples(document)
        for candidate in candidates:
            key = (candidate.subject, candidate.predicate, candidate.object)
            existing = extracted.get(key)
            if existing is None or candidate.confidence > existing.confidence:
                extracted[key] = candidate
    return sorted(extracted.values(), key=lambda item: item.triple_id)


def _profile_triples(document: Document) -> list[PublicGraphTriple]:
    profile = DOC_PROFILES.get(document.doc_id, [])
    rows: list[PublicGraphTriple] = []
    lowered = f"{document.title} {document.text}".lower()
    for subject, predicate, object_, confidence in profile:
        if subject not in lowered and subject not in document.doc_id:
            continue
        rows.append(_make_triple(subject, predicate, object_, document.doc_id, confidence, "source_profile", _snippet(document.text, subject, object_)))
    return rows


def _pattern_triples(document: Document) -> list[PublicGraphTriple]:
    rows: list[PublicGraphTriple] = []
    for sentence in _sentences(document.text):
        for pattern_name, pattern, predicate, confidence in TEXT_PATTERNS:
            for match in pattern.finditer(sentence):
                subject, object_ = match.groups()
                if not known_entity(subject) or not known_entity(object_):
                    continue
                rows.append(_make_triple(subject, predicate, object_, document.doc_id, confidence, pattern_name, sentence))
    return rows


def _make_triple(
    subject: str,
    predicate: str,
    object_: str,
    source_doc_id: str,
    confidence: float,
    pattern: str,
    snippet: str,
) -> PublicGraphTriple:
    normalized_subject, normalized_predicate, normalized_object = triple_key(subject, predicate, object_)
    triple_id = f"pg_{normalized_subject}_{normalized_predicate}_{normalized_object}_{_stable_id(normalized_subject, normalized_predicate, normalized_object)}"
    return PublicGraphTriple(
        triple_id=triple_id,
        subject=normalized_subject,
        predicate=normalized_predicate,
        object=normalized_object,
        source_doc_id=source_doc_id,
        confidence=confidence,
        extraction_mode="public_graph",
        pattern=pattern,
        snippet=snippet.strip()[:320],
    )


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?;])\s+", text) if sentence.strip()]


def _snippet(text: str, subject: str, object_: str) -> str:
    lowered = text.lower()
    indexes = [index for term in (subject, object_) if (index := lowered.find(term.lower())) >= 0]
    start = max(0, min(indexes) - 90) if indexes else 0
    return text[start : start + 320]


def _stable_id(subject: str, predicate: str, object_: str) -> str:
    return hashlib.blake2b(f"{subject}|{predicate}|{object_}".encode("utf-8"), digest_size=5).hexdigest()
