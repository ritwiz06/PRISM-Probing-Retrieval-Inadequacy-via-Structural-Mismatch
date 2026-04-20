from __future__ import annotations

import re

from prism.schemas import RetrievedItem


def rescue_topk_evidence(query: str, evidence: list[RetrievedItem], selected_backend: str) -> tuple[list[RetrievedItem], dict[str, object]]:
    """Reorder top-k evidence using transparent query/evidence heuristics.

    The rescue layer never fetches new evidence and does not use gold labels. It
    only promotes a better-supported item already present in top-k.
    """

    if len(evidence) < 2:
        return evidence, {"applied": False, "reason": "Fewer than two evidence items.", "selected_backend": selected_backend}
    query_terms = _tokens(query)
    negated_terms = _negated_terms(query)
    if not negated_terms:
        return evidence, {
            "applied": False,
            "reason": "No explicit negated/distractor span was detected, so rescue stayed disabled.",
            "selected_backend": selected_backend,
        }
    identifiers = _identifiers(query)
    scored: list[tuple[float, int, RetrievedItem, dict[str, object]]] = []
    for rank, item in enumerate(evidence):
        text = f"{item.item_id} {item.content} {' '.join(str(v) for v in item.metadata.values())}".lower()
        tokens = _tokens(text)
        overlap = len(query_terms & tokens) / max(1, len(query_terms))
        identifier_hits = sum(1 for identifier in identifiers if identifier.lower() in text)
        negated_hits = sum(1 for token in negated_terms if token in text)
        source_bonus = 0.04 if selected_backend in str(item.metadata.get("contributing_backends", "")) else 0.0
        score = overlap + 0.18 * identifier_hits - 0.28 * negated_hits + source_bonus - 0.015 * rank
        scored.append(
            (
                score,
                rank,
                _with_rescue_metadata(
                    item,
                    score=score,
                    original_rank=rank + 1,
                    overlap=overlap,
                    identifier_hits=identifier_hits,
                    negated_hits=negated_hits,
                ),
                {
                    "item_id": item.item_id,
                    "original_rank": rank + 1,
                    "rescue_score": round(score, 6),
                    "query_overlap": round(overlap, 6),
                    "identifier_hits": identifier_hits,
                    "negated_hits": negated_hits,
                },
            )
        )
    reordered = sorted(scored, key=lambda row: (-row[0], row[1]))
    new_evidence = [row[2] for row in reordered]
    original = scored[0]
    best = reordered[0]
    enough_margin = best[0] >= original[0] + 0.12
    negation_improves = best[3]["negated_hits"] < original[3]["negated_hits"]
    applied = new_evidence[0].item_id != evidence[0].item_id and enough_margin and negation_improves
    if not applied:
        new_evidence = evidence
    return new_evidence, {
        "applied": applied,
        "reason": "Promoted top-k evidence by query overlap, identifier support, and negated-distractor penalties."
        if applied
        else "Original top evidence remained best after rescue scoring.",
        "selected_backend": selected_backend,
        "original_top_id": evidence[0].item_id,
        "rescued_top_id": new_evidence[0].item_id,
        "negated_terms": sorted(negated_terms),
        "identifiers": identifiers,
        "scores": [row[3] for row in reordered],
    }


def _with_rescue_metadata(
    item: RetrievedItem,
    *,
    score: float,
    original_rank: int,
    overlap: float,
    identifier_hits: int,
    negated_hits: int,
) -> RetrievedItem:
    metadata = dict(item.metadata)
    metadata.update(
        {
            "topk_rescue_checked": True,
            "topk_rescue_score": round(score, 6),
            "topk_original_rank": original_rank,
            "topk_query_overlap": round(overlap, 6),
            "topk_identifier_hits": identifier_hits,
            "topk_negated_hits": negated_hits,
        }
    )
    return RetrievedItem(
        item_id=item.item_id,
        content=item.content,
        score=item.score,
        source_type=item.source_type,
        metadata=metadata,
    )


def _tokens(text: str) -> set[str]:
    stop = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "what", "which", "not", "with", "also"}
    return {token for token in re.findall(r"[a-z0-9._§:/-]+", text.lower()) if len(token) > 2 and token not in stop}


def _identifiers(query: str) -> list[str]:
    patterns = [
        r"\bRFC-?\d+\b",
        r"\bICD-10\s+[A-Z]\d{2}\.\d\b",
        r"\b\d{3}\.\d{3}\b",
        r"§\d+",
        r"\b[a-zA-Z_][\w]*\.[\w.]+\b",
    ]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, query))
    return matches


def _negated_terms(query: str) -> set[str]:
    lowered = query.lower()
    terms: set[str] = set()
    for marker in ("not", "despite", "although", "even if", "rather than", "instead of"):
        for match in re.finditer(rf"{re.escape(marker)}\s+([^,?.;:]+)", lowered):
            terms.update(list(_tokens(match.group(1)))[:6])
    return terms
