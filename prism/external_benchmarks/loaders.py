from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


EXTERNAL_BENCHMARK_PATH = Path("data/processed/external_mini_benchmark.jsonl")


@dataclass(frozen=True, slots=True)
class ExternalBenchmarkItem:
    id: str
    query: str
    source_dataset: str
    route_family: str
    gold_answer: str
    gold_evidence_text: str = ""
    difficulty: str = "mini"
    tag: str = ""
    notes: str = ""


def load_external_mini_benchmark(path: str | Path = EXTERNAL_BENCHMARK_PATH) -> list[ExternalBenchmarkItem]:
    benchmark_path = Path(path)
    if not benchmark_path.exists():
        from prism.external_benchmarks.mini_benchmark import build_external_mini_benchmark

        build_external_mini_benchmark(benchmark_path)
    rows = benchmark_path.read_text(encoding="utf-8").strip().splitlines()
    return [ExternalBenchmarkItem(**json.loads(row)) for row in rows if row.strip()]


def write_external_mini_benchmark(items: list[ExternalBenchmarkItem], path: str | Path = EXTERNAL_BENCHMARK_PATH) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(json.dumps(asdict(item), sort_keys=True) for item in items) + "\n", encoding="utf-8")
    return output_path


def benchmark_counts(items: list[ExternalBenchmarkItem]) -> dict[str, dict[str, int]]:
    route_family: dict[str, int] = {}
    source_dataset: dict[str, int] = {}
    for item in items:
        route_family[item.route_family] = route_family.get(item.route_family, 0) + 1
        source_dataset[item.source_dataset] = source_dataset.get(item.source_dataset, 0) + 1
    return {"route_family": dict(sorted(route_family.items())), "source_dataset": dict(sorted(source_dataset.items()))}
