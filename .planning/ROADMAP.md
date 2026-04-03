# Roadmap: Epistract Cross-Domain KG Framework

## Milestones

- Complete **v1.0 STA Contract Extraction + Dashboard** - Phases 1-5 (shipped 2026-04-02)
- Current **v2.0 Framework Architecture & Domain Developer Experience** - Phases 6-9 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 STA Contract Extraction + Dashboard (Phases 1-5) - SHIPPED 2026-04-02</summary>

- [x] **Phase 1: Domain Configuration** - Pluggable domain config system with contract ontology, preserving biomedical backward compatibility
- [x] **Phase 2: Document Ingestion** - Multi-format document parsing and triage for 62+ contract files
- [x] **Phase 3: Entity Extraction and Graph Construction** - Extract contract entities, resolve duplicates, and build the knowledge graph
- [x] **Phase 4: Cross-Reference Analysis** - Detect conflicts, gaps, and risks across contracts (the killer feature)
- [x] **Phase 5: Interactive Dashboard** - Web interface for exploring the contract knowledge graph

### Phase 1: Domain Configuration
**Goal**: Epistract supports multiple domains via pluggable configuration, with a contract domain ontology ready for extraction
**Depends on**: Nothing (first phase)
**Requirements**: DCFG-01, DCFG-02, DCFG-03, DCFG-04
**Success Criteria** (what must be TRUE):
  1. Running `epistract` with `--domain contract` loads the contract domain schema (entity types, relation types, extraction prompts)
  2. Running `epistract` with `--domain biomedical` (or default) produces identical output to the current pipeline for Scenarios 1-6
  3. A new domain can be added by creating a YAML config and prompt template directory without modifying pipeline code
  4. Contract domain defines all 7 entity types (Party, Obligation, Deadline, Cost, Clause, Service, Venue) and 6 relation types (OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS)
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Domain resolution infrastructure (domain_resolver.py + tests)
- [x] 01-02-PLAN.md — Contract domain package (domain.yaml + SKILL.md + references/)
- [x] 01-03-PLAN.md — Pipeline integration (wire scripts, commands, agents to domain resolver)

### Phase 2: Document Ingestion
**Goal**: All 62+ contract documents are parsed, triaged, and ready for extraction
**Depends on**: Phase 1
**Requirements**: INGS-01, INGS-02, INGS-03, INGS-04, INGS-05, INGS-06, INGS-07, INGS-08, INGS-09, INGS-10
**Success Criteria** (what must be TRUE):
  1. Every PDF in the contract corpus produces parseable text output (with OCR fallback for scanned documents)
  2. XLS and EML files in the corpus are ingested alongside PDFs through the same pipeline entry point
  3. Each ingested document has metadata captured (filename, source folder category, file size, page count)
  4. A triage report classifies each document as text-native, scanned, or mixed, and records parse quality
**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Test fixtures and core ingestion module (corpus scanning, parsing, text output)
- [x] 02-02-PLAN.md — Integration tests, triage validation, and CLI hardening

### Phase 3: Entity Extraction and Graph Construction
**Goal**: Contract entities are extracted from all documents, deduplicated, and assembled into a queryable knowledge graph
**Depends on**: Phase 2
**Requirements**: EXTR-01, EXTR-02, GRPH-01, GRPH-02
**Success Criteria** (what must be TRUE):
  1. Each ingested document produces extracted entities (parties, obligations, deadlines, costs, clauses, services) using domain-configured prompts
  2. Variant references to the same entity are resolved to a single canonical node (e.g., "Aramark" / "ARAMARK" / "the Caterer" map to one node)
  3. The knowledge graph is queryable via NetworkX with domain-specific node attributes (deadline dates, cost amounts, clause references)
  4. Graph visualization renders the contract KG with distinguishable entity types and navigable relations
**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md — Clause-aware chunking, entity resolution, and test fixtures (EXTR-01, EXTR-02)
- [x] 03-02-PLAN.md — Graph construction wiring, community labeling, visualization verification (GRPH-01, GRPH-02)

### Phase 4: Cross-Reference Analysis
**Goal**: The system surfaces conflicts, gaps, and risks that span multiple contracts -- insights a spreadsheet cannot reveal
**Depends on**: Phase 3
**Requirements**: XREF-01, XREF-02, XREF-03, XREF-04
**Success Criteria** (what must be TRUE):
  1. Entities appearing in multiple contracts are linked and identifiable as cross-contract references (same party, same date, same venue space)
  2. Contradictions between contracts are detected and reported (e.g., overlapping exclusive-use claims, incompatible schedules, conflicting terms)
  3. Coverage gaps are identified where event requirements lack corresponding contract obligations
  4. Risks are flagged by cross-referencing contract terms with dashboard planning data (budget mismatches, timeline conflicts, known venue constraints)
**Plans:** 3 plans

Plans:
- [x] 04-01-PLAN.md — Domain-aware epistemic dispatch, biomedical extraction, conflict rules YAML (XREF-01, XREF-02)
- [x] 04-02-PLAN.md — Contract epistemic analysis module: cross-contract linking, conflict detection, gap analysis, risk scoring (XREF-01, XREF-02, XREF-03, XREF-04)
- [x] 04-03-PLAN.md — Pipeline integration: wire epistemic analysis into extract_contracts.py, --master-doc CLI support (XREF-01, XREF-02, XREF-03, XREF-04)

### Phase 5: Interactive Dashboard
**Goal**: Sample Contract Analysis Workbench — a FastAPI-powered web application with chat-first interface backed by Claude Sonnet, interactive vis.js knowledge graph browser, and source document viewer for committee chairs
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02
**Success Criteria** (what must be TRUE):
  1. A web interface displays the contract knowledge graph with interactive filtering by vendor, date range, and risk level
  2. Users can switch between tabular views (obligations, deadlines, costs) and graph visualization of the same data
**Plans:** 4 plans
**UI hint**: yes

Plans:
- [x] 05-01-PLAN.md — Domain schema expansion (COMMITTEE, PERSON, EVENT, STAGE, ROOM) + synthetic test fixtures
- [x] 05-02-PLAN.md — FastAPI backend with data loader, graph API, source API, CLI launcher, and tests
- [x] 05-03-PLAN.md — Chat SSE endpoint with Claude Sonnet streaming and SME persona system prompt
- [x] 05-04-PLAN.md — Frontend SPA: HTML shell, CSS design system, chat/graph/sources panel modules

</details>

### v2.0 Framework Architecture & Domain Developer Experience (In Progress)

**Milestone Goal:** Transform epistract into a self-sufficient framework where a domain developer can install, create a new domain via wizard, and run the full pipeline -- without touching core code.

- [ ] **Phase 6: Repo Reorganization and Cleanup** - Restructure codebase into core/domains/examples with clean domain-agnostic imports
- [ ] **Phase 7: Testing Framework** - Comprehensive regression + integration test suite ensuring V1 parity and V2 production readiness
- [ ] **Phase 8: Domain Creation Wizard** - Auto-generate domain packages from sample documents via /epistract:domain
- [ ] **Phase 9: Consumer Decoupling and Standalone Install** - Decouple consumers into examples/, enable plugin install without repo clone
- [ ] **Phase 10: Documentation Refresh** - README, architecture diagrams, domain developer guide, and paper reframed as framework

## Phase Details

### Phase 6: Repo Reorganization and Cleanup
**Goal**: Codebase is cleanly separated into domain-agnostic core, domain configurations, and example consumers -- with stale V1 artifacts removed
**Depends on**: Phase 5 (V1 complete)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, CLEAN-01, CLEAN-02
**Success Criteria** (what must be TRUE):
  1. Repository has `core/`, `domains/`, and `examples/` top-level directories with extraction engine, graph builder, and epistemic layer in `core/`
  2. `import epistract.core` works without any domain-specific dependencies -- no contract or biomedical imports at the core level
  3. Adding a new domain requires only creating files under `domains/<name>/` -- zero modifications to anything in `core/`
  4. Stale V1 planning artifacts, scratch files, and orphaned outputs are removed from the repo
  5. All V1 requirements in REQUIREMENTS.md are marked complete with phase references
**Plans**: 3 plans

Plans:
- [x] 06-01-PLAN.md — Create core/, domains/, examples/ structure and move all files (ARCH-01, ARCH-03)
- [x] 06-02-PLAN.md — Update test imports and verify core import independence (ARCH-02)
- [x] 06-03-PLAN.md — Remove stale V1 artifacts and mark requirements complete (CLEAN-01, CLEAN-02)

### Phase 7: Testing Framework
**Goal**: Comprehensive test suite locks down V1 regression coverage and validates every V2 capability from install through extraction -- production-ready quality gate
**Depends on**: Phase 6
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):
  1. V1 regression suite passes -- ingestion, extraction, graph build, epistemic analysis, community labeling all produce correct output against reorganized codebase
  2. Every `/epistract:*` command (setup, ingest, build, query, export, view, validate, epistemic, ask, dashboard) has an integration test that runs without error
  3. Every skill and agent produces valid output format against test fixtures
  4. End-to-end pipeline test proves the full lifecycle: install → domain selection → ingest → extract → graph build → epistemic analysis → export
  5. KG provenance tests (32 existing) pass against the reorganized codebase
  6. Both drug-discovery and contract domains produce valid graphs through the same pipeline entry point
**Plans**: 3 plans

Plans:
- [ ] 07-01-PLAN.md — Test infrastructure, fixtures, and unit tier (conftest.py, pyproject.toml, markers, schema validation)
- [ ] 07-02-PLAN.md — Integration tests for command entry points, KG provenance conversion, cross-domain verification
- [ ] 07-03-PLAN.md — E2E pipeline tests and Makefile tiered test targets

### Phase 8: Domain Creation Wizard
**Goal**: A domain developer can point the wizard at sample documents and get a complete, working domain package generated automatically
**Depends on**: Phase 7 (needs test infrastructure to validate generated domains)
**Requirements**: WIZD-01, WIZD-02, WIZD-03, WIZD-04
**Success Criteria** (what must be TRUE):
  1. Running `/epistract:domain` with a path to sample documents produces a proposed entity/relation schema based on document analysis
  2. The wizard generates a complete domain package -- domain.yaml, SKILL.md, and epistemic rules -- ready to use without manual editing
  3. The wizard proposes epistemic layer rules appropriate to the domain (e.g., contradiction patterns, confidence heuristics, gap detection logic)
  4. A domain generated by the wizard works end-to-end with the standard pipeline: ingest, extract, build graph, run epistemic analysis -- no code changes needed
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 9: Consumer Decoupling and Standalone Install
**Goal**: Framework installs cleanly as a standalone tool, consumers are decoupled examples, and pre-built domains are available out of the box
**Depends on**: Phase 6
**Requirements**: CONS-01, CONS-02, INST-01, INST-02, INST-03
**Success Criteria** (what must be TRUE):
  1. Workbench lives in `examples/` and works with any domain's graph output -- not hardcoded to contracts
  2. Telegram bot lives in `examples/` and works with any domain's graph output -- not hardcoded to contracts
  3. Running `/epistract:setup` on a fresh machine installs the framework without needing to clone the repo or download demo data
  4. Pre-built domains (drug-discovery, contracts) are available immediately after install without additional setup
  5. Plugin package excludes demo data, test corpora, and paper artifacts -- clean install footprint
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] TBD

### Phase 10: Documentation Refresh
**Goal**: All documentation presents epistract as a domain-agnostic framework with clear paths for both using pre-built domains and creating new ones
**Depends on**: Phase 8, Phase 9
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. README leads with framework identity and offers dual-path quick-start: "Use a pre-built domain" or "Create your own domain"
  2. Architecture diagrams show three-layer separation (core pipeline, domain configs, example consumers) and the two-layer KG (brute facts + epistemic)
  3. Domain developer guide walks through the full workflow: install, create domain via wizard, ingest documents, explore graph, analyze with epistemic layer
  4. Paper (title, abstract, architecture sections) is reframed around the framework -- not the STA use case
**Plans**: TBD

Plans:
- [ ] TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 6 -> 7 -> 8 -> 9 -> 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Domain Configuration | v1.0 | 3/3 | Complete | 2026-03-29 |
| 2. Document Ingestion | v1.0 | 2/2 | Complete | 2026-03-29 |
| 3. Entity Extraction and Graph Construction | v1.0 | 2/2 | Complete | 2026-03-29 |
| 4. Cross-Reference Analysis | v1.0 | 3/3 | Complete | 2026-03-31 |
| 5. Interactive Dashboard | v1.0 | 4/4 | Complete | 2026-04-02 |
| 6. Repo Reorganization and Cleanup | v2.0 | 0/3 | Planning | - |
| 7. Testing Framework | v2.0 | 0/3 | Planning | - |
| 8. Domain Creation Wizard | v2.0 | 0/? | Not started | - |
| 9. Consumer Decoupling and Standalone Install | v2.0 | 0/? | Not started | - |
| 10. Documentation Refresh | v2.0 | 0/? | Not started | - |
