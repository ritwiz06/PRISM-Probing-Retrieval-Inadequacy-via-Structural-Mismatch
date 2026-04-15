from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SemanticQuery:
    query: str
    gold_route: str
    gold_answer: str
    gold_evidence_doc_id: str
    notes: str = ""


SEMANTIC_QUERIES: tuple[SemanticQuery, ...] = (
    SemanticQuery("Which idea is solastalgia homesick planet?", "dense", "Climate anxiety.", "sem_climate_anxiety", "Paraphrase of climate anxiety."),
    SemanticQuery("Which pattern is the charlatan feeling after success?", "dense", "Impostor syndrome.", "sem_impostor_syndrome"),
    SemanticQuery("Which idea is daylight carbohydrate alchemy?", "dense", "Photosynthesis.", "sem_photosynthesis"),
    SemanticQuery("What is novelty adoption cascade?", "dense", "Diffusion of innovations.", "sem_diffusion_innovations"),
    SemanticQuery("What is an asphalt warmth pocket?", "dense", "Urban heat island.", "sem_urban_heat_island"),
    SemanticQuery("Which idea is durable recall filing?", "dense", "Memory consolidation.", "sem_memory_consolidation"),
    SemanticQuery("Which response is a benign trigger false alarm?", "dense", "Allergy.", "sem_allergy"),
    SemanticQuery("Which root fungus web links neighboring vegetation?", "dense", "Mycorrhizal network.", "sem_mycorrhizal_network"),
    SemanticQuery("Which issue is an automated unfairness pattern?", "dense", "Algorithmic bias.", "sem_algorithmic_bias"),
    SemanticQuery("Which idea is an internal metronome?", "dense", "Circadian rhythm.", "sem_circadian_rhythm"),
    SemanticQuery("Which tool is a pollution price signal?", "dense", "Carbon pricing.", "sem_carbon_pricing"),
    SemanticQuery("Which theory frames selfhood through autobiography?", "dense", "Narrative identity.", "sem_narrative_identity"),
    SemanticQuery("Which term names a collaborative web resource governed by users?", "dense", "Digital commons.", "sem_digital_commons"),
    SemanticQuery("Which loop is planetary moisture circulation?", "dense", "Water cycle.", "sem_water_cycle"),
    SemanticQuery("Which method is reward driven agent training?", "dense", "Reinforcement learning.", "sem_reinforcement_learning"),
    SemanticQuery("Which approach is lexical neighborhood meaning?", "dense", "Distributional semantics.", "sem_distributional_semantics"),
    SemanticQuery("Which problem is alert churn scatters concentration?", "dense", "Attention fragmentation.", "sem_attention_fragmentation"),
    SemanticQuery("Which concept is a habitat job slot?", "dense", "Ecological niche.", "sem_ecological_niche"),
    SemanticQuery("Which view says standpoint shapes knowing?", "dense", "Situated knowledge.", "sem_situated_knowledge"),
    SemanticQuery("Which effect is minor starting nudge cascades?", "dense", "Butterfly effect.", "sem_butterfly_effect"),
)


def load_semantic_queries() -> list[SemanticQuery]:
    return list(SEMANTIC_QUERIES)


def load_semantic_smoke_queries(limit: int = 5) -> list[str]:
    return [item.query for item in SEMANTIC_QUERIES[:limit]]
