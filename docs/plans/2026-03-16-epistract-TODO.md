# Epistract TODO

## Documentation
- [ ] Convert all ASCII art diagrams in README.md, DEVELOPER.md, and design specs to Mermaid diagrams (or render with `beautiful-mermaid` for SVG/ASCII output)
- [ ] Diagrams to convert:
  - [ ] DEVELOPER.md: main architecture diagram
  - [ ] docs/epistract-plugin-design.md: data flow pipeline diagram
  - [ ] docs/epistract-plugin-design.md: Claude-as-extractor adapter diagram
  - [ ] docs/drug-discovery-domain-spec.md: Central Dogma Chain
  - [ ] docs/drug-discovery-domain-spec.md: Protein Function Chain
  - [ ] docs/drug-discovery-domain-spec.md: Drug Action Chain
  - [ ] docs/drug-discovery-domain-spec.md: Hybrid Extraction Architecture (Phase 1/Phase 2)
  - [ ] docs/drug-discovery-domain-spec.md: Validation Pipeline system diagram

## Phase 1 — Extraction + KG + Visualization
- [ ] Implement plugin commands
- [ ] Implement drug-discovery-extraction skill (SKILL.md)
- [ ] Implement domain.yaml
- [ ] Implement extraction adapter scripts
- [ ] Implement molecular validation scripts
- [ ] Implement extractor and validator agents
- [ ] End-to-end test with real PubMed abstracts

## Phase 2 — Enrichment, Name Resolution, Neo4j + Vector RAG

### Chemical Name Resolution (IUPAC → SMILES cascade)
> Plan: `.claude/plans/goofy-wibbling-feigenbaum.md`

- [ ] Tier 0: Bundled drug cache (auto-generated from ChEMBL, ~2000 drugs)
  - [ ] `scripts/generate_drug_cache.py` — pulls approved drugs with SMILES from ChEMBL
  - [ ] `skills/drug-discovery-extraction/validation-scripts/drug_cache.json` — output cache
- [ ] Tier 1: OPSIN local JAR (systematic IUPAC names, offline)
  - [ ] `resolve_names.py` — subprocess call to `java -jar opsin.jar -osmi` (no REST!)
  - [ ] Document JVM requirement; skip gracefully if no JVM
  - [ ] Download JAR in `setup.sh` (optional, ~8MB from Maven Central)
- [ ] Tier 2: PubChem PUG REST (common names, CAS — opt-in only)
  - [ ] `--allow-network` flag required; all calls logged
- [ ] Tier 3: Structured parse error → LLM agent for retry
  - [ ] Capture OPSIN positional parse errors → `resolution_failures.json`
  - [ ] Validator agent reads failures and attempts LLM-assisted correction
- [ ] Core resolver module: `skills/drug-discovery-extraction/validation-scripts/resolve_names.py`
- [ ] Wire into `scripts/validate_molecules.py` with `--resolve-names` / `--allow-network` flags
- [ ] Unit + integration tests (cache hit, OPSIN subprocess, network isolation, cascade ordering)

### External Enrichment
- [ ] PubChem/ChEMBL/UniProt API lookups adding nodes from external knowledge bases
- [ ] Cross-reference resolution (UniChem, CAS → PubChem CID)

### Graph-Grounded Conversational RAG
- [ ] `/epistract-ask` command — load `graph_data.json`, translate NL to graph traversals
- [ ] Session-persistent graph memory (graph stays loaded after ingest)
- [ ] Graph-grounded answers (responses cite KG facts, not training data)
- [ ] Cross-session persistence (load previously built graph into new session)

### Epistemic Analysis (Super Domain Layer)
> Analysis: `docs/analysis/super-domain-epistemic-analysis.md`
> Addendum: `docs/analysis/super-domain-addendum.md`
> Reference: Eric Little, [LinkedIn post](https://www.linkedin.com/posts/eric-little-71b2a0b_pleased-to-announce-that-i-will-be-speaking-activity-7442581339096313856-wEFc), KG Conference NYC, May 2026

- [x] Empirical analysis of epistemic patterns across 6 scenarios
- [x] POC script: `scripts/label_epistemic.py` (validated against all 6 graphs)
- [x] Command: `/epistract-epistemic` (`commands/epistemic.md`)
- [x] Decision doc: communities complement Super Domains, don't replace them
- [ ] Add extraction-time tagging (`epistemic_status`, `claim_group` fields in extractor prompt)
- [ ] Improve contradiction detection (opposing allele effects, not just positive/negative polarity)
- [ ] Add temporal scoping (development_stage transitions → temporal Super Domain layers)
- [ ] Integrate claims_layer.json into `/epistract-view` visualization
- [ ] Incorporate Eric Little's feedback after KG Conference discussion

### Neo4j + Vector RAG
- [ ] Neo4j exporter (MERGE-based, idempotent)
- [ ] Vector embeddings (sentence-transformers or Neo4j built-in)
- [ ] Combined graph+vector RAG query layer
- [ ] Production query commands

### Documentation
- [ ] Update DEVELOPER.md Phase 2 section with name resolution pipeline
- [ ] Update architecture diagram with resolver module
