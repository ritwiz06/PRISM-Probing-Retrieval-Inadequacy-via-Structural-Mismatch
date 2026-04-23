from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import html
import json
import re
from pathlib import Path

from prism.schemas import Document


@dataclass(frozen=True, slots=True)
class NormalizedDocument:
    document: Document
    metadata: dict[str, object]


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_raw_document(
    *,
    text: str,
    title: str = "",
    source_type: str,
    provenance: str,
    doc_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> NormalizedDocument:
    cleaned = normalize_text(text)
    stable_id = doc_id or _stable_doc_id(title or provenance, cleaned)
    document = Document(
        doc_id=stable_id,
        title=title or stable_id,
        text=cleaned,
        source=f"{source_type}:{provenance}",
    )
    return NormalizedDocument(
        document=document,
        metadata={
            "doc_id": stable_id,
            "title": document.title,
            "source_type": source_type,
            "provenance": provenance,
            "text_length": len(cleaned),
            "sections": _section_headings(text),
            **(metadata or {}),
        },
    )


def normalize_file(path: str | Path) -> NormalizedDocument:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    raw = file_path.read_text(encoding="utf-8", errors="ignore")
    title = file_path.stem.replace("_", " ").replace("-", " ").strip().title()
    if suffix == ".json":
        raw, title = _json_text_and_title(raw, fallback_title=title)
    return normalize_raw_document(
        text=raw,
        title=title,
        source_type=f"file:{suffix.removeprefix('.') or 'text'}",
        provenance=str(file_path),
        doc_id=_stable_doc_id(str(file_path), raw),
        metadata={"file_suffix": suffix},
    )


def document_metadata_payload(name: str, normalized: list[NormalizedDocument]) -> dict[str, object]:
    return {
        "name": name,
        "document_count": len(normalized),
        "documents": [entry.metadata for entry in normalized],
        "schema": {
            "doc_id": "stable id",
            "title": "document title",
            "source_type": "file/url/source_pack/local_demo",
            "provenance": "path or URL/source registry id",
            "text_length": "cleaned text length",
        },
    }


def as_documents(normalized: list[NormalizedDocument]) -> list[Document]:
    return [entry.document for entry in normalized]


def as_metadata_rows(normalized: list[NormalizedDocument]) -> list[dict[str, object]]:
    return [dict(entry.metadata) for entry in normalized]


def _json_text_and_title(raw: str, fallback_title: str) -> tuple[str, str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw, fallback_title
    if isinstance(parsed, dict):
        title = str(parsed.get("title") or parsed.get("name") or fallback_title)
        values = []
        for key, value in parsed.items():
            if isinstance(value, (str, int, float, bool)):
                values.append(f"{key}: {value}")
            elif isinstance(value, list):
                values.append(f"{key}: " + " ".join(str(item) for item in value[:20]))
        return "\n".join(values), title
    if isinstance(parsed, list):
        return "\n".join(json.dumps(item, sort_keys=True) for item in parsed[:100]), fallback_title
    return str(parsed), fallback_title


def _section_headings(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            headings.append(stripped.lstrip("#").strip())
        elif re.match(r"^[A-Z][A-Za-z0-9 /:-]{3,80}$", stripped):
            headings.append(stripped)
    return headings[:20]


def _stable_doc_id(seed: str, text: str) -> str:
    digest = hashlib.sha1(f"{seed}\n{text[:500]}".encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "_", seed.lower()).strip("_")[-40:] or "document"
    return f"oc_{slug}_{digest}"

