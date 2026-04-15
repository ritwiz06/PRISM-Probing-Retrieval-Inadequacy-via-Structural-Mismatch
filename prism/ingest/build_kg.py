from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path

from prism.config import load_config
from prism.logging_utils import configure_logging
from prism.schemas import Triple
from prism.utils import ensure_directories, read_jsonl_documents, write_jsonl_triples

LOGGER = logging.getLogger(__name__)


def _curated_demo_triples() -> list[Triple]:
    triples = [
        Triple("kg_mammal_is_vertebrate", "mammal", "is_a", "vertebrate", "doc_mammal"),
        Triple("kg_bird_is_vertebrate", "bird", "is_a", "vertebrate", "kg_doc_bird"),
        Triple("kg_bat_is_mammal", "bat", "is_a", "mammal", "doc_mammal"),
        Triple("kg_whale_is_mammal", "whale", "is_a", "mammal", "kg_doc_whale"),
        Triple("kg_dolphin_is_mammal", "dolphin", "is_a", "mammal", "kg_doc_dolphin"),
        Triple("kg_penguin_is_bird", "penguin", "is_a", "bird", "kg_doc_penguin"),
        Triple("kg_ostrich_is_bird", "ostrich", "is_a", "bird", "kg_doc_ostrich"),
        Triple("kg_sparrow_is_bird", "sparrow", "is_a", "bird", "kg_doc_sparrow"),
        Triple("kg_bat_capable_fly", "bat", "capable_of", "fly", "doc_mammal"),
        Triple("kg_bat_has_wings", "bat", "has_property", "wings", "doc_mammal"),
        Triple("kg_bat_has_echolocation", "bat", "has_property", "echolocation", "doc_mammal"),
        Triple("kg_bat_eats_mosquito", "bat", "eats", "mosquito", "kg_doc_bat_food"),
        Triple("kg_whale_not_fly", "whale", "not_capable_of", "fly", "kg_doc_whale"),
        Triple("kg_whale_capable_swim", "whale", "capable_of", "swim", "kg_doc_whale"),
        Triple("kg_dolphin_not_fly", "dolphin", "not_capable_of", "fly", "kg_doc_dolphin"),
        Triple("kg_dolphin_capable_swim", "dolphin", "capable_of", "swim", "kg_doc_dolphin"),
        Triple("kg_penguin_not_fly", "penguin", "not_capable_of", "fly", "kg_doc_penguin"),
        Triple("kg_penguin_capable_swim", "penguin", "capable_of", "swim", "kg_doc_penguin"),
        Triple("kg_ostrich_not_fly", "ostrich", "not_capable_of", "fly", "kg_doc_ostrich"),
        Triple("kg_sparrow_capable_fly", "sparrow", "capable_of", "fly", "kg_doc_sparrow"),
        Triple("kg_sparrow_has_wings", "sparrow", "has_property", "wings", "kg_doc_sparrow"),
        Triple("kg_mammal_produces_milk", "mammal", "produces", "milk", "kg_doc_mammal"),
        Triple("kg_bat_produces_milk", "bat", "produces", "milk", "doc_mammal"),
        Triple("kg_whale_produces_milk", "whale", "produces", "milk", "kg_doc_whale"),
        Triple("kg_dolphin_produces_milk", "dolphin", "produces", "milk", "kg_doc_dolphin"),
        Triple("kg_property_question_routes_kg", "property_question", "routes_to", "kg", "doc_policy"),
        Triple("kg_lexical_question_routes_bm25", "lexical_question", "routes_to", "bm25", "doc_bm25"),
        Triple("kg_semantic_question_routes_dense", "semantic_question", "routes_to", "dense", "doc_bm25"),
        Triple("kg_relation_question_routes_hybrid", "relation_question", "routes_to", "hybrid", "doc_policy"),
    ]

    animals = [
        ("cat", "mammal", "kg_doc_cat"),
        ("dog", "mammal", "kg_doc_dog"),
        ("horse", "mammal", "kg_doc_horse"),
        ("cow", "mammal", "kg_doc_cow"),
        ("elephant", "mammal", "kg_doc_elephant"),
        ("mouse", "mammal", "kg_doc_mouse"),
        ("kangaroo", "mammal", "kg_doc_kangaroo"),
        ("platypus", "mammal", "kg_doc_platypus"),
        ("eagle", "bird", "kg_doc_eagle"),
        ("owl", "bird", "kg_doc_owl"),
        ("duck", "bird", "kg_doc_duck"),
        ("chicken", "bird", "kg_doc_chicken"),
        ("salmon", "fish", "kg_doc_salmon"),
        ("shark", "fish", "kg_doc_shark"),
        ("frog", "amphibian", "kg_doc_frog"),
        ("lizard", "reptile", "kg_doc_lizard"),
    ]
    for animal, klass, source in animals:
        triples.append(Triple(f"kg_{animal}_is_{klass}", animal, "is_a", klass, source))
        if klass == "mammal":
            triples.append(Triple(f"kg_{animal}_not_fly", animal, "not_capable_of", "fly", source))
            triples.append(Triple(f"kg_{animal}_produces_milk", animal, "produces", "milk", source))
        if klass == "bird" and animal in {"eagle", "owl", "duck"}:
            triples.append(Triple(f"kg_{animal}_capable_fly", animal, "capable_of", "fly", source))
            triples.append(Triple(f"kg_{animal}_has_wings", animal, "has_property", "wings", source))
        if klass == "bird" and animal in {"eagle", "owl", "chicken"}:
            triples.append(Triple(f"kg_{animal}_not_swim", animal, "not_capable_of", "swim", source))
        if animal in {"duck", "salmon", "shark", "frog"}:
            triples.append(Triple(f"kg_{animal}_capable_swim", animal, "capable_of", "swim", source))

    classes = [
        ("fish", "vertebrate"),
        ("amphibian", "vertebrate"),
        ("reptile", "vertebrate"),
        ("vertebrate", "animal"),
        ("mosquito", "insect"),
        ("insect", "animal"),
        ("wing", "body_part"),
        ("wings", "body_part"),
        ("echolocation", "sensory_ability"),
        ("fly", "movement"),
        ("swim", "movement"),
        ("milk", "substance"),
    ]
    for subject, object_ in classes:
        triples.append(Triple(f"kg_{subject}_is_{object_}", subject, "is_a", object_, f"kg_doc_{subject}"))

    relations = [
        ("eagle", "eats", "fish"),
        ("owl", "eats", "mouse"),
        ("cat", "eats", "mouse"),
        ("frog", "eats", "mosquito"),
        ("duck", "has_property", "wings"),
        ("chicken", "has_property", "wings"),
        ("penguin", "has_property", "wings"),
        ("ostrich", "has_property", "wings"),
        ("chicken", "not_capable_of", "fly"),
        ("platypus", "has_property", "bill"),
        ("elephant", "has_property", "trunk"),
        ("whale", "has_property", "blowhole"),
        ("dolphin", "has_property", "echolocation"),
    ]
    for subject, predicate, object_ in relations:
        triples.append(Triple(f"kg_{subject}_{predicate}_{object_}", subject, predicate, object_, f"kg_doc_{subject}"))

    return triples


def _load_extra_triples(paths: list[Path]) -> list[Triple]:
    extras: list[Triple] = []
    for path in paths:
        if not path.exists():
            continue
        if path.suffix == ".json":
            rows = json.loads(path.read_text(encoding="utf-8"))
            extras.extend(Triple(**row) for row in rows)
        elif path.suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as file:
                extras.extend(Triple(**row) for row in csv.DictReader(file))
    return extras


def build_kg(corpus_path: str | None = None, output_path: str | None = None, extra_paths: list[str] | None = None) -> Path:
    config = load_config()
    configure_logging(config.log_level)
    ensure_directories([config.paths.raw_dir, config.paths.processed_dir, config.paths.indices_dir])

    resolved_corpus_path = Path(corpus_path or Path(config.paths.processed_dir) / "corpus.jsonl")
    if resolved_corpus_path.exists():
        _ = read_jsonl_documents(resolved_corpus_path)

    default_extra_paths = [
        Path(config.paths.raw_dir) / "kg_extra_triples.json",
        Path(config.paths.raw_dir) / "kg_extra_triples.csv",
    ]
    paths = [Path(path) for path in extra_paths] if extra_paths else default_extra_paths
    triples = _curated_demo_triples() + _load_extra_triples(paths)
    triples = sorted({triple.triple_id: triple for triple in triples}.values(), key=lambda triple: triple.triple_id)

    kg_path = Path(output_path or Path(config.paths.processed_dir) / "kg_triples.jsonl")
    write_jsonl_triples(kg_path, triples)

    ttl_path = Path(config.paths.processed_dir) / "kg.ttl"
    ttl_lines = [
        "@prefix prism: <https://prism.local/kg/> .",
        "",
        *[f"prism:{_ttl_name(triple.subject)} prism:{_ttl_name(triple.predicate)} prism:{_ttl_name(triple.object)} ." for triple in triples],
    ]
    ttl_path.write_text("\n".join(ttl_lines) + "\n", encoding="utf-8")

    LOGGER.info("Wrote %s triples to %s and Turtle to %s", len(triples), kg_path, ttl_path)
    return kg_path


def _ttl_name(value: str) -> str:
    return value.replace(" ", "_").replace("-", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local PRISM KG.")
    parser.add_argument("--corpus-path", default=None, help="Optional corpus JSONL path.")
    parser.add_argument("--output", default=None, help="Optional KG triple output path.")
    parser.add_argument("--extra", action="append", default=None, help="Optional JSON/CSV file with extra triples.")
    args = parser.parse_args()
    path = build_kg(corpus_path=args.corpus_path, output_path=args.output, extra_paths=args.extra)
    print(f"kg_path={path}")


if __name__ == "__main__":
    main()
