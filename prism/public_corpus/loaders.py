from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

PUBLIC_BENCHMARK_PATH = Path("data/processed/public_corpus_benchmark.jsonl")
ROUTE_FAMILIES = ("bm25", "dense", "kg", "hybrid")
SPLITS = ("dev", "test")


@dataclass(frozen=True, slots=True)
class PublicBenchmarkItem:
    id: str
    query: str
    split: str
    route_family: str
    source_dataset_style: str
    gold_answer: str
    gold_source_doc_ids: list[str]
    gold_evidence_text: str = ""
    difficulty: str = "public_raw"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.split not in SPLITS:
            raise ValueError(f"Unsupported split for {self.id}: {self.split}")
        if self.route_family not in ROUTE_FAMILIES:
            raise ValueError(f"Unsupported route family for {self.id}: {self.route_family}")
        if not self.gold_source_doc_ids:
            raise ValueError(f"Public benchmark item {self.id} must have at least one gold source doc id.")


def load_public_benchmark(
    path: str | Path = PUBLIC_BENCHMARK_PATH,
    split: str | None = None,
) -> list[PublicBenchmarkItem]:
    benchmark_path = Path(path)
    if not benchmark_path.exists():
        from prism.public_corpus.benchmark_builder import build_public_benchmark

        build_public_benchmark(benchmark_path)
    rows = benchmark_path.read_text(encoding="utf-8").strip().splitlines()
    items = [PublicBenchmarkItem(**json.loads(row)) for row in rows if row.strip()]
    return [item for item in items if split is None or item.split == split]


def write_public_benchmark(
    items: list[PublicBenchmarkItem],
    path: str | Path = PUBLIC_BENCHMARK_PATH,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(asdict(item), sort_keys=True) for item in items) + "\n",
        encoding="utf-8",
    )
    return output_path


def public_benchmark_counts(items: list[PublicBenchmarkItem]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {"split": {}, "route_family": {}, "source_dataset_style": {}}
    for item in items:
        counts["split"][item.split] = counts["split"].get(item.split, 0) + 1
        counts["route_family"][item.route_family] = counts["route_family"].get(item.route_family, 0) + 1
        counts["source_dataset_style"][item.source_dataset_style] = counts["source_dataset_style"].get(
            item.source_dataset_style, 0
        ) + 1
    return {key: dict(sorted(value.items())) for key, value in counts.items()}
