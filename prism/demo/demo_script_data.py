from __future__ import annotations

from prism.demo.presets import FINAL_DEMO_PRESETS, SAFE_FALLBACK_SEQUENCE, presets_payload


DEMO_SCRIPT_STEPS: tuple[dict[str, object], ...] = (
    {
        "step": 1,
        "title": "Production path",
        "mode": "benchmark mode",
        "preset": "Lexical: exact RFC identifier",
        "show": ["query features", "computed RAS scores", "BM25 evidence", "final answer"],
        "talk_track": "Start with the default production router: computed RAS chooses the minimum-adequacy-risk backend.",
    },
    {
        "step": 2,
        "title": "Representation contrast",
        "mode": "benchmark mode",
        "preset": "Semantic: paraphrased feeling",
        "show": ["Dense evidence", "alternate route table", "answer trace"],
        "talk_track": "Switch to a conceptual query to show that exact lexical matching is not enough.",
    },
    {
        "step": 3,
        "title": "Structured reasoning",
        "mode": "benchmark mode",
        "preset": "Deductive: animal capability",
        "show": ["KG evidence", "structured trace", "soundness note"],
        "talk_track": "Show why deductive claims require graph-style evidence rather than only nearest text.",
    },
    {
        "step": 4,
        "title": "Open-corpus workspace",
        "mode": "source-pack mode",
        "preset": "Open Corpus: source-pack climate anxiety",
        "show": ["runtime corpus metadata", "source pack provenance", "query-local graph panel"],
        "talk_track": "Move beyond fixed benchmarks while keeping the corpus bounded and reproducible.",
    },
    {
        "step": 5,
        "title": "Research comparison",
        "mode": "benchmark mode",
        "preset": "Hard Case: misleading exact term",
        "show": ["Compare Routers tab", "RAS_V3/RAS_V4 status", "calibrated rescue caveat"],
        "talk_track": "Close with the honest research story: route adequacy matters, but hard cases still need evidence rescue.",
    },
)


def demo_script_payload() -> dict[str, object]:
    return {
        "production_router": "computed_ras",
        "research_overlays": ["calibrated_rescue", "classifier_router", "ras_v3", "ras_v4", "optional_llm"],
        "safe_fallback_sequence": list(SAFE_FALLBACK_SEQUENCE),
        "presets": presets_payload(),
        "script_steps": list(DEMO_SCRIPT_STEPS),
        "fallback_note": "If source packs, local LLM, or query-local graph extraction are unavailable, use the safe fallback sequence in benchmark mode.",
    }
