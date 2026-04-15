from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text.strip("'\"")


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]

    def parse_block(start_index: int, parent_indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        index = start_index

        while index < len(lines):
            raw_line = lines[index]
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            if indent <= parent_indent:
                break

            line = raw_line.strip()
            if line.startswith("- "):
                raise ValueError(f"Unexpected list item at root level: {raw_line}")

            key, _, remainder = line.partition(":")
            key = key.strip()
            if not _:
                raise ValueError(f"Invalid config line: {raw_line}")

            if remainder.strip():
                mapping[key] = _parse_scalar(remainder.strip())
                index += 1
                continue

            next_index = index + 1
            if next_index >= len(lines):
                mapping[key] = {}
                index += 1
                continue

            next_raw_line = lines[next_index]
            next_indent = len(next_raw_line) - len(next_raw_line.lstrip(" "))
            if next_indent <= indent:
                mapping[key] = {}
                index += 1
                continue

            next_line = next_raw_line.strip()
            if next_line.startswith("- "):
                items: list[Any] = []
                while next_index < len(lines):
                    item_raw = lines[next_index]
                    item_indent = len(item_raw) - len(item_raw.lstrip(" "))
                    if item_indent <= indent:
                        break
                    item_line = item_raw.strip()
                    if not item_line.startswith("- "):
                        raise ValueError(f"Mixed list/mapping content under {key}: {item_raw}")
                    items.append(_parse_scalar(item_line[2:]))
                    next_index += 1
                mapping[key] = items
                index = next_index
                continue

            nested_mapping, next_index = parse_block(next_index, indent)
            mapping[key] = nested_mapping
            index = next_index

        return mapping, index

    parsed, _ = parse_block(0, -1)
    return parsed


@dataclass(slots=True)
class PathConfig:
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    indices_dir: str = "data/indices"
    eval_dir: str = "data/eval"


@dataclass(slots=True)
class RetrievalConfig:
    default_top_k: int = 3
    dense_weight: float = 0.5
    sparse_weight: float = 0.3
    kg_weight: float = 0.2
    dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dense_chunk_size: int = 80
    dense_chunk_overlap: int = 20
    dense_backend: str = "sentence-transformers"


@dataclass(slots=True)
class EvaluationConfig:
    smoke_queries: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    project_name: str = "PRISM"
    log_level: str = "INFO"
    data_dir: str = "data"
    paths: PathConfig = field(default_factory=PathConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)


def _config_from_mapping(mapping: dict[str, Any]) -> AppConfig:
    paths = PathConfig(**mapping.get("paths", {}))
    retrieval = RetrievalConfig(**mapping.get("retrieval", {}))
    evaluation = EvaluationConfig(**mapping.get("evaluation", {}))
    return AppConfig(
        project_name=mapping.get("project_name", "PRISM"),
        log_level=str(mapping.get("log_level", "INFO")),
        data_dir=str(mapping.get("data_dir", "data")),
        paths=paths,
        retrieval=retrieval,
        evaluation=evaluation,
    )


def load_config(path: str | os.PathLike[str] | None = None) -> AppConfig:
    config_path = Path(path or os.getenv("PRISM_CONFIG", "configs/default.yaml"))
    if not config_path.exists():
        return AppConfig()

    mapping = _parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    config = _config_from_mapping(mapping)

    env_log_level = os.getenv("PRISM_LOG_LEVEL")
    env_data_dir = os.getenv("PRISM_DATA_DIR")
    if env_log_level:
        config.log_level = env_log_level
    if env_data_dir:
        config.data_dir = env_data_dir
        config.paths = PathConfig(
            raw_dir=str(Path(env_data_dir) / "raw"),
            processed_dir=str(Path(env_data_dir) / "processed"),
            indices_dir=str(Path(env_data_dir) / "indices"),
            eval_dir=str(Path(env_data_dir) / "eval"),
        )
    return config
