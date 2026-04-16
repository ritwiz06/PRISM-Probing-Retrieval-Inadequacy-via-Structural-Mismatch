from __future__ import annotations

import argparse
from pathlib import Path

from prism.public_corpus.build_public_corpus import build_public_corpus
from prism.public_corpus.loaders import (
    PUBLIC_BENCHMARK_PATH,
    PublicBenchmarkItem,
    public_benchmark_counts,
    write_public_benchmark,
)


def build_public_benchmark(path: str | Path = PUBLIC_BENCHMARK_PATH) -> Path:
    build_public_corpus()
    items = _benchmark_items()
    output_path = write_public_benchmark(items, path)
    return output_path


def _benchmark_items() -> list[PublicBenchmarkItem]:
    rows = [
        ("pub_bm25_01", "RFC-7231", "dev", "bm25", "BEIR-style lexical", "HTTP/1.1 Semantics and Content", ["pub_rfc_7231"], "RFC-7231"),
        ("pub_bm25_02", "What does 45 CFR 164.512 cover?", "dev", "bm25", "official regulation", "uses and disclosures for which authorization or opportunity to agree or object is not required", ["pub_hipaa_164_512"], "164.512"),
        ("pub_bm25_03", "J18.9", "dev", "bm25", "medical code lookup", "pneumonia unspecified organism", ["pub_icd_j18_9"], "J18.9"),
        ("pub_bm25_04", "torch.nn.CrossEntropyLoss", "dev", "bm25", "official docs", "criterion that computes cross entropy loss", ["pub_torch_cross_entropy"], "torch.nn.CrossEntropyLoss"),
        ("pub_bm25_05", "numpy.linalg.svd", "dev", "bm25", "official docs", "singular value decomposition", ["pub_numpy_svd"], "numpy.linalg.svd"),
        ("pub_bm25_06", "PostgreSQL jsonb binary JSON type", "dev", "bm25", "official docs", "binary JSON data type", ["pub_postgres_jsonb"], "jsonb"),
        ("pub_bm25_07", "RFC-9110", "test", "bm25", "BEIR-style lexical", "HTTP Semantics", ["pub_rfc_9110"], "RFC-9110"),
        ("pub_bm25_08", "RFC-7235 authentication", "test", "bm25", "BEIR-style lexical", "HTTP/1.1 Authentication", ["pub_rfc_7235"], "RFC-7235"),
        ("pub_bm25_09", "RFC-3986 URI generic syntax", "test", "bm25", "BEIR-style lexical", "Uniform Resource Identifier generic syntax", ["pub_rfc_3986"], "RFC-3986"),
        ("pub_bm25_10", "45 CFR 164.510 opportunity to agree or object", "test", "bm25", "official regulation", "uses and disclosures requiring an opportunity to agree or object", ["pub_hipaa_164_510"], "164.510"),
        ("pub_bm25_11", "Python dataclasses generated special methods", "test", "bm25", "official docs", "decorator and functions for automatically adding generated special methods", ["pub_python_dataclass"], "dataclasses"),
        ("pub_bm25_12", "TfidfVectorizer raw documents matrix TF-IDF features", "test", "bm25", "official docs", "convert raw documents to a matrix of TF-IDF features", ["pub_sklearn_tfidf"], "TfidfVectorizer"),
        ("pub_dense_01", "What feels like worry or grief about the climate future?", "dev", "dense", "Natural Questions-style semantic", "climate anxiety", ["pub_climate_anxiety"], "distress, worry, fear, or grief"),
        ("pub_dense_02", "What process turns light energy into stored chemical energy?", "dev", "dense", "Natural Questions-style semantic", "photosynthesis", ["pub_photosynthesis"], "convert light energy into chemical energy"),
        ("pub_dense_03", "What concept explains why city centers can be hotter than nearby countryside?", "dev", "dense", "Natural Questions-style semantic", "urban heat island", ["pub_urban_heat_island"], "warmer than nearby rural areas"),
        ("pub_dense_04", "What process makes a temporary memory more stable over time?", "dev", "dense", "TriviaQA-style semantic", "memory consolidation", ["pub_memory_consolidation"], "temporary memory becomes more stable"),
        ("pub_dense_05", "What term describes unfair repeatable errors from automated systems?", "dev", "dense", "Natural Questions-style semantic", "algorithmic bias", ["pub_algorithmic_bias"], "unfair outcomes"),
        ("pub_dense_06", "What is the roughly 24-hour internal body cycle called?", "dev", "dense", "TriviaQA-style semantic", "circadian rhythm", ["pub_circadian_rhythm"], "24-hour cycle"),
        ("pub_dense_07", "What learning setup lets an agent improve using rewards and penalties?", "test", "dense", "Natural Questions-style semantic", "reinforcement learning", ["pub_reinforcement_learning"], "learns behavior from rewards"),
        ("pub_dense_08", "What economic model keeps materials in use instead of treating them as waste?", "test", "dense", "Natural Questions-style semantic", "circular economy", ["pub_circular_economy"], "keep products and materials in use"),
        ("pub_dense_09", "What cycle moves water through evaporation, rain, and runoff?", "test", "dense", "TriviaQA-style semantic", "water cycle", ["pub_water_cycle"], "evaporation, condensation, precipitation"),
        ("pub_dense_10", "What immune response mistakes harmless substances for threats?", "test", "dense", "Natural Questions-style semantic", "allergy", ["pub_allergy"], "immune system reaction"),
        ("pub_dense_11", "What theory explains how new ideas spread through a social system?", "test", "dense", "MS MARCO-style semantic", "diffusion of innovations", ["pub_diffusion_innovations"], "spread through a social system"),
        ("pub_dense_12", "What view of word meaning uses neighboring contexts?", "test", "dense", "MS MARCO-style semantic", "distributional semantics", ["pub_distributional_semantics"], "contexts in which words appear"),
        ("pub_kg_01", "Is a bat a mammal?", "dev", "kg", "WebQSP-style structured", "Yes. bat is_a mammal", ["pub_bat"], "bat is a mammal"),
        ("pub_kg_02", "Can a bat fly?", "dev", "kg", "WebQSP-style structured", "Yes. bat capable_of fly", ["pub_bat"], "capable of powered flight"),
        ("pub_kg_03", "Is a penguin a bird?", "dev", "kg", "WebQSP-style structured", "Yes. penguin is_a bird", ["pub_penguin"], "penguin is a bird"),
        ("pub_kg_04", "Can a penguin fly?", "dev", "kg", "WebQSP-style structured", "No. penguin not_capable_of fly", ["pub_penguin"], "not capable of flight"),
        ("pub_kg_05", "Is a dolphin a mammal?", "dev", "kg", "WebQSP-style structured", "Yes. dolphin is_a mammal", ["pub_dolphin"], "dolphin is a mammal"),
        ("pub_kg_06", "Are all mammals able to fly?", "dev", "kg", "CWQ-style structured", "No. Counterexample evidence", ["pub_bat", "pub_dolphin", "pub_whale"], "counterexample"),
        ("pub_kg_07", "Is a whale a mammal?", "test", "kg", "WebQSP-style structured", "Yes. whale is_a mammal", ["pub_whale"], "whale is a mammal"),
        ("pub_kg_08", "Is salmon a fish?", "test", "kg", "WebQSP-style structured", "Yes. salmon is_a fish", ["pub_salmon"], "salmon is a fish"),
        ("pub_kg_09", "Is a mosquito an insect?", "test", "kg", "WebQSP-style structured", "Yes. mosquito is_a insect", ["pub_mosquito"], "mosquito is an insect"),
        ("pub_kg_10", "Can an ostrich fly?", "test", "kg", "GrailQA-style structured", "No. ostrich not_capable_of fly", ["pub_ostrich"], "not capable of flight"),
        ("pub_kg_11", "Is a bird a vertebrate?", "test", "kg", "WebQSP-style structured", "Yes. bird is_a vertebrate", ["pub_bird"], "bird is a vertebrate"),
        ("pub_kg_12", "What property allows a bat to fly?", "test", "kg", "GrailQA-style structured", "wings", ["pub_bat", "pub_bat_echolocation"], "wings"),
        ("pub_hybrid_01", "What bridge connects bat and vertebrate?", "dev", "hybrid", "HotpotQA-style bridge", "mammal", ["pub_bat", "pub_mammal"], "bat connects to vertebrate through mammal"),
        ("pub_hybrid_02", "What bridge connects dolphin and vertebrate?", "dev", "hybrid", "HotpotQA-style bridge", "mammal", ["pub_dolphin", "pub_dolphin_mammal_swim"], "dolphin connects to vertebrate through mammal"),
        ("pub_hybrid_03", "What bridge connects penguin and vertebrate?", "dev", "hybrid", "2WikiMultihopQA-style bridge", "bird", ["pub_penguin", "pub_penguin_swimming"], "penguins are birds and vertebrates"),
        ("pub_hybrid_04", "What bridge connects salmon and vertebrate?", "dev", "hybrid", "2WikiMultihopQA-style bridge", "fish", ["pub_salmon", "pub_salmon_fish_migration"], "salmon connect to vertebrate through fish"),
        ("pub_hybrid_05", "What bridge connects mosquito and animal?", "dev", "hybrid", "HotpotQA-style bridge", "insect", ["pub_mosquito", "pub_mosquito_insect_flight"], "mosquito connects to animal through insect"),
        ("pub_hybrid_06", "What bridge connects ostrich and vertebrate?", "dev", "hybrid", "HotpotQA-style bridge", "bird", ["pub_ostrich", "pub_ostrich_bird_counterexample"], "ostrich connects to vertebrate through bird"),
        ("pub_hybrid_07", "What bridge connects eagle and vertebrate?", "test", "hybrid", "HotpotQA-style bridge", "bird", ["pub_eagle", "pub_eagle_bird_flight"], "eagle connects to vertebrate through bird"),
        ("pub_hybrid_08", "What bridge connects whale and vertebrate?", "test", "hybrid", "2WikiMultihopQA-style bridge", "mammal", ["pub_whale", "pub_whale_mammal_milk"], "whale connects to vertebrate through mammal"),
        ("pub_hybrid_09", "What bridge connects frog and animal?", "test", "hybrid", "2WikiMultihopQA-style bridge", "vertebrate", ["pub_frog", "pub_frog_vertebrate_amphibian"], "frog connects to animal through vertebrate"),
        ("pub_hybrid_10", "What bridge connects duck and vertebrate?", "test", "hybrid", "HotpotQA-style bridge", "bird", ["pub_duck_bird_swim"], "duck connects to vertebrate through bird"),
        ("pub_hybrid_11", "What bridge connects cat and vertebrate?", "test", "hybrid", "HotpotQA-style bridge", "mammal", ["pub_cat_mammal_pet"], "cat connects to vertebrate through mammal"),
        ("pub_hybrid_12", "What bridge connects owl and vertebrate?", "test", "hybrid", "2WikiMultihopQA-style bridge", "bird", ["pub_owl_bird_predator"], "owl connects to vertebrate through bird"),
    ]
    return [
        PublicBenchmarkItem(
            id=row[0],
            query=row[1],
            split=row[2],
            route_family=row[3],
            source_dataset_style=row[4],
            gold_answer=row[5],
            gold_source_doc_ids=row[6],
            gold_evidence_text=row[7],
        )
        for row in rows
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public raw-document benchmark.")
    parser.add_argument("--path", default=str(PUBLIC_BENCHMARK_PATH))
    args = parser.parse_args()
    path = build_public_benchmark(args.path)
    from prism.public_corpus.loaders import load_public_benchmark

    items = load_public_benchmark(path)
    print(
        "public_benchmark "
        f"path={path} total={len(items)} counts={public_benchmark_counts(items)}"
    )


if __name__ == "__main__":
    main()
