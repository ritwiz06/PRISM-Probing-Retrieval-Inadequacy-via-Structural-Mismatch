from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LexicalQuery:
    query: str
    gold_route: str
    gold_answer: str
    gold_evidence_doc_id: str


LEXICAL_QUERIES: tuple[LexicalQuery, ...] = (
    LexicalQuery("What does HIPAA 164.512 cover?", "bm25", "Uses and disclosures without authorization or opportunity to agree/object.", "lex_hipaa_164_512"),
    LexicalQuery("Find HIPAA section 164.510.", "bm25", "Uses and disclosures requiring an opportunity to agree or object.", "lex_hipaa_164_510"),
    LexicalQuery("Which HIPAA section is 164.514?", "bm25", "Other requirements relating to PHI uses and disclosures.", "lex_hipaa_164_514"),
    LexicalQuery("What is ICD-10 J18.9?", "bm25", "Pneumonia, unspecified organism.", "lex_icd_j18_9"),
    LexicalQuery("Look up ICD-10-CM code J18.0.", "bm25", "Bronchopneumonia, unspecified organism.", "lex_icd_j18_0"),
    LexicalQuery("Find code J18.1 in ICD-10-CM.", "bm25", "Lobar pneumonia, unspecified organism.", "lex_icd_j18_1"),
    LexicalQuery("What is torch.nn.CrossEntropyLoss?", "bm25", "Cross entropy loss for logits and targets.", "lex_torch_cross_entropy_loss"),
    LexicalQuery("Find torch.nn.NLLLoss.", "bm25", "Negative log likelihood loss.", "lex_torch_nll_loss"),
    LexicalQuery("What does torch.nn.BCELoss measure?", "bm25", "Binary cross entropy between targets and input probabilities.", "lex_torch_bce_loss"),
    LexicalQuery("What does RFC-7231 define?", "bm25", "HTTP/1.1 semantics and content.", "lex_rfc_7231"),
    LexicalQuery("Find RFC 7230.", "bm25", "HTTP/1.1 message syntax and routing.", "lex_rfc_7230"),
    LexicalQuery("What is RFC-7235 about?", "bm25", "HTTP/1.1 authentication framework.", "lex_rfc_7235"),
    LexicalQuery("What is 42 U.S.C. §1983?", "bm25", "Civil action for deprivation of rights under color of state law.", "lex_section_1983"),
    LexicalQuery("Find 42 USC §1981.", "bm25", "Equal rights under the law to make and enforce contracts.", "lex_section_1981"),
    LexicalQuery("What does §1985 concern?", "bm25", "Conspiracies to interfere with civil rights.", "lex_section_1985"),
    LexicalQuery("What is PostgreSQL jsonb_set?", "bm25", "Updates or inserts a value at a JSONB path.", "lex_postgres_jsonb_set"),
    LexicalQuery("Find PostgreSQL jsonb_insert.", "bm25", "Inserts a new value into a JSONB document.", "lex_postgres_jsonb_insert"),
    LexicalQuery("What does numpy.linalg.norm return?", "bm25", "A matrix or vector norm.", "lex_numpy_linalg_norm"),
    LexicalQuery("Find numpy.linalg.svd.", "bm25", "Singular value decomposition.", "lex_numpy_linalg_svd"),
    LexicalQuery("What is sklearn.feature_extraction.text.TfidfVectorizer?", "bm25", "A converter from raw documents to TF-IDF features.", "lex_sklearn_tfidf"),
)


def load_lexical_queries() -> list[LexicalQuery]:
    return list(LEXICAL_QUERIES)


def load_lexical_smoke_queries(limit: int = 5) -> list[str]:
    return [item.query for item in LEXICAL_QUERIES[:limit]]
