from __future__ import annotations

import re

ENTITY_ALIASES = {
    "bats": "bat",
    "bat": "bat",
    "penguins": "penguin",
    "penguin": "penguin",
    "dolphins": "dolphin",
    "dolphin": "dolphin",
    "whales": "whale",
    "whale": "whale",
    "salmon": "salmon",
    "mosquitoes": "mosquito",
    "mosquito": "mosquito",
    "ostriches": "ostrich",
    "ostrich": "ostrich",
    "eagles": "eagle",
    "eagle": "eagle",
    "frogs": "frog",
    "frog": "frog",
    "ducks": "duck",
    "duck": "duck",
    "cats": "cat",
    "cat": "cat",
    "owls": "owl",
    "owl": "owl",
    "mammals": "mammal",
    "mammal": "mammal",
    "birds": "bird",
    "bird": "bird",
    "fish": "fish",
    "insects": "insect",
    "insect": "insect",
    "amphibians": "amphibian",
    "amphibian": "amphibian",
    "vertebrates": "vertebrate",
    "vertebrate": "vertebrate",
    "animals": "animal",
    "animal": "animal",
    "wings": "wings",
    "wing": "wings",
    "fly": "fly",
    "flight": "fly",
    "swim": "swim",
    "swimming": "swim",
    "milk": "milk",
    "echolocation": "echolocation",
}

PREDICATE_ALIASES = {
    "is": "is_a",
    "is_a": "is_a",
    "are": "is_a",
    "capable": "capable_of",
    "capable_of": "capable_of",
    "not_capable_of": "not_capable_of",
    "has": "has_property",
    "has_property": "has_property",
    "produces": "produces",
    "eats": "eats",
}


def normalize_entity(value: str) -> str:
    text = re.sub(r"[^a-z0-9_ -]+", " ", value.lower()).strip()
    text = re.sub(r"\s+", " ", text)
    return ENTITY_ALIASES.get(text, text.replace(" ", "_"))


def normalize_predicate(value: str) -> str:
    text = value.lower().strip().replace(" ", "_")
    return PREDICATE_ALIASES.get(text, text)


def known_entity(value: str) -> bool:
    return normalize_entity(value) in set(ENTITY_ALIASES.values())


def triple_key(subject: str, predicate: str, object_: str) -> tuple[str, str, str]:
    return normalize_entity(subject), normalize_predicate(predicate), normalize_entity(object_)
