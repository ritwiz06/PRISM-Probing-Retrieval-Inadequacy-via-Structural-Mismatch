from __future__ import annotations

import argparse
from pathlib import Path

from prism.generalization.loaders import (
    GENERALIZATION_BENCHMARK_PATH,
    GeneralizationItem,
    benchmark_counts,
    write_generalization_benchmark,
)


def build_generalization_benchmark(path: str | Path = GENERALIZATION_BENCHMARK_PATH) -> dict[str, object]:
    items = _items()
    output_path = write_generalization_benchmark(items, path)
    return {"path": str(output_path), "total": len(items), "counts": benchmark_counts(items)}


def _items() -> list[GeneralizationItem]:
    rows: list[GeneralizationItem] = []
    rows.extend(_lexical_items())
    rows.extend(_semantic_items())
    rows.extend(_deductive_items())
    rows.extend(_relational_items())
    return rows


def _item(
    item_id: str,
    query: str,
    source: str,
    split: str,
    family: str,
    gold_answer: str,
    evidence: str,
    tag: str,
    notes: str,
    difficulty: str = "held_out",
) -> GeneralizationItem:
    return GeneralizationItem(
        id=item_id,
        query=query,
        source_dataset=source,
        split=split,
        route_family=family,
        gold_answer=gold_answer,
        gold_evidence_text=evidence,
        difficulty=difficulty,
        tag=tag,
        notes=notes,
    )


def _lexical_items() -> list[GeneralizationItem]:
    rows = [
        ("gen_lex_dev_001", "Find exact RFC-7231 semantics.", "BEIR-Robust", "dev", "HTTP/1.1 semantics and content", "RFC-7231 defines HTTP/1.1 semantics and content.", "identifier"),
        ("gen_lex_dev_002", "RFC-7230 message syntax and routing", "BEIR-Robust", "dev", "HTTP/1.1 message syntax, routing", "RFC-7230 defines HTTP/1.1 message syntax and routing.", "identifier"),
        ("gen_lex_dev_003", "HIPAA section 164.512 authorization not required", "BEIR-FiQA", "dev", "authorization or opportunity to agree or object is not required", "HIPAA section 164.512 covers uses and disclosures for which authorization is not required.", "legal_section"),
        ("gen_lex_dev_004", "HIPAA 164.514 protected health information", "BEIR-FiQA", "dev", "protected health information", "HIPAA section 164.514 covers protected health information requirements.", "legal_section"),
        ("gen_lex_dev_005", "ICD-10-CM code J18.9", "BEIR-BioASQ", "dev", "pneumonia, unspecified organism", "ICD-10-CM code J18.9 identifies pneumonia, unspecified organism.", "medical_code"),
        ("gen_lex_dev_006", "ICD-10 J18.0 bronchopneumonia", "BEIR-BioASQ", "dev", "bronchopneumonia, unspecified organism", "ICD-10-CM code J18.0 identifies bronchopneumonia.", "medical_code"),
        ("gen_lex_dev_007", "torch.nn.CrossEntropyLoss exact API", "BEIR-CodeSearch", "dev", "cross entropy loss", "torch.nn.CrossEntropyLoss computes cross entropy loss.", "api_identifier"),
        ("gen_lex_dev_008", "torch.nn.NLLLoss exact API", "BEIR-CodeSearch", "dev", "negative log likelihood loss", "torch.nn.NLLLoss computes the negative log likelihood loss.", "api_identifier"),
        ("gen_lex_dev_009", "PostgreSQL jsonb_set JSONB path", "BEIR-CodeSearch", "dev", "updates or inserts a value", "PostgreSQL jsonb_set updates or inserts a value.", "api_identifier"),
        ("gen_lex_dev_010", "numpy.linalg.svd exact function", "BEIR-CodeSearch", "dev", "singular value decomposition", "numpy.linalg.svd performs singular value decomposition.", "api_identifier"),
        ("gen_lex_test_001", "42 U.S.C. §1983 civil action", "BEIR-Robust", "test", "civil action for deprivation of rights", "42 U.S.C. §1983 provides a civil action for deprivation of rights.", "legal_section"),
        ("gen_lex_test_002", "42 U.S.C. §1981 contracts", "BEIR-Robust", "test", "make and enforce contracts", "42 U.S.C. §1981 protects equal rights to make and enforce contracts.", "legal_section"),
        ("gen_lex_test_003", "sklearn.feature_extraction.text.TfidfVectorizer exact class", "BEIR-CodeSearch", "test", "TF-IDF features", "TfidfVectorizer converts raw documents to TF-IDF features.", "api_identifier"),
        ("gen_lex_test_004", "sklearn.feature_extraction.text.CountVectorizer exact class", "BEIR-CodeSearch", "test", "matrix of token counts", "CountVectorizer converts text documents to a matrix of token counts.", "api_identifier"),
        ("gen_lex_test_005", "HTML aria-label accessible name", "BEIR-Robust", "test", "accessible name", "The aria-label attribute defines an accessible name.", "web_identifier"),
        ("gen_lex_test_006", "HTML aria-labelledby current element", "BEIR-Robust", "test", "identifies elements that label the current element", "The aria-labelledby attribute identifies elements that label the current element.", "web_identifier"),
        ("gen_lex_test_007", "RFC-7235 authentication framework", "BEIR-Robust", "test", "authentication framework", "RFC-7235 defines the HTTP/1.1 authentication framework.", "identifier"),
        ("gen_lex_test_008", "PostgreSQL jsonb_insert exact function", "BEIR-CodeSearch", "test", "inserts a new value", "PostgreSQL jsonb_insert inserts a new value into a JSONB document.", "api_identifier"),
        ("gen_lex_test_009", "numpy.linalg.norm exact function", "BEIR-CodeSearch", "test", "matrix or vector norm", "numpy.linalg.norm returns a matrix or vector norm.", "api_identifier"),
        ("gen_lex_test_010", "torch.nn.BCELoss exact API", "BEIR-CodeSearch", "test", "binary cross entropy", "torch.nn.BCELoss measures binary cross entropy.", "api_identifier"),
    ]
    return [
        _item(item_id, query, source, split, "bm25", gold, evidence, tag, "Public lexical-retrieval style exact or near-exact lookup.")
        for item_id, query, source, split, gold, evidence, tag in rows
    ]


def _semantic_items() -> list[GeneralizationItem]:
    rows = [
        ("gen_sem_dev_001", "Which concept describes worry about ecological loss and climate futures?", "NaturalQuestions-style", "dev", "Climate anxiety", "Climate anxiety describes distress and worry about climate change.", "paraphrase"),
        ("gen_sem_dev_002", "Which concept describes feeling like a fraud despite competence?", "NaturalQuestions-style", "dev", "Impostor syndrome", "Impostor syndrome is persistent self-doubt despite competence.", "paraphrase"),
        ("gen_sem_dev_003", "Which concept converts sunlight, carbon dioxide, and water into stored energy?", "TriviaQA-style", "dev", "Photosynthesis", "Photosynthesis converts sunlight, carbon dioxide, and water into stored chemical energy.", "paraphrase"),
        ("gen_sem_dev_004", "Which concept explains new ideas spreading through social systems?", "TriviaQA-style", "dev", "Diffusion of innovations", "Diffusion of innovations explains how new ideas spread through communities.", "paraphrase"),
        ("gen_sem_dev_005", "Which concept names city warmth from built surfaces?", "NaturalQuestions-style", "dev", "Urban heat island", "An urban heat island occurs when built surfaces make a city warmer.", "paraphrase"),
        ("gen_sem_dev_006", "Which concept stabilizes learning during sleep?", "NaturalQuestions-style", "dev", "Memory consolidation", "Memory consolidation makes experiences and learning more stable, especially during sleep.", "paraphrase"),
        ("gen_sem_dev_007", "Which concept means immune overreaction to harmless pollen?", "TriviaQA-style", "dev", "Allergy", "An allergy is an immune response to usually harmless substances such as pollen.", "paraphrase"),
        ("gen_sem_dev_008", "Which concept describes plant-root fungal nutrient signaling?", "TriviaQA-style", "dev", "Mycorrhizal network", "A mycorrhizal network connects fungi and plant roots.", "paraphrase"),
        ("gen_sem_dev_009", "Which concept captures unfair skewed automated outputs?", "MSMARCO-style", "dev", "Algorithmic bias", "Algorithmic bias produces unfair or systematically skewed outputs.", "paraphrase"),
        ("gen_sem_dev_010", "Which concept is an internal daily timing cycle?", "MSMARCO-style", "dev", "Circadian rhythm", "A circadian rhythm is an internal daily timing cycle.", "paraphrase"),
        ("gen_sem_test_001", "Which concept puts a price on greenhouse gas emissions?", "NaturalQuestions-style", "test", "Carbon pricing", "Carbon pricing attaches a cost to greenhouse gas emissions.", "paraphrase"),
        ("gen_sem_test_002", "Which concept organizes memories into a life story?", "NaturalQuestions-style", "test", "Narrative identity", "Narrative identity organizes memories and events into a life story.", "paraphrase"),
        ("gen_sem_test_003", "Which concept is shared online knowledge with community governance?", "MSMARCO-style", "test", "Digital commons", "Digital commons are shared online knowledge resources maintained by communities.", "paraphrase"),
        ("gen_sem_test_004", "Which concept tracks evaporation, condensation, precipitation, and runoff?", "TriviaQA-style", "test", "Water cycle", "The water cycle includes evaporation, condensation, precipitation, and runoff.", "paraphrase"),
        ("gen_sem_test_005", "Which concept trains agents through rewards and feedback?", "MSMARCO-style", "test", "Reinforcement learning", "Reinforcement learning trains agents through rewards and feedback.", "paraphrase"),
        ("gen_sem_test_006", "Which concept represents meaning through nearby context?", "MSMARCO-style", "test", "Distributional semantics", "Distributional semantics represents word meaning through nearby context.", "paraphrase"),
        ("gen_sem_test_007", "Which concept describes focus divided by notifications?", "NaturalQuestions-style", "test", "Attention fragmentation", "Attention fragmentation describes reduced focus from notifications and interruptions.", "paraphrase"),
        ("gen_sem_test_008", "Which concept describes a species role in an environment?", "TriviaQA-style", "test", "Ecological niche", "An ecological niche is the role a species occupies in an environment.", "paraphrase"),
        ("gen_sem_test_009", "Which concept says perspective and lived context shape knowledge?", "NaturalQuestions-style", "test", "Situated knowledge", "Situated knowledge emphasizes perspective and lived context.", "paraphrase"),
        ("gen_sem_test_010", "Which concept names tiny changes causing large later effects?", "TriviaQA-style", "test", "Butterfly effect", "The butterfly effect names sensitive dependence on initial conditions.", "paraphrase"),
    ]
    return [
        _item(item_id, query, source, split, "dense", gold, evidence, tag, "Public semantic-QA style paraphrase grounded in local semantic corpus.")
        for item_id, query, source, split, gold, evidence, tag in rows
    ]


def _deductive_items() -> list[GeneralizationItem]:
    rows = [
        ("gen_kg_dev_001", "Is a bat a mammal?", "WebQSP-style", "dev", "bat is_a mammal", "bat is_a mammal", "membership"),
        ("gen_kg_dev_002", "Is a penguin a bird?", "WebQSP-style", "dev", "penguin is_a bird", "penguin is_a bird", "membership"),
        ("gen_kg_dev_003", "Is a whale a mammal?", "WebQSP-style", "dev", "whale is_a mammal", "whale is_a mammal", "membership"),
        ("gen_kg_dev_004", "Is a salmon a vertebrate?", "GrailQA-style", "dev", "salmon is_a fish ; fish is_a vertebrate", "salmon is_a fish and fish is_a vertebrate", "two_hop"),
        ("gen_kg_dev_005", "Can a mammal fly?", "CWQ-style", "dev", "bat capable_of fly", "bat is_a mammal ; bat capable_of fly", "existential"),
        ("gen_kg_dev_006", "Are all mammals able to fly?", "CWQ-style", "dev", "No. Counterexample", "whale is_a mammal ; whale not_capable_of fly", "universal"),
        ("gen_kg_dev_007", "What property allows a bat to fly?", "WebQSP-style", "dev", "wings", "bat has_property wings", "property"),
        ("gen_kg_dev_008", "What property does whale have?", "WebQSP-style", "dev", "blowhole", "whale has_property blowhole", "property"),
        ("gen_kg_dev_009", "What eats mosquito?", "WebQSP-style", "dev", "bat eats mosquito", "bat eats mosquito", "inverse_relation"),
        ("gen_kg_dev_010", "Does a mammal produce milk?", "GrailQA-style", "dev", "mammal produces milk", "mammal produces milk", "property"),
        ("gen_kg_test_001", "Is a duck a bird?", "WebQSP-style", "test", "duck is_a bird", "duck is_a bird", "membership"),
        ("gen_kg_test_002", "Is a frog a vertebrate?", "GrailQA-style", "test", "frog is_a amphibian ; amphibian is_a vertebrate", "frog is_a amphibian and amphibian is_a vertebrate", "two_hop"),
        ("gen_kg_test_003", "Is a mosquito an animal?", "GrailQA-style", "test", "mosquito is_a insect ; insect is_a animal", "mosquito is_a insect and insect is_a animal", "two_hop"),
        ("gen_kg_test_004", "Can a bird fly?", "CWQ-style", "test", "eagle capable_of fly", "eagle is_a bird ; eagle capable_of fly", "existential"),
        ("gen_kg_test_005", "Are all birds able to swim?", "CWQ-style", "test", "No. Counterexample", "eagle is_a bird ; eagle not_capable_of swim", "universal"),
        ("gen_kg_test_006", "What property does dolphin have?", "WebQSP-style", "test", "echolocation", "dolphin has_property echolocation", "property"),
        ("gen_kg_test_007", "What eats mouse?", "WebQSP-style", "test", "cat eats mouse", "cat eats mouse", "inverse_relation"),
        ("gen_kg_test_008", "Does a whale produce milk?", "GrailQA-style", "test", "whale produces milk", "whale produces milk", "property"),
        ("gen_kg_test_009", "Can a whale swim?", "CWQ-style", "test", "whale capable_of swim", "whale capable_of swim", "property"),
        ("gen_kg_test_010", "What property allows a sparrow to fly?", "WebQSP-style", "test", "wings", "sparrow has_property wings", "property"),
    ]
    return [
        _item(item_id, query, source, split, "kg", gold, evidence, tag, "Public structured-QA style query grounded in the local demo KG.")
        for item_id, query, source, split, gold, evidence, tag in rows
    ]


def _relational_items() -> list[GeneralizationItem]:
    rows = [
        ("gen_rel_dev_001", "What bridge connects bat and vertebrate?", "HotpotQA-style", "dev", "bat is_a mammal ; mammal is_a vertebrate", "bat connects to vertebrate through mammal", "bridge"),
        ("gen_rel_dev_002", "What bridge connects penguin and vertebrate?", "HotpotQA-style", "dev", "penguin is_a bird ; bird is_a vertebrate", "penguin connects to vertebrate through bird", "bridge"),
        ("gen_rel_dev_003", "What bridge connects whale and vertebrate?", "2WikiMultihopQA-style", "dev", "whale is_a mammal ; mammal is_a vertebrate", "whale connects to vertebrate through mammal", "bridge"),
        ("gen_rel_dev_004", "What bridge connects salmon and vertebrate?", "2WikiMultihopQA-style", "dev", "salmon is_a fish ; fish is_a vertebrate", "salmon connects to vertebrate through fish", "bridge"),
        ("gen_rel_dev_005", "What bridge connects mosquito and animal?", "HotpotQA-style", "dev", "mosquito is_a insect ; insect is_a animal", "mosquito connects to animal through insect", "bridge"),
        ("gen_rel_dev_006", "What relation connects bat and mosquito?", "HotpotQA-style", "dev", "bat eats mosquito", "bat eats mosquito", "relation"),
        ("gen_rel_dev_007", "What relation connects eagle and fish?", "HotpotQA-style", "dev", "eagle eats fish", "eagle eats fish", "relation"),
        ("gen_rel_dev_008", "What relation connects frog and mosquito?", "HotpotQA-style", "dev", "frog eats mosquito", "frog eats mosquito", "relation"),
        ("gen_rel_dev_009", "What relation connects dolphin and echolocation?", "2WikiMultihopQA-style", "dev", "dolphin has_property echolocation", "dolphin has property echolocation", "relation"),
        ("gen_rel_dev_010", "What relation connects mammal and milk?", "2WikiMultihopQA-style", "dev", "mammal produces milk", "mammal produces milk", "relation"),
        ("gen_rel_test_001", "What relation connects duck and swim?", "HotpotQA-style", "test", "duck capable_of swim", "duck is capable of swim", "relation"),
        ("gen_rel_test_002", "What relation connects whale and swim?", "HotpotQA-style", "test", "whale capable_of swim", "whale is capable of swim", "relation"),
        ("gen_rel_test_003", "What relation connects cat and mouse?", "HotpotQA-style", "test", "cat eats mouse", "cat eats mouse", "relation"),
        ("gen_rel_test_004", "What relation connects owl and mouse?", "2WikiMultihopQA-style", "test", "owl eats mouse", "owl eats mouse", "relation"),
        ("gen_rel_test_005", "What relation connects sparrow and wings?", "2WikiMultihopQA-style", "test", "sparrow has_property wings", "sparrow has property wings", "relation"),
        ("gen_rel_test_006", "What bridge connects mammal and animal?", "HotpotQA-style", "test", "mammal is_a vertebrate ; vertebrate is_a animal", "mammal connects to animal through vertebrate", "bridge"),
        ("gen_rel_test_007", "What bridge connects bird and animal?", "HotpotQA-style", "test", "bird is_a vertebrate ; vertebrate is_a animal", "bird connects to animal through vertebrate", "bridge"),
        ("gen_rel_test_008", "What relation connects penguin and swim?", "2WikiMultihopQA-style", "test", "penguin capable_of swim", "penguin is capable of swim", "relation"),
        ("gen_rel_test_009", "What relation connects bat and fly?", "HotpotQA-style", "test", "bat capable_of fly", "bat is capable of fly", "relation"),
        ("gen_rel_test_010", "What relation connects mammal and vertebrate?", "2WikiMultihopQA-style", "test", "mammal is_a vertebrate", "mammal is a vertebrate", "relation"),
    ]
    return [
        _item(item_id, query, source, split, "hybrid", gold, evidence, tag, "Public multi-hop or bridge-QA style query grounded in local text plus KG.")
        for item_id, query, source, split, gold, evidence, tag in rows
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's held-out generalization v2 benchmark.")
    parser.add_argument("--output", default=str(GENERALIZATION_BENCHMARK_PATH))
    args = parser.parse_args()
    payload = build_generalization_benchmark(args.output)
    print(f"generalization_v2_benchmark={payload['total']} output={payload['path']}")
    print(f"split_counts={payload['counts']['split']}")
    print(f"route_family_counts={payload['counts']['route_family']}")
    print(f"source_dataset_counts={payload['counts']['source_dataset']}")


if __name__ == "__main__":
    main()
