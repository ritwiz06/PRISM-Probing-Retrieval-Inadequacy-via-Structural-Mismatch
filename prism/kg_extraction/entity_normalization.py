from __future__ import annotations

import re


ENTITY_ALIASES = {
    "bats": "bat",
    "bat": "bat",
    "mammals": "mammal",
    "mammal": "mammal",
    "vertebrates": "vertebrate",
    "vertebrate": "vertebrate",
    "birds": "bird",
    "bird": "bird",
    "penguins": "penguin",
    "penguin": "penguin",
    "whales": "whale",
    "whale": "whale",
    "dolphins": "dolphin",
    "dolphin": "dolphin",
    "salmon": "salmon",
    "mosquitoes": "mosquito",
    "mosquito": "mosquito",
    "insects": "insect",
    "insect": "insect",
    "frogs": "frog",
    "frog": "frog",
    "eagles": "eagle",
    "eagle": "eagle",
    "owls": "owl",
    "owl": "owl",
    "ducks": "duck",
    "duck": "duck",
    "sparrows": "sparrow",
    "sparrow": "sparrow",
    "cats": "cat",
    "cat": "cat",
    "mice": "mouse",
    "mouse": "mouse",
    "fish": "fish",
    "animal": "animal",
    "animals": "animal",
    "wings": "wings",
    "wing": "wing",
    "fly": "fly",
    "flight": "fly",
    "swim": "swim",
    "milk": "milk",
    "echolocation": "echolocation",
}
KNOWN_ENTITIES = set(ENTITY_ALIASES.values())

PREDICATE_ALIASES = {
    "is": "is_a",
    "is a": "is_a",
    "are": "is_a",
    "connects through": "is_a",
    "capable of": "capable_of",
    "can": "capable_of",
    "has property": "has_property",
    "property": "has_property",
    "eats": "eats",
    "produces": "produces",
}

STOP_OBJECT_SUFFIXES = (" class", " relation", " facts", " evidence", " animal")


def normalize_entity(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_ -]+", " ", value.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;-")
    for suffix in STOP_OBJECT_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    if cleaned in ENTITY_ALIASES:
        return ENTITY_ALIASES[cleaned]
    if cleaned.endswith("s") and cleaned[:-1] in ENTITY_ALIASES:
        return ENTITY_ALIASES[cleaned[:-1]]
    return cleaned.replace(" ", "_")


def normalize_predicate(value: str) -> str:
    cleaned = re.sub(r"[^a-z_ ]+", " ", value.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return PREDICATE_ALIASES.get(cleaned, cleaned.replace(" ", "_"))


def triple_key(subject: str, predicate: str, object_: str) -> tuple[str, str, str]:
    return normalize_entity(subject), normalize_predicate(predicate), normalize_entity(object_)


def is_known_entity(value: str) -> bool:
    return normalize_entity(value) in KNOWN_ENTITIES
