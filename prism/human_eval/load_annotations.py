from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from prism.human_eval.rubric import RUBRIC_FIELDS
from prism.human_eval.validation import discover_annotation_files

ANNOTATION_DIR = Path("data/human_eval/annotations")


@dataclass(frozen=True, slots=True)
class AnnotationRecord:
    evaluator_id: str
    item_id: str
    scores: dict[str, int]
    major_error_type: str
    is_usable: str
    notes: str
    source_file: str


def load_annotations(annotation_dir: str | Path = ANNOTATION_DIR) -> list[AnnotationRecord]:
    directory = Path(annotation_dir)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        return []
    rows: list[AnnotationRecord] = []
    for path in discover_annotation_files(directory):
        rows.extend(_load_file(path))
    return rows


def _load_file(path: Path) -> list[AnnotationRecord]:
    rows: list[AnnotationRecord] = []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for raw in reader:
            if not raw.get("item_id"):
                continue
            evaluator = str(raw.get("evaluator_id") or path.stem)
            scores = {field: _score(raw.get(field, "")) for field in RUBRIC_FIELDS}
            rows.append(
                AnnotationRecord(
                    evaluator_id=evaluator,
                    item_id=str(raw["item_id"]),
                    scores=scores,
                    major_error_type=str(raw.get("major_error_type") or "none").strip() or "none",
                    is_usable=str(raw.get("is_usable") or "").strip().lower(),
                    notes=str(raw.get("notes") or ""),
                    source_file=str(path),
                )
            )
    return rows


def _score(value: str | None) -> int:
    try:
        score = int(str(value or "").strip())
    except ValueError:
        return 0
    return score if 1 <= score <= 3 else 0
