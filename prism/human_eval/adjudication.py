from __future__ import annotations

from prism.human_eval.compare_annotations import analyze_comparative_annotations


def build_adjudication_queue() -> list[dict[str, object]]:
    """Return the current comparative adjudication queue.

    This thin wrapper keeps adjudication as a named concept while reusing the
    comparative annotation analyzer as the source of truth.
    """

    payload = analyze_comparative_annotations()
    return list(payload.get("adjudication_queue", []))
