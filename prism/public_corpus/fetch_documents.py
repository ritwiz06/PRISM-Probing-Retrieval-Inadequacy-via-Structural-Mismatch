from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from prism.public_corpus.source_registry import PublicSource, public_sources

RAW_PUBLIC_DIR = Path("data/raw/public_corpus")
FETCH_MANIFEST_PATH = RAW_PUBLIC_DIR / "fetch_manifest.json"


def fetch_public_documents(
    raw_dir: str | Path = RAW_PUBLIC_DIR,
    refresh: bool = False,
    timeout_seconds: int = 8,
    sources: list[PublicSource] | None = None,
) -> dict[str, object]:
    """Fetch or reuse public raw documents with offline fallback snapshots."""
    output_dir = Path(raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_sources = sources or public_sources()
    rows: list[dict[str, object]] = []

    for source in selected_sources:
        raw_path = output_dir / f"{source.source_id}.txt"
        status = "cached"
        error = ""
        if refresh or not raw_path.exists():
            try:
                text = _fetch_url(source.url, timeout_seconds=timeout_seconds)
                raw_path.write_text(_raw_payload(source, text, "fetched"), encoding="utf-8")
                status = "fetched"
            except (OSError, URLError, TimeoutError, ValueError) as exc:
                error = str(exc)
                if source.fallback_text:
                    raw_path.write_text(_raw_payload(source, source.fallback_text, "fallback_snapshot"), encoding="utf-8")
                    status = "fallback_snapshot"
                else:
                    status = "skipped"
        rows.append(
            {
                **asdict(source),
                "raw_path": str(raw_path),
                "status": status,
                "error": error,
                "available": raw_path.exists() and status != "skipped",
            }
        )

    summary = {
        "raw_dir": str(output_dir),
        "total_sources": len(selected_sources),
        "fetched": sum(1 for row in rows if row["status"] == "fetched"),
        "cached": sum(1 for row in rows if row["status"] == "cached"),
        "fallback_snapshot": sum(1 for row in rows if row["status"] == "fallback_snapshot"),
        "skipped": sum(1 for row in rows if row["status"] == "skipped"),
        "sources": rows,
    }
    (output_dir / "fetch_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _fetch_url(url: str, timeout_seconds: int) -> str:
    request = Request(url, headers={"User-Agent": "PRISM public corpus builder/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read(1_500_000)
        charset = response.headers.get_content_charset() or "utf-8"
    text = raw.decode(charset, errors="replace")
    if len(text.strip()) < 80:
        raise ValueError("Fetched document was too short to use.")
    return text


def _raw_payload(source: PublicSource, text: str, status: str) -> str:
    metadata = {
        "source_id": source.source_id,
        "title": source.title,
        "url": source.url,
        "source_type": source.source_type,
        "route_family": source.route_family,
        "fetch_status": status,
        "notes": source.notes,
    }
    return "PRISM_PUBLIC_SOURCE_METADATA " + json.dumps(metadata, sort_keys=True) + "\n\n" + text.strip() + "\n"


def main() -> None:
    summary = fetch_public_documents()
    print(
        "public_fetch "
        f"total={summary['total_sources']} fetched={summary['fetched']} cached={summary['cached']} "
        f"fallback_snapshot={summary['fallback_snapshot']} skipped={summary['skipped']} "
        f"manifest={RAW_PUBLIC_DIR / 'fetch_manifest.json'}"
    )


if __name__ == "__main__":
    main()
