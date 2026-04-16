from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

PUBLIC_STRUCTURE_BENCHMARK_PATH = Path("data/processed/public_structure_benchmark.jsonl")
ROUTE_FAMILIES = ("kg", "hybrid")
SPLITS = ("dev", "test")


@dataclass(frozen=True, slots=True)
class PublicStructureItem:
    id: str
    query: str
    split: str
    route_family: str
    gold_answer: str
    gold_source_doc_ids: list[str]
    gold_triple_ids: list[str]
    gold_path_ids: list[str]
    gold_evidence_text: str = ""
    provenance: str = "public_graph"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.split not in SPLITS:
            raise ValueError(f"Unsupported split for {self.id}: {self.split}")
        if self.route_family not in ROUTE_FAMILIES:
            raise ValueError(f"Unsupported route family for {self.id}: {self.route_family}")
        if not self.gold_source_doc_ids:
            raise ValueError(f"Public structure item {self.id} must include source doc ids.")


def load_public_structure_benchmark(
    path: str | Path = PUBLIC_STRUCTURE_BENCHMARK_PATH,
    split: str | None = None,
) -> list[PublicStructureItem]:
    benchmark_path = Path(path)
    if not benchmark_path.exists():
        from prism.public_graph.benchmark_builder import build_public_structure_benchmark

        build_public_structure_benchmark(benchmark_path)
    rows = benchmark_path.read_text(encoding="utf-8").strip().splitlines()
    items = [PublicStructureItem(**json.loads(row)) for row in rows if row.strip()]
    return [item for item in items if split is None or item.split == split]


def write_public_structure_benchmark(
    items: list[PublicStructureItem],
    path: str | Path = PUBLIC_STRUCTURE_BENCHMARK_PATH,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(asdict(item), sort_keys=True) for item in items) + "\n",
        encoding="utf-8",
    )
    return output_path


def public_structure_counts(items: list[PublicStructureItem]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {"split": {}, "route_family": {}, "provenance": {}}
    for item in items:
        counts["split"][item.split] = counts["split"].get(item.split, 0) + 1
        counts["route_family"][item.route_family] = counts["route_family"].get(item.route_family, 0) + 1
        counts["provenance"][item.provenance] = counts["provenance"].get(item.provenance, 0) + 1
    return {key: dict(sorted(value.items())) for key, value in counts.items()}
