# Phase 3: Entity Extraction and Graph Construction - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 03-entity-extraction-and-graph-construction
**Areas discussed:** Extraction strategy, Entity resolution, Graph attributes, Quality & testing

---

## Extraction Strategy

### Chunking Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Clause-aware chunking | Split at section/clause boundaries. Keeps legal context intact. | :heavy_check_mark: |
| Fixed ~10K chunks | Reuse existing ~10K character chunking from biomedical. | |
| Whole-document | Feed entire ingested text to Claude at once. | |

**User's choice:** Clause-aware chunking
**Notes:** None

### Agent Dispatch

| Option | Description | Selected |
|--------|-------------|----------|
| Parallel agents (4+ concurrent) | Existing pattern, one agent per document. | :heavy_check_mark: |
| Batch sequential | Process one at a time. | |
| Tiered by readiness score | Prioritize by triage.json score. | |

**User's choice:** Parallel agents (4+ concurrent)
**Notes:** None

### Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| One merged per document | Combine all chunk extractions into single JSON. | :heavy_check_mark: |
| One per chunk, merge later | Store chunk-level JSONs separately. | |

**User's choice:** One merged per document
**Notes:** None

### Prompt Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Full SKILL.md context | Pass entire contract SKILL.md to each agent. | :heavy_check_mark: |
| Minimal: types + hints only | Extract just entity_types and extraction_hints. | |

**User's choice:** Full SKILL.md context
**Notes:** None

### Chunker Implementation

| Option | Description | Selected |
|--------|-------------|----------|
| Python pre-processor | New script that splits at clause boundaries before agent dispatch. | :heavy_check_mark: |
| Agent handles chunking | Extraction agent reads full text and splits internally. | |
| Hybrid | Python coarse split, agent refines. | |

**User's choice:** Python pre-processor
**Notes:** None

### Cross-Reference Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Extract as-is, resolve in graph | Extract reference as attribute, resolve during graph construction. | :heavy_check_mark: |
| Include neighboring context | Include overlap or referenced sections in chunks. | |
| You decide | Claude's discretion. | |

**User's choice:** Extract as-is, resolve in graph
**Notes:** None

### Agent Reuse

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse extractor.md | Existing agent is already domain-aware. | :heavy_check_mark: |
| New contract-specific agent | Create agents/contract-extractor.md. | |
| Extend extractor.md | Add contract hints while keeping generic. | |

**User's choice:** Reuse extractor.md
**Notes:** None

### Extraction Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All 62+ documents | Full extraction in one pass. | |
| Representative subset first | Start with 5-10, validate, then rest. | |
| Category-by-category | Process one category at a time. | |

**User's choice:** Other (free text)
**Notes:** User clarified: "Full 62 is just this corpus (Scenario 7). This number depends on the scenario, corpus, and domain." Pipeline should be corpus-agnostic.

### Chunk Storage

| Option | Description | Selected |
|--------|-------------|----------|
| Intermediate files | Write chunks to disk. Allows re-running without re-chunking. | :heavy_check_mark: |
| In-memory only | Chunker returns list, passed to agent dispatch. | |

**User's choice:** Intermediate files
**Notes:** None

### Chunker Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Fall back to fixed-size chunks | Revert to ~10K at paragraph boundaries when no structure found. | :heavy_check_mark: |
| Treat entire doc as one chunk | Pass whole text if no structure. | |
| You decide | Claude's discretion. | |

**User's choice:** Fall back to fixed-size chunks
**Notes:** None

---

## Entity Resolution

### Deduplication Approach

| Option | Description | Selected |
|--------|-------------|----------|
| String similarity (SemHash) | Fuzzy matching with normalization. | |
| LLM-assisted resolution | Second Claude pass reviews all entities. | |
| Seed registry + fuzzy match | Pre-populate from contract preambles. | |
| Hybrid | Seed + SemHash + LLM fallback. | |

**User's choice:** Other (free text)
**Notes:** User redirected the question: "The contract extract should be a research on what other git repos and applications and best practices exist for reviewing contracts, and analyzing them from auditability, estimations, predictions and analysis tools. Let's look at requirements and see if there are ontologies and taxonomies already available. Shouldn't that be similar to how we do biological?" This is a fundamental insight -- entity resolution should leverage established domain ontologies, just like biomedical uses HGNC, MeSH, DrugBank.

### Research Scope

| Option | Description | Selected |
|--------|-------------|----------|
| General contract analysis | Research legal ontologies and tools broadly. | |
| Event/venue contracts specifically | Focus narrowly on event planning. | |
| Both: general + event examples | General ontologies validated with event examples. | :heavy_check_mark: |

**User's choice:** Both: general framework, event examples
**Notes:** None

### Ontology Integration

| Option | Description | Selected |
|--------|-------------|----------|
| Adapt to domain.yaml | Map external ontology into existing YAML schema. | :heavy_check_mark: |
| Use external ontology directly | Adopt native format, adapt sift-kg. | |
| Reference only | Use as naming reference, keep own type system. | |

**User's choice:** Adapt to domain.yaml
**Notes:** None

### Resolution Baseline

| Option | Description | Selected |
|--------|-------------|----------|
| SemHash baseline + research upgrade | Implement SemHash now, upgrade after research. | :heavy_check_mark: |
| Wait for research | Don't implement until researcher investigates. | |
| Extraction-time normalization only | Rely on prompt quality for normalization. | |

**User's choice:** SemHash baseline + research upgrade
**Notes:** None

### Alias Extraction

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, extract aliases | Capture formal name AND defined-term alias. | :heavy_check_mark: |
| No, resolve post-extraction | Extract whatever name appears, resolve later. | |
| You decide | Claude's discretion. | |

**User's choice:** Yes, extract aliases
**Notes:** None

---

## Graph Attributes

### Attribute Richness

| Option | Description | Selected |
|--------|-------------|----------|
| Structured attributes | Typed attributes per entity type. | :heavy_check_mark: |
| Minimal: name + type + context | Basics only, details in free text. | |
| You decide | Claude's discretion. | |

**User's choice:** Structured attributes
**Notes:** None

### Edge Provenance

| Option | Description | Selected |
|--------|-------------|----------|
| Clause-level provenance | Each relation stores source contract and section. | :heavy_check_mark: |
| Document-level only | Track source document but not section. | |
| Full: document + section + page | Maximum provenance. | |

**User's choice:** Clause-level provenance
**Notes:** None

### Cost Storage

| Option | Description | Selected |
|--------|-------------|----------|
| Both: parsed + original | Parsed numeric for filtering + original text for audit. | :heavy_check_mark: |
| Parsed numeric only | Structured numbers only. | |
| Original text only | Contract language as-is. | |

**User's choice:** Both: parsed + original
**Notes:** None

---

## Quality & Testing

### Validation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Schema validation + confidence | Validate JSON structure and confidence ranges. | |
| LLM-based review pass | Second Claude pass for hallucination/miss detection. | |
| Both | Schema + LLM review. | |
| You decide | Claude's discretion. | :heavy_check_mark: |

**User's choice:** You decide
**Notes:** None

### Test Data

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic contract fixtures | Extend tests/fixtures/ with small contracts. | :heavy_check_mark: |
| Real contract subset | Use 2-3 real contracts. | |
| Both | Synthetic for unit, real for integration. | |

**User's choice:** Synthetic contract fixtures
**Notes:** None

### Visualization Testing

| Option | Description | Selected |
|--------|-------------|----------|
| Basic viz in Phase 3 | Verify pyvis HTML viewer renders contract graph. | :heavy_check_mark: |
| Defer to Phase 5 | Skip visualization testing. | |
| You decide | Claude's discretion. | |

**User's choice:** Basic viz in Phase 3
**Notes:** None

---

## Claude's Discretion

- Validation strategy for extraction quality
- Internal design of clause-aware chunker
- Exact attribute schemas beyond types specified
- SemHash configuration parameters
- Merged extraction structure from chunk-level outputs

## Deferred Ideas

None -- discussion stayed within phase scope.
