# Process Guide: Prompt 7 Answer Synthesis and Reasoning Trace

## Basic Summary

This step added the final user-facing PRISM layer: given a query, PRISM parses routing features, computes RAS scores, chooses a backend, retrieves evidence, synthesizes a deterministic answer, and records a concise reasoning trace. No paid APIs or hosted LLMs are used.

## How Answer Synthesis Works In This Repo

Answer synthesis means turning retrieved evidence into a final response. In this project, synthesis is handled by `prism/answering/generator.py`.

The synthesizer receives:

- The original user query.
- Parsed query features from the RAS feature parser.
- RAS scores for each backend.
- The selected backend.
- Retrieved evidence items.

It returns a structured answer object instead of a plain string. That object keeps the final answer together with evidence ids, snippets, route rationale, support score, and trace steps. This is important because PRISM is not only trying to answer; it is trying to show why a particular retrieval representation was chosen.

## Why The Answerer Is Deterministic

The current answerer uses rules and templates rather than a cloud LLM. This keeps the runtime local, reproducible, and testable.

For this sprint, deterministic behavior is useful because:

- Tests can compare outputs consistently.
- Benchmark scoring does not depend on randomness.
- The demo can show routing and evidence behavior clearly.
- The project avoids paid APIs.

The tradeoff is that answers are simpler and less conversational than a full generative model.

## Backend-Specific Answer Styles

BM25 is used for lexical and exact identifier queries. Its answer style surfaces the matched document title or identifier directly, because the point of BM25 here is exact token evidence such as `RFC-7231`, `J18.9`, or `torch.nn.CrossEntropyLoss`.

Dense retrieval is used for semantic questions. Its answer style gives a short natural-language summary from the most relevant text chunk. Dense retrieval is better when the query is conceptual and the exact query words may not appear in the document.

KG retrieval is used for deductive questions. Its answer style focuses on structured facts, membership, properties, paths, and counterexamples. For example, a question like "Can a mammal fly?" should use facts about bats being mammals and bats being able to fly, not just a semantically similar paragraph.

Hybrid retrieval is used for relational questions. Its answer style explains a connection using fused evidence from multiple backends. The top evidence may include a KG path plus a text snippet, and the answer names that mixed evidence instead of pretending it came from only one source.

## How Reasoning Traces Are Produced

Reasoning traces are produced by `prism/answering/reasoning_trace.py`.

Each trace is a small list of inspectable steps:

- Parse query features.
- Score RAS by backend.
- Select the backend with the best routing fit.
- Retrieve evidence from that backend.
- Synthesize the answer from the selected evidence.

The trace records the selected backend, the route rationale, which evidence ids were used, and why non-selected backends were not preferred. This is not hidden chain-of-thought; it is a user-facing audit trace for the routing and evidence decisions the program actually made.

## How Confidence And Support Are Derived

The current support score is a simple deterministic signal. It uses the number of retrieved evidence items and their available retrieval scores. It should be read as "how much local retrieved support the answer used," not as a calibrated probability that the answer is true.

This distinction matters. A high support score means the local retriever found strong local evidence. It does not mean the system has checked the entire internet or proven the answer in a formal theorem-proving sense.

## End-To-End CLI

The new CLI entry point is:

```bash
.venv/bin/python3 -m prism.app.answer_query --query "Can a mammal fly?"
```

The CLI output shows:

- Query.
- Parsed features.
- RAS scores.
- Selected backend.
- Top evidence.
- Final structured answer.
- Reasoning trace.

This is the easiest way to demonstrate PRISM’s full path from query to backend selection to evidence-backed answer.

## End-To-End Evaluation

The combined evaluator is:

```bash
.venv/bin/python3 -m prism.eval.verify_end_to_end
```

It evaluates 80 total queries:

- 20 lexical queries.
- 20 semantic queries.
- 20 deductive queries.
- 20 relational queries.

It reports route accuracy, evidence hit@k, normalized answer match, per-slice breakdowns, confusion summary, and sample traces.

## Concepts And Terms Used

Answer synthesis means building the final response from retrieved evidence.

Structured answer means the answer is represented as data with fields like final text, evidence ids, backend, route rationale, and support score.

Reasoning trace means a concise audit record of routing, evidence, and synthesis decisions. In this repo it is not an LLM chain-of-thought; it is a transparent program trace.

RAS means Representation Adequacy Score. It is the computed routing score used to choose BM25, Dense, KG, or Hybrid.

Evidence id means a stable identifier for a retrieved document, chunk, triple, path, or fused bundle.

Support score means a simple local evidence-strength signal. It is not a formal confidence probability.

Closed-world demo assumption means the KG verifier treats the curated local KG as the relevant world for the demo. This allows counterexample checks for universal-style questions, but it is not the same as proving something about the real world.

Normalized exact match means the evaluator lowercases and normalizes answer text before checking whether the expected answer is present or sufficiently matched.

## Current Limitations

The answerer is reliable and local, but intentionally simple. It does not yet use Ollama or llama.cpp for fluent local generation.

Semantic answers mostly restate the best chunk. More advanced summarization would need a local model or richer templates.

KG universal reasoning works only over the curated demo graph. It should not be treated as complete world knowledge.

Hybrid answers currently emphasize the top fused evidence bundle. A later step could make multi-evidence explanations more detailed and more natural.
