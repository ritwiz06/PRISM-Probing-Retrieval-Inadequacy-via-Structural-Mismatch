from __future__ import annotations

import argparse
from pathlib import Path

from prism.external_benchmarks.loaders import (
    EXTERNAL_BENCHMARK_PATH,
    ExternalBenchmarkItem,
    benchmark_counts,
    write_external_mini_benchmark,
)


def build_external_mini_benchmark(path: str | Path = EXTERNAL_BENCHMARK_PATH) -> dict[str, object]:
    items = _normalized_items()
    output_path = write_external_mini_benchmark(items, path)
    counts = benchmark_counts(items)
    return {"path": str(output_path), "total": len(items), "counts": counts}


def _normalized_items() -> list[ExternalBenchmarkItem]:
    return [
        ExternalBenchmarkItem("ext_lex_001", "RFC-7231", "BEIR", "bm25", "HTTP/1.1 semantics and content.", "RFC-7231 defines HTTP/1.1 semantics and content.", tag="exact_identifier", notes="BEIR-style exact-match lookup."),
        ExternalBenchmarkItem("ext_lex_002", "What is ICD-10 J18.9?", "BEIR", "bm25", "Pneumonia, unspecified organism.", "ICD-10-CM J18.9 maps to pneumonia, unspecified organism.", tag="medical_code"),
        ExternalBenchmarkItem("ext_lex_003", "Find HIPAA section 164.512.", "BEIR", "bm25", "Uses and disclosures without authorization or opportunity to agree/object.", "HIPAA 164.512 covers uses and disclosures without authorization.", tag="legal_section"),
        ExternalBenchmarkItem("ext_lex_004", "What is torch.nn.CrossEntropyLoss?", "BEIR", "bm25", "Cross entropy loss for logits and targets.", "torch.nn.CrossEntropyLoss is cross entropy loss for logits and targets.", tag="api_identifier"),
        ExternalBenchmarkItem("ext_lex_005", "Find PostgreSQL jsonb_insert.", "BEIR", "bm25", "Inserts a new value into a JSONB document.", "PostgreSQL jsonb_insert inserts a new value into a JSONB document.", tag="api_identifier"),
        ExternalBenchmarkItem("ext_lex_006", "What is 42 U.S.C. §1983?", "BEIR", "bm25", "Civil action for deprivation of rights under color of state law.", "42 U.S.C. §1983 concerns civil action for deprivation of rights.", tag="legal_section"),
        ExternalBenchmarkItem("ext_lex_007", "Find numpy.linalg.svd.", "BEIR", "bm25", "Singular value decomposition.", "numpy.linalg.svd performs singular value decomposition.", tag="api_identifier"),
        ExternalBenchmarkItem("ext_lex_008", "What does sklearn.feature_extraction.text.TfidfVectorizer do?", "BEIR", "bm25", "A converter from raw documents to TF-IDF features.", "TfidfVectorizer converts raw documents to TF-IDF features.", tag="api_identifier"),
        ExternalBenchmarkItem("ext_sem_001", "What feels like climate anxiety?", "Natural Questions", "dense", "Climate anxiety.", "Climate anxiety describes distress about climate change.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_002", "Which condition is the charlatan feeling after success?", "Natural Questions", "dense", "Impostor syndrome.", "Impostor syndrome involves feeling like a fraud despite success.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_003", "What concept turns daylight into carbohydrates?", "Natural Questions", "dense", "Photosynthesis.", "Photosynthesis converts light energy into chemical energy.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_004", "What is a city asphalt warmth pocket called?", "Natural Questions", "dense", "Urban heat island.", "An urban heat island occurs when built surfaces make a city warmer.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_005", "Which concept describes durable recall filing during sleep?", "Natural Questions", "dense", "Memory consolidation.", "Memory consolidation stabilizes learned information.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_006", "Which term means automated unfairness pattern?", "Natural Questions", "dense", "Algorithmic bias.", "Algorithmic bias is a systematic unfairness pattern in automated outputs.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_007", "What is the internal metronome of daily biology?", "Natural Questions", "dense", "Circadian rhythm.", "Circadian rhythm is an internal biological clock.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_sem_008", "Which term names reward driven agent training?", "Natural Questions", "dense", "Reinforcement learning.", "Reinforcement learning trains agents through rewards and penalties.", tag="semantic_paraphrase"),
        ExternalBenchmarkItem("ext_kg_001", "Is a bat a mammal?", "WebQSP", "kg", "Yes. bat is_a mammal.", "bat is_a mammal", tag="membership"),
        ExternalBenchmarkItem("ext_kg_002", "Can a mammal fly?", "WebQSP", "kg", "Yes, under the demo KG there exists a mammal, bat, that can fly.", "bat is_a mammal ; bat capable_of fly", tag="existential"),
        ExternalBenchmarkItem("ext_kg_003", "Are all mammals able to fly?", "WebQSP", "kg", "No. whale and dolphin are mammal counterexamples.", "whale is_a mammal ; whale not_capable_of fly", tag="universal_counterexample"),
        ExternalBenchmarkItem("ext_kg_004", "What property allows a bat to fly?", "WebQSP", "kg", "bat has_property wings and bat capable_of fly.", "bat has_property wings", tag="property"),
        ExternalBenchmarkItem("ext_kg_005", "Can a whale swim?", "WebQSP", "kg", "Yes. whale capable_of swim.", "whale capable_of swim", tag="property"),
        ExternalBenchmarkItem("ext_kg_006", "Is a salmon a vertebrate?", "WebQSP", "kg", "Indirectly yes through salmon is_a fish and fish is_a vertebrate.", "salmon is_a fish ; fish is_a vertebrate", tag="two_hop"),
        ExternalBenchmarkItem("ext_kg_007", "What eats mosquito?", "WebQSP", "kg", "bat eats mosquito and frog eats mosquito.", "bat eats mosquito", tag="relation_lookup"),
        ExternalBenchmarkItem("ext_kg_008", "Are all birds able to swim?", "WebQSP", "kg", "No. eagle and chicken are bird counterexamples.", "eagle is_a bird ; eagle not_capable_of swim", tag="universal_counterexample"),
        ExternalBenchmarkItem("ext_rel_001", "What bridge connects bat and vertebrate?", "HotpotQA", "hybrid", "bat -> mammal -> vertebrate plus text bridge evidence.", "bat connects to vertebrate through mammal", tag="bridge"),
        ExternalBenchmarkItem("ext_rel_002", "What bridge connects penguin and vertebrate?", "HotpotQA", "hybrid", "penguin -> bird -> vertebrate plus text bridge evidence.", "penguin connects to vertebrate through bird", tag="bridge"),
        ExternalBenchmarkItem("ext_rel_003", "What relation connects bat and mosquito?", "HotpotQA", "hybrid", "bat eats mosquito plus text relation evidence.", "bat eats mosquito", tag="relation"),
        ExternalBenchmarkItem("ext_rel_004", "What relation connects dolphin and echolocation?", "HotpotQA", "hybrid", "dolphin has_property echolocation plus text relation evidence.", "dolphin has_property echolocation", tag="relation"),
        ExternalBenchmarkItem("ext_rel_005", "What bridge connects salmon and vertebrate?", "HotpotQA", "hybrid", "salmon -> fish -> vertebrate plus text bridge evidence.", "salmon connects to vertebrate through fish", tag="bridge"),
        ExternalBenchmarkItem("ext_rel_006", "What relation connects mammal and milk?", "HotpotQA", "hybrid", "mammal produces milk plus text relation evidence.", "mammal produces milk", tag="relation"),
        ExternalBenchmarkItem("ext_rel_007", "What relation connects owl and mouse?", "HotpotQA", "hybrid", "owl eats mouse plus text relation evidence.", "owl eats mouse", tag="relation"),
        ExternalBenchmarkItem("ext_rel_008", "What relation connects duck and swim?", "HotpotQA", "hybrid", "duck capable_of swim plus text relation evidence.", "duck capable_of swim", tag="relation"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's normalized external mini-benchmark.")
    parser.add_argument("--output", default=str(EXTERNAL_BENCHMARK_PATH))
    args = parser.parse_args()
    payload = build_external_mini_benchmark(args.output)
    print(f"external_mini_benchmark={payload['total']} output={payload['path']}")
    print(f"route_family_counts={payload['counts']['route_family']}")
    print(f"source_dataset_counts={payload['counts']['source_dataset']}")


if __name__ == "__main__":
    main()
