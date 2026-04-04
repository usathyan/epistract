# Requirements: Epistract Cross-Domain KG Framework

**Defined:** 2026-03-29
**Core Value:** Extract knowledge, not information. Any corpus, any domain — plug in a schema, get a knowledge graph with epistemic layer.

## v1 Requirements (Complete)

All 24 requirements delivered across Phases 1-5. Shipped 2026-04-02.
See v1 traceability below.

### Domain Configuration
- [x] **DCFG-01**: Pluggable domain configurations via YAML schema
- [x] **DCFG-02**: Contract domain ontology (11 entity types, 11 relation types)
- [x] **DCFG-03**: Domain-specific extraction prompt templates
- [x] **DCFG-04**: Biomedical pipeline backward compatibility

### Document Ingestion
- [x] **INGS-01**: PDF document ingestion (60 files)
- [x] **INGS-02**: XLS document ingestion
- [x] **INGS-03**: EML document ingestion
- [x] **INGS-04**: Document triage and prioritization
- [x] **INGS-05**: OCR for scanned documents
- [x] **INGS-06**: Metadata capture (dates, parties, amounts)
- [x] **INGS-07**: Large document handling (12-31 MB PDFs)
- [x] **INGS-08**: Document deduplication
- [x] **INGS-09**: Chunk-based extraction for large documents
- [x] **INGS-10**: Ingestion progress reporting

### Entity Extraction
- [x] **EXTR-01**: Contract entity extraction using domain prompts
- [x] **EXTR-02**: Entity resolution and deduplication

### Graph Construction
- [x] **GRPH-01**: NetworkX knowledge graph via sift-kg
- [x] **GRPH-02**: Domain-specific node attributes

### Cross-Reference Analysis
- [x] **XREF-01**: Cross-contract entity linking
- [x] **XREF-02**: Conflict detection (53 conflicts found)
- [x] **XREF-03**: Coverage gap analysis
- [x] **XREF-04**: Risk flagging

### Interactive Dashboard
- [x] **DASH-01**: Interactive web interface with filterable graph
- [x] **DASH-02**: Entity exploration by type (tabular + graph)

## v2 Requirements

### Repo Architecture

- [x] **ARCH-01**: Core pipeline in `core/`, domains in `domains/`, consumers in `examples/`
- [x] **ARCH-02**: Core pipeline imports without domain-specific dependencies
- [x] **ARCH-03**: New domain = new files in `domains/` only, no core changes

### Domain Wizard

- [x] **WIZD-01**: `/epistract:domain` analyzes sample docs and proposes domain schema
- [x] **WIZD-02**: Wizard generates complete domain package (domain.yaml + SKILL.md + epistemic rules)
- [x] **WIZD-03**: Wizard proposes domain-appropriate epistemic layer rules
- [x] **WIZD-04**: Generated domain works with standard pipeline without modification

### Standalone Install

- [ ] **INST-01**: Plugin installs and runs `/epistract:setup` without repo clone
- [x] **INST-02**: Pre-built domains (drug-discovery, contracts) available out of the box
- [ ] **INST-03**: Plugin excludes demo data, test corpora, paper artifacts

### Documentation

- [ ] **DOCS-01**: README reframed as framework with dual-path quick-start
- [ ] **DOCS-02**: Architecture diagrams show three-layer separation
- [ ] **DOCS-03**: Domain developer guide covers full adoption workflow
- [ ] **DOCS-04**: Paper updated to framework framing

### Consumer Decoupling

- [x] **CONS-01**: Workbench in `examples/`, works with any domain
- [ ] **CONS-02**: Telegram bot in `examples/`, works with any domain

### Testing Framework

- [x] **TEST-01**: V1 regression suite — every V1 capability (ingestion, extraction, graph build, epistemic analysis, community labeling) has automated tests that pass against the reorganized codebase
- [x] **TEST-02**: Command coverage — every `/epistract:*` command (setup, ingest, build, query, export, view, validate, epistemic, ask, dashboard) has an integration test verifying it runs without error
- [x] **TEST-03**: Skill coverage — every skill (drug-discovery-extraction, contract-extraction, domain wizard) has tests verifying correct output format
- [x] **TEST-04**: Agent coverage — extractor and validator agents produce valid DocumentExtraction JSON against test fixtures
- [x] **TEST-05**: End-to-end pipeline test — from fresh install through domain selection, document ingestion, extraction, graph build, epistemic analysis, and export — single test proves the full lifecycle
- [x] **TEST-06**: KG provenance regression — the 32 existing provenance tests (chat→graph→source tracing) pass against the reorganized codebase
- [x] **TEST-07**: Cross-domain verification — both drug-discovery and contract domains produce valid graphs through the same pipeline entry point

### Cleanup

- [x] **CLEAN-01**: Stale V1 artifacts removed
- [x] **CLEAN-02**: V1 requirements marked complete

## Deferred (V3)

- **BIOU-01**: Biomedical domain migrated to V2 architecture with full backward compatibility
- **DOMN-01**: Domain registry — discover and load domains dynamically

## Out of Scope

| Feature | Reason |
|---------|--------|
| Contract editing or authoring | Read-only analysis tool |
| Real-time contract monitoring | Batch extraction |
| New domain implementations | Wizard enables them; V2 doesn't ship new domains beyond existing two |
| Cloud deployment / Vercel | Local-first tool |
| Mobile app | Telegram serves as mobile interface |
| Modifying biomedical scenarios 1-6 | V3 concern |

## Traceability

### v1 (Complete)

| Requirement | Phase | Status |
|-------------|-------|--------|
| DCFG-01..04 | Phase 1 | Complete |
| INGS-01..10 | Phase 2 | Complete |
| EXTR-01..02 | Phase 3 | Complete |
| GRPH-01..02 | Phase 3 | Complete |
| XREF-01..04 | Phase 4 | Complete |
| DASH-01..02 | Phase 5 | Complete |

### v2 (Mapped to Phases 6-10)

| Requirement | Phase | Plan | Status |
|-------------|-------|------|--------|
| ARCH-01 | Phase 6 | 06-01 | Complete |
| ARCH-02 | Phase 6 | 06-02 | Complete |
| ARCH-03 | Phase 6 | 06-01 | Complete |
| CLEAN-01 | Phase 6 | 06-03 | Complete |
| CLEAN-02 | Phase 6 | 06-03 | Complete |
| TEST-01 | Phase 7 | — | Pending |
| TEST-02 | Phase 7 | — | Pending |
| TEST-03 | Phase 7 | — | Pending |
| TEST-04 | Phase 7 | — | Pending |
| TEST-05 | Phase 7 | — | Pending |
| TEST-06 | Phase 7 | — | Pending |
| TEST-07 | Phase 7 | — | Pending |
| WIZD-01 | Phase 8 | — | Pending |
| WIZD-02 | Phase 8 | — | Pending |
| WIZD-03 | Phase 8 | — | Pending |
| WIZD-04 | Phase 8 | — | Pending |
| CONS-01 | Phase 9 | — | Pending |
| CONS-02 | Phase 9 | — | Pending |
| INST-01 | Phase 9 | — | Pending |
| INST-02 | Phase 9 | — | Pending |
| INST-03 | Phase 9 | — | Pending |
| DOCS-01 | Phase 10 | — | Pending |
| DOCS-02 | Phase 10 | — | Pending |
| DOCS-03 | Phase 10 | — | Pending |
| DOCS-04 | Phase 10 | — | Pending |

**v2 Coverage:**
- v2 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-03-29 (v1), 2026-04-02 (v2)*
*Last updated: 2026-04-02 — V2 roadmap mapped*
