from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from pathlib import Path

from prism.public_corpus.clean_and_chunk import METADATA_PREFIX, clean_public_text
from prism.public_corpus.source_registry import PublicSource, public_sources, sources_by_id
from prism.schemas import Document

PUBLIC_ENRICHED_METADATA_PATH = Path("data/processed/public_corpus_enriched_metadata.json")

IDENTIFIER_PATTERNS = (
    re.compile(r"\bRFC[- ]?\d{3,5}\b", re.IGNORECASE),
    re.compile(r"\bICD[- ]?10(?:[- ]?CM)?\s+[A-Z]\d{2}(?:\.\d+)?\b", re.IGNORECASE),
    re.compile(r"\b[A-Z]\d{2}(?:\.\d+)?\b"),
    re.compile(r"\b(?:HIPAA|45\s+CFR)\s+\d{3}\.\d{3}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}\.\d{3}\b"),
    re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*){1,}\b"),
    re.compile(r"\b[A-Z][A-Za-z0-9]+Vectorizer\b"),
)


@dataclass(frozen=True, slots=True)
class PublicDocumentMetadata:
    doc_id: str
    title: str
    source_type: str
    route_family: str
    url: str
    fetch_status: str
    canonical_identifiers: list[str]
    aliases: list[str]
    section_headings: list[str]
    lead_summary: str
    body_char_count: int


def extract_identifiers(text: str) -> list[str]:
    identifiers: set[str] = set()
    for pattern in IDENTIFIER_PATTERNS:
        for match in pattern.findall(text):
            identifiers.add(_normalize_identifier(match))
    return sorted(identifier for identifier in identifiers if identifier)


def enrich_public_documents(raw_dir: str | Path = "data/raw/public_corpus") -> dict[str, PublicDocumentMetadata]:
    source_lookup = sources_by_id()
    enriched: dict[str, PublicDocumentMetadata] = {}
    for raw_path in sorted(Path(raw_dir).glob("*.txt")):
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        metadata, body = _split_metadata(text)
        source_id = str(metadata.get("source_id") or raw_path.stem)
        source = source_lookup.get(source_id)
        if source is None:
            continue
        cleaned = clean_public_text(body, source)
        row = enrich_source_document(source, cleaned, str(metadata.get("fetch_status", "unknown")))
        enriched[source.source_id] = row
    return enriched


def enrich_source_document(source: PublicSource, cleaned_text: str, fetch_status: str = "unknown") -> PublicDocumentMetadata:
    identifiers = extract_identifiers(f"{source.title} {source.expected_answer} {source.fallback_text} {cleaned_text}")
    aliases = _aliases_for_source(source, identifiers)
    return PublicDocumentMetadata(
        doc_id=source.source_id,
        title=source.title,
        source_type=source.source_type,
        route_family=source.route_family,
        url=source.url,
        fetch_status=fetch_status,
        canonical_identifiers=identifiers,
        aliases=aliases,
        section_headings=_section_headings(cleaned_text),
        lead_summary=_lead_summary(cleaned_text, source),
        body_char_count=len(cleaned_text),
    )


def write_enriched_metadata(
    metadata: dict[str, PublicDocumentMetadata],
    path: str | Path = PUBLIC_ENRICHED_METADATA_PATH,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({doc_id: asdict(row) for doc_id, row in sorted(metadata.items())}, indent=2),
        encoding="utf-8",
    )
    return output_path


def load_enriched_metadata(
    path: str | Path = PUBLIC_ENRICHED_METADATA_PATH,
) -> dict[str, PublicDocumentMetadata]:
    metadata_path = Path(path)
    if not metadata_path.exists():
        metadata = enrich_public_documents()
        write_enriched_metadata(metadata, metadata_path)
        return metadata
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return {doc_id: PublicDocumentMetadata(**row) for doc_id, row in payload.items()}


def enriched_document_text(document: Document, metadata: PublicDocumentMetadata | None) -> str:
    if metadata is None:
        return document.text
    fields = [
        f"Title: {metadata.title}",
        f"Canonical identifiers: {', '.join(metadata.canonical_identifiers)}",
        f"Aliases: {', '.join(metadata.aliases)}",
        f"Lead summary: {metadata.lead_summary}",
        "Body:",
        document.text,
    ]
    return "\n".join(field for field in fields if field.strip())


def _split_metadata(text: str) -> tuple[dict[str, object], str]:
    first, _, rest = text.partition("\n")
    if first.startswith(METADATA_PREFIX):
        return json.loads(first.removeprefix(METADATA_PREFIX)), rest
    return {}, text


def _normalize_identifier(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip())
    text = re.sub(r"\bRFC\s+(\d+)\b", r"RFC-\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bICD[- ]?10(?:[- ]?CM)?\s+([A-Z]\d{2}(?:\.\d+)?)\b", r"ICD-10 \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b45\s+CFR\s+(\d{3}\.\d{3})\b", r"45 CFR \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bHIPAA\s+(\d{3}\.\d{3})\b", r"HIPAA \1", text, flags=re.IGNORECASE)
    return text


def _aliases_for_source(source: PublicSource, identifiers: list[str]) -> list[str]:
    aliases = {
        source.title,
        source.title.lower(),
        source.expected_answer,
        source.expected_answer.lower(),
        source.source_id.replace("pub_", "").replace("_", " "),
    }
    for identifier in identifiers:
        aliases.add(identifier)
        aliases.add(identifier.lower())
        aliases.add(identifier.replace("-", " "))
        aliases.add(identifier.replace(" ", "-"))
        if " " in identifier:
            aliases.add(identifier.split()[-1])
    if source.source_type == "official_docs":
        aliases.add(source.title.split()[-1])
    if source.source_id == "pub_python_dataclass":
        aliases.update({"dataclasses", "python dataclasses", "dataclass"})
    if source.source_id == "pub_sklearn_tfidf":
        aliases.update({"TfidfVectorizer", "tfidfvectorizer", "TF-IDF features"})
    return sorted(alias for alias in aliases if alias)


def _section_headings(text: str) -> list[str]:
    candidates = re.findall(r"(?:^|\. )([A-Z][A-Za-z0-9 /-]{4,60})(?= \w)", text[:2500])
    seen: list[str] = []
    for candidate in candidates:
        candidate = candidate.strip(" .")
        if candidate and candidate not in seen:
            seen.append(candidate)
        if len(seen) >= 8:
            break
    return seen


def _lead_summary(text: str, source: PublicSource, limit: int = 420) -> str:
    fallback = f"{source.title}. {source.expected_answer}. {source.fallback_text}"
    selected = text if len(text.strip()) >= 80 else fallback
    sentences = re.split(r"(?<=[.!?])\s+", selected.strip())
    lead = " ".join(sentences[:3]).strip() or fallback
    return lead[:limit].strip()


def main() -> None:
    metadata = enrich_public_documents()
    path = write_enriched_metadata(metadata)
    identifier_docs = sum(1 for row in metadata.values() if row.canonical_identifiers)
    print(f"public_enriched_metadata path={path} documents={len(metadata)} identifier_docs={identifier_docs}")


if __name__ == "__main__":
    main()
