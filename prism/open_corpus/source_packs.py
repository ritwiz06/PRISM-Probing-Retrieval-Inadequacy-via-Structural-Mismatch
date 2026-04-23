from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourcePackDocument:
    doc_id: str
    title: str
    text: str
    source_url: str
    route_family_hint: str


@dataclass(frozen=True, slots=True)
class SourcePack:
    name: str
    description: str
    documents: tuple[SourcePackDocument, ...]


SOURCE_PACKS: dict[str, SourcePack] = {
    "wikipedia": SourcePack(
        name="wikipedia",
        description="Small offline Wikipedia-style concept pack for semantic and relational smoke tests.",
        documents=(
            SourcePackDocument(
                "pack_wikipedia_climate_anxiety",
                "Climate Anxiety",
                "Climate anxiety is distress, worry, or unease about climate change and ecological loss. It can feel like dread about a warming future.",
                "https://en.wikipedia.org/wiki/Eco-anxiety",
                "dense",
            ),
            SourcePackDocument(
                "pack_wikipedia_bat",
                "Bat",
                "A bat is a mammal. Bats are vertebrates and many bats use wings for powered flight and echolocation for navigation.",
                "https://en.wikipedia.org/wiki/Bat",
                "kg",
            ),
            SourcePackDocument(
                "pack_wikipedia_photosynthesis",
                "Photosynthesis",
                "Photosynthesis is the process by which plants and some organisms convert light energy into chemical energy such as sugars.",
                "https://en.wikipedia.org/wiki/Photosynthesis",
                "dense",
            ),
            SourcePackDocument(
                "pack_wikipedia_bridge_bat_vertebrate",
                "Bat And Vertebrate Bridge",
                "The bridge connecting bat and vertebrate is mammal: bat is a mammal, and mammal is a class of vertebrate.",
                "https://en.wikipedia.org/wiki/Vertebrate",
                "hybrid",
            ),
        ),
    ),
    "rfc_specs": SourcePack(
        name="rfc_specs",
        description="Small RFC/specification pack with exact identifier-heavy snippets.",
        documents=(
            SourcePackDocument(
                "pack_rfc_7231",
                "RFC-7231",
                "RFC-7231 defines HTTP/1.1 semantics and content, including request methods, response status codes, and representation metadata.",
                "https://www.rfc-editor.org/rfc/rfc7231",
                "bm25",
            ),
            SourcePackDocument(
                "pack_rfc_7230",
                "RFC-7230",
                "RFC-7230 defines HTTP/1.1 message syntax and routing. It is a near-match distractor for RFC-7231.",
                "https://www.rfc-editor.org/rfc/rfc7230",
                "bm25",
            ),
            SourcePackDocument(
                "pack_rfc_9110",
                "RFC-9110",
                "RFC-9110 updates HTTP semantics and consolidates parts of the HTTP specification family.",
                "https://www.rfc-editor.org/rfc/rfc9110",
                "bm25",
            ),
        ),
    ),
    "medical_codes": SourcePack(
        name="medical_codes",
        description="Small medical/formal-code source pack for exact-match testing.",
        documents=(
            SourcePackDocument("pack_icd_j18_9", "ICD-10 J18.9", "ICD-10 J18.9 refers to pneumonia, unspecified organism.", "https://icd.who.int/", "bm25"),
            SourcePackDocument("pack_icd_j18_1", "ICD-10 J18.1", "ICD-10 J18.1 refers to lobar pneumonia, unspecified organism.", "https://icd.who.int/", "bm25"),
            SourcePackDocument("pack_hipaa_164_512", "HIPAA 164.512", "HIPAA 164.512 describes uses and disclosures for which authorization or an opportunity to agree or object is not required.", "https://www.hhs.gov/hipaa/", "bm25"),
        ),
    ),
    "policy_docs": SourcePack(
        name="policy_docs",
        description="Small policy/legal source pack for exact and deductive examples.",
        documents=(
            SourcePackDocument("pack_section_1983", "Section 1983", "42 U.S.C. §1983 creates a civil action for deprivation of rights under color of state law.", "https://www.law.cornell.edu/uscode/text/42/1983", "bm25"),
            SourcePackDocument("pack_privacy_notice", "Privacy Notice", "A privacy notice explains how an organization collects, uses, shares, and protects personal information.", "https://www.ftc.gov/", "dense"),
        ),
    ),
    "cs_api_docs": SourcePack(
        name="cs_api_docs",
        description="Small computer-science API pack for dotted identifiers.",
        documents=(
            SourcePackDocument("pack_torch_cross_entropy", "torch.nn.CrossEntropyLoss", "torch.nn.CrossEntropyLoss computes cross entropy loss between input logits and target class indices.", "https://pytorch.org/docs/", "bm25"),
            SourcePackDocument("pack_numpy_svd", "numpy.linalg.svd", "numpy.linalg.svd computes singular value decomposition for an array-like matrix.", "https://numpy.org/doc/", "bm25"),
            SourcePackDocument("pack_faiss_index", "FAISS IndexFlatIP", "FAISS IndexFlatIP performs inner-product nearest-neighbor search over dense vectors.", "https://faiss.ai/", "dense"),
        ),
    ),
}


def get_source_pack(name: str) -> SourcePack:
    if name not in SOURCE_PACKS:
        raise ValueError(f"Unknown source pack {name!r}. Available packs: {', '.join(sorted(SOURCE_PACKS))}")
    return SOURCE_PACKS[name]


def list_source_packs() -> list[str]:
    return sorted(SOURCE_PACKS)

