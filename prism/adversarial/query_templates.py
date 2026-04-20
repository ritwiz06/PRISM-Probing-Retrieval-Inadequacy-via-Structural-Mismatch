from __future__ import annotations

AMBIGUITY_TAGS = (
    "lexical_semantic_overlap",
    "misleading_exact_term",
    "identifier_with_distractor_language",
    "noisy_structure",
    "wrong_bridge_distractor",
    "top1_topk_gap_risk",
    "public_document_noise",
    "route_boundary_ambiguity",
    "identifier_ambiguity",
)

DIFFICULTY_LEVELS = ("hard", "adversarial")


def validate_ambiguity_tags(tags: list[str]) -> None:
    unknown = sorted(set(tags) - set(AMBIGUITY_TAGS))
    if unknown:
        raise ValueError(f"Unsupported adversarial ambiguity tag(s): {unknown}")


def tag_description(tag: str) -> str:
    descriptions = {
        "lexical_semantic_overlap": "The query has exact terms but asks for a conceptual answer, or vice versa.",
        "misleading_exact_term": "A high-salience exact token points toward a plausible wrong source.",
        "identifier_with_distractor_language": "An identifier query includes natural-language wording that can look semantic.",
        "noisy_structure": "The structured evidence is present but surrounded by distracting public or textual evidence.",
        "wrong_bridge_distractor": "A relational query has a plausible but wrong bridge or neighboring relation.",
        "top1_topk_gap_risk": "The right evidence may appear in top-k even when the top-1 hit is a near miss.",
        "public_document_noise": "The query uses public-document phrasing or boilerplate-like wording.",
        "route_boundary_ambiguity": "The query sits close to a BM25/Dense/KG/Hybrid route boundary.",
        "identifier_ambiguity": "Nearby identifiers differ by a small token or punctuation change.",
    }
    return descriptions.get(tag, tag)
