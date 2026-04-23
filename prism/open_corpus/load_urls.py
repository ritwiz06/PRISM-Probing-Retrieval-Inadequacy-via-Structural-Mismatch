from __future__ import annotations

import hashlib
from pathlib import Path
import urllib.error
import urllib.request

from prism.open_corpus.normalize_documents import NormalizedDocument, normalize_raw_document


def load_url_documents(
    urls: list[str],
    *,
    cache_dir: str | Path = "data/raw/open_corpus_urls",
    timeout_seconds: float = 8.0,
) -> tuple[list[NormalizedDocument], list[dict[str, object]]]:
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    documents: list[NormalizedDocument] = []
    fetch_log: list[dict[str, object]] = []
    for url in urls:
        target = cache_path / f"{hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]}.html"
        status = "cached"
        if not target.exists():
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "PRISM-open-corpus/0.1"})
                with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                    target.write_bytes(response.read())
                status = "fetched"
            except (OSError, urllib.error.URLError, TimeoutError) as exc:
                fetch_log.append({"url": url, "status": "skipped", "error": str(exc), "cache_path": str(target)})
                continue
        raw = target.read_text(encoding="utf-8", errors="ignore")
        documents.append(
            normalize_raw_document(
                text=raw,
                title=_title_from_url(url),
                source_type="url",
                provenance=url,
                doc_id=f"url_{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}",
                metadata={"cache_path": str(target), "fetch_status": status},
            )
        )
        fetch_log.append({"url": url, "status": status, "cache_path": str(target)})
    return documents, fetch_log


def _title_from_url(url: str) -> str:
    tail = url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ")
    return tail.title() or url

