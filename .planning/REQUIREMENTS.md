# Requirements: Epistract Cross-Domain KG Framework

**Defined:** 2026-03-29
**Core Value:** Every obligation, deadline, cost, and party relationship across 62+ vendor contracts must be extractable, queryable, and cross-referenced — so event organizers can spot conflicts, gaps, and risks before they become on-site problems.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Domain Configuration

- [x] **DCFG-01**: System supports pluggable domain configurations via YAML schema defining entity types, relation types, and extraction prompts per domain
- [x] **DCFG-02**: Contract domain ontology defines entity types (Party, Obligation, Deadline, Cost, Clause, Service, Venue) and relation types (OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS)
- [x] **DCFG-03**: Domain-specific extraction prompt templates guide Claude to extract contract-relevant entities and relations
- [x] **DCFG-04**: Existing biomedical extraction pipeline (Scenarios 1-6) continues to work unchanged — biomedical migration to domain config deferred to v2 after contract domain proves the pattern

### Document Ingestion

- [x] **INGS-01**: System ingests PDF contract documents from a user-provided local corpus path via CLI argument
- [x] **INGS-02**: System ingests XLS and EML files through the same Kreuzberg parsing pipeline as PDFs
- [x] **INGS-03**: Document metadata (filename, file_path, file_size_bytes, page_count, category, parse_type, text_length, parse_errors, extraction_readiness_score) is captured per document in triage.json
- [x] **INGS-04**: Documents are triaged as text-native, scanned, or mixed; scanned documents are auto-OCR'd via Kreuzberg's Tesseract backend
- [x] **INGS-05**: Each ingested document produces a per-document text file at `ingested/<doc_id>.txt` in the output directory, where doc_id is the sanitized lowercase filename
- [x] **INGS-06**: Document category is auto-detected from the top-level folder name under the corpus root (Hotel, PCC, AV, Catering, Security, EMS; unknown folders get "uncategorized")
- [x] **INGS-07**: Corpus directory is scanned recursively — all files in nested subdirectories are discovered
- [x] **INGS-08**: Parse failures (corrupted, encrypted, unsupported) are logged in triage.json and skipped; pipeline continues with remaining documents
- [x] **INGS-09**: A new standalone `scripts/ingest_documents.py` implements the ingestion pipeline following existing script patterns (sys.argv CLI, pathlib, Rich progress bar)
- [x] **INGS-10**: Development tests use small synthetic contract PDF fixtures in `tests/fixtures/` (no real contract data committed to repo)

### Entity Extraction

- [x] **EXTR-01**: System extracts contract entities (parties, obligations, deadlines, costs, clauses, services) from ingested documents using domain-configured prompts
- [x] **EXTR-02**: Entity resolution deduplicates variant references to the same real-world entity (e.g., "Aramark" / "ARAMARK" / "the Caterer" / "exclusive caterer")

### Graph Construction

- [x] **GRPH-01**: Extracted entities and relations are assembled into a NetworkX knowledge graph using the existing sift-kg pipeline
- [x] **GRPH-02**: Graph nodes carry domain-specific attributes (e.g., obligation deadlines, cost amounts, clause references)

### Cross-Reference Analysis

- [x] **XREF-01**: System links entities that appear across multiple contracts (same party, same date, same venue space)
- [x] **XREF-02**: System detects conflicts between contracts (contradictory terms, overlapping exclusive-use claims, incompatible schedules)
- [x] **XREF-03**: System identifies coverage gaps (expected obligations based on event requirements vs. what contracts actually cover)
- [x] **XREF-04**: System flags risks based on contract terms cross-referenced with dashboard planning data (budget mismatches, timeline conflicts, known venue constraints)

### Interactive Dashboard

- [x] **DASH-01**: Interactive web interface displays the contract knowledge graph with filterable views
- [x] **DASH-02**: Users can explore entities by type (parties, obligations, deadlines, costs) with tabular and graph views

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Telegram Integration

- **TELE-01**: Telegram bot accepts natural language questions about the contract KG
- **TELE-02**: Bot supports quick lookups (single entity/clause retrieval)
- **TELE-03**: Bot supports cross-contract reasoning queries
- **TELE-04**: Multi-turn conversation maintains KG context

### Enhanced Presentation

- **PRES-01**: Committee-oriented dashboard views (filter by committee responsibility area)
- **PRES-02**: Source drill-down from graph nodes to original contract text with page/section reference
- **PRES-03**: Source provenance tracking (which document, page, section each entity came from)

### Advanced Extraction

- **ADVX-01**: Seed registry pre-populated from Sample_Conference_Master.md for entity normalization
- **ADVX-02**: Structure-preserving extraction maintaining tables and clause hierarchy
- **ADVX-03**: Cross-reference-aware chunking for large contracts

### Biomedical Unification

- **BIOU-01**: Migrate biomedical extraction (Scenarios 1-6) to domain config pattern — biomedical becomes a YAML domain config like contracts

### Additional Domains

- **DOMN-01**: Regulatory compliance domain schema for clinical development use case

## Out of Scope

| Feature | Reason |
|---------|--------|
| Contract editing or authoring | Read-only analysis tool, not a CLM platform |
| Real-time contract monitoring | Batch extraction; contracts don't change frequently |
| Workflow/approval management | Dashboard project handles committee workflows |
| Contract template generation | Out of scope for analysis tool |
| Modifying biomedical scenarios 1-6 | Existing scenarios preserved as-is |
| Mobile app | Telegram (v2) serves as mobile interface |
| 2016 Atlantic City data as extraction source | Historical reference only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DCFG-01 | Phase 1 | Complete |
| DCFG-02 | Phase 1 | Complete |
| DCFG-03 | Phase 1 | Complete |
| DCFG-04 | Phase 1 | Complete |
| INGS-01 | Phase 2 | Complete |
| INGS-02 | Phase 2 | Complete |
| INGS-03 | Phase 2 | Complete |
| INGS-04 | Phase 2 | Complete |
| INGS-05 | Phase 2 | Complete |
| INGS-06 | Phase 2 | Complete |
| INGS-07 | Phase 2 | Complete |
| INGS-08 | Phase 2 | Complete |
| INGS-09 | Phase 2 | Complete |
| INGS-10 | Phase 2 | Complete |
| EXTR-01 | Phase 3 | Complete |
| EXTR-02 | Phase 3 | Complete |
| GRPH-01 | Phase 3 | Complete |
| GRPH-02 | Phase 3 | Complete |
| XREF-01 | Phase 4 | Complete |
| XREF-02 | Phase 4 | Complete |
| XREF-03 | Phase 4 | Complete |
| XREF-04 | Phase 4 | Complete |
| DASH-01 | Phase 5 | Complete |
| DASH-02 | Phase 5 | Complete |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 after roadmap creation*
