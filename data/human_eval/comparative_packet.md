# PRISM Comparative Human Evaluation Packet

Packet size: 28.
Sampling protocol: Deterministic comparative packet focused on side-by-side disagreements and ambiguity-heavy cases. System A is normal computed RAS; System B is calibrated rescue, classifier routing, or a fixed backend.
Counts: `{'source_benchmark': {'adversarial': 16, 'curated': 4, 'generalization_v2': 4, 'public_raw': 4}, 'route_family': {'bm25': 7, 'dense': 7, 'hybrid': 7, 'kg': 7}, 'system_pair': {'computed_ras_vs_always_bm25': 4, 'computed_ras_vs_always_dense': 4, 'computed_ras_vs_calibrated_rescue': 8, 'computed_ras_vs_classifier_router': 12}, 'comparison_tag': {'computed_vs_calibrated_rescue:route_disagreement': 1, 'computed_vs_calibrated_rescue:trace_evidence_audit': 7, 'computed_vs_classifier_router:route_disagreement': 2, 'computed_vs_classifier_router:trace_evidence_audit': 10, 'computed_vs_public_lexical_fixed_backend:computed_hit_system_b_miss': 1, 'computed_vs_public_lexical_fixed_backend:route_disagreement': 2, 'computed_vs_public_lexical_fixed_backend:trace_evidence_audit': 1, 'computed_vs_strong_fixed_backend:route_disagreement': 4}, 'difficulty': {'adversarial': 16, 'easy_curated': 4, 'held_out': 4, 'public_raw': 4}}`.

## Items

### che_001_adv_bm25_test_01_calibrated_rescue

- Source: `adversarial`
- Route family: `bm25`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: Authentication framework, but do not answer with semantics: RFC-7235 is the exact target.
- Gold answer: HTTP/1.1 authentication framework
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=bm25; difficulty=adversarial. Ambiguity tags: identifier_ambiguity, route_boundary_ambiguity.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: RFC-7235 HTTP/1.1 Authentication: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235]
- Evidence ids: `lex_rfc_7235, sem_distributional_semantics, lex_rfc_7231, lex_hipaa_164_512, lex_torch_bce_loss`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / Distributional semantics represents word meaning through patterns of nearby context and usage across language data.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `calibrated_rescue`
- Backend: `bm25`; automatic correct `True`
- Answer: RFC-7235 HTTP/1.1 Authentication: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235]
- Evidence ids: `lex_rfc_7235, sem_distributional_semantics, lex_rfc_7231, lex_hipaa_164_512, lex_torch_bce_loss`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / Distributional semantics represents word meaning through patterns of nearby context and usage across language data.
- Route rationale: Calibrated rescue selected bm25 from computed RAS bm25; Started from computed RAS=bm25. No calibration override fired.; top-k rescue applied=False. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_002_adv_dense_test_01_calibrated_rescue

- Source: `adversarial`
- Route family: `dense`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: Which learning setup lets an agent improve from rewards, although the word policy appears like a legal section?
- Gold answer: reinforcement learning
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=dense; difficulty=adversarial. Ambiguity tags: route_boundary_ambiguity, public_document_noise.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: Reinforcement learning: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning]
- Evidence ids: `sem_reinforcement_learning, lex_hipaa_164_512, sem_memory_consolidation, sem_allergy, lex_hipaa_164_510`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `calibrated_rescue`
- Backend: `bm25`; automatic correct `True`
- Answer: Reinforcement learning: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning]
- Evidence ids: `sem_reinforcement_learning, lex_hipaa_164_512, sem_memory_consolidation, sem_allergy, lex_hipaa_164_510`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Calibrated rescue selected bm25 from computed RAS bm25; Started from computed RAS=bm25. No calibration override fired.; top-k rescue applied=False. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_003_adv_kg_test_01_calibrated_rescue

- Source: `adversarial`
- Route family: `kg`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: Can a bird swim when duck swims but eagle does not?
- Gold answer: Yes. duck capable_of swim
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=kg; difficulty=adversarial. Ambiguity tags: noisy_structure, wrong_bridge_distractor.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. Existential support in the demo KG: penguin is_a bird ; penguin capable_of swim. [evidence: path:kg_penguin_is_bird->kg_penguin_capable_swim]
- Evidence ids: `path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: penguin is_a bird ; penguin capable_of swim / duck is_a bird ; duck capable_of swim
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `calibrated_rescue`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. Existential support in the demo KG: penguin is_a bird ; penguin capable_of swim. [evidence: path:kg_penguin_is_bird->kg_penguin_capable_swim]
- Evidence ids: `path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: penguin is_a bird ; penguin capable_of swim / duck is_a bird ; duck capable_of swim
- Route rationale: Calibrated rescue selected kg from computed RAS kg; Started from computed RAS=kg. No calibration override fired.; top-k rescue applied=False. Selected kg for deductive/structured signals with minimum RAS=0.400.

### che_004_adv_hybrid_test_01_calibrated_rescue

- Source: `adversarial`
- Route family: `hybrid`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: What bridge connects whale and vertebrate when ocean semantics are more salient?
- Gold answer: mammal
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=hybrid; difficulty=adversarial. Ambiguity tags: lexical_semantic_overlap, wrong_bridge_distractor.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_whale_is_mammal->kg_mammal_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+doc_mammal`
- Evidence snippets: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `calibrated_rescue`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_whale_is_mammal->kg_mammal_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+doc_mammal`
- Evidence snippets: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Calibrated rescue selected hybrid from computed RAS hybrid; Started from computed RAS=hybrid. No calibration override fired.; top-k rescue applied=False. Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### che_005_adv_bm25_test_02_calibrated_rescue

- Source: `adversarial`
- Route family: `bm25`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: HIPAA 164.510 opportunity to agree or object, with 164.512 nearby in the page noise.
- Gold answer: uses and disclosures requiring an opportunity to agree or object
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=bm25; difficulty=adversarial. Ambiguity tags: identifier_ambiguity, public_document_noise.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: HIPAA 45 CFR 164.510: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. [evidence: lex_hipaa_164_510]
- Evidence ids: `lex_hipaa_164_510, lex_hipaa_164_512, sem_allergy, lex_hipaa_164_514, rel_owl_mouse`
- Evidence snippets: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `calibrated_rescue`
- Backend: `bm25`; automatic correct `True`
- Answer: HIPAA 45 CFR 164.510: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. [evidence: lex_hipaa_164_510]
- Evidence ids: `lex_hipaa_164_510, lex_hipaa_164_512, sem_allergy, lex_hipaa_164_514, rel_owl_mouse`
- Evidence snippets: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Calibrated rescue selected bm25 from computed RAS bm25; Started from computed RAS=bm25. No calibration override fired.; top-k rescue applied=False. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_006_adv_dense_test_02_calibrated_rescue

- Source: `adversarial`
- Route family: `dense`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:route_disagreement`
- Query: What model keeps materials in use rather than waste, despite the exact phrase jsonb_set in the distractor?
- Gold answer: circular economy
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:route_disagreement. Source=adversarial; family=dense; difficulty=adversarial. Route disagreement: A=bm25, B=dense. Ambiguity tags: misleading_exact_term, lexical_semantic_overlap.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: Circular economy: A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. [evidence: sem_circular_economy]
- Evidence ids: `sem_circular_economy, lex_postgres_jsonb_set, rel_owl_mouse, rel_mammal_milk, rel_frog_mosquito`
- Evidence snippets: A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. / PostgreSQL jsonb_set updates or inserts a value at a specified JSONB path.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `calibrated_rescue`
- Backend: `dense`; automatic correct `True`
- Answer: Circular economy. A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. [evidence: sem_circular_economy::chunk_0]
- Evidence ids: `sem_circular_economy::chunk_0, lex_postgres_jsonb_set::chunk_0, lex_postgres_jsonb_insert::chunk_0, sem_background_007::chunk_0, sem_background_047::chunk_0`
- Evidence snippets: A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. / PostgreSQL jsonb_set updates or inserts a value at a specified JSONB path.
- Route rationale: Calibrated rescue selected dense from computed RAS bm25; Started from computed RAS=bm25. Semantic wording with negated/distractor identifier overrode BM25 to Dense.; top-k rescue applied=False. Selected dense for semantic/paraphrase signals with minimum RAS=1.200.

### che_007_adv_kg_test_02_calibrated_rescue

- Source: `adversarial`
- Route family: `kg`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: Are all birds able to swim when duck is a positive distractor?
- Gold answer: No. Counterexample evidence
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=kg; difficulty=adversarial. Ambiguity tags: noisy_structure, wrong_bridge_distractor.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: No. Counterexample evidence: owl is_a bird ; owl not_capable_of swim; eagle is_a bird ; eagle not_capable_of swim; chicken is_a bird ; chicken not_capable_of swim. [evidence: path:kg_owl_is_bird->kg_owl_not_swim, path:kg_eagle_is_bird->kg_eagle_not_swim, path:kg_chicken_is_bird->kg_chicken_not_swim]
- Evidence ids: `path:kg_owl_is_bird->kg_owl_not_swim, path:kg_eagle_is_bird->kg_eagle_not_swim, path:kg_chicken_is_bird->kg_chicken_not_swim, path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: owl is_a bird ; owl not_capable_of swim / eagle is_a bird ; eagle not_capable_of swim
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `calibrated_rescue`
- Backend: `kg`; automatic correct `True`
- Answer: No. Counterexample evidence: owl is_a bird ; owl not_capable_of swim; eagle is_a bird ; eagle not_capable_of swim; chicken is_a bird ; chicken not_capable_of swim. [evidence: path:kg_owl_is_bird->kg_owl_not_swim, path:kg_eagle_is_bird->kg_eagle_not_swim, path:kg_chicken_is_bird->kg_chicken_not_swim]
- Evidence ids: `path:kg_owl_is_bird->kg_owl_not_swim, path:kg_eagle_is_bird->kg_eagle_not_swim, path:kg_chicken_is_bird->kg_chicken_not_swim, path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: owl is_a bird ; owl not_capable_of swim / eagle is_a bird ; eagle not_capable_of swim
- Route rationale: Calibrated rescue selected kg from computed RAS kg; Started from computed RAS=kg. No calibration override fired.; top-k rescue applied=False. Selected kg for deductive/structured signals with minimum RAS=0.400.

### che_008_adv_hybrid_test_02_calibrated_rescue

- Source: `adversarial`
- Route family: `hybrid`; difficulty `adversarial`
- Comparison tag: `computed_vs_calibrated_rescue:trace_evidence_audit`
- Query: What relation connects eagle and fish if bird-to-vertebrate is nearby?
- Gold answer: eagle eats fish
- Selection reason: Selected for computed_vs_calibrated_rescue. Resolved tag: computed_vs_calibrated_rescue:trace_evidence_audit. Source=adversarial; family=hybrid; difficulty=adversarial. Ambiguity tags: wrong_bridge_distractor, top1_topk_gap_risk.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate
[bm25:rel_eagle_fish] The eagle to fish relation is dietary: eagle eats fish in the demo KG.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_eagle_is_bird->kg_bird_is_vertebrate,rel_eagle_fish]
- Evidence ids: `hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_eagle_fish, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_eagle_fish, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_whale_vertebrate`
- Evidence snippets: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_eagle_fish] The eagle to fish relation is dietary: eagle eats fish in the demo KG. / [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `calibrated_rescue`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate
[bm25:rel_eagle_fish] The eagle to fish relation is dietary: eagle eats fish in the demo KG.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_eagle_is_bird->kg_bird_is_vertebrate,rel_eagle_fish]
- Evidence ids: `hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_eagle_fish, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_eagle_fish, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_whale_vertebrate`
- Evidence snippets: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_eagle_fish] The eagle to fish relation is dietary: eagle eats fish in the demo KG. / [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Calibrated rescue selected hybrid from computed RAS hybrid; Started from computed RAS=hybrid. No calibration override fired.; top-k rescue applied=False. Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### che_009_adv_bm25_test_03_classifier_router

- Source: `adversarial`
- Route family: `bm25`; difficulty `adversarial`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: numpy.linalg.norm describes geometry and magnitude, but the exact function is the answer source.
- Gold answer: matrix or vector norm
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=adversarial; family=bm25; difficulty=adversarial. Ambiguity tags: lexical_semantic_overlap, identifier_with_distractor_language.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: numpy.linalg.norm: numpy.linalg.norm returns a matrix or vector norm, with behavior controlled by ord and axis. [evidence: lex_numpy_linalg_norm]
- Evidence ids: `lex_numpy_linalg_norm, sem_water_cycle, sem_background_077, sem_background_057, sem_background_037`
- Evidence snippets: numpy.linalg.norm returns a matrix or vector norm, with behavior controlled by ord and axis. / The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `bm25`; automatic correct `True`
- Answer: numpy.linalg.norm: numpy.linalg.norm returns a matrix or vector norm, with behavior controlled by ord and axis. [evidence: lex_numpy_linalg_norm]
- Evidence ids: `lex_numpy_linalg_norm, sem_water_cycle, sem_background_077, sem_background_057, sem_background_037`
- Evidence snippets: numpy.linalg.norm returns a matrix or vector norm, with behavior controlled by ord and axis. / The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems.
- Route rationale: Classifier router selected bm25. Production RAS would select bm25. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_010_adv_dense_test_03_classifier_router

- Source: `adversarial`
- Route family: `dense`; difficulty `adversarial`
- Comparison tag: `computed_vs_classifier_router:route_disagreement`
- Query: Which cycle moves water through evaporation and rain, not RFC routing?
- Gold answer: water cycle
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:route_disagreement. Source=adversarial; family=dense; difficulty=adversarial. Route disagreement: A=bm25, B=dense. Ambiguity tags: misleading_exact_term, public_document_noise.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: Water cycle: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. [evidence: sem_water_cycle]
- Evidence ids: `sem_water_cycle, lex_hipaa_164_512, lex_rfc_7230, sem_photosynthesis, sem_circadian_rhythm`
- Evidence snippets: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `dense`; automatic correct `True`
- Answer: Water cycle. The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. [evidence: sem_water_cycle::chunk_0]
- Evidence ids: `sem_water_cycle::chunk_0, doc_policy::chunk_0, lex_rfc_7230::chunk_0, rel_mosquito_animal::chunk_0, sem_mycorrhizal_network::chunk_0`
- Evidence snippets: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. / Property and membership questions should route to the KG backend. Multi-hop questions should route to hybrid.
- Route rationale: Classifier router selected dense. Production RAS would select bm25. Selected dense for semantic/paraphrase signals with minimum RAS=1.200.

### che_011_adv_kg_test_03_classifier_router

- Source: `adversarial`
- Route family: `kg`; difficulty `adversarial`
- Comparison tag: `computed_vs_classifier_router:route_disagreement`
- Query: Is mosquito an animal through insect, even though the query sounds like a public health document?
- Gold answer: Yes. mosquito is_a insect ; insect is_a animal
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:route_disagreement. Source=adversarial; family=kg; difficulty=adversarial. Route disagreement: A=kg, B=dense. Ambiguity tags: public_document_noise, noisy_structure.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: Yes, indirectly: mosquito is_a insect ; insect is_a animal. [evidence: path:kg_mosquito_is_insect->kg_insect_is_animal]
- Evidence ids: `path:kg_mosquito_is_insect->kg_insect_is_animal`
- Evidence snippets: mosquito is_a insect ; insect is_a animal
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `dense`; automatic correct `True`
- Answer: Mosquito to animal bridge. A mosquito connects to animal through insect: mosquito is an insect, and insect is an animal. [evidence: rel_mosquito_animal::chunk_0]
- Evidence ids: `rel_mosquito_animal::chunk_0, rel_frog_mosquito::chunk_0, rel_bat_mosquito::chunk_0, rel_insect_animal::chunk_0, sem_background_046::chunk_0`
- Evidence snippets: A mosquito connects to animal through insect: mosquito is an insect, and insect is an animal. / The frog to mosquito relation is dietary: frog eats mosquito in the demo KG.
- Route rationale: Classifier router selected dense. Production RAS would select kg. Selected dense for semantic/paraphrase signals with minimum RAS=1.000.

### che_012_adv_hybrid_test_03_classifier_router

- Source: `adversarial`
- Route family: `hybrid`; difficulty `adversarial`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: What bridge connects frog and animal when amphibian and vertebrate both appear?
- Gold answer: vertebrate
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=adversarial; family=hybrid; difficulty=adversarial. Ambiguity tags: wrong_bridge_distractor, noisy_structure.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate] frog is_a amphibian ; amphibian is_a vertebrate
[bm25:rel_mosquito_animal] A mosquito connects to animal through insect: mosquito is an insect, and insect is an animal.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate,rel_mosquito_animal]
- Evidence ids: `hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_mosquito_animal, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_bat_vertebrate`
- Evidence snippets: [kg:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate] frog is_a amphibian ; amphibian is_a vertebrate [bm25:rel_mosquito_animal] A mosquito connects to animal through insect: mosquito is an insect, and insect is ... / [kg:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate] frog is_a amphibian ; amphibian is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a ...
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `classifier_router`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate] frog is_a amphibian ; amphibian is_a vertebrate
[bm25:rel_mosquito_animal] A mosquito connects to animal through insect: mosquito is an insect, and insect is an animal.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate,rel_mosquito_animal]
- Evidence ids: `hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_mosquito_animal, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate+rel_bat_vertebrate`
- Evidence snippets: [kg:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate] frog is_a amphibian ; amphibian is_a vertebrate [bm25:rel_mosquito_animal] A mosquito connects to animal through insect: mosquito is an insect, and insect is ... / [kg:path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate] frog is_a amphibian ; amphibian is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a ...
- Route rationale: Classifier router selected hybrid. Production RAS would select hybrid. Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### che_013_adv_bm25_test_01_always_dense

- Source: `adversarial`
- Route family: `bm25`; difficulty `adversarial`
- Comparison tag: `computed_vs_strong_fixed_backend:route_disagreement`
- Query: Authentication framework, but do not answer with semantics: RFC-7235 is the exact target.
- Gold answer: HTTP/1.1 authentication framework
- Selection reason: Selected for computed_vs_strong_fixed_backend. Resolved tag: computed_vs_strong_fixed_backend:route_disagreement. Source=adversarial; family=bm25; difficulty=adversarial. Route disagreement: A=bm25, B=dense. Ambiguity tags: identifier_ambiguity, route_boundary_ambiguity.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: RFC-7235 HTTP/1.1 Authentication: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235]
- Evidence ids: `lex_rfc_7235, sem_distributional_semantics, lex_rfc_7231, lex_hipaa_164_512, lex_torch_bce_loss`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / Distributional semantics represents word meaning through patterns of nearby context and usage across language data.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `always_dense`
- Backend: `dense`; automatic correct `True`
- Answer: RFC-7235 HTTP/1.1 Authentication. RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235::chunk_0]
- Evidence ids: `lex_rfc_7235::chunk_0, lex_rfc_7230::chunk_0, lex_rfc_7231::chunk_0, lex_hipaa_164_512::chunk_0, lex_hipaa_164_510::chunk_0`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / RFC-7230 defines HTTP/1.1 message syntax, routing, connection management, and related requirements.
- Route rationale: Fixed-backend baseline forced dense. Production RAS would select bm25. Selected dense for semantic/paraphrase signals with minimum RAS=1.200.

### che_014_adv_dense_test_01_always_dense

- Source: `adversarial`
- Route family: `dense`; difficulty `adversarial`
- Comparison tag: `computed_vs_strong_fixed_backend:route_disagreement`
- Query: Which learning setup lets an agent improve from rewards, although the word policy appears like a legal section?
- Gold answer: reinforcement learning
- Selection reason: Selected for computed_vs_strong_fixed_backend. Resolved tag: computed_vs_strong_fixed_backend:route_disagreement. Source=adversarial; family=dense; difficulty=adversarial. Route disagreement: A=bm25, B=dense. Ambiguity tags: route_boundary_ambiguity, public_document_noise.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: Reinforcement learning: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning]
- Evidence ids: `sem_reinforcement_learning, lex_hipaa_164_512, sem_memory_consolidation, sem_allergy, lex_hipaa_164_510`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `always_dense`
- Backend: `dense`; automatic correct `True`
- Answer: Reinforcement learning. Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning::chunk_0]
- Evidence ids: `sem_reinforcement_learning::chunk_0, sem_background_008::chunk_0, sem_background_028::chunk_0, sem_background_068::chunk_0, sem_background_048::chunk_0`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / This concise background note discusses language acquisition with emphasis on definitions, mechanisms, examples, and practical consequences for general knowledge retrieval. It is included to broaden the semantic corpus...
- Route rationale: Fixed-backend baseline forced dense. Production RAS would select bm25. Selected dense for semantic/paraphrase signals with minimum RAS=1.200.

### che_015_adv_kg_test_01_always_dense

- Source: `adversarial`
- Route family: `kg`; difficulty `adversarial`
- Comparison tag: `computed_vs_strong_fixed_backend:route_disagreement`
- Query: Can a bird swim when duck swims but eagle does not?
- Gold answer: Yes. duck capable_of swim
- Selection reason: Selected for computed_vs_strong_fixed_backend. Resolved tag: computed_vs_strong_fixed_backend:route_disagreement. Source=adversarial; family=kg; difficulty=adversarial. Route disagreement: A=kg, B=dense. Ambiguity tags: noisy_structure, wrong_bridge_distractor.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. Existential support in the demo KG: penguin is_a bird ; penguin capable_of swim. [evidence: path:kg_penguin_is_bird->kg_penguin_capable_swim]
- Evidence ids: `path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: penguin is_a bird ; penguin capable_of swim / duck is_a bird ; duck capable_of swim
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `always_dense`
- Backend: `dense`; automatic correct `True`
- Answer: Duck swim relation. The duck to swim relation is capability based: duck is capable of swim. [evidence: rel_duck_swim::chunk_0]
- Evidence ids: `rel_duck_swim::chunk_0, rel_eagle_fish::chunk_0, rel_penguin_vertebrate::chunk_0, rel_penguin_swim::chunk_0, rel_sparrow_wings::chunk_0`
- Evidence snippets: The duck to swim relation is capability based: duck is capable of swim. / The eagle to fish relation is dietary: eagle eats fish in the demo KG.
- Route rationale: Fixed-backend baseline forced dense. Production RAS would select kg. Selected dense for semantic/paraphrase signals with minimum RAS=1.000.

### che_016_adv_hybrid_test_01_always_dense

- Source: `adversarial`
- Route family: `hybrid`; difficulty `adversarial`
- Comparison tag: `computed_vs_strong_fixed_backend:route_disagreement`
- Query: What bridge connects whale and vertebrate when ocean semantics are more salient?
- Gold answer: mammal
- Selection reason: Selected for computed_vs_strong_fixed_backend. Resolved tag: computed_vs_strong_fixed_backend:route_disagreement. Source=adversarial; family=hybrid; difficulty=adversarial. Route disagreement: A=hybrid, B=dense. Ambiguity tags: lexical_semantic_overlap, wrong_bridge_distractor.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_whale_is_mammal->kg_mammal_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+doc_mammal`
- Evidence snippets: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `always_dense`
- Backend: `dense`; automatic correct `True`
- Answer: Whale to vertebrate bridge. A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. [evidence: rel_whale_vertebrate::chunk_0]
- Evidence ids: `rel_whale_vertebrate::chunk_0, rel_whale_swim::chunk_0, rel_salmon_vertebrate::chunk_0, rel_dolphin_echolocation::chunk_0, sem_background_071::chunk_0`
- Evidence snippets: A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / The whale to swim relation is capability based: whale is capable of swim.
- Route rationale: Fixed-backend baseline forced dense. Production RAS would select hybrid. Selected dense for semantic/paraphrase signals with minimum RAS=1.000.

### che_017_pub_bm25_07_always_bm25

- Source: `public_raw`
- Route family: `bm25`; difficulty `public_raw`
- Comparison tag: `computed_vs_public_lexical_fixed_backend:trace_evidence_audit`
- Query: RFC-9110
- Gold answer: HTTP Semantics
- Selection reason: Selected for computed_vs_public_lexical_fixed_backend. Resolved tag: computed_vs_public_lexical_fixed_backend:trace_evidence_audit. Source=public_raw; family=bm25; difficulty=public_raw.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `False`
- Answer: Water cycle: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. [evidence: sem_water_cycle]
- Evidence ids: `sem_water_cycle, sem_urban_heat_island, sem_situated_knowledge, sem_reinforcement_learning, sem_photosynthesis`
- Evidence snippets: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. / An urban heat island occurs when built surfaces make a city warmer than surrounding rural areas.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `always_bm25`
- Backend: `bm25`; automatic correct `False`
- Answer: Water cycle: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. [evidence: sem_water_cycle]
- Evidence ids: `sem_water_cycle, sem_urban_heat_island, sem_situated_knowledge, sem_reinforcement_learning, sem_photosynthesis`
- Evidence snippets: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. / An urban heat island occurs when built surfaces make a city warmer than surrounding rural areas.
- Route rationale: Fixed-backend baseline forced bm25. Production RAS would select bm25. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_018_pub_dense_07_always_bm25

- Source: `public_raw`
- Route family: `dense`; difficulty `public_raw`
- Comparison tag: `computed_vs_public_lexical_fixed_backend:route_disagreement`
- Query: What learning setup lets an agent improve using rewards and penalties?
- Gold answer: reinforcement learning
- Selection reason: Selected for computed_vs_public_lexical_fixed_backend. Resolved tag: computed_vs_public_lexical_fixed_backend:route_disagreement. Source=public_raw; family=dense; difficulty=public_raw. Route disagreement: A=dense, B=bm25.

#### System A

- Label: `computed_ras`
- Backend: `dense`; automatic correct `True`
- Answer: Reinforcement learning. Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning::chunk_0]
- Evidence ids: `sem_reinforcement_learning::chunk_0, sem_memory_consolidation::chunk_0, sem_collective_intelligence::chunk_0, sem_algorithmic_bias::chunk_0, sem_background_048::chunk_0`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / Memory consolidation is the process by which experiences and learning become more stable over time, especially during sleep.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

#### System B

- Label: `always_bm25`
- Backend: `bm25`; automatic correct `True`
- Answer: Reinforcement learning: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning]
- Evidence ids: `sem_reinforcement_learning, sem_situated_knowledge, sem_memory_consolidation, rel_mosquito_animal, sem_ecological_niche`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / Situated knowledge emphasizes that perspective, social position, and lived context shape what people observe and know.
- Route rationale: Fixed-backend baseline forced bm25. Production RAS would select dense. Selected bm25 for lexical/exact-match signals with minimum RAS=1.000.

### che_019_pub_kg_07_always_bm25

- Source: `public_raw`
- Route family: `kg`; difficulty `public_raw`
- Comparison tag: `computed_vs_public_lexical_fixed_backend:route_disagreement`
- Query: Is a whale a mammal?
- Gold answer: Yes. whale is_a mammal
- Selection reason: Selected for computed_vs_public_lexical_fixed_backend. Resolved tag: computed_vs_public_lexical_fixed_backend:route_disagreement. Source=public_raw; family=kg; difficulty=public_raw. Route disagreement: A=kg, B=bm25.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. whale is_a mammal. [evidence: kg_whale_is_mammal]
- Evidence ids: `kg_whale_is_mammal`
- Evidence snippets: whale is_a mammal
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `always_bm25`
- Backend: `bm25`; automatic correct `True`
- Answer: Whale to vertebrate bridge: A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. [evidence: rel_whale_vertebrate]
- Evidence ids: `rel_whale_vertebrate, rel_bat_vertebrate, rel_mammal_vertebrate, doc_mammal, rel_whale_swim`
- Evidence snippets: A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate.
- Route rationale: Fixed-backend baseline forced bm25. Production RAS would select kg. Selected bm25 for lexical/exact-match signals with minimum RAS=1.000.

### che_020_pub_hybrid_07_always_bm25

- Source: `public_raw`
- Route family: `hybrid`; difficulty `public_raw`
- Comparison tag: `computed_vs_public_lexical_fixed_backend:computed_hit_system_b_miss`
- Query: What bridge connects eagle and vertebrate?
- Gold answer: bird
- Selection reason: Selected for computed_vs_public_lexical_fixed_backend. Resolved tag: computed_vs_public_lexical_fixed_backend:computed_hit_system_b_miss. Source=public_raw; family=hybrid; difficulty=public_raw. Route disagreement: A=hybrid, B=bm25. Automatic correctness disagreement: A=True, B=False.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_eagle_is_bird->kg_bird_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_salmon_vertebrate`
- Evidence snippets: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `always_bm25`
- Backend: `bm25`; automatic correct `False`
- Answer: Whale to vertebrate bridge: A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. [evidence: rel_whale_vertebrate]
- Evidence ids: `rel_whale_vertebrate, rel_salmon_vertebrate, rel_penguin_vertebrate, rel_bat_vertebrate, rel_mosquito_animal`
- Evidence snippets: A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Fixed-backend baseline forced bm25. Production RAS would select hybrid. Selected bm25 for lexical/exact-match signals with minimum RAS=1.000.

### che_021_gen_lex_test_001_classifier_router

- Source: `generalization_v2`
- Route family: `bm25`; difficulty `held_out`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: 42 U.S.C. §1983 civil action
- Gold answer: civil action for deprivation of rights
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=generalization_v2; family=bm25; difficulty=held_out. Ambiguity tags: legal_section.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: 42 U.S.C. §1983: 42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law. [evidence: lex_section_1983]
- Evidence ids: `lex_section_1983, lex_section_1985, lex_section_1981, sem_water_cycle, sem_urban_heat_island`
- Evidence snippets: 42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law. / 42 U.S.C. §1985 concerns conspiracies to interfere with civil rights.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `bm25`; automatic correct `True`
- Answer: 42 U.S.C. §1983: 42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law. [evidence: lex_section_1983]
- Evidence ids: `lex_section_1983, lex_section_1985, lex_section_1981, sem_water_cycle, sem_urban_heat_island`
- Evidence snippets: 42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law. / 42 U.S.C. §1985 concerns conspiracies to interfere with civil rights.
- Route rationale: Classifier router selected bm25. Production RAS would select bm25. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_022_gen_sem_test_001_classifier_router

- Source: `generalization_v2`
- Route family: `dense`; difficulty `held_out`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: Which concept puts a price on greenhouse gas emissions?
- Gold answer: Carbon pricing
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=generalization_v2; family=dense; difficulty=held_out. Ambiguity tags: paraphrase.

#### System A

- Label: `computed_ras`
- Backend: `dense`; automatic correct `True`
- Answer: Carbon pricing. Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices. [evidence: sem_carbon_pricing::chunk_0]
- Evidence ids: `sem_carbon_pricing::chunk_0, sem_climate_anxiety::chunk_0, sem_photosynthesis::chunk_0, sem_background_047::chunk_0, sem_background_007::chunk_0`
- Evidence snippets: Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices. / Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

#### System B

- Label: `classifier_router`
- Backend: `dense`; automatic correct `True`
- Answer: Carbon pricing. Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices. [evidence: sem_carbon_pricing::chunk_0]
- Evidence ids: `sem_carbon_pricing::chunk_0, sem_climate_anxiety::chunk_0, sem_photosynthesis::chunk_0, sem_background_047::chunk_0, sem_background_007::chunk_0`
- Evidence snippets: Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices. / Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures.
- Route rationale: Classifier router selected dense. Production RAS would select dense. Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### che_023_gen_kg_test_001_classifier_router

- Source: `generalization_v2`
- Route family: `kg`; difficulty `held_out`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: Is a duck a bird?
- Gold answer: duck is_a bird
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=generalization_v2; family=kg; difficulty=held_out. Ambiguity tags: membership.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. duck is_a bird. [evidence: kg_duck_is_bird]
- Evidence ids: `kg_duck_is_bird`
- Evidence snippets: duck is_a bird
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. duck is_a bird. [evidence: kg_duck_is_bird]
- Evidence ids: `kg_duck_is_bird`
- Evidence snippets: duck is_a bird
- Route rationale: Classifier router selected kg. Production RAS would select kg. Selected kg for deductive/structured signals with minimum RAS=0.400.

### che_024_gen_rel_test_001_classifier_router

- Source: `generalization_v2`
- Route family: `hybrid`; difficulty `held_out`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: What relation connects duck and swim?
- Gold answer: duck capable_of swim
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=generalization_v2; family=hybrid; difficulty=held_out. Ambiguity tags: relation.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:kg_duck_capable_swim] duck capable_of swim
[bm25:rel_duck_swim] The duck to swim relation is capability based: duck is capable of swim.. This combines structured evidence plus text relation evidence. [fused evidence: kg_duck_capable_swim,rel_duck_swim]
- Evidence ids: `hybrid:bundle:kg_duck_capable_swim+rel_duck_swim, hybrid:bundle:kg_duck_capable_swim+rel_whale_swim, hybrid:bundle:kg_duck_capable_swim+rel_penguin_swim, hybrid:text:rel_duck_swim, hybrid:text:rel_whale_swim`
- Evidence snippets: [kg:kg_duck_capable_swim] duck capable_of swim [bm25:rel_duck_swim] The duck to swim relation is capability based: duck is capable of swim. / [kg:kg_duck_capable_swim] duck capable_of swim [bm25:rel_whale_swim] The whale to swim relation is capability based: whale is capable of swim.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `classifier_router`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:kg_duck_capable_swim] duck capable_of swim
[bm25:rel_duck_swim] The duck to swim relation is capability based: duck is capable of swim.. This combines structured evidence plus text relation evidence. [fused evidence: kg_duck_capable_swim,rel_duck_swim]
- Evidence ids: `hybrid:bundle:kg_duck_capable_swim+rel_duck_swim, hybrid:bundle:kg_duck_capable_swim+rel_whale_swim, hybrid:bundle:kg_duck_capable_swim+rel_penguin_swim, hybrid:text:rel_duck_swim, hybrid:text:rel_whale_swim`
- Evidence snippets: [kg:kg_duck_capable_swim] duck capable_of swim [bm25:rel_duck_swim] The duck to swim relation is capability based: duck is capable of swim. / [kg:kg_duck_capable_swim] duck capable_of swim [bm25:rel_whale_swim] The whale to swim relation is capability based: whale is capable of swim.
- Route rationale: Classifier router selected hybrid. Production RAS would select hybrid. Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### che_025_curated_000_classifier_router

- Source: `curated`
- Route family: `bm25`; difficulty `easy_curated`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: What does HIPAA 164.512 cover?
- Gold answer: Uses and disclosures without authorization or opportunity to agree/object.
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=curated; family=bm25; difficulty=easy_curated.

#### System A

- Label: `computed_ras`
- Backend: `bm25`; automatic correct `True`
- Answer: HIPAA 45 CFR 164.512: HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required. [evidence: lex_hipaa_164_512]
- Evidence ids: `lex_hipaa_164_512, lex_hipaa_164_514, lex_hipaa_164_510, sem_situated_knowledge, sem_water_cycle`
- Evidence snippets: HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required. / HIPAA section 164.514 covers other requirements relating to uses and disclosures of protected health information.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `bm25`; automatic correct `True`
- Answer: HIPAA 45 CFR 164.512: HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required. [evidence: lex_hipaa_164_512]
- Evidence ids: `lex_hipaa_164_512, lex_hipaa_164_514, lex_hipaa_164_510, sem_situated_knowledge, sem_water_cycle`
- Evidence snippets: HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required. / HIPAA section 164.514 covers other requirements relating to uses and disclosures of protected health information.
- Route rationale: Classifier router selected bm25. Production RAS would select bm25. Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### che_026_curated_020_classifier_router

- Source: `curated`
- Route family: `dense`; difficulty `easy_curated`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: Which idea is solastalgia homesick planet?
- Gold answer: Climate anxiety.
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=curated; family=dense; difficulty=easy_curated.

#### System A

- Label: `computed_ras`
- Backend: `dense`; automatic correct `True`
- Answer: Climate anxiety. Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures. [evidence: sem_climate_anxiety::chunk_0]
- Evidence ids: `sem_climate_anxiety::chunk_0, sem_background_003::chunk_0, sem_background_023::chunk_0, sem_background_063::chunk_0, sem_background_043::chunk_0`
- Evidence snippets: Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures. / This concise background note discusses solar eclipses with emphasis on definitions, mechanisms, examples, and practical consequences for general knowledge retrieval. It is included to broaden the semantic corpus witho...
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

#### System B

- Label: `classifier_router`
- Backend: `dense`; automatic correct `True`
- Answer: Climate anxiety. Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures. [evidence: sem_climate_anxiety::chunk_0]
- Evidence ids: `sem_climate_anxiety::chunk_0, sem_background_003::chunk_0, sem_background_023::chunk_0, sem_background_063::chunk_0, sem_background_043::chunk_0`
- Evidence snippets: Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures. / This concise background note discusses solar eclipses with emphasis on definitions, mechanisms, examples, and practical consequences for general knowledge retrieval. It is included to broaden the semantic corpus witho...
- Route rationale: Classifier router selected dense. Production RAS would select dense. Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### che_027_curated_040_classifier_router

- Source: `curated`
- Route family: `kg`; difficulty `easy_curated`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: Is a bat a mammal?
- Gold answer: Yes. bat is_a mammal.
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=curated; family=kg; difficulty=easy_curated.

#### System A

- Label: `computed_ras`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. bat is_a mammal. [evidence: kg_bat_is_mammal]
- Evidence ids: `kg_bat_is_mammal`
- Evidence snippets: bat is_a mammal
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

#### System B

- Label: `classifier_router`
- Backend: `kg`; automatic correct `True`
- Answer: Yes. bat is_a mammal. [evidence: kg_bat_is_mammal]
- Evidence ids: `kg_bat_is_mammal`
- Evidence snippets: bat is_a mammal
- Route rationale: Classifier router selected kg. Production RAS would select kg. Selected kg for deductive/structured signals with minimum RAS=0.400.

### che_028_curated_060_classifier_router

- Source: `curated`
- Route family: `hybrid`; difficulty `easy_curated`
- Comparison tag: `computed_vs_classifier_router:trace_evidence_audit`
- Query: What bridge connects bat and vertebrate?
- Gold answer: bat -> mammal -> vertebrate plus text bridge evidence.
- Selection reason: Selected for computed_vs_classifier_router. Resolved tag: computed_vs_classifier_router:trace_evidence_audit. Source=curated; family=hybrid; difficulty=easy_curated.

#### System A

- Label: `computed_ras`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate
[bm25:rel_bat_vertebrate] A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_bat_is_mammal->kg_mammal_is_vertebrate,rel_bat_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_mosquito_animal`
- Evidence snippets: [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate [bm25:rel_bat_vertebrate] A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate. / [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

#### System B

- Label: `classifier_router`
- Backend: `hybrid`; automatic correct `True`
- Answer: Hybrid connection: [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate
[bm25:rel_bat_vertebrate] A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_bat_is_mammal->kg_mammal_is_vertebrate,rel_bat_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_mosquito_animal`
- Evidence snippets: [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate [bm25:rel_bat_vertebrate] A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate. / [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.
- Route rationale: Classifier router selected hybrid. Production RAS would select hybrid. Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.
