from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


GENERALIZATION_BENCHMARK_PATH = Path("data/processed/generalization_v2_benchmark.jsonl")
ROUTE_FAMILIES = ("bm25", "dense", "kg", "hybrid")
SPLITS = ("dev", "test")


@dataclass(frozen=True, slots=True)
class GeneralizationItem:
    id: str
    query: str
    source_dataset: str
    split: str
    route_family: str
    gold_answer: str
    gold_evidence_text: str = ""
    difficulty: str = "held_out"
    tag: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if self.split not in SPLITS:
            raise ValueError(f"Unsupported split for {self.id}: {self.split}")
        if self.route_family not in ROUTE_FAMILIES:
            raise ValueError(f"Unsupported route family for {self.id}: {self.route_family}")


def load_generalization_benchmark(
    path: str | Path = GENERALIZATION_BENCHMARK_PATH,
    split: str | None = None,
) -> list[GeneralizationItem]:
    benchmark_path = Path(path)
    if not benchmark_path.exists():
        from prism.generalization.benchmark_builder import build_generalization_benchmark

        build_generalization_benchmark(benchmark_path)
    rows = benchmark_path.read_text(encoding="utf-8").strip().splitlines()
    items = [GeneralizationItem(**json.loads(row)) for row in rows if row.strip()]
    return [item for item in items if split is None or item.split == split]


def write_generalization_benchmark(
    items: list[GeneralizationItem],
    path: str | Path = GENERALIZATION_BENCHMARK_PATH,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(asdict(item), sort_keys=True) for item in items) + "\n",
        encoding="utf-8",
    )
    return output_path


def benchmark_counts(items: list[GeneralizationItem]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {"split": {}, "route_family": {}, "source_dataset": {}}
    for item in items:
        counts["split"][item.split] = counts["split"].get(item.split, 0) + 1
        counts["route_family"][item.route_family] = counts["route_family"].get(item.route_family, 0) + 1
        counts["source_dataset"][item.source_dataset] = counts["source_dataset"].get(item.source_dataset, 0) + 1
    return {key: dict(sorted(value.items())) for key, value in counts.items()}
