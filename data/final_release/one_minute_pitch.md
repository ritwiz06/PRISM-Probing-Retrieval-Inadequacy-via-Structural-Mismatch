# One Minute Pitch

PRISM is a representation-aware retrieval system. Instead of sending every query to the same retriever, it asks which evidence structure is most adequate for the question: lexical text, dense semantics, graph structure, or a hybrid path. That routing decision is made by `computed_ras`, which remains the production router because it is deterministic and stable across curated, held-out, public-document, and open-corpus evaluations.

The key research result is that route adequacy helps, but hard adversarial cases still require better evidence use. That is why calibrated rescue remains stronger than route-only learned variants on adversarial answer accuracy. The project is strong enough for demo and paper drafting, while still being honest about what remains unresolved.
