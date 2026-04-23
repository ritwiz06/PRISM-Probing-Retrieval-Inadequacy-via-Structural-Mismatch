from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from prism.human_eval.rubric import COMPARATIVE_FIELDS, RUBRIC_FIELDS
from prism.utils import read_json, write_json

HUMAN_EVAL_DIR = Path("data/human_eval")
ANNOTATION_VALIDATION_JSON = HUMAN_EVAL_DIR / "annotation_validation_summary.json"
ANNOTATION_VALIDATION_CSV = HUMAN_EVAL_DIR / "annotation_validation_summary.csv"
ANNOTATION_VALIDATION_MD = HUMAN_EVAL_DIR / "annotation_validation_summary.md"

STANDARD_REQUIRED_COLUMNS = (
    "evaluator_id",
    "item_id",
    *RUBRIC_FIELDS,
    "major_error_type",
    "is_usable",
    "notes",
)

COMPARATIVE_REQUIRED_COLUMNS = (
    "evaluator_id",
    "comparative_item_id",
    *COMPARATIVE_FIELDS,
    "judgment_confidence",
    "major_difference_type",
    "needs_adjudication",
    "notes",
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    scope: str
    file: str
    row_number: int
    severity: str
    issue: str


def discover_annotation_files(annotation_dir: str | Path) -> list[Path]:
    directory = Path(annotation_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [path for path in directory.iterdir() if path.is_file() and not path.name.startswith(".")]
    return sorted(paths)


def validate_all_annotations(
    *,
    standard_dir: str | Path = HUMAN_EVAL_DIR / "annotations",
    comparative_dir: str | Path = HUMAN_EVAL_DIR / "comparative_annotations",
    standard_packet_path: str | Path = HUMAN_EVAL_DIR / "eval_packet.json",
    comparative_packet_path: str | Path = HUMAN_EVAL_DIR / "comparative_packet.json",
) -> dict[str, object]:
    standard_ids = _packet_ids(standard_packet_path, "item_id")
    comparative_ids = _packet_ids(comparative_packet_path, "comparative_item_id")
    standard = _validate_scope(
        scope="standard",
        annotation_dir=standard_dir,
        required_columns=STANDARD_REQUIRED_COLUMNS,
        id_column="item_id",
        valid_ids=standard_ids,
        score_columns=RUBRIC_FIELDS,
        choice_columns=(),
    )
    comparative = _validate_scope(
        scope="comparative",
        annotation_dir=comparative_dir,
        required_columns=COMPARATIVE_REQUIRED_COLUMNS,
        id_column="comparative_item_id",
        valid_ids=comparative_ids,
        score_columns=("judgment_confidence",),
        choice_columns=COMPARATIVE_FIELDS,
    )
    issues = [*standard["issues"], *comparative["issues"]]
    payload = {
        "status": "valid_with_warnings" if issues else "valid",
        "standard": {key: value for key, value in standard.items() if key != "issues"},
        "comparative": {key: value for key, value in comparative.items() if key != "issues"},
        "issue_count": len(issues),
        "issues": [asdict(issue) for issue in issues],
        "policy": "Rows with missing required columns, unknown item ids, invalid scores, or invalid choices are reported. Loaders keep parseable rows, but analysis only counts rows tied to known packet item ids.",
    }
    write_json(ANNOTATION_VALIDATION_JSON, payload)
    _write_validation_csv(ANNOTATION_VALIDATION_CSV, payload)
    ANNOTATION_VALIDATION_MD.write_text(_validation_markdown(payload), encoding="utf-8")
    return payload


def _validate_scope(
    *,
    scope: str,
    annotation_dir: str | Path,
    required_columns: Iterable[str],
    id_column: str,
    valid_ids: set[str],
    score_columns: Iterable[str],
    choice_columns: Iterable[str],
) -> dict[str, object]:
    files = discover_annotation_files(annotation_dir)
    issues: list[ValidationIssue] = []
    valid_rows = 0
    total_rows = 0
    evaluators: set[str] = set()
    recognized_items: set[str] = set()
    for path in files:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            headers = set(reader.fieldnames or [])
            missing = [column for column in required_columns if column not in headers]
            if missing:
                issues.append(
                    ValidationIssue(
                        scope=scope,
                        file=str(path),
                        row_number=0,
                        severity="error",
                        issue=f"Missing required columns: {', '.join(missing)}",
                    )
                )
                continue
            for row_number, row in enumerate(reader, start=2):
                total_rows += 1
                item_id = (row.get(id_column) or "").strip()
                evaluator_id = (row.get("evaluator_id") or path.stem).strip() or path.stem
                if evaluator_id:
                    evaluators.add(evaluator_id)
                row_issues = []
                if not item_id:
                    row_issues.append("missing item id")
                elif item_id not in valid_ids:
                    row_issues.append(f"unknown item id {item_id}")
                for column in score_columns:
                    if _score(row.get(column, "")) == 0:
                        row_issues.append(f"invalid score/confidence in {column}")
                for column in choice_columns:
                    if _choice(row.get(column, "")) == "":
                        row_issues.append(f"invalid A/B/Tie choice in {column}")
                if row_issues:
                    for issue in row_issues:
                        issues.append(
                            ValidationIssue(
                                scope=scope,
                                file=str(path),
                                row_number=row_number,
                                severity="warning",
                                issue=issue,
                            )
                        )
                else:
                    valid_rows += 1
                    recognized_items.add(item_id)
    return {
        "annotation_dir": str(annotation_dir),
        "file_count": len(files),
        "files": [str(path) for path in files],
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "evaluator_count": len(evaluators),
        "evaluators": sorted(evaluators),
        "recognized_item_count": len(recognized_items),
        "packet_item_count": len(valid_ids),
        "issues": issues,
    }


def _packet_ids(packet_path: str | Path, id_column: str) -> set[str]:
    path = Path(packet_path)
    if not path.exists():
        return set()
    payload = read_json(path)
    return {str(item[id_column]) for item in payload.get("items", []) if id_column in item}


def _score(value: str | None) -> int:
    try:
        parsed = int(str(value or "").strip())
    except ValueError:
        return 0
    return parsed if 1 <= parsed <= 3 else 0


def _choice(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "a":
        return "A"
    if normalized == "b":
        return "B"
    if normalized == "tie":
        return "Tie"
    return ""


def _write_validation_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["scope", "file", "row_number", "severity", "issue"])
        writer.writeheader()
        for issue in payload["issues"]:
            writer.writerow(issue)
        if not payload["issues"]:
            writer.writerow({"scope": "all", "file": "", "row_number": "", "severity": "ok", "issue": "No validation issues."})


def _validation_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Human Annotation Validation Summary",
        "",
        f"Status: `{payload['status']}`.",
        f"Issue count: {payload['issue_count']}.",
        "",
        "## Standard Annotations",
        "",
        *_scope_lines(payload["standard"]),
        "",
        "## Comparative Annotations",
        "",
        *_scope_lines(payload["comparative"]),
        "",
        "## Issues",
        "",
    ]
    if payload["issues"]:
        lines.extend(
            [
                f"- `{issue['scope']}` {issue['file']} row {issue['row_number']}: {issue['severity']} - {issue['issue']}"
                for issue in payload["issues"][:100]
            ]
        )
    else:
        lines.append("- No validation issues found.")
    lines.extend(["", "## Policy", "", str(payload["policy"]), ""])
    return "\n".join(lines)


def _scope_lines(scope_payload: dict[str, object]) -> list[str]:
    return [
        f"- Files: {scope_payload['file_count']}",
        f"- Rows: {scope_payload['valid_rows']} valid / {scope_payload['total_rows']} total",
        f"- Evaluators: {scope_payload['evaluator_count']} ({', '.join(scope_payload['evaluators'])})",
        f"- Recognized packet items: {scope_payload['recognized_item_count']} / {scope_payload['packet_item_count']}",
    ]
