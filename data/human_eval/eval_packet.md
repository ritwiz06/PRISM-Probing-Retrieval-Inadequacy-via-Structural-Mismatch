# PRISM Human Evaluation Packet

Packet size: 36.
Sampling protocol: Deterministic balanced packet: curated, generalization_v2, public_raw, and adversarial examples, with calibrated adversarial variants included for rescue-path auditing.
Counts: `{'benchmark_source': {'adversarial': 12, 'curated': 8, 'generalization_v2': 8, 'public_raw': 8}, 'route_family': {'bm25': 9, 'dense': 9, 'hybrid': 9, 'kg': 9}, 'difficulty': {'adversarial': 12, 'easy_curated': 8, 'held_out': 8, 'public_raw': 8}, 'system_variant': {'calibrated_ras': 4, 'computed_ras': 32}, 'automatic_correct': {'False': 1, 'True': 35}}`.

## Items

### he_001_curated_000_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: What does HIPAA 164.512 cover?
- Gold answer: Uses and disclosures without authorization or opportunity to agree/object.
- Final answer: HIPAA 45 CFR 164.512: HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required. [evidence: lex_hipaa_164_512]
- Evidence ids: `lex_hipaa_164_512, lex_hipaa_164_514, lex_hipaa_164_510, sem_situated_knowledge, sem_water_cycle`
- Evidence snippets: HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required. / HIPAA section 164.514 covers other requirements relating to uses and disclosures of protected health information.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_002_curated_001_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: Find HIPAA section 164.510.
- Gold answer: Uses and disclosures requiring an opportunity to agree or object.
- Final answer: HIPAA 45 CFR 164.510: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. [evidence: lex_hipaa_164_510]
- Evidence ids: `lex_hipaa_164_510, lex_hipaa_164_514, lex_hipaa_164_512, doc_exact, sem_water_cycle`
- Evidence snippets: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. / HIPAA section 164.514 covers other requirements relating to uses and disclosures of protected health information.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_003_curated_020_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `dense`; predicted `dense`
- Automatic correct: `True`
- Query: Which idea is solastalgia homesick planet?
- Gold answer: Climate anxiety.
- Final answer: Climate anxiety. Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures. [evidence: sem_climate_anxiety::chunk_0]
- Evidence ids: `sem_climate_anxiety::chunk_0, sem_background_003::chunk_0, sem_background_023::chunk_0, sem_background_063::chunk_0, sem_background_043::chunk_0`
- Evidence snippets: Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures. / This concise background note discusses solar eclipses with emphasis on definitions, mechanisms, examples, and practical consequences for general knowledge retrieval. It is included to broaden the semantic corpus witho...
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### he_004_curated_021_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `dense`; predicted `dense`
- Automatic correct: `True`
- Query: Which pattern is the charlatan feeling after success?
- Gold answer: Impostor syndrome.
- Final answer: Impostor syndrome. Impostor syndrome is persistent self-doubt where capable people feel like frauds despite evidence of competence. [evidence: sem_impostor_syndrome::chunk_0]
- Evidence ids: `sem_impostor_syndrome::chunk_0, sem_narrative_identity::chunk_0, sem_attention_fragmentation::chunk_0, sem_butterfly_effect::chunk_0, sem_distributional_semantics::chunk_0`
- Evidence snippets: Impostor syndrome is persistent self-doubt where capable people feel like frauds despite evidence of competence. / Narrative identity is the way people form a sense of self by organizing memories and events into a life story.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### he_005_curated_040_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Is a bat a mammal?
- Gold answer: Yes. bat is_a mammal.
- Final answer: Yes. bat is_a mammal. [evidence: kg_bat_is_mammal]
- Evidence ids: `kg_bat_is_mammal`
- Evidence snippets: bat is_a mammal
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_006_curated_041_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Can a mammal fly?
- Gold answer: Yes, under the demo KG there exists a mammal, bat, that can fly.
- Final answer: Yes. Existential support in the demo KG: bat is_a mammal ; bat capable_of fly. [evidence: path:kg_bat_is_mammal->kg_bat_capable_fly]
- Evidence ids: `path:kg_bat_is_mammal->kg_bat_capable_fly`
- Evidence snippets: bat is_a mammal ; bat capable_of fly
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_007_curated_060_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What bridge connects bat and vertebrate?
- Gold answer: bat -> mammal -> vertebrate plus text bridge evidence.
- Final answer: Hybrid connection: [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate
[bm25:rel_bat_vertebrate] A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_bat_is_mammal->kg_mammal_is_vertebrate,rel_bat_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_bat_is_mammal->kg_mammal_is_vertebrate+rel_mosquito_animal`
- Evidence snippets: [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate [bm25:rel_bat_vertebrate] A bat connects to vertebrate through the mammal class: bat is a mammal, and mammal is a vertebrate. / [kg:path:kg_bat_is_mammal->kg_mammal_is_vertebrate] bat is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_008_curated_061_computed_ras

- Benchmark: `curated`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What bridge connects penguin and vertebrate?
- Gold answer: penguin -> bird -> vertebrate plus text bridge evidence.
- Final answer: Hybrid connection: [kg:path:kg_penguin_is_bird->kg_bird_is_vertebrate] penguin is_a bird ; bird is_a vertebrate
[bm25:rel_penguin_vertebrate] A penguin connects to vertebrate through bird: penguin is a bird, and bird is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_penguin_is_bird->kg_bird_is_vertebrate,rel_penguin_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_penguin_is_bird->kg_bird_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_penguin_is_bird->kg_bird_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_penguin_is_bird->kg_bird_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_penguin_is_bird->kg_bird_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_penguin_is_bird->kg_bird_is_vertebrate+rel_mosquito_animal`
- Evidence snippets: [kg:path:kg_penguin_is_bird->kg_bird_is_vertebrate] penguin is_a bird ; bird is_a vertebrate [bm25:rel_penguin_vertebrate] A penguin connects to vertebrate through bird: penguin is a bird, and bird is a vertebrate. / [kg:path:kg_penguin_is_bird->kg_bird_is_vertebrate] penguin is_a bird ; bird is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_009_gen_lex_test_001_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: 42 U.S.C. §1983 civil action
- Gold answer: civil action for deprivation of rights
- Final answer: 42 U.S.C. §1983: 42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law. [evidence: lex_section_1983]
- Evidence ids: `lex_section_1983, lex_section_1985, lex_section_1981, sem_water_cycle, sem_urban_heat_island`
- Evidence snippets: 42 U.S.C. §1983 provides a civil action for deprivation of rights under color of state law. / 42 U.S.C. §1985 concerns conspiracies to interfere with civil rights.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_010_gen_lex_test_002_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: 42 U.S.C. §1981 contracts
- Gold answer: make and enforce contracts
- Final answer: 42 U.S.C. §1981: 42 U.S.C. §1981 protects equal rights under the law to make and enforce contracts. [evidence: lex_section_1981]
- Evidence ids: `lex_section_1981, lex_section_1985, lex_section_1983, sem_water_cycle, sem_urban_heat_island`
- Evidence snippets: 42 U.S.C. §1981 protects equal rights under the law to make and enforce contracts. / 42 U.S.C. §1985 concerns conspiracies to interfere with civil rights.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_011_gen_sem_test_001_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `dense`; predicted `dense`
- Automatic correct: `True`
- Query: Which concept puts a price on greenhouse gas emissions?
- Gold answer: Carbon pricing
- Final answer: Carbon pricing. Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices. [evidence: sem_carbon_pricing::chunk_0]
- Evidence ids: `sem_carbon_pricing::chunk_0, sem_climate_anxiety::chunk_0, sem_photosynthesis::chunk_0, sem_background_047::chunk_0, sem_background_007::chunk_0`
- Evidence snippets: Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices. / Climate anxiety describes distress and worry about climate change, ecological loss, and uncertain planetary futures.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### he_012_gen_sem_test_002_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `dense`; predicted `dense`
- Automatic correct: `True`
- Query: Which concept organizes memories into a life story?
- Gold answer: Narrative identity
- Final answer: Narrative identity. Narrative identity is the way people form a sense of self by organizing memories and events into a life story. [evidence: sem_narrative_identity::chunk_0]
- Evidence ids: `sem_narrative_identity::chunk_0, sem_memory_consolidation::chunk_0, sem_situated_knowledge::chunk_0, sem_collective_intelligence::chunk_0, sem_distributional_semantics::chunk_0`
- Evidence snippets: Narrative identity is the way people form a sense of self by organizing memories and events into a life story. / Memory consolidation is the process by which experiences and learning become more stable over time, especially during sleep.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### he_013_gen_kg_test_001_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Is a duck a bird?
- Gold answer: duck is_a bird
- Final answer: Yes. duck is_a bird. [evidence: kg_duck_is_bird]
- Evidence ids: `kg_duck_is_bird`
- Evidence snippets: duck is_a bird
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_014_gen_kg_test_002_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Is a frog a vertebrate?
- Gold answer: frog is_a amphibian ; amphibian is_a vertebrate
- Final answer: Yes, indirectly: frog is_a amphibian ; amphibian is_a vertebrate. [evidence: path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate]
- Evidence ids: `path:kg_frog_is_amphibian->kg_amphibian_is_vertebrate`
- Evidence snippets: frog is_a amphibian ; amphibian is_a vertebrate
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_015_gen_rel_test_001_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What relation connects duck and swim?
- Gold answer: duck capable_of swim
- Final answer: Hybrid connection: [kg:kg_duck_capable_swim] duck capable_of swim
[bm25:rel_duck_swim] The duck to swim relation is capability based: duck is capable of swim.. This combines structured evidence plus text relation evidence. [fused evidence: kg_duck_capable_swim,rel_duck_swim]
- Evidence ids: `hybrid:bundle:kg_duck_capable_swim+rel_duck_swim, hybrid:bundle:kg_duck_capable_swim+rel_whale_swim, hybrid:bundle:kg_duck_capable_swim+rel_penguin_swim, hybrid:text:rel_duck_swim, hybrid:text:rel_whale_swim`
- Evidence snippets: [kg:kg_duck_capable_swim] duck capable_of swim [bm25:rel_duck_swim] The duck to swim relation is capability based: duck is capable of swim. / [kg:kg_duck_capable_swim] duck capable_of swim [bm25:rel_whale_swim] The whale to swim relation is capability based: whale is capable of swim.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_016_gen_rel_test_002_computed_ras

- Benchmark: `generalization_v2`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What relation connects whale and swim?
- Gold answer: whale capable_of swim
- Final answer: Hybrid connection: [kg:kg_whale_capable_swim] whale capable_of swim
[bm25:rel_whale_swim] The whale to swim relation is capability based: whale is capable of swim.. This combines structured evidence plus text relation evidence. [fused evidence: kg_whale_capable_swim,rel_whale_swim]
- Evidence ids: `hybrid:bundle:kg_whale_capable_swim+rel_whale_swim, hybrid:bundle:kg_whale_capable_swim+rel_whale_vertebrate, hybrid:bundle:kg_whale_capable_swim+rel_duck_swim, hybrid:bundle:kg_whale_capable_swim+rel_penguin_swim, hybrid:text:rel_whale_swim`
- Evidence snippets: [kg:kg_whale_capable_swim] whale capable_of swim [bm25:rel_whale_swim] The whale to swim relation is capability based: whale is capable of swim. / [kg:kg_whale_capable_swim] whale capable_of swim [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_017_pub_bm25_07_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `False`
- Query: RFC-9110
- Gold answer: HTTP Semantics
- Final answer: Water cycle: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. [evidence: sem_water_cycle]
- Evidence ids: `sem_water_cycle, sem_urban_heat_island, sem_situated_knowledge, sem_reinforcement_learning, sem_photosynthesis`
- Evidence snippets: The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems. / An urban heat island occurs when built surfaces make a city warmer than surrounding rural areas.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_018_pub_bm25_08_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: RFC-7235 authentication
- Gold answer: HTTP/1.1 Authentication
- Final answer: RFC-7235 HTTP/1.1 Authentication: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235]
- Evidence ids: `lex_rfc_7235, sem_water_cycle, sem_urban_heat_island, sem_situated_knowledge, sem_reinforcement_learning`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / The water cycle describes evaporation, condensation, precipitation, runoff, and storage as water moves through Earth systems.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_019_pub_dense_07_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `dense`; predicted `dense`
- Automatic correct: `True`
- Query: What learning setup lets an agent improve using rewards and penalties?
- Gold answer: reinforcement learning
- Final answer: Reinforcement learning. Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning::chunk_0]
- Evidence ids: `sem_reinforcement_learning::chunk_0, sem_memory_consolidation::chunk_0, sem_collective_intelligence::chunk_0, sem_algorithmic_bias::chunk_0, sem_background_048::chunk_0`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / Memory consolidation is the process by which experiences and learning become more stable over time, especially during sleep.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### he_020_pub_dense_08_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `dense`; predicted `dense`
- Automatic correct: `True`
- Query: What economic model keeps materials in use instead of treating them as waste?
- Gold answer: circular economy
- Final answer: Circular economy. A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. [evidence: sem_circular_economy::chunk_0]
- Evidence ids: `sem_circular_economy::chunk_0, sem_carbon_pricing::chunk_0, sem_photosynthesis::chunk_0, sem_diffusion_innovations::chunk_0, sem_water_cycle::chunk_0`
- Evidence snippets: A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. / Carbon pricing uses taxes or markets to attach a cost to greenhouse gas emissions and encourage lower-carbon choices.
- Route rationale: Selected dense for semantic/paraphrase signals with minimum RAS=0.500.

### he_021_pub_kg_07_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Is a whale a mammal?
- Gold answer: Yes. whale is_a mammal
- Final answer: Yes. whale is_a mammal. [evidence: kg_whale_is_mammal]
- Evidence ids: `kg_whale_is_mammal`
- Evidence snippets: whale is_a mammal
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_022_pub_kg_08_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Is salmon a fish?
- Gold answer: Yes. salmon is_a fish
- Final answer: Yes. salmon is_a fish. [evidence: kg_salmon_is_fish]
- Evidence ids: `kg_salmon_is_fish`
- Evidence snippets: salmon is_a fish
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_023_pub_hybrid_07_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What bridge connects eagle and vertebrate?
- Gold answer: bird
- Final answer: Hybrid connection: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_eagle_is_bird->kg_bird_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_salmon_vertebrate`
- Evidence snippets: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_024_pub_hybrid_08_computed_ras

- Benchmark: `public_raw`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What bridge connects whale and vertebrate?
- Gold answer: mammal
- Final answer: Hybrid connection: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_whale_is_mammal->kg_mammal_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_mosquito_animal`
- Evidence snippets: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_025_adv_bm25_test_01_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: Authentication framework, but do not answer with semantics: RFC-7235 is the exact target.
- Gold answer: HTTP/1.1 authentication framework
- Final answer: RFC-7235 HTTP/1.1 Authentication: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235]
- Evidence ids: `lex_rfc_7235, sem_distributional_semantics, lex_rfc_7231, lex_hipaa_164_512, lex_torch_bce_loss`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / Distributional semantics represents word meaning through patterns of nearby context and usage across language data.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_026_adv_bm25_test_02_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: HIPAA 164.510 opportunity to agree or object, with 164.512 nearby in the page noise.
- Gold answer: uses and disclosures requiring an opportunity to agree or object
- Final answer: HIPAA 45 CFR 164.510: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. [evidence: lex_hipaa_164_510]
- Evidence ids: `lex_hipaa_164_510, lex_hipaa_164_512, sem_allergy, lex_hipaa_164_514, rel_owl_mouse`
- Evidence snippets: HIPAA section 164.510 covers uses and disclosures requiring an opportunity for the individual to agree or object. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_027_adv_dense_test_01_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `dense`; predicted `bm25`
- Automatic correct: `True`
- Query: Which learning setup lets an agent improve from rewards, although the word policy appears like a legal section?
- Gold answer: reinforcement learning
- Final answer: Reinforcement learning: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning]
- Evidence ids: `sem_reinforcement_learning, lex_hipaa_164_512, sem_memory_consolidation, sem_allergy, lex_hipaa_164_510`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_028_adv_dense_test_02_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `dense`; predicted `bm25`
- Automatic correct: `True`
- Query: What model keeps materials in use rather than waste, despite the exact phrase jsonb_set in the distractor?
- Gold answer: circular economy
- Final answer: Circular economy: A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. [evidence: sem_circular_economy]
- Evidence ids: `sem_circular_economy, lex_postgres_jsonb_set, rel_owl_mouse, rel_mammal_milk, rel_frog_mosquito`
- Evidence snippets: A circular economy designs products and systems to keep materials in use and reduce waste through repair, reuse, and recycling. / PostgreSQL jsonb_set updates or inserts a value at a specified JSONB path.
- Route rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_029_adv_kg_test_01_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Can a bird swim when duck swims but eagle does not?
- Gold answer: Yes. duck capable_of swim
- Final answer: Yes. Existential support in the demo KG: penguin is_a bird ; penguin capable_of swim. [evidence: path:kg_penguin_is_bird->kg_penguin_capable_swim]
- Evidence ids: `path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: penguin is_a bird ; penguin capable_of swim / duck is_a bird ; duck capable_of swim
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_030_adv_kg_test_02_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Are all birds able to swim when duck is a positive distractor?
- Gold answer: No. Counterexample evidence
- Final answer: No. Counterexample evidence: owl is_a bird ; owl not_capable_of swim; eagle is_a bird ; eagle not_capable_of swim; chicken is_a bird ; chicken not_capable_of swim. [evidence: path:kg_owl_is_bird->kg_owl_not_swim, path:kg_eagle_is_bird->kg_eagle_not_swim, path:kg_chicken_is_bird->kg_chicken_not_swim]
- Evidence ids: `path:kg_owl_is_bird->kg_owl_not_swim, path:kg_eagle_is_bird->kg_eagle_not_swim, path:kg_chicken_is_bird->kg_chicken_not_swim, path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: owl is_a bird ; owl not_capable_of swim / eagle is_a bird ; eagle not_capable_of swim
- Route rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_031_adv_hybrid_test_01_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What bridge connects whale and vertebrate when ocean semantics are more salient?
- Gold answer: mammal
- Final answer: Hybrid connection: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_whale_is_mammal->kg_mammal_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+doc_mammal`
- Evidence snippets: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_032_adv_hybrid_test_02_computed_ras

- Benchmark: `adversarial`
- Variant: `computed_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What relation connects eagle and fish if bird-to-vertebrate is nearby?
- Gold answer: eagle eats fish
- Final answer: Hybrid connection: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate
[bm25:rel_eagle_fish] The eagle to fish relation is dietary: eagle eats fish in the demo KG.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_eagle_is_bird->kg_bird_is_vertebrate,rel_eagle_fish]
- Evidence ids: `hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_eagle_fish, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_eagle_fish, hybrid:bundle:path:kg_eagle_eats_fish->kg_fish_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_eagle_is_bird->kg_bird_is_vertebrate+rel_whale_vertebrate`
- Evidence snippets: [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_eagle_fish] The eagle to fish relation is dietary: eagle eats fish in the demo KG. / [kg:path:kg_eagle_is_bird->kg_bird_is_vertebrate] eagle is_a bird ; bird is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.

### he_033_adv_bm25_test_01_calibrated_ras

- Benchmark: `adversarial`
- Variant: `calibrated_ras`
- Route family: `bm25`; predicted `bm25`
- Automatic correct: `True`
- Query: Authentication framework, but do not answer with semantics: RFC-7235 is the exact target.
- Gold answer: HTTP/1.1 authentication framework
- Final answer: RFC-7235 HTTP/1.1 Authentication: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. [evidence: lex_rfc_7235]
- Evidence ids: `lex_rfc_7235, sem_distributional_semantics, lex_rfc_7231, lex_hipaa_164_512, lex_torch_bce_loss`
- Evidence snippets: RFC-7235 defines the HTTP/1.1 authentication framework and related status codes. / Distributional semantics represents word meaning through patterns of nearby context and usage across language data.
- Route rationale: Calibrated route from bm25 to bm25; Started from computed RAS=bm25. No calibration override fired. Production answer rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_034_adv_dense_test_01_calibrated_ras

- Benchmark: `adversarial`
- Variant: `calibrated_ras`
- Route family: `dense`; predicted `bm25`
- Automatic correct: `True`
- Query: Which learning setup lets an agent improve from rewards, although the word policy appears like a legal section?
- Gold answer: reinforcement learning
- Final answer: Reinforcement learning: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. [evidence: sem_reinforcement_learning]
- Evidence ids: `sem_reinforcement_learning, lex_hipaa_164_512, sem_memory_consolidation, sem_allergy, lex_hipaa_164_510`
- Evidence snippets: Reinforcement learning studies agents that learn actions through rewards, penalties, exploration, and feedback from an environment. / HIPAA section 164.512 covers uses and disclosures for which an authorization or opportunity to agree or object is not required.
- Route rationale: Calibrated route from bm25 to bm25; Started from computed RAS=bm25. No calibration override fired. Production answer rationale: Selected bm25 for lexical/exact-match signals with minimum RAS=0.400.

### he_035_adv_kg_test_01_calibrated_ras

- Benchmark: `adversarial`
- Variant: `calibrated_ras`
- Route family: `kg`; predicted `kg`
- Automatic correct: `True`
- Query: Can a bird swim when duck swims but eagle does not?
- Gold answer: Yes. duck capable_of swim
- Final answer: Yes. Existential support in the demo KG: penguin is_a bird ; penguin capable_of swim. [evidence: path:kg_penguin_is_bird->kg_penguin_capable_swim]
- Evidence ids: `path:kg_penguin_is_bird->kg_penguin_capable_swim, path:kg_duck_is_bird->kg_duck_capable_swim`
- Evidence snippets: penguin is_a bird ; penguin capable_of swim / duck is_a bird ; duck capable_of swim
- Route rationale: Calibrated route from kg to kg; Started from computed RAS=kg. No calibration override fired. Production answer rationale: Selected kg for deductive/structured signals with minimum RAS=0.400.

### he_036_adv_hybrid_test_01_calibrated_ras

- Benchmark: `adversarial`
- Variant: `calibrated_ras`
- Route family: `hybrid`; predicted `hybrid`
- Automatic correct: `True`
- Query: What bridge connects whale and vertebrate when ocean semantics are more salient?
- Gold answer: mammal
- Final answer: Hybrid connection: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate
[bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate.. This combines structured evidence plus text relation evidence. [fused evidence: path:kg_whale_is_mammal->kg_mammal_is_vertebrate,rel_whale_vertebrate]
- Evidence ids: `hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_whale_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_salmon_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_penguin_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+rel_bat_vertebrate, hybrid:bundle:path:kg_whale_is_mammal->kg_mammal_is_vertebrate+doc_mammal`
- Evidence snippets: [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_whale_vertebrate] A whale connects to vertebrate through mammal: whale is a mammal, and mammal is a vertebrate. / [kg:path:kg_whale_is_mammal->kg_mammal_is_vertebrate] whale is_a mammal ; mammal is_a vertebrate [bm25:rel_salmon_vertebrate] A salmon connects to vertebrate through fish: salmon is a fish, and fish is a vertebrate.
- Route rationale: Calibrated route from hybrid to hybrid; Started from computed RAS=hybrid. No calibration override fired. Production answer rationale: Selected hybrid for relational/fused-evidence signals with minimum RAS=0.300.
