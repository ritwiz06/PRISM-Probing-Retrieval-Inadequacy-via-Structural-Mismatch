# PRISM Process Guide For Beginners

This file explains:

- what has been used so far
- what was being thought during implementation
- why those choices were made
- the basic concepts and terms used in this project
- how the current code flows from one step to the next
- how to reason about design choices while you build the next parts

The goal is to help you understand the system while building it, not just copy code.

## 1. What kind of project this is

PRISM is a retrieval-routing project.

That means:

1. a user asks a question
2. the system decides what kind of retrieval is best
3. the system collects evidence
4. the system answers using that evidence

This is different from a plain chatbot that tries to answer from its own memory only.

Another way to say it:

- a normal chatbot mainly does language prediction
- a RAG system adds a search step before answering
- PRISM adds one more layer: it decides which kind of search is most appropriate

So PRISM is not only a question-answering system. It is also a retrieval decision system.

That is the key idea of the project.

## 2. Basic LLM and RAG concepts

### LLM

LLM means Large Language Model.

Examples:

- GPT-style models
- Llama-style models
- Mistral-style models

An LLM predicts text. It is good at language, but it does not automatically know which source is most reliable for a specific question.

This is a very important beginner point:

- an LLM can sound confident even when it is wrong
- an LLM may blend together partial memories
- an LLM usually does not naturally expose the path it used to reach an answer

That is why retrieval matters. Retrieval gives the model evidence outside its internal parameters.

### RAG

RAG means Retrieval-Augmented Generation.

Simple meaning:

- retrieve evidence first
- generate the answer second

Why use RAG:

- it reduces hallucination
- it allows citing evidence
- it lets you use local/private documents

But RAG has its own failure mode:

- if the wrong evidence is retrieved, the answer can still be wrong

So in practice, a RAG pipeline has at least two major risk points:

1. retrieval failure
2. answer generation failure

PRISM focuses heavily on the first one, especially the mistake of using the wrong retrieval structure.

### Retriever

A retriever is the part that searches for relevant evidence.

In this project there will be several retrievers:

- BM25 for lexical search
- Dense retrieval for semantic similarity
- KG retrieval for graph-style facts and relations
- Hybrid retrieval for combining signals

A retriever usually does three things:

1. convert the query into a form it can search with
2. compare the query against stored data
3. return the best matching results with scores

Those scores are not universal truth. They are backend-specific relevance signals.

### Backend

Backend here means a retrieval strategy, not a web server.

Examples:

- BM25 backend
- Dense backend
- KG backend
- Hybrid backend

### Evidence

Evidence is the information retrieved to support an answer.

Examples:

- a document chunk
- a section of formal text
- a knowledge graph triple

### Provenance

Provenance means where the evidence came from.

Examples:

- document id
- source file
- triple id

This matters because PRISM should show why it answered the way it did.

If provenance is missing, then even a correct answer is weaker because you cannot inspect or verify it.

## 3. Concepts specific to PRISM

### Structural mismatch

Structural mismatch means the form of the question does not match the form of the retrieval system being used.

Examples:

- asking for an exact code or section number using a semantic retriever
- asking a relation-chain question using a simple lexical retriever

Why it matters:

- a good answer may fail if the wrong retrieval structure is chosen

This idea is central enough to restate with examples.

Example 1:

Query:

- "What exact section mentions 164.512?"

Best fit:

- lexical retrieval such as BM25

Why:

- the exact number matters
- small token differences matter a lot

Failure mode if routed to dense retrieval:

- dense retrieval may find semantically related privacy text but miss the exact section

Example 2:

Query:

- "What feels like climate anxiety?"

Best fit:

- dense retrieval

Why:

- this is concept-based language
- the wording may vary across documents

Failure mode if routed to BM25:

- exact token overlap may be weak even when the meaning is close

Example 3:

Query:

- "Is a bat a mammal, and can it fly?"

Best fit:

- KG retrieval

Why:

- this is naturally represented as linked facts or triples

Example 4:

Query:

- "What chain of relations connects entity A to entity B?"

Best fit:

- hybrid or graph-heavy retrieval

Why:

- one isolated sentence match may not be enough
- you may need multiple linked pieces of evidence

### RAS

RAS here is the routing score used to decide which backend is the best fit.

In the current scaffold, the score is computed from rules based on query features.

Lower score means better backend choice.

You can think of RAS as a penalty system.

Simple intuition:

- if the query looks lexical, BM25 gets penalized less
- if the query looks semantic, dense retrieval gets penalized less
- if the query looks deductive or property-based, KG gets penalized less
- if the query looks multi-hop or relational, hybrid gets penalized less

This is not the same as a retrieval score.

Important distinction:

- retrieval score = "how relevant is this document/triple to the query within one backend?"
- RAS score = "which backend should I trust most before retrieval?"

### Query features

These are signals extracted from the user query.

Examples:

- lexical
- semantic
- deductive
- relational

These features help decide whether BM25, dense, KG, or hybrid retrieval should be chosen.

Another useful way to think about query features:

- they are not the answer
- they are not evidence
- they are hints about the structure of the question

That means feature parsing is a classification problem over question form.

### Soundness

Soundness means the answer process follows the rules needed for trust.

In this project that includes:

- selected backend should be the lowest-RAS backend
- answer should include evidence ids
- universal claims need stronger support

Why universal claims are dangerous:

If the answer says:

- "all mammals can fly"

that is a much stronger claim than:

- "some mammals can fly"

A universal claim can be disproven by one counterexample. So the evidence standard must be higher.

## 4. Why the project was built in this order

The first implementation step was not “build the smartest retriever.”

Instead, the first step was:

- make the repository installable
- make the folder structure real
- make each module importable
- make basic tests pass
- make smoke CLIs work

Why this order is correct:

- it reduces early chaos
- it gives you stable interfaces
- it prevents later features from being built on broken scaffolding

This is a common engineering pattern:

1. create the skeleton
2. wire data flow
3. verify the plumbing
4. then deepen each component

This matters more in LLM systems than many beginners expect.

Why:

- LLM/RAG systems have many moving parts
- failures can hide inside interfaces between modules
- if everything is built at once, debugging becomes vague and expensive

A common beginner mistake is to try to build the "smart" part first. In practice, the disciplined path is better:

1. make the interfaces real
2. make the artifacts real
3. make the tests real
4. then improve the intelligence behind those interfaces

## 5. What was used so far

### Python 3.11

Why:

- required by the plan
- modern typing and dataclass support
- stable for CLI and test workflows

### `pyproject.toml`

Why:

- modern Python packaging standard
- supports editable install
- central place for project metadata

It also matters for developer workflow.

When you run:

```bash
pip install -e .
```

the `-e` means editable install.

That means:

- Python installs the package in development mode
- code changes in the working directory are reflected without reinstalling every time

That is exactly what you want during active development.

### Dataclasses

Used in:

- `prism/config.py`
- `prism/schemas.py`

Why:

- good for structured data
- easier to read than loose dictionaries everywhere
- makes code safer and more explicit

Without dataclasses, you often end up passing around loose dictionaries like:

```python
{"doc_id": "123", "title": "Doc", "text": "..."}
```

That works at first, but it becomes harder to reason about:

- what keys are required?
- what types are expected?
- which modules rely on which fields?

Dataclasses make that contract explicit.

### `slots=True`

Used on the dataclasses.

Why:

- slightly lighter objects
- more disciplined structure

Important lesson:

- slotted dataclasses do not behave exactly like regular objects with `__dict__`
- that is why `asdict(...)` had to be used when writing JSONL

This is a good example of a real engineering lesson:

- small performance or structure improvements sometimes change object behavior
- when that happens, serialization code must be written more carefully

### JSON and JSONL

Why:

- easy to inspect by hand
- easy to read and write in Python
- useful for corpus and triple storage

Difference:

- JSON usually stores one whole structure
- JSONL stores one JSON object per line

Why JSONL is useful for retrieval systems:

- it is easy to append
- it is easy to stream line by line
- each document or triple can be treated as one record

That makes it practical for corpora, logs, and intermediate datasets.

### YAML-style config

Why:

- cleaner than hardcoding constants inside the code
- easier to change environment-specific paths

### Environment variables

Used:

- `PRISM_CONFIG`
- `PRISM_LOG_LEVEL`
- `PRISM_DATA_DIR`

Why:

- lets tests and local runs change behavior without editing code

This is especially useful in tests because tests should not write into your real project data directory.

Instead, they can point to a temporary location and cleanly throw it away afterward.

### Logging

Why:

- pipeline code should say what it is doing
- logs are better than many scattered prints

What good logs help with:

- knowing which file was written
- knowing how many records were processed
- seeing which backend was used
- spotting where a failure happened in a multi-step pipeline

### Pytest

Why:

- standard Python testing tool
- very good for small modular tests
- essential for keeping the sprint stable

You should think of tests as project memory.

They record what the system is supposed to keep doing.

That becomes critical in a sprint because every new feature risks breaking an older one.

## 6. What was being thought during implementation

This section explains the reasoning behind the earlier choices.

### Thought 1: do not start with full retrieval complexity

Reason:

- the plan is a 10-day solo sprint
- too much complexity early creates fragile code

So the first version focused on:

- interfaces
- file structure
- tests
- smoke commands

### Thought 2: keep modules small

Reason:

- you asked for small modular Python files
- smaller files are easier to debug and easier to understand when learning

### Thought 3: make the pipeline testable before it is “smart”

Reason:

- a simple but runnable pipeline is more useful than a clever design that has not been executed end to end

### Thought 4: computed routing must exist early

Reason:

- the AGENTS instructions say computed RAS is the default router
- if that is delayed too long, the project drifts away from its main objective

### Thought 5: use local seed data first

Reason:

- real ingestion can be added later
- seed data makes it possible to test routing, answer flow, and evaluation right now

### Thought 6: fix failures immediately

Reason:

- smoke tests are only useful if kept green
- broken tests slow all later work

That is why the config parser and JSONL writer were fixed as soon as they failed.

Two more implementation thoughts are worth making explicit.

### Thought 7: prefer deterministic behavior early

Reason:

- deterministic systems are easier to debug than probabilistic ones
- computed routing gives stable outputs during early development

This is one reason the project does not start by depending on an LLM-only router.

### Thought 8: keep artifacts inspectable on disk

Reason:

- if a corpus file, KG file, or evaluation result exists on disk, you can inspect it directly
- that reduces confusion compared with purely in-memory pipelines

For a beginner, inspectable artifacts are extremely valuable because they turn hidden state into visible state.

## 7. Explanation of the current module layout

### `prism/config.py`

Purpose:

- load config
- define config structure
- apply env overrides

How to think about it:

- this module answers "where should things go and what settings should they use?"

Why it exists as a separate file:

- every module should not reinvent path logic or environment lookup
- configuration logic becomes easier to test in one place

### `prism/logging_utils.py`

Purpose:

- initialize logging in a consistent way

Why consistency matters:

- if every module logs differently, debugging becomes noisy and fragmented
- a shared logging format makes the pipeline easier to read

### `prism/schemas.py`

Purpose:

- define the shared data models passed across modules

You can think of `schemas.py` as the shared language of the codebase.

If ingestion creates `Document` objects and retrieval expects `Document` objects, that shared contract reduces confusion.

### `prism/utils.py`

Purpose:

- common file and serialization helpers

Why this is useful:

- it avoids copy-pasting file-writing code into many modules
- it keeps low-level helper logic out of the main business logic

### `prism/ingest/`

Purpose:

- build local data artifacts such as the corpus and KG

In other words:

- ingestion takes source material and turns it into machine-usable local artifacts

This is the "prepare the searchable world" stage.

### `prism/retrievers/`

Purpose:

- implement different retrieval methods

This is the "search the prepared world" stage.

### `prism/ras/`

Purpose:

- parse query features
- compute routing scores
- choose the backend

This is the "decide how to search" stage.

### `prism/answer/`

Purpose:

- turn retrieved evidence into an answer and a trace

This is the "answer from evidence" stage.

### `prism/eval/`

Purpose:

- run benchmarks
- compute metrics
- store evaluation output

This is the "measure whether the system is any good" stage.

### `prism/ui/`

Purpose:

- present the system in a demo interface

This is the "make the internal pipeline visible to a user" stage.

## 8. End-to-end walkthrough of the current pipeline

This section explains what happens when the current scaffold runs.

Take this command:

```bash
python3 -m prism.eval.run_eval --smoke
```

The rough flow is:

1. `run_eval.py` loads config
2. logging is configured
3. required directories are created if missing
4. the script checks whether corpus and KG artifacts already exist
5. if they do not exist, the build scripts create them
6. documents and triples are loaded from disk
7. retriever objects are created
8. smoke queries are loaded
9. for each query, the RAS router selects a backend
10. the chosen retriever returns evidence
11. a basic answer is generated from that evidence
12. a trace is built
13. simple soundness checks are applied
14. results are saved as JSON

This is important because it shows the project is already a pipeline, even if several parts are still placeholders.

If you understand this flow, you understand the project at a systems level.

## 9. How each current script contributes to that pipeline

### `prism.ingest.build_corpus`

Current role:

- creates a small local corpus from seed documents

Why it exists now:

- evaluation and retrieval cannot run without documents

Future role:

- pull from larger real data sources and build a larger corpus

### `prism.ingest.build_kg`

Current role:

- writes a small set of triples and a Turtle-style file

Why it exists now:

- KG retrieval and route testing need graph-like evidence

Future role:

- build a richer knowledge graph with provenance and better schema support

### `prism.eval.run_eval`

Current role:

- exercise the whole pipeline over a tiny query set

Why it matters:

- it is one of the fastest ways to find system-wide integration problems

## 10. Retrieval methods in much more detail - Bookmark

### BM25 retrieval

BM25 is a classic lexical information retrieval method.

You can think of it as an improved keyword matching approach.

It does not try to understand meaning the way dense retrieval does.
It cares strongly about:

- which words appear
- how often they appear
- how rare they are across the corpus

Why BM25 is strong:

- excellent for exact terms
- excellent for identifiers
- excellent for section numbers, codes, names, and rare tokens

Why BM25 can fail:

- weak on paraphrases
- weak when relevant text uses different wording

Example:

Query:

- "exact identifier"

If a document literally contains those words, BM25 is usually strong.

### Dense retrieval

Dense retrieval usually works by converting text into vectors called embeddings.

Embeddings are numeric representations of meaning.

Two texts with similar meaning can end up close together in vector space even if they use different words.

Why dense retrieval is strong:

- semantic similarity
- paraphrases
- concept-level matching

Why dense retrieval can fail:

- exact identifiers may get blurred
- subtle wording differences may be lost
- rare codes or section references may not dominate enough

### KG retrieval

KG retrieval works over structured facts rather than plain free text.

A fact is often represented as a triple:

- subject
- predicate
- object

Example:

- `bat is_a mammal`

Why KG retrieval is strong:

- explicit relations
- property lookup
- membership and class logic
- multi-step graph traversal

Why KG retrieval can fail:

- if the graph does not contain the needed fact
- if the graph schema is too limited
- if the question depends more on descriptive text than discrete relations

### Hybrid retrieval

Hybrid retrieval combines multiple retrieval strategies.

Typical reason to use it:

- one backend finds good text
- another backend finds good structured relations
- combining them gives better overall coverage

Hybrid systems can be strong, but they are also more complex:

- score fusion is tricky
- debugging is harder
- provenance handling is more involved

## 11. Why BM25 is your next important milestone

Your selected task mentions implementing BM25 with `rank-bm25`.

That is a good next step because BM25 gives you:

- a real backend instead of a placeholder
- a strong baseline for lexical queries
- a concrete way to demonstrate retrieval mismatch

Why it matters for PRISM specifically:

- if lexical queries are not handled well, the router cannot prove that structure-aware routing helps

In other words, PRISM needs strong specialized backends. Otherwise routing improvements are hard to demonstrate.

## 12. Why save/load matters for retrievers

A beginner question is often:

- "Why not just rebuild everything every time?"

Because real retrieval systems can become expensive to rebuild.

Save/load matters because:

- startup becomes faster
- smoke tests can reuse artifacts
- evaluation becomes reproducible
- the indexing step becomes separate from the query step

That separation is important engineering discipline.

You want to distinguish:

1. ingestion/build time
2. retrieval/query time

Those are different stages with different performance costs.

## 13. Why exact-match precision matters

Your BM25 task emphasizes high precision for lexical exact-match queries.

Precision means:

- when the system returns something, how often is it actually correct or relevant?

High precision for exact-match queries matters because users often ask things like:

- section numbers
- API names
- parameter names
- codes
- identifiers

If the system answers these loosely, trust drops quickly.

For such queries, returning a vaguely related paragraph is often worse than returning nothing.

That is why lexical retrieval needs to be treated as a specialized capability, not just a weaker form of semantic search.

## 14. The difference between “working code” and “research-valid code”

This is useful to understand early.

Working code means:

- it runs
- it produces outputs
- tests pass

Research-valid code means:

- results are reproducible
- comparisons are fair
- metrics are meaningful
- claims are supported by evidence

PRISM needs both, but the usual sequence is:

1. make it work
2. make it correct
3. make it measurable
4. make it persuasive

The current scaffold is mainly in stage 1 with some early stage 2 discipline.

## 15. How to think when you add a new module

When adding a new feature, ask:

1. what problem does this solve in the pipeline?
2. what inputs does it need?
3. what outputs should it produce?
4. which existing schema should represent those outputs?
5. what file artifact, if any, should it write?
6. how will I test it in isolation?
7. how will I test it inside the full pipeline?

That thought process is more important than memorizing individual code snippets.

## 16. How to read and learn from tests

Beginners often read the main code but skip the tests. That is a mistake.

Tests are useful because they tell you:

- what behavior matters
- what edge cases were considered
- what assumptions the code is allowed to make

For example:

- a BM25 test can tell you that exact-match ranking is the intended behavior
- a pipeline test can tell you which artifacts are expected after a smoke run

If you are learning the system, tests are one of the fastest ways to understand intent.

## 17. Common beginner confusions in this project

### "Is the router the same thing as the retriever?"

No.

- router chooses which backend to use
- retriever performs search inside that backend

### "Is RAS the same as BM25 score?"

No.

- RAS chooses a backend
- BM25 score ranks documents inside one backend

### "Is an LLM required for every part of PRISM?"

No.

In fact, a major project constraint is to avoid depending on paid APIs and to keep the default router computed rather than LLM-only.

### "If tests pass, is the project finished?"

No.

Passing tests means the checked behaviors are working.
It does not mean the full research goals have been achieved.

## 18. Suggested reading order inside the codebase

If you want more detail than the first guide provided, use this order and ask “what goes in and what comes out?” for each file:

1. `prism/schemas.py`
2. `prism/config.py`
3. `prism/utils.py`
4. `prism/ingest/build_corpus.py`
5. `prism/ingest/build_kg.py`
6. `prism/ras/feature_parser.py`
7. `prism/ras/penalty_table.py`
8. `prism/ras/compute_ras.py`
9. `prism/eval/run_eval.py`
10. `tests/test_pipeline.py`

That reading path goes from basic data definitions to full-system execution.

## 19. Important beginner terms from the current code

### CLI

CLI means Command Line Interface.

Examples in this project:

- `python3 -m prism.ingest.build_corpus`
- `python3 -m prism.ingest.build_kg`
- `python3 -m prism.eval.run_eval --smoke`

These commands let you run parts of the system without needing a web UI.

### Smoke test

A smoke test is a quick, shallow test that checks whether the basic path works.

It does not prove the whole system is correct.

It answers a smaller question:

- does the thing run at all?

### Top-k retrieval

This means returning the best `k` results for a query.

Example:

- top 3 results
- top 5 results

### Exact-match lexical query

This is a query where specific words, codes, identifiers, or section names matter a lot.

Example:

- “What does section 164.512 say?”

These queries often need BM25 or another lexical retriever instead of semantic similarity.

### Dense retrieval (reference)

Dense retrieval compares vector embeddings.

It is good when two texts mean similar things even if they do not use the exact same words.

### KG retrieval (reference)

KG means Knowledge Graph.

A knowledge graph stores facts as nodes and relations.

Example:

- `bat is_a mammal`
- `bat capable_of fly`

This is useful for property, class, and relation questions.

### Hybrid retrieval (reference)

Hybrid retrieval combines more than one retrieval method.

This is useful when one method alone is not enough.

## 20. What is still not done

The scaffold exists, but important pieces are still placeholders.

Examples:

- real BM25 with `rank-bm25`
- real dense index
- real KG querying logic
- real hybrid fusion strategy
- full UI
- larger evaluation dataset

This is normal. The current state is the foundation layer.

## 21. How to read the project as a beginner

Recommended order:

1. read `README.md`
2. read `configs/default.yaml`
3. read `prism/schemas.py`
4. read `prism/config.py`
5. read `prism/ingest/build_corpus.py`
6. read `prism/ingest/build_kg.py`
7. read `prism/ras/feature_parser.py`
8. read `prism/ras/compute_ras.py`
9. read `prism/eval/run_eval.py`
10. read the tests in `tests/`

Why this order:

- first understand the data and config
- then understand how data is built
- then understand how routing works
- then understand how the system is tested

## 22. Practical advice while implementing the rest

When adding a new feature, ask these questions:

1. what input shape does it expect?
2. what output shape should it return?
3. which existing schema should it use?
4. how will it be configured?
5. how will it be tested?
6. how will I know it worked from logs or artifacts?

If you follow those questions, the project will stay much more manageable.

## 23. Suggested next learning step

The next most useful concept for you to understand is BM25 versus dense retrieval.

Why:

- it is central to PRISM
- it directly affects routing quality
- your next implementation task is BM25

If you want, the next step I can take is to add a third file that explains:

- BM25 in plain English
- dense retrieval in plain English
- when each one fails
- how that connects to structural mismatch in PRISM

## 24. BM25 Implementation Details Added On 2026-04-10

This section explains the BM25 work that was added after the initial scaffold.

### What changed in plain English

Before this task, the BM25 retriever was only a placeholder.

It ranked documents using a simple token-overlap score.

Now it uses `BM25Okapi` from the `rank-bm25` package.

That means BM25 is now a real lexical retriever instead of a temporary stand-in.

### Why `rank-bm25` was added

BM25 is a standard lexical retrieval algorithm.

It is strong when exact words and identifiers matter.

Examples:

- `164.512`
- `J18.9`
- `torch.nn.CrossEntropyLoss`
- `§1983`
- `RFC-7231`

Those examples are not just normal English words.

They are identifiers.

If punctuation or numbers are lost, retrieval quality can drop.

### What tokenization means here

Tokenization means splitting text into searchable units.

For normal English, tokenization might split this:

```text
HIPAA section 164.512 covers disclosures.
```

into something like:

```text
hipaa
section
164.512
covers
disclosures
```

The important part is that `164.512` stays together.

If a tokenizer split it into `164` and `512`, exact-match retrieval would become weaker.

### What normalization means here

Normalization means making query text and document text consistent.

The current normalization lowercases text.

Example:

```text
torch.nn.CrossEntropyLoss
```

becomes:

```text
torch.nn.crossentropyloss
```

This is useful because a user might type different capitalization.

The goal is to make capitalization not matter while preserving the identifier structure.

### Why punctuation preservation matters

Some punctuation is noise.

But in formal identifiers, punctuation can be meaningful.

Examples:

- `J18.9` is not the same as `J189`
- `RFC-7231` is more specific than just `RFC`
- `torch.nn.CrossEntropyLoss` identifies a specific API path
- `§1983` identifies a legal section

That is why the BM25 tokenizer preserves punctuation inside tokens when reasonable:

- `.`
- `_`
- `-`
- `:`
- `/`
- `§`

### What exact identifier boosting means

BM25 gives each document a score.

For exact identifiers, the implementation adds a small practical boost when an identifier token from the query appears in the document.

Why:

- exact identifiers should strongly outrank near matches
- `164.512` should beat `164.510`
- `J18.9` should beat `J18.0`
- `torch.nn.CrossEntropyLoss` should beat `torch.nn.NLLLoss`

This does not replace BM25.

It is a precision-oriented adjustment on top of BM25Okapi.

### What near-match distractors are

Near-match distractors are intentionally similar documents.

They are used to test whether retrieval is precise.

Example group:

- HIPAA `164.510`
- HIPAA `164.512`
- HIPAA `164.514`

If the query asks for `164.512`, the retriever should not return `164.510` first just because the surrounding words are similar.

This is how we test exact-match precision.

### What save/load means for BM25

The BM25 retriever now supports saving and loading artifacts.

Save means:

- write the documents and tokenized corpus to disk

Load means:

- read those artifacts back
- rebuild the BM25Okapi index

Why this matters:

- real retrieval indexes may take time to build
- evaluation should be reproducible
- loading an existing artifact is cleaner than rebuilding every time

### What the lexical benchmark slice is

A lexical benchmark slice is a small set of queries designed to test exact-match retrieval.

The new slice has 20 queries.

Each query stores:

- gold route
- gold answer
- gold evidence doc id

Gold route is `bm25` for all 20 because this slice is specifically for lexical exact-match retrieval.

### What the lexical verification script does

The script:

```bash
python3 -m prism.eval.verify_lexical
```

does this:

1. loads or builds the corpus
2. builds the BM25 retriever
3. runs 20 lexical queries
4. checks whether the correct evidence doc is ranked first
5. writes `data/eval/lexical_verification.json`

The current result is:

```text
lexical_top1=20/20 accuracy=1.00 passed=True
```

The acceptance threshold was at least 16 out of 20.

### What changed in smoke evaluation

Smoke evaluation now includes five lexical BM25 queries in addition to the original broad smoke queries.

This means the smoke path now checks that BM25 is actually exercised.

The smoke command:

```bash
python3 -m prism.eval.run_eval --backend bm25 --smoke
```

now runs 8 total smoke queries:

- 3 original scaffold smoke queries
- 5 lexical BM25 smoke queries

### What tests were added

Tests were added for:

- exact-match outranking near matches
- dotted API identifier retrieval
- BM25 save/load round-trip
- sorted retrieval scores
- identifier-only lexical routing to BM25
- 20-query lexical verification threshold
- updated smoke pipeline query count

### Important environment lesson from this task

The command:

```bash
python3 -m pip install -e .
```

failed on the system Python because the environment is externally managed under PEP 668.

That means Python is protecting the Homebrew-managed installation from direct package changes.

The practical solution was to create a local virtual environment:

```bash
python3 -m venv .venv
```

Then the project was installed inside that venv.

When running commands, the venv was put first on `PATH`:

```bash
PATH=/Users/ritik/Documents/Projects/LLMRouter/.venv/bin:$PATH pytest -q
```

This made `pytest` and `python3` use the local project environment.

### Known limitations after this BM25 step

The BM25 backend is now real, but the project is still not complete.

Current limitations:

- the lexical slice is hand-built and small
- the exact identifier boost should be validated on larger corpora later
- dense retrieval is still placeholder-level
- KG retrieval is still placeholder-level
- hybrid retrieval is still placeholder-level
- answer generation is still not a final local LLM implementation

This is still the correct progress order.

The lexical backend now gives PRISM one real specialized retrieval capability, which is needed before the router can be meaningfully evaluated.
