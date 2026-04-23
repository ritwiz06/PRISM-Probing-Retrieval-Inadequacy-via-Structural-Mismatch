from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class DemoPreset:
    title: str
    query: str
    expected_route: str
    expected_evidence_source: str
    presenter_note: str
    demo_mode: str = "benchmark mode"
    safe_fallback: bool = True
    category: str = "core"
    badge: str = "Core"


FINAL_DEMO_PRESETS: tuple[DemoPreset, ...] = (
    DemoPreset(
        title="Lexical: exact RFC identifier",
        query="RFC-7231",
        expected_route="bm25",
        expected_evidence_source="formal document chunk for RFC-7231",
        presenter_note="Shows why exact identifiers should route to BM25 rather than semantic similarity.",
        category="lexical",
        badge="Exact ID",
    ),
    DemoPreset(
        title="Lexical: medical code",
        query="What is ICD-10 J18.9?",
        expected_route="bm25",
        expected_evidence_source="formal ICD-style code snippet",
        presenter_note="Use this to show identifier extraction and exact-code grounding.",
        category="lexical",
        badge="Code lookup",
    ),
    DemoPreset(
        title="Semantic: paraphrased feeling",
        query="What feels like climate anxiety?",
        expected_route="dense",
        expected_evidence_source="semantic corpus chunk about climate anxiety",
        presenter_note="Shows semantic retrieval when the query is conceptual rather than identifier-heavy.",
        category="semantic",
        badge="Conceptual",
    ),
    DemoPreset(
        title="Semantic: rare paraphrase",
        query="What is an asphalt warmth pocket?",
        expected_route="dense",
        expected_evidence_source="semantic paraphrase chunk",
        presenter_note="Use this when explaining why Dense was upgraded to sentence-transformers + FAISS.",
        category="semantic",
        badge="Paraphrase",
    ),
    DemoPreset(
        title="Deductive: animal capability",
        query="Can a mammal fly?",
        expected_route="kg",
        expected_evidence_source="curated KG triples about mammal/bat/capability",
        presenter_note="Shows structured reasoning and why KG evidence is auditable.",
        category="deductive",
        badge="KG",
    ),
    DemoPreset(
        title="Deductive: universal scope",
        query="Are all mammals able to fly?",
        expected_route="kg",
        expected_evidence_source="KG support plus counterexample-style reasoning",
        presenter_note="Shows soundness handling for universal claims.",
        category="deductive",
        badge="Universal",
    ),
    DemoPreset(
        title="Relational: bridge path",
        query="What bridge connects bat and vertebrate?",
        expected_route="hybrid",
        expected_evidence_source="hybrid evidence combining text and graph path through mammal",
        presenter_note="Shows multi-hop/bridge reasoning and backend fusion.",
        category="relational",
        badge="Bridge",
    ),
    DemoPreset(
        title="Relational: dolphin and echolocation",
        query="What relation connects dolphin and echolocation?",
        expected_route="hybrid",
        expected_evidence_source="hybrid text and KG relation evidence",
        presenter_note="Shows relational lookup where both text support and structure matter.",
        category="relational",
        badge="Relation",
    ),
    DemoPreset(
        title="Open Corpus: source-pack climate anxiety",
        query="What feels like climate anxiety?",
        expected_route="dense",
        expected_evidence_source="wikipedia source pack",
        presenter_note="Switch to source-pack mode and show PRISM operating outside the fixed benchmark corpus.",
        demo_mode="source-pack mode",
        category="open-corpus",
        badge="Source pack",
    ),
    DemoPreset(
        title="Open Corpus: local demo graph",
        query="What bridge connects bat and vertebrate?",
        expected_route="hybrid",
        expected_evidence_source="local demo folder query-local graph",
        presenter_note="Switch to local demo folder mode and show query-local graph extraction.",
        demo_mode="local demo folder mode",
        category="open-corpus",
        badge="Local graph",
    ),
    DemoPreset(
        title="Hard Case: misleading exact term",
        query="Which concept feels like RFC-7231 but is about worry?",
        expected_route="dense",
        expected_evidence_source="adversarial hard-case context",
        presenter_note="Use this to explain the adversarial route-boundary weakness and why calibrated rescue is analysis-only.",
        category="hard-case",
        badge="Boundary",
    ),
)


SAFE_FALLBACK_SEQUENCE: tuple[str, ...] = (
    "Lexical: exact RFC identifier",
    "Semantic: paraphrased feeling",
    "Deductive: animal capability",
    "Relational: bridge path",
)


def preset_options() -> list[str]:
    return [preset.title for preset in FINAL_DEMO_PRESETS]


def preset_by_title(title: str) -> DemoPreset:
    for preset in FINAL_DEMO_PRESETS:
        if preset.title == title:
            return preset
    raise KeyError(f"Unknown demo preset: {title}")


def presets_payload() -> list[dict[str, object]]:
    return [asdict(preset) for preset in FINAL_DEMO_PRESETS]


def grouped_presets_payload() -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for preset in FINAL_DEMO_PRESETS:
        grouped.setdefault(preset.category, []).append(asdict(preset))
    return grouped
