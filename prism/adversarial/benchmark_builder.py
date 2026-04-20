from __future__ import annotations

import argparse
from pathlib import Path

from prism.adversarial.loaders import (
    ADVERSARIAL_BENCHMARK_PATH,
    AdversarialItem,
    adversarial_counts,
    write_adversarial_benchmark,
)
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.public_corpus.build_public_corpus import build_public_corpus
from prism.public_graph.build_public_graph import build_public_graph


def build_adversarial_benchmark(
    output_path: str | Path = ADVERSARIAL_BENCHMARK_PATH,
) -> Path:
    corpus_path = build_corpus()
    build_kg(corpus_path=str(corpus_path))
    public_path = build_public_corpus()
    build_public_graph(public_path)
    return write_adversarial_benchmark(_items(), output_path)


def _item(
    id_: str,
    split: str,
    family: str,
    query: str,
    answer: str,
    source_ids: list[str],
    triple_ids: list[str],
    tags: list[str],
    evidence_text: str,
    notes: str,
    difficulty: str = "hard",
) -> AdversarialItem:
    return AdversarialItem(
        id=id_,
        query=query,
        split=split,
        intended_route_family=family,
        difficulty=difficulty,
        ambiguity_tags=tags,
        gold_answer=answer,
        gold_source_doc_ids=source_ids,
        gold_triple_ids=triple_ids,
        gold_evidence_text=evidence_text,
        notes=notes,
    )


def _items() -> list[AdversarialItem]:
    rows: list[AdversarialItem] = []
    rows.extend(_bm25_items())
    rows.extend(_dense_items())
    rows.extend(_kg_items())
    rows.extend(_hybrid_items())
    return rows


def _bm25_items() -> list[AdversarialItem]:
    return [
        _item(
            "adv_bm25_dev_01",
            "dev",
            "bm25",
            "In plain language, what is RFC-7231 really about, not RFC-7230 routing?",
            "HTTP/1.1 semantics and content",
            ["lex_rfc_7231", "pub_rfc_7231"],
            [],
            ["lexical_semantic_overlap", "identifier_ambiguity", "top1_topk_gap_risk"],
            "RFC-7231 defines HTTP/1.1 semantics and content.",
            "Looks semantic but the exact RFC identifier decides the answer.",
        ),
        _item(
            "adv_bm25_dev_02",
            "dev",
            "bm25",
            "Which HIPAA provision, 164.512 rather than 164.510, covers disclosures when authorization is not required?",
            "authorization or opportunity to agree or object is not required",
            ["lex_hipaa_164_512", "pub_hipaa_164_512"],
            [],
            ["identifier_ambiguity", "identifier_with_distractor_language"],
            "HIPAA section 164.512 covers uses and disclosures for which authorization is not required.",
            "Near-match legal sections differ by one digit.",
        ),
        _item(
            "adv_bm25_dev_03",
            "dev",
            "bm25",
            "For unspecified pneumonia, should the exact ICD-10 code be J18.9 or the nearby J18.1?",
            "J18.9 identifies pneumonia, unspecified organism",
            ["lex_icd_j18_9", "pub_icd_j18_9"],
            [],
            ["identifier_ambiguity", "top1_topk_gap_risk"],
            "ICD-10-CM code J18.9 identifies pneumonia, unspecified organism.",
            "Medical code lookup with nearby distractor code.",
        ),
        _item(
            "adv_bm25_dev_04",
            "dev",
            "bm25",
            "The API that computes cross entropy loss from logits is torch.nn.CrossEntropyLoss, not BCELoss; what does it compute?",
            "cross entropy loss",
            ["lex_torch_cross_entropy_loss", "pub_torch_cross_entropy"],
            [],
            ["identifier_with_distractor_language", "lexical_semantic_overlap"],
            "torch.nn.CrossEntropyLoss computes cross entropy loss between input logits and target class indices or probabilities.",
            "Looks like a conceptual ML loss question but needs exact API disambiguation.",
        ),
        _item(
            "adv_bm25_dev_05",
            "dev",
            "bm25",
            "Civil rights question with contracts nearby: what does 42 U.S.C. §1983 provide?",
            "civil action for deprivation of rights",
            ["lex_section_1983"],
            [],
            ["identifier_ambiguity", "public_document_noise"],
            "42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law.",
            "Legal identifier has nearby §1981 and §1985 distractors.",
        ),
        _item(
            "adv_bm25_dev_06",
            "dev",
            "bm25",
            "Which sklearn class makes raw documents into TF-IDF features even though the query says topic meaning and semantic search?",
            "TfidfVectorizer converts raw documents to TF-IDF features",
            ["lex_sklearn_tfidf", "pub_sklearn_tfidf"],
            [],
            ["lexical_semantic_overlap", "misleading_exact_term"],
            "TfidfVectorizer converts a collection of raw documents to a matrix of TF-IDF features.",
            "Semantic words are distractors; the class name and phrase are lexical evidence.",
        ),
        _item(
            "adv_bm25_test_01",
            "test",
            "bm25",
            "Authentication framework, but do not answer with semantics: RFC-7235 is the exact target.",
            "HTTP/1.1 authentication framework",
            ["lex_rfc_7235", "pub_rfc_7235"],
            [],
            ["identifier_ambiguity", "route_boundary_ambiguity"],
            "RFC-7235 defines the HTTP/1.1 authentication framework.",
            "Identifier-heavy query includes semantic wording.",
            "adversarial",
        ),
        _item(
            "adv_bm25_test_02",
            "test",
            "bm25",
            "HIPAA 164.510 opportunity to agree or object, with 164.512 nearby in the page noise.",
            "uses and disclosures requiring an opportunity to agree or object",
            ["lex_hipaa_164_510", "pub_hipaa_164_510"],
            [],
            ["identifier_ambiguity", "public_document_noise"],
            "HIPAA section 164.510 covers uses and disclosures requiring an opportunity to agree or object.",
            "Near-match public regulation identifiers.",
            "adversarial",
        ),
        _item(
            "adv_bm25_test_03",
            "test",
            "bm25",
            "numpy.linalg.norm describes geometry and magnitude, but the exact function is the answer source.",
            "matrix or vector norm",
            ["lex_numpy_linalg_norm"],
            [],
            ["lexical_semantic_overlap", "identifier_with_distractor_language"],
            "numpy.linalg.norm returns a matrix or vector norm.",
            "Could look semantic because of geometry wording.",
            "adversarial",
        ),
        _item(
            "adv_bm25_test_04",
            "test",
            "bm25",
            "PostgreSQL jsonb_insert, not jsonb_set, inserts what into a JSONB document?",
            "inserts a new value",
            ["lex_postgres_jsonb_insert"],
            [],
            ["identifier_ambiguity", "top1_topk_gap_risk"],
            "PostgreSQL jsonb_insert inserts a new value into a JSONB document.",
            "Near-match API names can swap rank order.",
            "adversarial",
        ),
        _item(
            "adv_bm25_test_05",
            "test",
            "bm25",
            "HTML aria-labelledby looks like accessibility semantics; what does that exact attribute identify?",
            "elements that label the current element",
            ["lex_html_aria_labelledby"],
            [],
            ["identifier_ambiguity", "lexical_semantic_overlap"],
            "The aria-labelledby attribute identifies elements that label the current element.",
            "Nearby aria-label distractor plus semantic wording.",
            "adversarial",
        ),
        _item(
            "adv_bm25_test_06",
            "test",
            "bm25",
            "Python dataclasses generated special methods, but do not route class substring to KG.",
            "automatically adding generated special methods",
            ["pub_python_dataclass"],
            [],
            ["public_document_noise", "route_boundary_ambiguity", "misleading_exact_term"],
            "The dataclasses module provides a decorator and functions for automatically adding generated special methods.",
            "Regression guard for class-substring false positives.",
            "adversarial",
        ),
    ]


def _dense_items() -> list[AdversarialItem]:
    return [
        _item("adv_dense_dev_01", "dev", "dense", "Which concept feels like RFC-7231 for emotions: worry or grief about climate futures?", "climate anxiety", ["sem_climate_anxiety", "pub_climate_anxiety"], [], ["lexical_semantic_overlap", "misleading_exact_term"], "Climate anxiety describes distress and worry about climate change.", "Exact RFC token is a distractor; concept is semantic."),
        _item("adv_dense_dev_02", "dev", "dense", "What process turns daylight into stored chemical energy even if PostgreSQL JSONB also stores values?", "photosynthesis", ["sem_photosynthesis", "pub_photosynthesis"], [], ["misleading_exact_term", "lexical_semantic_overlap"], "Photosynthesis converts sunlight, carbon dioxide, and water into stored chemical energy.", "Storage wording can pull JSONB distractors."),
        _item("adv_dense_dev_03", "dev", "dense", "What concept explains city neighborhoods acting like a heat section 164.512 trap?", "urban heat island", ["sem_urban_heat_island", "pub_urban_heat_island"], [], ["misleading_exact_term", "public_document_noise"], "An urban heat island occurs when built surfaces make a city warmer than surrounding rural areas.", "Legal section token is irrelevant noise."),
        _item("adv_dense_dev_04", "dev", "dense", "What process makes learning stable overnight, not CountVectorizer token counts?", "memory consolidation", ["sem_memory_consolidation", "pub_memory_consolidation"], [], ["lexical_semantic_overlap", "misleading_exact_term"], "Memory consolidation makes experiences and learning more stable over time, especially during sleep.", "Exact code term distracts from semantic concept."),
        _item("adv_dense_dev_05", "dev", "dense", "Which condition is an immune false alarm for harmless pollen, not ICD-10 J18.9 pneumonia?", "allergy", ["sem_allergy", "pub_allergy"], [], ["misleading_exact_term", "route_boundary_ambiguity"], "An allergy is an immune response to usually harmless substances such as pollen.", "Medical code mention is a lexical distractor."),
        _item("adv_dense_dev_06", "dev", "dense", "Which concept captures unfair automated outputs even when civil rights §1983 appears in the wording?", "algorithmic bias", ["sem_algorithmic_bias", "pub_algorithmic_bias"], [], ["lexical_semantic_overlap", "misleading_exact_term"], "Algorithmic bias produces unfair or systematically skewed outputs.", "Legal identifier distracts from semantic ML/social concept."),
        _item("adv_dense_test_01", "test", "dense", "Which learning setup lets an agent improve from rewards, although the word policy appears like a legal section?", "reinforcement learning", ["sem_reinforcement_learning", "pub_reinforcement_learning"], [], ["route_boundary_ambiguity", "public_document_noise"], "Reinforcement learning studies agents that learn actions through rewards and feedback.", "Policy wording can look formal or legal.", "adversarial"),
        _item("adv_dense_test_02", "test", "dense", "What model keeps materials in use rather than waste, despite the exact phrase jsonb_set in the distractor?", "circular economy", ["sem_circular_economy", "pub_circular_economy"], [], ["misleading_exact_term", "lexical_semantic_overlap"], "A circular economy keeps materials in use and reduces waste.", "Exact API term is irrelevant.", "adversarial"),
        _item("adv_dense_test_03", "test", "dense", "Which cycle moves water through evaporation and rain, not RFC routing?", "water cycle", ["sem_water_cycle", "pub_water_cycle"], [], ["misleading_exact_term", "public_document_noise"], "The water cycle describes evaporation, condensation, precipitation, runoff, and storage.", "RFC routing term is distractor.", "adversarial"),
        _item("adv_dense_test_04", "test", "dense", "What view of word meaning uses nearby contexts even though the query says lexical identifier?", "distributional semantics", ["sem_distributional_semantics", "pub_distributional_semantics"], [], ["lexical_semantic_overlap", "route_boundary_ambiguity"], "Distributional semantics represents word meaning through patterns of nearby context.", "Contains lexical marker but asks conceptual semantics.", "adversarial"),
        _item("adv_dense_test_05", "test", "dense", "Which concept describes focus divided by notifications while aria-label appears in the browser chrome?", "attention fragmentation", ["sem_attention_fragmentation"], [], ["public_document_noise", "misleading_exact_term"], "Attention fragmentation describes reduced focus from notifications and interruptions.", "Public UI wording distracts lexical retrievers.", "adversarial"),
        _item("adv_dense_test_06", "test", "dense", "Which idea says tiny starting changes cause large later effects, not numpy.linalg.svd decomposition?", "butterfly effect", ["sem_butterfly_effect"], [], ["misleading_exact_term", "lexical_semantic_overlap"], "The butterfly effect names sensitive dependence on initial conditions.", "API token is a high-salience distractor.", "adversarial"),
    ]


def _kg_items() -> list[AdversarialItem]:
    return [
        _item("adv_kg_dev_01", "dev", "kg", "Under the closed-world demo structure, can a mammal fly despite RFC-7231 also mentioning methods?", "Yes. bat capable_of fly", ["doc_mammal", "pub_bat"], ["kg_bat_capable_fly"], ["route_boundary_ambiguity", "noisy_structure"], "bat capable_of fly", "Existential deductive query with lexical distractor."),
        _item("adv_kg_dev_02", "dev", "kg", "Are all mammals able to fly when bat is the tempting positive example?", "No. Counterexample evidence", ["kg_doc_dolphin", "kg_doc_whale", "pub_dolphin"], ["kg_dolphin_not_fly", "kg_whale_not_fly"], ["noisy_structure", "route_boundary_ambiguity"], "dolphin not_capable_of fly; whale not_capable_of fly", "Universal query needs counterexamples."),
        _item("adv_kg_dev_03", "dev", "kg", "Is a bat a mammal or just a semantic article about flight?", "Yes. bat is_a mammal", ["doc_mammal", "pub_bat"], ["kg_bat_is_mammal"], ["lexical_semantic_overlap", "noisy_structure"], "bat is_a mammal", "Membership should prefer structure over text similarity."),
        _item("adv_kg_dev_04", "dev", "kg", "Can a penguin fly if the public page says bird and wings nearby?", "No. penguin not_capable_of fly", ["kg_doc_penguin", "pub_penguin"], ["kg_penguin_not_fly"], ["wrong_bridge_distractor", "noisy_structure"], "penguin not_capable_of fly", "Wings/bird evidence is a plausible wrong bridge."),
        _item("adv_kg_dev_05", "dev", "kg", "What property allows a bat to fly when echolocation is also a bat property?", "wings", ["doc_mammal", "pub_bat"], ["kg_bat_has_wings"], ["wrong_bridge_distractor", "top1_topk_gap_risk"], "bat has_property wings", "Competing bat property can outrank wings."),
        _item("adv_kg_dev_06", "dev", "kg", "Is salmon a vertebrate if the text only says fish first?", "Yes. salmon is_a fish ; fish is_a vertebrate", ["kg_doc_salmon", "kg_doc_fish", "pub_salmon"], ["kg_salmon_is_fish", "kg_fish_is_vertebrate"], ["noisy_structure", "top1_topk_gap_risk"], "salmon is_a fish and fish is_a vertebrate", "Two-hop inheritance can be missed by single-evidence retrieval."),
        _item("adv_kg_test_01", "test", "kg", "Can a bird swim when duck swims but eagle does not?", "Yes. duck capable_of swim", ["kg_doc_duck", "kg_doc_eagle"], ["kg_duck_capable_swim"], ["noisy_structure", "wrong_bridge_distractor"], "duck capable_of swim", "Existential class query with counterexample-like distractor.", "adversarial"),
        _item("adv_kg_test_02", "test", "kg", "Are all birds able to swim when duck is a positive distractor?", "No. Counterexample evidence", ["kg_doc_eagle", "kg_doc_owl"], ["kg_eagle_not_swim", "kg_owl_not_swim"], ["noisy_structure", "wrong_bridge_distractor"], "eagle not_capable_of swim; owl not_capable_of swim", "Universal query must not stop at duck.", "adversarial"),
        _item("adv_kg_test_03", "test", "kg", "Is mosquito an animal through insect, even though the query sounds like a public health document?", "Yes. mosquito is_a insect ; insect is_a animal", ["kg_doc_mosquito", "kg_doc_insect", "pub_mosquito"], ["kg_mosquito_is_insect", "kg_insect_is_animal"], ["public_document_noise", "noisy_structure"], "mosquito is_a insect and insect is_a animal", "Two-hop class membership with public-text noise.", "adversarial"),
        _item("adv_kg_test_04", "test", "kg", "What property does dolphin have: swim capability or echolocation property?", "echolocation", ["kg_doc_dolphin", "pub_dolphin"], ["kg_dolphin_has_property_echolocation"], ["wrong_bridge_distractor", "top1_topk_gap_risk"], "dolphin has_property echolocation", "Capability relation is a plausible but wrong property answer.", "adversarial"),
        _item("adv_kg_test_05", "test", "kg", "Does a whale produce milk under KG scope, not under semantic ocean text?", "Yes. whale produces milk", ["kg_doc_whale", "pub_whale"], ["kg_whale_produces_milk"], ["lexical_semantic_overlap", "noisy_structure"], "whale produces milk", "Structured property lookup with semantic text distractors.", "adversarial"),
        _item("adv_kg_test_06", "test", "kg", "What eats mouse: owl or cat, if both relations are present?", "cat eats mouse", ["kg_doc_cat", "kg_doc_owl"], ["kg_cat_eats_mouse", "kg_owl_eats_mouse"], ["top1_topk_gap_risk", "noisy_structure"], "cat eats mouse; owl eats mouse", "Inverse relation has multiple valid evidence paths.", "adversarial"),
    ]


def _hybrid_items() -> list[AdversarialItem]:
    return [
        _item("adv_hybrid_dev_01", "dev", "hybrid", "What bridge connects bat and vertebrate when RFC-7231 also says routing?", "mammal", ["rel_bat_vertebrate", "pub_bat", "pub_mammal"], ["kg_bat_is_mammal", "kg_mammal_is_vertebrate"], ["wrong_bridge_distractor", "misleading_exact_term"], "bat connects to vertebrate through mammal", "Relational bridge with exact RFC distractor."),
        _item("adv_hybrid_dev_02", "dev", "hybrid", "What bridge connects penguin and vertebrate if wings are a misleading clue?", "bird", ["rel_penguin_vertebrate", "pub_penguin"], ["kg_penguin_is_bird", "kg_bird_is_vertebrate"], ["wrong_bridge_distractor", "top1_topk_gap_risk"], "penguin connects to vertebrate through bird", "Property clue competes with bridge class."),
        _item("adv_hybrid_dev_03", "dev", "hybrid", "What relation connects bat and mosquito when public text also mentions disease?", "bat eats mosquito", ["rel_bat_mosquito", "kg_doc_bat_food"], ["kg_bat_eats_mosquito"], ["public_document_noise", "route_boundary_ambiguity"], "bat eats mosquito", "Public health wording can distract Dense."),
        _item("adv_hybrid_dev_04", "dev", "hybrid", "What bridge connects salmon and vertebrate, not the semantic concept water cycle?", "fish", ["rel_salmon_vertebrate", "pub_salmon"], ["kg_salmon_is_fish", "kg_fish_is_vertebrate"], ["misleading_exact_term", "wrong_bridge_distractor"], "salmon connects to vertebrate through fish", "Semantic water terms distract from bridge."),
        _item("adv_hybrid_dev_05", "dev", "hybrid", "What relation connects mammal and milk while HIPAA 164.512 appears as irrelevant boilerplate?", "mammal produces milk", ["rel_mammal_milk", "kg_doc_mammal"], ["kg_mammal_produces_milk"], ["public_document_noise", "misleading_exact_term"], "mammal produces milk", "Identifier-like boilerplate distracts retrieval."),
        _item("adv_hybrid_dev_06", "dev", "hybrid", "What bridge connects mosquito and animal when fly capability is a tempting relation?", "insect", ["rel_mosquito_animal", "pub_mosquito"], ["kg_mosquito_is_insect", "kg_insect_is_animal"], ["wrong_bridge_distractor", "top1_topk_gap_risk"], "mosquito connects to animal through insect", "Capability relation can outrank class bridge."),
        _item("adv_hybrid_test_01", "test", "hybrid", "What bridge connects whale and vertebrate when ocean semantics are more salient?", "mammal", ["rel_whale_vertebrate", "pub_whale"], ["kg_whale_is_mammal", "kg_mammal_is_vertebrate"], ["lexical_semantic_overlap", "wrong_bridge_distractor"], "whale connects to vertebrate through mammal", "Semantic whale/ocean text is a distractor.", "adversarial"),
        _item("adv_hybrid_test_02", "test", "hybrid", "What relation connects eagle and fish if bird-to-vertebrate is nearby?", "eagle eats fish", ["rel_eagle_fish", "kg_doc_eagle"], ["kg_eagle_eats_fish"], ["wrong_bridge_distractor", "top1_topk_gap_risk"], "eagle eats fish", "Nearby class bridge competes with dietary relation.", "adversarial"),
        _item("adv_hybrid_test_03", "test", "hybrid", "What bridge connects frog and animal when amphibian and vertebrate both appear?", "vertebrate", ["pub_frog", "pub_frog_vertebrate_amphibian"], ["kg_frog_is_amphibian", "kg_amphibian_is_vertebrate"], ["wrong_bridge_distractor", "noisy_structure"], "frog connects to animal through vertebrate", "Two plausible intermediate classes appear.", "adversarial"),
        _item("adv_hybrid_test_04", "test", "hybrid", "What relation connects owl and mouse while wings and flight are strong distractors?", "owl eats mouse", ["rel_owl_mouse", "kg_doc_owl"], ["kg_owl_eats_mouse"], ["wrong_bridge_distractor", "top1_topk_gap_risk"], "owl eats mouse", "Property/capability evidence competes with relation evidence.", "adversarial"),
        _item("adv_hybrid_test_05", "test", "hybrid", "What bridge connects cat and vertebrate even though mouse relation is nearby?", "mammal", ["pub_cat_mammal_pet", "rel_cat_mouse"], ["kg_cat_is_mammal", "kg_mammal_is_vertebrate"], ["wrong_bridge_distractor", "route_boundary_ambiguity"], "cat connects to vertebrate through mammal", "Diet relation competes with class bridge.", "adversarial"),
        _item("adv_hybrid_test_06", "test", "hybrid", "What relation connects bat and fly, not the exact torch.nn.CrossEntropyLoss API?", "bat capable_of fly", ["rel_bat_fly", "doc_mammal"], ["kg_bat_capable_fly"], ["misleading_exact_term", "route_boundary_ambiguity"], "bat capable_of fly", "API identifier distracts from relational evidence.", "adversarial"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's hard ambiguity/adversarial benchmark.")
    parser.add_argument("--output", default=str(ADVERSARIAL_BENCHMARK_PATH))
    args = parser.parse_args()
    path = build_adversarial_benchmark(args.output)
    from prism.adversarial.loaders import load_adversarial_benchmark

    items = load_adversarial_benchmark(path)
    print(f"adversarial_benchmark path={path} total={len(items)} counts={adversarial_counts(items)}")


if __name__ == "__main__":
    main()
