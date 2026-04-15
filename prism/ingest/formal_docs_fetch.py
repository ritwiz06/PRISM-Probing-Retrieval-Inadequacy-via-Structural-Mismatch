from __future__ import annotations

from prism.schemas import Document


def fetch_documents() -> list[Document]:
    return [
        Document(
            doc_id="doc_policy",
            title="PRISM Policy",
            text="Property and membership questions should route to the KG backend. Multi-hop questions should route to hybrid.",
            source="seed:formal",
        ),
        Document(
            doc_id="doc_exact",
            title="Identifier Guide",
            text="Exact identifiers, codes, and section references are best handled by sparse lexical retrieval.",
            source="seed:formal",
        ),
        Document(
            doc_id="lex_hipaa_164_512",
            title="HIPAA 45 CFR 164.512",
            text="HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.",
            source="lexical:hipaa",
        ),
        Document(
            doc_id="lex_hipaa_164_510",
            title="HIPAA 45 CFR 164.510",
            text="HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object.",
            source="lexical:hipaa",
        ),
        Document(
            doc_id="lex_hipaa_164_514",
            title="HIPAA 45 CFR 164.514",
            text="HIPAA section 164.514 covers other requirements relating to uses and disclosures of protected health information.",
            source="lexical:hipaa",
        ),
        Document(
            doc_id="lex_icd_j18_9",
            title="ICD-10-CM J18.9",
            text="ICD-10-CM code J18.9 identifies pneumonia, unspecified organism.",
            source="lexical:icd10",
        ),
        Document(
            doc_id="lex_icd_j18_0",
            title="ICD-10-CM J18.0",
            text="ICD-10-CM code J18.0 identifies bronchopneumonia, unspecified organism.",
            source="lexical:icd10",
        ),
        Document(
            doc_id="lex_icd_j18_1",
            title="ICD-10-CM J18.1",
            text="ICD-10-CM code J18.1 identifies lobar pneumonia, unspecified organism.",
            source="lexical:icd10",
        ),
        Document(
            doc_id="lex_torch_cross_entropy_loss",
            title="torch.nn.CrossEntropyLoss",
            text="torch.nn.CrossEntropyLoss computes cross entropy loss between input logits and target class indices or probabilities.",
            source="lexical:pytorch",
        ),
        Document(
            doc_id="lex_torch_nll_loss",
            title="torch.nn.NLLLoss",
            text="torch.nn.NLLLoss computes the negative log likelihood loss and is commonly paired with LogSoftmax.",
            source="lexical:pytorch",
        ),
        Document(
            doc_id="lex_torch_bce_loss",
            title="torch.nn.BCELoss",
            text="torch.nn.BCELoss measures binary cross entropy between target and input probabilities.",
            source="lexical:pytorch",
        ),
        Document(
            doc_id="lex_rfc_7231",
            title="RFC-7231 HTTP/1.1 Semantics and Content",
            text="RFC-7231 defines HTTP/1.1 semantics and content, including methods, status codes, and content negotiation.",
            source="lexical:rfc",
        ),
        Document(
            doc_id="lex_rfc_7230",
            title="RFC-7230 HTTP/1.1 Message Syntax and Routing",
            text="RFC-7230 defines HTTP/1.1 message syntax, routing, connection management, and related requirements.",
            source="lexical:rfc",
        ),
        Document(
            doc_id="lex_rfc_7235",
            title="RFC-7235 HTTP/1.1 Authentication",
            text="RFC-7235 defines the HTTP/1.1 authentication framework and related status codes.",
            source="lexical:rfc",
        ),
        Document(
            doc_id="lex_section_1983",
            title="42 U.S.C. §1983",
            text="42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law.",
            source="lexical:law",
        ),
        Document(
            doc_id="lex_section_1981",
            title="42 U.S.C. §1981",
            text="42 U.S.C. §1981 protects equal rights under the law to make and enforce contracts.",
            source="lexical:law",
        ),
        Document(
            doc_id="lex_section_1985",
            title="42 U.S.C. §1985",
            text="42 U.S.C. §1985 concerns conspiracies to interfere with civil rights.",
            source="lexical:law",
        ),
        Document(
            doc_id="lex_postgres_jsonb_set",
            title="PostgreSQL jsonb_set",
            text="PostgreSQL jsonb_set updates or inserts a value at a specified JSONB path.",
            source="lexical:postgres",
        ),
        Document(
            doc_id="lex_postgres_jsonb_insert",
            title="PostgreSQL jsonb_insert",
            text="PostgreSQL jsonb_insert inserts a new value into a JSONB document at a specified path.",
            source="lexical:postgres",
        ),
        Document(
            doc_id="lex_numpy_linalg_norm",
            title="numpy.linalg.norm",
            text="numpy.linalg.norm returns a matrix or vector norm, with behavior controlled by ord and axis.",
            source="lexical:numpy",
        ),
        Document(
            doc_id="lex_numpy_linalg_svd",
            title="numpy.linalg.svd",
            text="numpy.linalg.svd performs singular value decomposition on an array.",
            source="lexical:numpy",
        ),
        Document(
            doc_id="lex_sklearn_tfidf",
            title="sklearn.feature_extraction.text.TfidfVectorizer",
            text="TfidfVectorizer converts a collection of raw documents to a matrix of TF-IDF features.",
            source="lexical:sklearn",
        ),
        Document(
            doc_id="lex_sklearn_count",
            title="sklearn.feature_extraction.text.CountVectorizer",
            text="CountVectorizer converts text documents to a matrix of token counts.",
            source="lexical:sklearn",
        ),
        Document(
            doc_id="lex_html_aria_label",
            title="HTML aria-label",
            text="The aria-label attribute defines an accessible name for an element when no visible label is available.",
            source="lexical:html",
        ),
        Document(
            doc_id="lex_html_aria_labelledby",
            title="HTML aria-labelledby",
            text="The aria-labelledby attribute identifies elements that label the current element.",
            source="lexical:html",
        ),
    ]
