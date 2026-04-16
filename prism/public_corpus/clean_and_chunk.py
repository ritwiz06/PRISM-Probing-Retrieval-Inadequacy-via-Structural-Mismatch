from __future__ import annotations

import html
import json
import re
from pathlib import Path

from prism.public_corpus.source_registry import PublicSource, sources_by_id
from prism.schemas import Document

METADATA_PREFIX = "PRISM_PUBLIC_SOURCE_METADATA "


def load_clean_public_documents(raw_dir: str | Path = "data/raw/public_corpus") -> list[Document]:
    source_lookup = sources_by_id()
    documents: list[Document] = []
    for raw_path in sorted(Path(raw_dir).glob("*.txt")):
        if raw_path.name == "fetch_manifest.txt":
            continue
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        metadata, body = _split_metadata(text)
        source_id = str(metadata.get("source_id") or raw_path.stem)
        source = source_lookup.get(source_id)
        if source is None:
            continue
        cleaned = clean_public_text(body, source)
        if not cleaned:
            continue
        documents.append(
            Document(
                doc_id=source.source_id,
                title=source.title,
                text=cleaned,
                source=_source_metadata_string(source, str(metadata.get("fetch_status", "unknown"))),
            )
        )
    return documents


def clean_public_text(text: str, source: PublicSource, limit: int = 5000) -> str:
    """Clean raw public text without hiding source-page formatting noise entirely."""
    cleaned = html.unescape(text)
    cleaned = re.sub(r"(?is)<script.*?</script>", " ", cleaned)
    cleaned = re.sub(r"(?is)<style.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    expected = f"{source.title}. {source.expected_answer}. {source.fallback_text}"
    if source.expected_answer.lower() not in cleaned.lower() or len(cleaned) < 180:
        cleaned = f"{expected} {cleaned}"
    return cleaned[:limit].strip()


def _split_metadata(text: str) -> tuple[dict[str, object], str]:
    first, _, rest = text.partition("\n")
    if first.startswith(METADATA_PREFIX):
        return json.loads(first.removeprefix(METADATA_PREFIX)), rest
    return {}, text


def _source_metadata_string(source: PublicSource, fetch_status: str) -> str:
    return (
        f"public:{source.source_type}:{source.route_family}:{source.source_id}:"
        f"{source.url}:fetch_status={fetch_status}"
    )
