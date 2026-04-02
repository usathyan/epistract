# Requirements: Epistract Cross-Domain KG Framework

**Defined:** 2026-03-29
**Core Value:** Extract knowledge, not information. Any corpus, any domain — plug in a schema, get a knowledge graph with epistemic layer.

## v1 Requirements (Complete)

All 24 requirements delivered. See v1 traceability below.

### Domain Configuration
- [x] **DCFG-01**: Pluggable domain configurations via YAML schema
- [x] **DCFG-02**: Contract domain ontology (11 entity types, 11 relation types)
- [x] **DCFG-03**: Domain-specific extraction prompt templates
- [x] **DCFG-04**: Biomedical pipeline backward compatibility

### Document Ingestion
- [x] **INGS-01** through **INGS-10**: PDF/XLS/EML ingestion, triage, OCR, metadata capture

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

- [ ] **ARCH-01**: Core pipeline in `core/`, domains in `domains/`, consumers in `examples/`
- [ ] **ARCH-02**: Core pipeline imports without domain-specific dependencies
- [ ] **ARCH-03**: New domain = new files in `domains/` only, no core changes

### Domain Wizard

- [ ] **WIZD-01**: `/epistract:domain` analyzes sample docs and proposes domain schema
- [ ] **WIZD-02**: Wizard generates complete domain package (domain.yaml + SKILL.md + epistemic rules)
- [ ] **WIZD-03**: Wizard proposes domain-appropriate epistemic layer rules
- [ ] **WIZD-04**: Generated domain works with standard pipeline without modification

### Standalone Install

- [ ] **INST-01**: Plugin installs and runs `/epistract:setup` without repo clone
- [ ] **INST-02**: Pre-built domains (drug-discovery, contracts) available out of the box
- [ ] **INST-03**: Plugin excludes demo data, test corpora, paper artifacts

### Documentation

- [ ] **DOCS-01**: README reframed as framework with dual-path quick-start
- [ ] **DOCS-02**: Architecture diagrams show three-layer separation
- [ ] **DOCS-03**: Domain developer guide covers full adoption workflow
- [ ] **DOCS-04**: Paper updated to framework framing

### Consumer Decoupling

- [ ] **CONS-01**: Workbench in `examples/`, works with any domain
- [ ] **CONS-02**: Telegram bot in `examples/`, works with any domain

### Cleanup

- [ ] **CLEAN-01**: Stale V1 artifacts removed
- [ ] **CLEAN-02**: V1 requirements marked complete

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

### v2 (Pending — updated during roadmap creation)

| Requirement | Phase | Plan | Status |
|-------------|-------|------|--------|
| ARCH-01 | — | — | Pending |
| ARCH-02 | — | — | Pending |
| ARCH-03 | — | — | Pending |
| WIZD-01 | — | — | Pending |
| WIZD-02 | — | — | Pending |
| WIZD-03 | — | — | Pending |
| WIZD-04 | — | — | Pending |
| INST-01 | — | — | Pending |
| INST-02 | — | — | Pending |
| INST-03 | — | — | Pending |
| DOCS-01 | — | — | Pending |
| DOCS-02 | — | — | Pending |
| DOCS-03 | — | — | Pending |
| DOCS-04 | — | — | Pending |
| CONS-01 | — | — | Pending |
| CONS-02 | — | — | Pending |
| CLEAN-01 | — | — | Pending |
| CLEAN-02 | — | — | Pending |

**v2 Coverage:**
- v2 requirements: 18 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 18

---
*Requirements defined: 2026-03-29 (v1), 2026-04-02 (v2)*
*Last updated: 2026-04-02 — V2 requirements added*
