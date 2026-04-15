from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RelationalQuery:
    query: str
    gold_route: str
    gold_answer: str
    gold_evidence_ids: list[str] = field(default_factory=list)
    notes: str = ""


RELATIONAL_QUERIES: tuple[RelationalQuery, ...] = (
    RelationalQuery("What bridge connects bat and vertebrate?", "hybrid", "bat -> mammal -> vertebrate plus text bridge evidence.", ["path:kg_bat_is_mammal->kg_mammal_is_vertebrate", "rel_bat_vertebrate"], "2-hop class bridge"),
    RelationalQuery("What bridge connects penguin and vertebrate?", "hybrid", "penguin -> bird -> vertebrate plus text bridge evidence.", ["path:kg_penguin_is_bird->kg_bird_is_vertebrate", "rel_penguin_vertebrate"]),
    RelationalQuery("What bridge connects whale and vertebrate?", "hybrid", "whale -> mammal -> vertebrate plus text bridge evidence.", ["path:kg_whale_is_mammal->kg_mammal_is_vertebrate", "rel_whale_vertebrate"]),
    RelationalQuery("What bridge connects salmon and vertebrate?", "hybrid", "salmon -> fish -> vertebrate plus text bridge evidence.", ["path:kg_salmon_is_fish->kg_fish_is_vertebrate", "rel_salmon_vertebrate"]),
    RelationalQuery("What bridge connects mosquito and animal?", "hybrid", "mosquito -> insect -> animal plus text bridge evidence.", ["path:kg_mosquito_is_insect->kg_insect_is_animal", "rel_mosquito_animal"]),
    RelationalQuery("What relation connects bat and fly?", "hybrid", "bat capable_of fly plus text relation evidence.", ["kg_bat_capable_fly", "rel_bat_fly"]),
    RelationalQuery("What relation connects bat and mosquito?", "hybrid", "bat eats mosquito plus text relation evidence.", ["kg_bat_eats_mosquito", "rel_bat_mosquito"]),
    RelationalQuery("What relation connects eagle and fish?", "hybrid", "eagle eats fish plus text relation evidence.", ["kg_eagle_eats_fish", "rel_eagle_fish"]),
    RelationalQuery("What relation connects frog and mosquito?", "hybrid", "frog eats mosquito plus text relation evidence.", ["kg_frog_eats_mosquito", "rel_frog_mosquito"]),
    RelationalQuery("What relation connects dolphin and echolocation?", "hybrid", "dolphin has_property echolocation plus text relation evidence.", ["kg_dolphin_has_property_echolocation", "rel_dolphin_echolocation"]),
    RelationalQuery("What relation connects mammal and milk?", "hybrid", "mammal produces milk plus text relation evidence.", ["kg_mammal_produces_milk", "rel_mammal_milk"]),
    RelationalQuery("What relation connects penguin and swim?", "hybrid", "penguin capable_of swim plus text relation evidence.", ["kg_penguin_capable_swim", "rel_penguin_swim"]),
    RelationalQuery("What relation connects bird and vertebrate?", "hybrid", "bird is_a vertebrate plus text relation evidence.", ["kg_bird_is_vertebrate", "rel_bird_vertebrate"]),
    RelationalQuery("What relation connects insect and animal?", "hybrid", "insect is_a animal plus text relation evidence.", ["kg_insect_is_animal", "rel_insect_animal"]),
    RelationalQuery("What relation connects sparrow and wings?", "hybrid", "sparrow has_property wings plus text relation evidence.", ["kg_sparrow_has_wings", "rel_sparrow_wings"]),
    RelationalQuery("What relation connects duck and swim?", "hybrid", "duck capable_of swim plus text relation evidence.", ["kg_duck_capable_swim", "rel_duck_swim"]),
    RelationalQuery("What relation connects whale and swim?", "hybrid", "whale capable_of swim plus text relation evidence.", ["kg_whale_capable_swim", "rel_whale_swim"]),
    RelationalQuery("What relation connects cat and mouse?", "hybrid", "cat eats mouse plus text relation evidence.", ["kg_cat_eats_mouse", "rel_cat_mouse"]),
    RelationalQuery("What relation connects owl and mouse?", "hybrid", "owl eats mouse plus text relation evidence.", ["kg_owl_eats_mouse", "rel_owl_mouse"]),
    RelationalQuery("What relation connects mammal and vertebrate?", "hybrid", "mammal is_a vertebrate plus text relation evidence.", ["kg_mammal_is_vertebrate", "rel_mammal_vertebrate"]),
)


def load_relational_queries() -> list[RelationalQuery]:
    return list(RELATIONAL_QUERIES)


def load_relational_smoke_queries(limit: int = 5) -> list[str]:
    return [item.query for item in RELATIONAL_QUERIES[:limit]]
