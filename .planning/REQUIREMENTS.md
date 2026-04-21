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

- [x] **INST-01**: Plugin installs and runs `/epistract:setup` without repo clone
- [x] **INST-02**: Pre-built domains (drug-discovery, contracts) available out of the box
- [x] **INST-03**: Plugin excludes demo data, test corpora, paper artifacts

### Documentation

- [x] **DOCS-01**: README reframed as framework with dual-path quick-start
- [x] **DOCS-02**: Architecture diagrams show three-layer separation
- [x] **DOCS-03**: Domain developer guide covers full adoption workflow
- [x] **DOCS-04**: Paper updated to framework framing

### Consumer Decoupling

- [x] **CONS-01**: Workbench in `examples/`, works with any domain
- [x] **CONS-02**: Telegram bot in `examples/`, works with any domain

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

### E2E Validation and Release (Phase 11)

- [x] **E2E-01**: Drug discovery scenarios (1-6) regenerate graphs with >=80% of V1 baseline entity/relation counts
- [x] **E2E-02**: Contract scenario regenerates graph with >=80% of V1 baseline (341 nodes, 663 edges)
- [ ] **E2E-03**: All extractions run through `/epistract:*` plugin commands (not raw scripts)
- [x] **E2E-04**: Both epistemic layers (molecular validation + conflict detection) produce correct output
- [x] **E2E-05**: Repeatable regression script exists (`make regression`) that diffs against baseline snapshots
- [ ] **E2E-06**: Graph visualizations are demonstration-ready for both domains
- [x] **REL-01**: Repository clean — no junk files, stale artifacts, or large binaries tracked
- [x] **REL-02**: .gitignore comprehensive — .planning/, worktrees, extraction output, contract data excluded
- [ ] **REL-03**: Feature branch synced, PR merged, v2.0.0 tagged and released on GitHub

## v3 Requirements (In Progress)

### Graph Fidelity & Honest Limits (Phase 12)

- [x] **FIDL-01**: Domain wizard reads sample documents via `sift_kg.ingest.reader.read_document` so PDF and other binary formats produce extracted text — not raw `%PDF-1.4` binary headers — for the 3-pass LLM schema discovery. Replaces `Path.read_text(errors="replace")` at `core/domain_wizard.py:63`. Graceful fallback when sift-kg is not installed.

### Extraction Pipeline Reliability (Phase 13)

- [x] **FIDL-02a**: Extractor agent prompt enforces the DocumentExtraction JSON contract — `document_id`, `entities`, `relations` declared as REQUIRED top-level fields; agents write ONLY via `build_extraction.py` (never direct Write); stdin-pipe retry on Bash permission denial; report failure in summary if both paths fail.
- [x] **FIDL-02b**: Post-extraction normalization runs automatically as Step 3.5 of `/epistract:ingest`, standardizing filenames, inferring `document_id`, deduping, coercing schema drift, and emitting `_normalization_report.json`. Pipeline aborts before graph build if pass-rate < `--fail-threshold` (default 0.95).
- [x] **FIDL-02c**: Extraction metadata is honest: `model_used` and `cost_usd` sourced from CLI flags / env var / `null` — never hardcoded. `build_extraction.py` validates payload against `DocumentExtraction` Pydantic model at write time; raises on malformed input.

### Chunk Overlap (Phase 14)

- [x] **FIDL-03**: Chunk boundaries emit sentence-aware overlap so entities and relations whose mentions straddle a 10,000-char chunk boundary reach the extractor. Overlap is the last 3 sentences of the previous chunk (capped at 1500 chars), produced by `blingfire.text_to_sentences_and_offsets`, emitted at every split point in `core/chunk_document.py` (`_split_at_paragraphs` sub-chunks, `_merge_small_sections` ARTICLE-boundary flushes, `_split_fixed` fallback). Each chunk JSON records `overlap_prev_chars`, `overlap_next_chars`, `is_overlap_region`, and an honest per-sub-chunk `char_offset`. `blingfire` is a required runtime dep; missing import raises loud with install hint. No CLI flag, no env var — pit-of-success default.

### Format Discovery Parity (Phase 15)

- [x] **FIDL-04**: `core/ingest_documents.discover_corpus` delegates to `sift_kg.ingest.reader` so every Kreuzberg-supported format (per backend `supported_extensions()`) is discovered without a hardcoded allowlist. Discovery remains pure extension-match. `.zip` archives excluded (breaks per-document provenance). Image extensions (`.png`, `.jpg`, `.tif`, etc.) gated by `ocr=True`. `triage.json` gains a `warnings[]` field per doc for post-discovery extraction failures (`extraction_failed`, `empty_text`, etc.). Loud ImportError when `sift_kg.ingest.reader` is missing — no silent fallback. `commands/ingest.md` format prose aligns with the runtime-resolved set.

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

### v2 (Mapped to Phases 6-11)

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
| E2E-01 | Phase 11 | 11-01, 11-03 | Pending |
| E2E-02 | Phase 11 | 11-01, 11-03 | Pending |
| E2E-03 | Phase 11 | 11-03 | Pending |
| E2E-04 | Phase 11 | 11-01, 11-03 | Pending |
| E2E-05 | Phase 11 | 11-01 | Pending |
| E2E-06 | Phase 11 | 11-03 | Pending |
| REL-01 | Phase 11 | 11-02 | Pending |
| REL-02 | Phase 11 | 11-02 | Pending |
| REL-03 | Phase 11 | 11-04 | Pending |

**v2 Coverage:**
- v2 requirements: 34 total (25 original + 9 Phase 11)
- Mapped to phases: 34
- Unmapped: 0

### v3 (Mapped to Phases 12+)

| Requirement | Phase | Plan | Status |
|-------------|-------|------|--------|
| FIDL-01 | Phase 12 | 12-01 | Complete |
| FIDL-02a | Phase 13 | 13-03 | Pending |
| FIDL-02b | Phase 13 | 13-02, 13-04 | Pending |
| FIDL-02c | Phase 13 | 13-01 | Pending |
| FIDL-03 | Phase 14 | 14-01, 14-02, 14-03, 14-04 | Complete |
| FIDL-04 | Phase 15 | 15-01, 15-02 | Complete |

---
*Requirements defined: 2026-03-29 (v1), 2026-04-02 (v2), 2026-04-04 (Phase 11)*
*Last updated: 2026-04-21 — FIDL-04 complete (Plan 15-01 discovery delegation + Plan 15-02 E2E acceptance + V2 floor guard)*
