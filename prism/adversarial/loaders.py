from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from prism.adversarial.query_templates import DIFFICULTY_LEVELS, validate_ambiguity_tags

ADVERSARIAL_BENCHMARK_PATH = Path("data/processed/adversarial_benchmark.jsonl")
ROUTE_FAMILIES = ("bm25", "dense", "kg", "hybrid")
SPLITS = ("dev", "test")


@dataclass(frozen=True, slots=True)
class AdversarialItem:
    id: str
    query: str
    split: str
    intended_route_family: str
    difficulty: str
    ambiguity_tags: list[str]
    gold_answer: str
    gold_source_doc_ids: list[str]
    gold_triple_ids: list[str]
    gold_evidence_text: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if self.split not in SPLITS:
            raise ValueError(f"Unsupported adversarial split for {self.id}: {self.split}")
        if self.intended_route_family not in ROUTE_FAMILIES:
            raise ValueError(f"Unsupported adversarial route family for {self.id}: {self.intended_route_family}")
        if self.difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(f"Unsupported adversarial difficulty for {self.id}: {self.difficulty}")
        if not self.ambiguity_tags:
            raise ValueError(f"Adversarial item {self.id} must include at least one ambiguity tag.")
        validate_ambiguity_tags(self.ambiguity_tags)
        if not self.gold_source_doc_ids and not self.gold_triple_ids:
            raise ValueError(f"Adversarial item {self.id} needs source doc ids or triple ids.")


def load_adversarial_benchmark(
    path: str | Path = ADVERSARIAL_BENCHMARK_PATH,
    split: str | None = None,
) -> list[AdversarialItem]:
    benchmark_path = Path(path)
    if not benchmark_path.exists():
        from prism.adversarial.benchmark_builder import build_adversarial_benchmark

        build_adversarial_benchmark(benchmark_path)
    rows = benchmark_path.read_text(encoding="utf-8").strip().splitlines()
    items = [AdversarialItem(**json.loads(row)) for row in rows if row.strip()]
    return [item for item in items if split is None or item.split == split]


def write_adversarial_benchmark(
    items: list[AdversarialItem],
    path: str | Path = ADVERSARIAL_BENCHMARK_PATH,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(asdict(item), sort_keys=True) for item in items) + "\n",
        encoding="utf-8",
    )
    return output_path


def adversarial_counts(items: list[AdversarialItem]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {"split": {}, "intended_route_family": {}, "difficulty": {}, "ambiguity_tags": {}}
    for item in items:
        counts["split"][item.split] = counts["split"].get(item.split, 0) + 1
        counts["intended_route_family"][item.intended_route_family] = counts["intended_route_family"].get(item.intended_route_family, 0) + 1
        counts["difficulty"][item.difficulty] = counts["difficulty"].get(item.difficulty, 0) + 1
        for tag in item.ambiguity_tags:
            counts["ambiguity_tags"][tag] = counts["ambiguity_tags"].get(tag, 0) + 1
    return {key: dict(sorted(value.items())) for key, value in counts.items()}
