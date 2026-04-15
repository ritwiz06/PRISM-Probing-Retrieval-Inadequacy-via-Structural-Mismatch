from __future__ import annotations

import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def overlap_score(query: str, text: str) -> float:
    query_counts = Counter(tokenize(query))
    text_counts = Counter(tokenize(text))
    shared = sum(min(query_counts[token], text_counts[token]) for token in query_counts)
    total = sum(query_counts.values()) or 1
    return shared / total


def jaccard_score(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens | text_tokens)
