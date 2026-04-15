from __future__ import annotations

from prism.ras.compute_ras import route_query


def render_state(query: str) -> dict[str, object]:
    decision = route_query(query)
    return {
        "query": query,
        "selected_backend": decision.selected_backend,
        "ras_scores": decision.ras_scores,
    }


def main() -> None:
    sample = render_state("Can mammals fly?")
    print(sample)


if __name__ == "__main__":
    main()
