from __future__ import annotations

import json
from pathlib import Path

from prism.eval.run_eval import run_evaluation
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg


def test_smoke_pipeline_writes_artifacts(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PRISM_DATA_DIR", str(data_dir))
    monkeypatch.setenv("PRISM_CONFIG", str(_write_config(tmp_path, data_dir)))

    corpus_path = build_corpus()
    kg_path = build_kg()
    payload = run_evaluation(smoke=True)

    assert corpus_path.exists()
    assert kg_path.exists()
    assert payload["summary"]["num_queries"] == 23

    eval_path = data_dir / "eval" / "smoke_eval.json"
    assert eval_path.exists()
    stored = json.loads(eval_path.read_text(encoding="utf-8"))
    assert "route_accuracy" in stored


def _write_config(tmp_path: Path, data_dir: Path) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_name: PRISM",
                "log_level: INFO",
                f"data_dir: {data_dir}",
                "paths:",
                f"  raw_dir: {data_dir / 'raw'}",
                f"  processed_dir: {data_dir / 'processed'}",
                f"  indices_dir: {data_dir / 'indices'}",
                f"  eval_dir: {data_dir / 'eval'}",
                "retrieval:",
                "  default_top_k: 2",
                "evaluation:",
                "  smoke_queries:",
                "    - What is PRISM?",
                "    - Which backend handles exact identifiers?",
                "    - Can mammals fly?",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path
