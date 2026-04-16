from __future__ import annotations

import argparse
from pathlib import Path

from prism.ingest.build_corpus import build_corpus
from prism.schemas import Document
from prism.utils import read_jsonl_documents, write_jsonl_documents


CLEAN_CORPUS_PATH = Path("data/processed/corpus.jsonl")
NOISY_CORPUS_PATH = Path("data/processed/corpus_noisy.jsonl")


def build_noisy_corpus(
    clean_path: str | Path = CLEAN_CORPUS_PATH,
    output_path: str | Path = NOISY_CORPUS_PATH,
) -> dict[str, object]:
    clean_corpus_path = Path(clean_path)
    if not clean_corpus_path.exists():
        build_corpus(output_path=str(clean_corpus_path))
    clean_documents = read_jsonl_documents(clean_corpus_path)
    noisy_documents = sorted(clean_documents + _noise_documents(), key=lambda document: document.doc_id)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl_documents(output, noisy_documents)
    return {
        "clean_path": str(clean_corpus_path),
        "path": str(output),
        "clean_count": len(clean_documents),
        "noise_count": len(noisy_documents) - len(clean_documents),
        "total": len(noisy_documents),
    }


def load_noisy_corpus(path: str | Path = NOISY_CORPUS_PATH) -> list[Document]:
    corpus_path = Path(path)
    if not corpus_path.exists():
        build_noisy_corpus(output_path=corpus_path)
    return read_jsonl_documents(corpus_path)


def _noise_documents() -> list[Document]:
    documents: list[Document] = []
    documents.extend(_lexical_distractors())
    documents.extend(_semantic_distractors())
    documents.extend(_relational_clutter())
    documents.extend(_mixed_quality_background())
    return documents


def _lexical_distractors() -> list[Document]:
    rows = [
        ("noise_lex_rfc_7231_errata", "RFC-7231 errata discussion", "RFC-7231 appears in an errata note that also references RFC-7230 and RFC-7235, but this note does not define HTTP semantics."),
        ("noise_lex_rfc_7321", "RFC-7321 distractor", "RFC-7321 is a nearby-looking identifier used here as a lexical distractor for RFC-7231."),
        ("noise_lex_hipaa_164_512_notes", "HIPAA 164.512 meeting notes", "HIPAA 164.512 is mentioned next to 164.510 and 164.514 in compliance training notes without the authoritative answer."),
        ("noise_lex_icd_j18_9_billing", "J18.9 billing memo", "J18.9, J18.0, and J18.1 appear in a billing memo with mixed pneumonia examples and no definitive mapping."),
        ("noise_lex_torch_cross_entropy_blog", "Cross entropy blog", "A blog compares torch.nn.CrossEntropyLoss, torch.nn.NLLLoss, and torch.nn.BCELoss but gives informal advice rather than API definitions."),
        ("noise_lex_sklearn_vectorizers", "Sklearn vectorizer comparison", "TfidfVectorizer and CountVectorizer are compared in a tutorial with overlapping vocabulary and code fragments."),
        ("noise_lex_jsonb_functions", "JSONB function comparison", "PostgreSQL jsonb_set and jsonb_insert both manipulate JSONB paths, making this a near-match distractor."),
        ("noise_lex_section_198x", "Civil rights sections overview", "Sections §1981, §1983, and §1985 are listed together in a broad overview with similar civil-rights language."),
        ("noise_lex_numpy_linalg", "Numpy linear algebra quick notes", "numpy.linalg.norm and numpy.linalg.svd are both named in generic notes about array computations."),
        ("noise_lex_html_aria", "ARIA naming overview", "aria-label and aria-labelledby both appear in accessibility guidance about element names."),
    ]
    return [Document(doc_id=doc_id, title=title, text=text, source="noise:lexical") for doc_id, title, text in rows]


def _semantic_distractors() -> list[Document]:
    rows = [
        ("climate grief", "Climate grief is sadness about ecological loss; it overlaps with climate anxiety but emphasizes mourning rather than anxious anticipation."),
        ("test anxiety", "Test anxiety is worry before exams and can sound like climate anxiety in abstract discussions of stress."),
        ("plant respiration", "Plant respiration consumes stored sugars and releases energy, often confused with photosynthesis in short explanations."),
        ("solar panels", "Solar panels convert sunlight into electricity, a semantically similar but non-biological energy conversion process."),
        ("organizational diffusion", "Organizational diffusion describes spread of practices in firms and can distract from diffusion of innovations."),
        ("heat stress", "Heat stress describes physiological strain from high temperatures, related to but not identical with urban heat island."),
        ("sleep hygiene", "Sleep hygiene improves rest and memory but is not the same concept as memory consolidation."),
        ("autoimmune disease", "Autoimmune disease involves immune response but is not simply an allergy to harmless substances."),
        ("fungal pathogens", "Fungal pathogens can harm plants, unlike mycorrhizal networks that often exchange nutrients."),
        ("data drift", "Data drift changes model inputs over time and can be confused with algorithmic bias."),
        ("jet lag", "Jet lag disrupts daily timing but is not the underlying circadian rhythm itself."),
        ("cap and trade", "Cap and trade is one policy instrument related to carbon pricing but not the general concept."),
        ("memoir", "A memoir is a written life story, related to but narrower than narrative identity."),
        ("open data portal", "An open data portal can be part of digital commons but lacks the broader governance concept."),
        ("weather forecast", "Weather forecasts mention rain and evaporation but do not define the water cycle."),
        ("supervised learning", "Supervised learning uses labeled examples rather than rewards and penalties."),
        ("word embeddings", "Word embeddings are one implementation related to distributional semantics."),
        ("multitasking", "Multitasking divides attention but is broader than notification-driven attention fragmentation."),
        ("habitat", "A habitat is where an organism lives, while ecological niche includes role and interactions."),
        ("standpoint theory", "Standpoint theory overlaps with situated knowledge but is a more specific theoretical frame."),
    ]
    return [
        Document(
            doc_id=f"noise_sem_{index:03d}",
            title=f"Semantic distractor {index:03d}: {title.title()}",
            text=text,
            source="noise:semantic",
        )
        for index, (title, text) in enumerate(rows)
    ]


def _relational_clutter() -> list[Document]:
    rows = [
        ("noise_rel_bat_vertebrate_long", "Bat vertebrate mixed passage", "Bats, birds, and insects are discussed together. The passage mentions vertebrate animals, mammals, wings, flight, and mosquitoes in a cluttered order."),
        ("noise_rel_penguin_bridge", "Penguin bridge distractor", "Penguins are birds and birds are vertebrates, but this noisy passage also discusses swimming, wings, and flightlessness."),
        ("noise_rel_whale_swim", "Whale swimming notes", "Whales swim, produce milk, and are mammals; the passage repeats vertebrate and animal terms without a clean bridge statement."),
        ("noise_rel_food_web", "Food web clutter", "Owls, cats, frogs, bats, mice, mosquitoes, and fish appear in a noisy food-web summary with multiple eating relations."),
        ("noise_rel_echolocation", "Echolocation clutter", "Dolphins and bats both use echolocation, but the passage mixes property, sensory ability, and mammal facts."),
        ("noise_rel_milk", "Milk relation clutter", "Mammals produce milk, cows produce milk, whales produce milk, and bats produce milk are all stated in a dense list."),
        ("noise_rel_animal_bridge", "Animal class bridge clutter", "Birds, mammals, fish, amphibians, insects, vertebrates, and animals appear in a mixed taxonomy paragraph."),
        ("noise_rel_wings", "Wings relation clutter", "Sparrows, ducks, chickens, ostriches, and bats have wings, but not all fly."),
        ("noise_rel_swim", "Swimming capability clutter", "Ducks, penguins, frogs, salmon, sharks, whales, and dolphins are all named near the swim capability."),
        ("noise_rel_flight", "Flight capability clutter", "Bats, eagles, owls, sparrows, and ducks appear near fly, flight, wings, and movement language."),
    ]
    return [Document(doc_id=doc_id, title=title, text=text, source="noise:relational") for doc_id, title, text in rows]


def _mixed_quality_background() -> list[Document]:
    topics = [
        "public health surveillance", "renewable storage", "food webs", "language acquisition", "coral reefs",
        "glacier retreat", "peer review", "supply chains", "open source software", "data visualization",
        "ocean currents", "desertification", "human-computer interaction", "cognitive load", "solar eclipses",
        "antibiotic resistance", "river deltas", "volcanic islands", "biodiversity corridors", "plate tectonics",
    ]
    return [
        Document(
            doc_id=f"noise_background_{index:03d}",
            title=f"Noisy background {index:03d}: {topic.title()}",
            text=(
                f"This longer mixed-quality note mentions {topic}, definitions, mechanisms, examples, practical effects, "
                "retrieval keywords, unrelated identifiers, and generic facts. It is intentionally useful as clutter rather "
                "than as gold evidence for the held-out benchmark."
            ),
            source="noise:background",
        )
        for index, topic in enumerate(topics)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's noisy stress-test corpus.")
    parser.add_argument("--clean", default=str(CLEAN_CORPUS_PATH))
    parser.add_argument("--output", default=str(NOISY_CORPUS_PATH))
    args = parser.parse_args()
    payload = build_noisy_corpus(args.clean, args.output)
    print(
        f"noisy_corpus={payload['total']} clean={payload['clean_count']} "
        f"noise={payload['noise_count']} output={payload['path']}"
    )


if __name__ == "__main__":
    main()
