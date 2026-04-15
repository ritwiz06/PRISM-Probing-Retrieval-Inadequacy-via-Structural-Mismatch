from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DeductiveQuery:
    query: str
    gold_route: str
    gold_answer: str
    gold_evidence_ids: list[str] = field(default_factory=list)
    notes: str = ""


DEDUCTIVE_QUERIES: tuple[DeductiveQuery, ...] = (
    DeductiveQuery("Is a bat a mammal?", "kg", "Yes. bat is_a mammal.", ["kg_bat_is_mammal"], "membership"),
    DeductiveQuery("Can a mammal fly?", "kg", "Yes, under the demo KG there exists a mammal, bat, that can fly.", ["path:kg_bat_is_mammal->kg_bat_capable_fly"], "existential"),
    DeductiveQuery("Are all mammals able to fly?", "kg", "No. The demo KG contains mammal counterexamples such as whale not_capable_of fly.", ["path:kg_whale_is_mammal->kg_whale_not_fly", "path:kg_dolphin_is_mammal->kg_dolphin_not_fly"], "universal counterexample"),
    DeductiveQuery("Is a penguin a bird?", "kg", "Yes. penguin is_a bird.", ["kg_penguin_is_bird"], "membership"),
    DeductiveQuery("Are all birds able to fly?", "kg", "No. penguin and ostrich are bird counterexamples in the demo KG.", ["path:kg_penguin_is_bird->kg_penguin_not_fly", "path:kg_ostrich_is_bird->kg_ostrich_not_fly"], "universal counterexample"),
    DeductiveQuery("What property allows a bat to fly?", "kg", "The KG records bat has_property wings and bat capable_of fly.", ["kg_bat_has_wings", "kg_bat_capable_fly"], "property"),
    DeductiveQuery("What two-hop path connects bat to vertebrate?", "kg", "bat is_a mammal; mammal is_a vertebrate.", ["path:kg_bat_is_mammal->kg_mammal_is_vertebrate"], "2-hop path"),
    DeductiveQuery("What two-hop path connects penguin to vertebrate?", "kg", "penguin is_a bird; bird is_a vertebrate.", ["path:kg_penguin_is_bird->kg_bird_is_vertebrate"], "2-hop path"),
    DeductiveQuery("Can a whale fly?", "kg", "No. whale not_capable_of fly.", ["kg_whale_not_fly"], "property negation"),
    DeductiveQuery("Can a whale swim?", "kg", "Yes. whale capable_of swim.", ["kg_whale_capable_swim"], "property"),
    DeductiveQuery("Does a mammal produce milk?", "kg", "Yes. mammal produces milk.", ["kg_mammal_produces_milk"], "class property"),
    DeductiveQuery("Is a sparrow a bird?", "kg", "Yes. sparrow is_a bird.", ["kg_sparrow_is_bird"], "membership"),
    DeductiveQuery("Can a sparrow fly?", "kg", "Yes. sparrow capable_of fly.", ["kg_sparrow_capable_fly"], "property"),
    DeductiveQuery("What eats mosquito?", "kg", "bat eats mosquito and frog eats mosquito in the demo KG.", ["kg_bat_eats_mosquito", "kg_frog_eats_mosquito"], "relation lookup"),
    DeductiveQuery("What two-hop path connects whale to vertebrate?", "kg", "whale is_a mammal; mammal is_a vertebrate.", ["path:kg_whale_is_mammal->kg_mammal_is_vertebrate"], "2-hop path"),
    DeductiveQuery("Is a salmon a vertebrate?", "kg", "Indirectly yes through salmon is_a fish and fish is_a vertebrate.", ["path:kg_salmon_is_fish->kg_fish_is_vertebrate"], "2-hop inheritance"),
    DeductiveQuery("Are all birds able to swim?", "kg", "No. The demo KG contains bird counterexamples such as eagle not_capable_of swim.", ["path:kg_eagle_is_bird->kg_eagle_not_swim", "path:kg_chicken_is_bird->kg_chicken_not_swim"], "universal counterexample"),
    DeductiveQuery("What property does dolphin have?", "kg", "dolphin has_property echolocation.", ["kg_dolphin_has_property_echolocation"], "property"),
    DeductiveQuery("What two-hop path connects mosquito to animal?", "kg", "mosquito is_a insect; insect is_a animal.", ["path:kg_mosquito_is_insect->kg_insect_is_animal"], "2-hop path"),
    DeductiveQuery("Is a bat a vertebrate?", "kg", "Indirectly yes through bat is_a mammal and mammal is_a vertebrate.", ["path:kg_bat_is_mammal->kg_mammal_is_vertebrate"], "2-hop inheritance"),
)


def load_deductive_queries() -> list[DeductiveQuery]:
    return list(DEDUCTIVE_QUERIES)


def load_deductive_smoke_queries(limit: int = 5) -> list[str]:
    return [item.query for item in DEDUCTIVE_QUERIES[:limit]]
