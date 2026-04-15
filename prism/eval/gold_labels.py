from __future__ import annotations

from prism.eval.deductive_slice import load_deductive_queries
from prism.eval.lexical_slice import load_lexical_queries
from prism.eval.relational_slice import load_relational_queries
from prism.eval.semantic_slice import load_semantic_queries


def smoke_gold_routes() -> dict[str, str]:
    routes = {
        "What is PRISM?": "dense",
        "Which backend handles exact identifiers?": "bm25",
        "What exact identifier questions should use BM25?": "bm25",
        "Can mammals fly?": "kg",
    }
    routes.update({item.query: item.gold_route for item in load_lexical_queries()})
    routes.update({item.query: item.gold_route for item in load_semantic_queries()})
    routes.update({item.query: item.gold_route for item in load_deductive_queries()})
    routes.update({item.query: item.gold_route for item in load_relational_queries()})
    return routes


def smoke_gold_evidence_doc_ids() -> dict[str, str]:
    evidence = {item.query: item.gold_evidence_doc_id for item in load_lexical_queries()}
    evidence.update({item.query: item.gold_evidence_doc_id for item in load_semantic_queries()})
    evidence.update({item.query: item.gold_evidence_ids[0] for item in load_deductive_queries() if item.gold_evidence_ids})
    evidence.update({item.query: item.gold_evidence_ids[0] for item in load_relational_queries() if item.gold_evidence_ids})
    return evidence
