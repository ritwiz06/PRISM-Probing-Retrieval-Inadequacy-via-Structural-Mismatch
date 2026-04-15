from __future__ import annotations

import argparse
from pathlib import Path

from prism.config import load_config
from prism.demo.data import DEMO_PRESETS
from prism.eval.verify_end_to_end import verify_end_to_end
from prism.eval.verify_hybrid import verify_hybrid
from prism.eval.verify_kg import verify_kg
from prism.eval.verify_lexical import verify_lexical
from prism.eval.verify_semantic import verify_semantic
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.utils import read_json, read_jsonl_documents, read_jsonl_triples


def build_report_summary(refresh: bool = False) -> dict[str, object]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    if not corpus_path.exists():
        build_corpus()
    if not kg_path.exists():
        build_kg(corpus_path=str(corpus_path))

    return {
        "corpus_size": len(read_jsonl_documents(corpus_path)),
        "kg_size": len(read_jsonl_triples(kg_path)),
        "verification": {
            "lexical": _load_or_run(Path(config.paths.eval_dir) / "lexical_verification.json", verify_lexical, refresh),
            "semantic": _load_or_run(Path(config.paths.eval_dir) / "semantic_verification.json", verify_semantic, refresh),
            "kg": _load_or_run(Path(config.paths.eval_dir) / "kg_verification.json", verify_kg, refresh),
            "hybrid": _load_or_run(Path(config.paths.eval_dir) / "hybrid_verification.json", verify_hybrid, refresh),
            "end_to_end": _load_or_run(Path(config.paths.eval_dir) / "end_to_end_verification.json", verify_end_to_end, refresh),
        },
        "examples": [{"label": label, "query": query} for label, query in DEMO_PRESETS],
    }


def format_report(summary: dict[str, object]) -> str:
    verification = summary["verification"]
    end_to_end = verification["end_to_end"]
    lines = [
        "PRISM Demo Report Summary",
        f"Corpus documents: {summary['corpus_size']}",
        f"KG triples: {summary['kg_size']}",
        f"Lexical: top1={verification['lexical']['top1_correct']}/{verification['lexical']['total']} passed={verification['lexical']['passed']}",
        f"Semantic: dense_hit@{verification['semantic']['top_k']}={verification['semantic']['dense_hit_at_k']}/{verification['semantic']['total']} passed={verification['semantic']['passed']}",
        f"KG: hit@{verification['kg']['top_k']}={verification['kg']['kg_hit_at_k']}/{verification['kg']['total']} passed={verification['kg']['passed']}",
        f"Hybrid: hit@{verification['hybrid']['top_k']}={verification['hybrid']['hybrid_hit_at_k']}/{verification['hybrid']['total']} passed={verification['hybrid']['passed']}",
        f"End-to-end: total={end_to_end['total']} route_accuracy={end_to_end['route_accuracy']:.3f} evidence_hit@k={end_to_end['evidence_hit_at_k']:.3f} traces={end_to_end['trace_count']}/{end_to_end['total']} passed={end_to_end['passed']}",
        "Demo examples:",
    ]
    lines.extend(f"- {row['label']}: {row['query']}" for row in summary["examples"])
    return "\n".join(lines)


def _load_or_run(path: Path, fn, refresh: bool) -> dict[str, object]:
    if path.exists() and not refresh:
        return read_json(path)
    return fn()


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a concise local PRISM demo report summary.")
    parser.add_argument("--refresh", action="store_true", help="Re-run verification instead of reading existing result JSON.")
    args = parser.parse_args()
    print(format_report(build_report_summary(refresh=args.refresh)))


if __name__ == "__main__":
    main()
