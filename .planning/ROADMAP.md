# Roadmap: Epistract Cross-Domain KG Framework

## Overview

This roadmap transforms epistract from a biomedical-only extraction tool into a cross-domain knowledge graph framework, proving the pattern with Scenario 7: extracting structured knowledge from 62+ Sample 2026 event contracts. The journey moves from domain abstraction, through document ingestion and extraction, to graph construction, cross-reference analysis (the differentiating value), and finally an interactive dashboard for committee chairs.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Domain Configuration** - Pluggable domain config system with contract ontology, preserving biomedical backward compatibility
- [ ] **Phase 2: Document Ingestion** - Multi-format document parsing and triage for 62+ contract files
- [ ] **Phase 3: Entity Extraction and Graph Construction** - Extract contract entities, resolve duplicates, and build the knowledge graph
- [ ] **Phase 4: Cross-Reference Analysis** - Detect conflicts, gaps, and risks across contracts (the killer feature)
- [ ] **Phase 5: Interactive Dashboard** - Web interface for exploring the contract knowledge graph

## Phase Details

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
**Plans:** 2/2 plans

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
- [ ] 04-03-PLAN.md — Pipeline integration: wire epistemic analysis into extract_contracts.py, --master-doc CLI support (XREF-01, XREF-02, XREF-03, XREF-04)

### Phase 5: Interactive Dashboard
**Goal**: Sample Contract Analysis Workbench — a FastAPI-powered web application with chat-first interface backed by Claude Sonnet, interactive vis.js knowledge graph browser, and source document viewer for committee chairs
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02
**Success Criteria** (what must be TRUE):
  1. A web interface displays the contract knowledge graph with interactive filtering by vendor, date range, and risk level
  2. Users can switch between tabular views (obligations, deadlines, costs) and graph visualization of the same data
**Plans:** 0/4 plans executed
**UI hint**: yes

Plans:
- [x] 05-01-PLAN.md — Domain schema expansion (COMMITTEE, PERSON, EVENT, STAGE, ROOM) + synthetic test fixtures
- [x] 05-02-PLAN.md — FastAPI backend with data loader, graph API, source API, CLI launcher, and tests
- [ ] 05-03-PLAN.md — Chat SSE endpoint with Claude Sonnet streaming and SME persona system prompt
- [ ] 05-04-PLAN.md — Frontend SPA: HTML shell, CSS design system, chat/graph/sources panel modules

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Domain Configuration | 3/3 | Complete | 2026-03-29 |
| 2. Document Ingestion | 2/2 | Complete | 2026-03-29 |
| 3. Entity Extraction and Graph Construction | 2/2 | Complete | 2026-03-29 |
| 4. Cross-Reference Analysis | 1/3 | In Progress | - |
| 5. Interactive Dashboard | 0/4 | Planned    |  |

## Backlog

### Phase 999.1: V2 Documentation & Artifacts Refresh (BACKLOG)

**Goal:** Update all downstream artifacts to reflect epistract's reframing as a domain-agnostic knowledge graph framework. Includes: paper (title, abstract, architecture framing), README reposition, architecture diagrams (two-layer KG, domain-pluggable system), branding update, demo video for cross-domain capability.
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)
