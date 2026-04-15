from __future__ import annotations

from prism.ras.compute_ras import route_query


def test_routes_lexical_query_to_bm25() -> None:
    decision = route_query("What exact identifier should I use?")
    assert decision.selected_backend == "bm25"


def test_routes_identifier_only_query_to_bm25() -> None:
    decision = route_query("What does RFC-7231 define?")
    assert decision.selected_backend == "bm25"


def test_routes_deductive_query_to_kg() -> None:
    decision = route_query("Can a bat fly?")
    assert decision.selected_backend == "kg"


def test_routes_relational_query_to_hybrid() -> None:
    decision = route_query("What multi-hop relation chain connects these entities?")
    assert decision.selected_backend == "hybrid"
