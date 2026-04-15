from __future__ import annotations

import json
import logging
from pathlib import Path

from prism.schemas import Document

LOGGER = logging.getLogger(__name__)

DEFAULT_CURATED_TITLES = [
    "Climate anxiety",
    "Impostor syndrome",
    "Photosynthesis",
    "Diffusion of innovations",
    "Urban heat island",
    "Memory consolidation",
    "Allergy",
    "Mycorrhizal network",
    "Algorithmic bias",
    "Circadian rhythm",
    "Carbon pricing",
    "Narrative identity",
    "Digital commons",
    "Water cycle",
    "Reinforcement learning",
    "Distributional semantics",
    "Attention fragmentation",
    "Ecological niche",
    "Situated knowledge",
    "Butterfly effect",
    "Collective intelligence",
    "Circular economy",
]

SEMANTIC_SEED_PAGES: list[tuple[str, str, str]] = [
    ("sem_climate_anxiety", "Climate anxiety", "Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures."),
    ("sem_impostor_syndrome", "Impostor syndrome", "Impostor syndrome is persistent self-doubt where capable people feel like frauds despite evidence of competence."),
    ("sem_photosynthesis", "Photosynthesis", "Photosynthesis is the biological process where plants and other organisms convert sunlight, carbon dioxide, and water into stored chemical energy."),
    ("sem_diffusion_innovations", "Diffusion of innovations", "Diffusion of innovations explains how new ideas, practices, and technologies spread through communities and social systems."),
    ("sem_urban_heat_island", "Urban heat island", "An urban heat island occurs when built surfaces make a city warmer than surrounding rural areas."),
    ("sem_memory_consolidation", "Memory consolidation", "Memory consolidation is the process by which experiences and learning become more stable over time, especially during sleep."),
    ("sem_allergy", "Allergy", "An allergy is an immune response in which the body reacts strongly to a usually harmless substance such as pollen or food."),
    ("sem_mycorrhizal_network", "Mycorrhizal network", "A mycorrhizal network is a relationship between fungi and plant roots that can move nutrients and chemical signals through soil."),
    ("sem_algorithmic_bias", "Algorithmic bias", "Algorithmic bias occurs when data, model design, or deployment context produces unfair or systematically skewed outputs."),
    ("sem_circadian_rhythm", "Circadian rhythm", "A circadian rhythm is an internal daily timing cycle that helps regulate sleep, hormones, alertness, and metabolism."),
    ("sem_carbon_pricing", "Carbon pricing", "Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices."),
    ("sem_narrative_identity", "Narrative identity", "Narrative identity is the way people form a sense of self by organizing memories and events into a life story."),
    ("sem_digital_commons", "Digital commons", "Digital commons are shared online knowledge resources maintained through community norms, open collaboration, and collective governance."),
    ("sem_water_cycle", "Water cycle", "The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems."),
    ("sem_reinforcement_learning", "Reinforcement learning", "Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment."),
    ("sem_distributional_semantics", "Distributional semantics", "Distributional semantics represents word meaning through patterns of nearby context and usage across language data."),
    ("sem_attention_fragmentation", "Attention fragmentation", "Attention fragmentation describes reduced sustained focus when notifications, context switching, and interruptions divide cognitive effort."),
    ("sem_ecological_niche", "Ecological niche", "An ecological niche is the role a species occupies in an environment, including resources, interactions, and conditions for survival."),
    ("sem_situated_knowledge", "Situated knowledge", "Situated knowledge emphasizes that perspective, social position, and lived context shape what people observe and know."),
    ("sem_butterfly_effect", "Butterfly effect", "The butterfly effect names sensitive dependence where tiny changes in initial conditions can produce large later differences."),
    ("sem_collective_intelligence", "Collective intelligence", "Collective intelligence emerges when groups combine diverse information, coordination, and feedback to solve problems."),
    ("sem_circular_economy", "Circular economy", "A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling."),
]


def fetch_documents(
    raw_dir: str | Path = "data/raw",
    curated_titles: list[str] | None = None,
    refresh: bool = False,
    target_semantic_docs: int = 100,
) -> list[Document]:
    cache_path = Path(raw_dir) / "wikipedia_pages.jsonl"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not refresh:
        cached = _read_cache(cache_path)
        if cached:
            merged = {document.doc_id: document for document in cached}
            merged.update({document.doc_id: document for document in _core_scaffold_documents()})
            return sorted(merged.values(), key=lambda document: document.doc_id)

    titles = curated_titles or DEFAULT_CURATED_TITLES
    documents = _seed_documents(titles)
    documents.extend(_filler_documents(target_semantic_docs - len(documents)))
    documents.extend(_core_scaffold_documents())
    documents = sorted(documents, key=lambda document: document.doc_id)
    _write_cache(cache_path, documents)
    LOGGER.info("Cached %s curated semantic documents to %s", len(documents), cache_path)
    return documents


def _seed_documents(curated_titles: list[str]) -> list[Document]:
    allowed = set(curated_titles)
    return [
        Document(doc_id=doc_id, title=title, text=text, source="seed:wikipedia")
        for doc_id, title, text in SEMANTIC_SEED_PAGES
        if title in allowed
    ]


def _filler_documents(count: int) -> list[Document]:
    topics = [
        "plate tectonics", "coral reefs", "antibiotic resistance", "solar eclipses", "volcanic islands",
        "river deltas", "public health surveillance", "renewable energy storage", "language acquisition", "supply chains",
        "food webs", "ocean currents", "desertification", "glacier retreat", "biodiversity corridors",
        "cognitive load", "peer review", "open source software", "data visualization", "human-computer interaction",
    ]
    documents: list[Document] = []
    for index in range(max(0, count)):
        topic = topics[index % len(topics)]
        doc_id = f"sem_background_{index:03d}"
        title = f"Background note {index:03d}: {topic.title()}"
        text = (
            f"This concise background note discusses {topic} with emphasis on definitions, mechanisms, examples, "
            f"and practical consequences for general knowledge retrieval. It is included to broaden the semantic corpus "
            f"without building a full Wikipedia dump."
        )
        documents.append(Document(doc_id=doc_id, title=title, text=text, source="seed:wikipedia_background"))
    return documents


def _core_scaffold_documents() -> list[Document]:
    return [
        Document(
            doc_id="doc_prism",
            title="PRISM Overview",
            text="PRISM is a multi-representation retrieval router that compares BM25, dense, KG, and hybrid backends.",
            source="seed:wikipedia",
        ),
        Document(
            doc_id="doc_mammal",
            title="Mammal Facts",
            text="A mammal is a vertebrate animal. Bats are mammals and can fly.",
            source="seed:wikipedia",
        ),
        Document(
            doc_id="doc_bm25",
            title="Retrieval Routing Policy",
            text="Lexical or exact identifier questions should route to BM25. Semantic questions should route to dense retrieval.",
            source="seed:wikipedia",
        ),
    ] + _relational_documents()


def _relational_documents() -> list[Document]:
    rows = [
        ("rel_bat_vertebrate", "Bat to vertebrate bridge", "A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate."),
        ("rel_penguin_vertebrate", "Penguin to vertebrate bridge", "A penguin connects to vertebrate through bird: penguin is a bird, and bird is a vertebrate."),
        ("rel_whale_vertebrate", "Whale to vertebrate bridge", "A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate."),
        ("rel_salmon_vertebrate", "Salmon to vertebrate bridge", "A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate."),
        ("rel_mosquito_animal", "Mosquito to animal bridge", "A mosquito connects to animal through insect: mosquito is an insect, and insect is an animal."),
        ("rel_bat_fly", "Bat flight relation", "The bat to fly relation is supported by the KG fact that bat is capable of fly and text notes about bat flight."),
        ("rel_bat_mosquito", "Bat mosquito relation", "The bat to mosquito relation is dietary: bat eats mosquito in the demo KG."),
        ("rel_eagle_fish", "Eagle fish relation", "The eagle to fish relation is dietary: eagle eats fish in the demo KG."),
        ("rel_frog_mosquito", "Frog mosquito relation", "The frog to mosquito relation is dietary: frog eats mosquito in the demo KG."),
        ("rel_dolphin_echolocation", "Dolphin echolocation relation", "The dolphin to echolocation relation is a property relation: dolphin has property echolocation."),
        ("rel_mammal_milk", "Mammal milk relation", "The mammal to milk relation is production: mammal produces milk in the demo KG."),
        ("rel_penguin_swim", "Penguin swim relation", "The penguin to swim relation is capability: penguin is capable of swim in the demo KG."),
        ("rel_bird_vertebrate", "Bird vertebrate relation", "The bird to vertebrate relation is class inheritance: bird is a vertebrate."),
        ("rel_insect_animal", "Insect animal relation", "The insect to animal relation is class inheritance: insect is an animal."),
        ("rel_sparrow_wings", "Sparrow wings relation", "The sparrow to wings relation is property based: sparrow has property wings."),
        ("rel_duck_swim", "Duck swim relation", "The duck to swim relation is capability based: duck is capable of swim."),
        ("rel_whale_swim", "Whale swim relation", "The whale to swim relation is capability based: whale is capable of swim."),
        ("rel_cat_mouse", "Cat mouse relation", "The cat to mouse relation is dietary: cat eats mouse in the demo KG."),
        ("rel_owl_mouse", "Owl mouse relation", "The owl to mouse relation is dietary: owl eats mouse in the demo KG."),
        ("rel_mammal_vertebrate", "Mammal vertebrate relation", "The mammal to vertebrate relation is class inheritance: mammal is a vertebrate."),
    ]
    return [Document(doc_id=doc_id, title=title, text=text, source="seed:relational") for doc_id, title, text in rows]


def _write_cache(path: Path, documents: list[Document]) -> None:
    lines = [json.dumps(document.__dict__ if hasattr(document, "__dict__") else {
        "doc_id": document.doc_id,
        "title": document.title,
        "text": document.text,
        "source": document.source,
    }) for document in documents]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_cache(path: Path) -> list[Document]:
    try:
        rows = path.read_text(encoding="utf-8").strip().splitlines()
        return [Document(**json.loads(row)) for row in rows if row.strip()]
    except OSError as exc:
        LOGGER.warning("Could not read cached pages at %s: %s", path, exc)
        return []
