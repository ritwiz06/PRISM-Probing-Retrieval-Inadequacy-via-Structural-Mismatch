# Open-Domain Extension For Paper

PRISM was extended from a bounded benchmark system into a reusable source-pack/open-corpus workspace. Users can build runtime corpora from local files or built-in packs, inspect route scores, compare backends, and export query-local graph evidence.

## Source Packs
Current built-in packs include Wikipedia-style concepts and RFC specifications, with additional registries for medical codes, policy documents, and CS API docs.

## Query-Local Graphs
For each open-corpus query, PRISM can extract lightweight triples from top/local documents. These triples are provenance-linked and used by KG/Hybrid retrieval in open-corpus mode.

## Route Improvement
RAS v2 recommendation: `keep_analysis_only`. It is an interpretable hard-case experiment, not a production replacement for computed RAS.

## Limitation
This is source-pack and user-corpus QA, not live web-scale open-domain search. Query-local graph extraction is lightweight and can be noisy.
