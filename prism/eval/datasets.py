from __future__ import annotations

from prism.config import AppConfig
from prism.eval.deductive_slice import load_deductive_smoke_queries
from prism.eval.lexical_slice import load_lexical_smoke_queries
from prism.eval.relational_slice import load_relational_smoke_queries
from prism.eval.semantic_slice import load_semantic_smoke_queries


def load_smoke_queries(config: AppConfig) -> list[str]:
    base_queries = config.evaluation.smoke_queries or [
        "What is PRISM?",
        "What exact identifier questions should use BM25?",
        "Can mammals fly?",
    ]
    return (
        base_queries
        + load_lexical_smoke_queries()
        + load_semantic_smoke_queries()
        + load_deductive_smoke_queries()
        + load_relational_smoke_queries()
    )
