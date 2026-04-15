from __future__ import annotations


def summarize_results(results: list[dict[str, object]]) -> dict[str, int]:
    return {"num_queries": len(results)}
