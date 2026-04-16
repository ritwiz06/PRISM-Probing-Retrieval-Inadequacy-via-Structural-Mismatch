from __future__ import annotations

import argparse
from pathlib import Path

from prism.public_graph.build_public_graph import build_public_graph
from prism.public_graph.loaders import (
    PUBLIC_STRUCTURE_BENCHMARK_PATH,
    PublicStructureItem,
    public_structure_counts,
    write_public_structure_benchmark,
)


def build_public_structure_benchmark(path: str | Path = PUBLIC_STRUCTURE_BENCHMARK_PATH) -> Path:
    build_public_graph()
    items = _items()
    return write_public_structure_benchmark(items, path)


def _items() -> list[PublicStructureItem]:
    rows = [
        ("ps_kg_01", "Is a bat a mammal?", "dev", "kg", "Yes. bat is_a mammal", ["pub_bat"], ["pg_bat_is_a_mammal"], [], "bat is_a mammal"),
        ("ps_kg_02", "Can a bat fly?", "dev", "kg", "Yes. bat capable_of fly", ["pub_bat"], ["pg_bat_capable_of_fly"], [], "bat capable_of fly"),
        ("ps_kg_03", "What property allows a bat to fly?", "dev", "kg", "wings", ["pub_bat"], ["pg_bat_has_property_wings"], [], "bat has_property wings"),
        ("ps_kg_04", "Is a penguin a bird?", "dev", "kg", "Yes. penguin is_a bird", ["pub_penguin"], ["pg_penguin_is_a_bird"], [], "penguin is_a bird"),
        ("ps_kg_05", "Can a penguin fly?", "dev", "kg", "No. penguin not_capable_of fly", ["pub_penguin"], ["pg_penguin_not_capable_of_fly"], [], "penguin not_capable_of fly"),
        ("ps_kg_06", "Is a dolphin a mammal?", "dev", "kg", "Yes. dolphin is_a mammal", ["pub_dolphin"], ["pg_dolphin_is_a_mammal"], [], "dolphin is_a mammal"),
        ("ps_kg_07", "Are all mammals able to fly?", "dev", "kg", "No. Counterexample evidence", ["pub_dolphin", "pub_whale"], ["pg_dolphin_not_capable_of_fly", "pg_whale_not_capable_of_fly"], [], "mammal counterexample not_capable_of fly"),
        ("ps_kg_08", "Is a mosquito an insect?", "dev", "kg", "Yes. mosquito is_a insect", ["pub_mosquito"], ["pg_mosquito_is_a_insect"], [], "mosquito is_a insect"),
        ("ps_kg_09", "Is a whale a mammal?", "test", "kg", "Yes. whale is_a mammal", ["pub_whale"], ["pg_whale_is_a_mammal"], [], "whale is_a mammal"),
        ("ps_kg_10", "Is salmon a fish?", "test", "kg", "Yes. salmon is_a fish", ["pub_salmon"], ["pg_salmon_is_a_fish"], [], "salmon is_a fish"),
        ("ps_kg_11", "Can an ostrich fly?", "test", "kg", "No. ostrich not_capable_of fly", ["pub_ostrich"], ["pg_ostrich_not_capable_of_fly"], [], "ostrich not_capable_of fly"),
        ("ps_kg_12", "Is a bird a vertebrate?", "test", "kg", "Yes. bird is_a vertebrate", ["pub_bird"], ["pg_bird_is_a_vertebrate"], [], "bird is_a vertebrate"),
        ("ps_kg_13", "Is a frog a vertebrate?", "test", "kg", "Yes. frog is_a vertebrate", ["pub_frog"], ["pg_frog_is_a_vertebrate"], [], "frog is_a vertebrate"),
        ("ps_kg_14", "Can an eagle fly?", "test", "kg", "Yes. eagle capable_of fly", ["pub_eagle"], ["pg_eagle_capable_of_fly"], [], "eagle capable_of fly"),
        ("ps_kg_15", "Is a vertebrate an animal?", "test", "kg", "Yes. vertebrate is_a animal", ["pub_vertebrate"], ["pg_vertebrate_is_a_animal"], [], "vertebrate is_a animal"),
        ("ps_kg_16", "What property allows an owl to fly?", "test", "kg", "wings", ["pub_owl_bird_predator"], ["pg_owl_has_property_wings"], [], "owl has_property wings"),
        ("ps_hybrid_01", "What bridge connects bat and vertebrate?", "dev", "hybrid", "mammal", ["pub_bat", "pub_mammal"], ["pg_bat_is_a_mammal", "pg_mammal_is_a_vertebrate"], [], "bat mammal vertebrate"),
        ("ps_hybrid_02", "What bridge connects penguin and vertebrate?", "dev", "hybrid", "bird", ["pub_penguin", "pub_bird"], ["pg_penguin_is_a_bird", "pg_bird_is_a_vertebrate"], [], "penguin bird vertebrate"),
        ("ps_hybrid_03", "What bridge connects dolphin and vertebrate?", "dev", "hybrid", "mammal", ["pub_dolphin", "pub_mammal"], ["pg_dolphin_is_a_mammal", "pg_mammal_is_a_vertebrate"], [], "dolphin mammal vertebrate"),
        ("ps_hybrid_04", "What bridge connects salmon and vertebrate?", "dev", "hybrid", "fish", ["pub_salmon", "pub_salmon_fish_migration"], ["pg_salmon_is_a_fish", "pg_fish_is_a_vertebrate"], [], "salmon fish vertebrate"),
        ("ps_hybrid_05", "What bridge connects mosquito and animal?", "dev", "hybrid", "insect", ["pub_mosquito", "pub_mosquito_insect_flight"], ["pg_mosquito_is_a_insect", "pg_insect_is_a_animal"], [], "mosquito insect animal"),
        ("ps_hybrid_06", "What bridge connects ostrich and vertebrate?", "dev", "hybrid", "bird", ["pub_ostrich", "pub_bird"], ["pg_ostrich_is_a_bird", "pg_bird_is_a_vertebrate"], [], "ostrich bird vertebrate"),
        ("ps_hybrid_07", "What bridge connects eagle and vertebrate?", "dev", "hybrid", "bird", ["pub_eagle", "pub_bird"], ["pg_eagle_is_a_bird", "pg_bird_is_a_vertebrate"], [], "eagle bird vertebrate"),
        ("ps_hybrid_08", "What bridge connects whale and vertebrate?", "dev", "hybrid", "mammal", ["pub_whale", "pub_mammal"], ["pg_whale_is_a_mammal", "pg_mammal_is_a_vertebrate"], [], "whale mammal vertebrate"),
        ("ps_hybrid_09", "What bridge connects frog and animal?", "test", "hybrid", "vertebrate", ["pub_frog", "pub_vertebrate"], ["pg_frog_is_a_vertebrate", "pg_vertebrate_is_a_animal"], [], "frog vertebrate animal"),
        ("ps_hybrid_10", "What bridge connects duck and vertebrate?", "test", "hybrid", "bird", ["pub_duck_bird_swim", "pub_bird"], ["pg_duck_is_a_bird", "pg_bird_is_a_vertebrate"], [], "duck bird vertebrate"),
        ("ps_hybrid_11", "What bridge connects cat and vertebrate?", "test", "hybrid", "mammal", ["pub_cat_mammal_pet", "pub_mammal"], ["pg_cat_is_a_mammal", "pg_mammal_is_a_vertebrate"], [], "cat mammal vertebrate"),
        ("ps_hybrid_12", "What bridge connects owl and vertebrate?", "test", "hybrid", "bird", ["pub_owl_bird_predator", "pub_bird"], ["pg_owl_is_a_bird", "pg_bird_is_a_vertebrate"], [], "owl bird vertebrate"),
        ("ps_hybrid_13", "What bridge connects mammal and animal?", "test", "hybrid", "vertebrate", ["pub_mammal", "pub_vertebrate"], ["pg_mammal_is_a_vertebrate", "pg_vertebrate_is_a_animal"], [], "mammal vertebrate animal"),
        ("ps_hybrid_14", "What bridge connects bird and animal?", "test", "hybrid", "vertebrate", ["pub_bird", "pub_vertebrate"], ["pg_bird_is_a_vertebrate", "pg_vertebrate_is_a_animal"], [], "bird vertebrate animal"),
        ("ps_hybrid_15", "What bridge connects fish and animal?", "test", "hybrid", "vertebrate", ["pub_salmon_fish_migration", "pub_vertebrate"], ["pg_fish_is_a_vertebrate", "pg_vertebrate_is_a_animal"], [], "fish vertebrate animal"),
        ("ps_hybrid_16", "What relation connects insect and animal?", "test", "hybrid", "animal", ["pub_mosquito_insect_flight"], ["pg_insect_is_a_animal"], [], "insect is_a animal"),
    ]
    return [
        PublicStructureItem(
            id=row[0],
            query=row[1],
            split=row[2],
            route_family=row[3],
            gold_answer=row[4],
            gold_source_doc_ids=row[5],
            gold_triple_ids=_resolve_public_graph_ids(row[6]),
            gold_path_ids=row[7],
            gold_evidence_text=row[8],
        )
        for row in rows
    ]


def _resolve_public_graph_ids(prefixes: list[str]) -> list[str]:
    from prism.public_graph.build_public_graph import load_public_structure_triples

    triples = load_public_structure_triples("public_graph")
    resolved: list[str] = []
    for prefix in prefixes:
        matches = [triple.triple_id for triple in triples if triple.triple_id.startswith(prefix)]
        resolved.extend(matches or [prefix])
    return sorted(set(resolved))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public-structure benchmark.")
    parser.add_argument("--path", default=str(PUBLIC_STRUCTURE_BENCHMARK_PATH))
    args = parser.parse_args()
    path = build_public_structure_benchmark(args.path)
    items = _items()
    print(f"public_structure_benchmark path={path} total={len(items)} counts={public_structure_counts(items)}")


if __name__ == "__main__":
    main()
