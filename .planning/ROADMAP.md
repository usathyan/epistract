# Roadmap: Epistract Cross-Domain KG Framework

## Milestones

- Complete **v1.0 STA Contract Extraction + Dashboard** - Phases 1-5 (shipped 2026-04-02)
- Current **v2.0 Framework Architecture & Domain Developer Experience** - Phases 6-11 (in progress)

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
- [x] **Phase 10: Documentation Refresh** - README, architecture diagrams, domain developer guide, and paper reframed as framework (completed 2026-04-04)
- [x] **Phase 11: End-to-End Scenario Validation and v2.0 Release** - Regenerate all graphs, validate both use cases, repeatable regression suite, git sync + push v2.0 (completed 2026-04-17)

### v3.0 Graph Fidelity & Honest Limits (Planned)

**Milestone Goal:** Close the silent graph-quality ceilings surfaced during V2 review and fix the 5 bugs + 10 enhancements from the axmp-compliance custom-domain build. Make the extracted graph match what the README promises: wizard reads real documents (not binary), no dropped extractions during build, no dropped entities at chunk boundaries, every supported format actually discovered, domain awareness propagates to every consumer. Document post-fix limits in the README so users know what they are getting.

Phase priority is **blocking-ness first, silent quality second, polish last**. See `.planning/phases/12-*/SCOPE-ADDITIONS.md` for the full item analysis.

- [x] **Phase 12: Fix wizard PDF binary read (Bug 3)** - `core/domain_wizard.py:63` reads PDFs as raw binary via `Path.read_text(errors="replace")`, sending `%PDF-1.4` bytes to the LLM. Wizard produces garbage schemas for the most common document format. Swap to `sift_kg.ingest.reader.read_document()`. Single-function fix; unblocks the "create your own domain" path. (completed 2026-04-17)
- [ ] **Phase 13: Extraction pipeline reliability** - Addresses Bug 4 (30% extraction drop rate in 23-doc axmp-compliance build). Add post-extraction normalization step (Enh 2), enforce required JSON schema in extractor prompt (Enh 3), and capture accurate `model_used` + `cost_usd` in extraction metadata (Part 1 Item 4).
- [ ] **Phase 14: Chunk overlap** - `commands/ingest.md` promises overlap, `core/chunk_document.py` implements none. Silent recall loss on every graph built. Implement sliding-window overlap (character or sentence based).
- [ ] **Phase 15: Format discovery parity** - `core/ingest_documents.py:SUPPORTED_EXTENSIONS` discovers 9 extensions but README claims "75+ via Kreuzberg." PPTX/EPUB/MD/RTF/ODT/CSV silently skipped. Expand allowlist or probe at runtime.
- [ ] **Phase 16: Wizard sample window beyond 8KB** - `core/domain_wizard.py:105` truncates each sample to `doc_text[:8000]`. Tail vocabulary ignored. Multi-excerpt or summarize-then-analyze. **Depends on Phase 12** (wizard must read real text first).
- [ ] **Phase 17: Domain awareness in consumers** - Workbench ignores `--domain` flag (Bug 1), graph.html has empty title (Bug 2) and uses generic palette (Enh 7), system prompt hardcodes contracts vocab (Enh 9), dashboard needs auto-detection (Enh 10). Systemic "domain context doesn't propagate past graph build."
- [ ] **Phase 18: Per-domain epistemic & validator extensibility** - Custom epistemic rules as Python hooks beyond generic contradiction pairs (Enh 6), optional per-domain `validation/` scripts parallel to drug-discovery's `validate_molecules.py` (Enh 8), and the structural-biology doctype deferred from v2.0 (Part 1 Item 6).
- [ ] **Phase 19: Wizard & CLI ergonomics** - Safe slugification in `generate_domain_package()` (Bug 5), wizard emits `workbench/template.yaml` automatically (Enh 1), `--domain` accepts name-or-path gracefully (Enh 4), `--schema <file.json>` flag to bypass LLM discovery (Enh 5).
- [ ] **Phase 20: README "Pipeline Capacity & Limits" section** - Document post-fix values for wizard, ingestion, acquire, and epistemic limits. Must run after all other v3.0 phases so it documents reality, not aspiration.

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
- [x] 07-01-PLAN.md — Test infrastructure, fixtures, and unit tier (conftest.py, pyproject.toml, markers, schema validation)
- [x] 07-02-PLAN.md — Integration tests for command entry points, KG provenance conversion, cross-domain verification
- [x] 07-03-PLAN.md — E2E pipeline tests and Makefile tiered test targets

### Phase 8: Domain Creation Wizard
**Goal**: A domain developer can point the wizard at sample documents and get a complete, working domain package generated automatically
**Depends on**: Phase 7 (needs test infrastructure to validate generated domains)
**Requirements**: WIZD-01, WIZD-02, WIZD-03, WIZD-04
**Success Criteria** (what must be TRUE):
  1. Running `/epistract:domain` with a path to sample documents produces a proposed entity/relation schema based on document analysis
  2. The wizard generates a complete domain package -- domain.yaml, SKILL.md, and epistemic rules -- ready to use without manual editing
  3. The wizard proposes epistemic layer rules appropriate to the domain (e.g., contradiction patterns, confidence heuristics, gap detection logic)
  4. A domain generated by the wizard works end-to-end with the standard pipeline: ingest, extract, build graph, run epistemic analysis -- no code changes needed
**Plans**: 3 plans

Plans:
- [x] 08-01-PLAN.md — Generalize epistemic dispatcher + wizard test fixtures (WIZD-04)
- [x] 08-02-PLAN.md — Core domain wizard module: analysis, generation, validation (WIZD-01, WIZD-02, WIZD-03)
- [x] 08-03-PLAN.md — /epistract:domain command + integration tests (WIZD-01, WIZD-02, WIZD-03, WIZD-04)

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
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [x] 09-01-PLAN.md — Template system + backend generalization (CONS-01, INST-02)
- [x] 09-02-PLAN.md — Frontend generalization for domain-agnostic workbench (CONS-01)
- [x] 09-03-PLAN.md — Telegram bot + plugin packaging (CONS-02, INST-01, INST-03)

### Phase 10: Documentation Refresh
**Goal**: All documentation presents epistract as a domain-agnostic framework with clear paths for both using pre-built domains and creating new ones
**Depends on**: Phase 8, Phase 9
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. README leads with framework identity and offers dual-path quick-start: "Use a pre-built domain" or "Create your own domain"
  2. Architecture diagrams show three-layer separation (core pipeline, domain configs, example consumers) and the two-layer KG (brute facts + epistemic)
  3. Domain developer guide walks through the full workflow: install, create domain via wizard, ingest documents, explore graph, analyze with epistemic layer
  4. Paper (title, abstract, architecture sections) is reframed around the framework -- not the STA use case
**Plans**: 4 plans

Plans:
- [x] 10-01-PLAN.md — Architecture diagrams (4 Mermaid + SVG) and gitignore STA audit
- [x] 10-02-PLAN.md — README rewrite (framework-first) + showcases + CLAUDE.md update
- [x] 10-03-PLAN.md — Domain developer guide rewrite (wizard-first structure)
- [x] 10-04-PLAN.md — Paper reframing (title, abstract, architecture, Case Study 2, conclusion)

### Phase 11: End-to-End Scenario Validation and v2.0 Release
**Goal**: Both use cases (drug discovery + contracts) produce demonstration-ready knowledge graphs through the new plugin and extraction pipeline, validated against baseline output. Closes with git sync to remote and v2.0 milestone completion.
**Depends on**: Phase 10
**Requirements**: E2E-01, E2E-02, E2E-03, E2E-04, E2E-05, E2E-06, REL-01, REL-02, REL-03
**Success Criteria** (what must be TRUE):
  1. Drug discovery scenarios (1-6) regenerate graphs with equivalent or better entity/relation counts, community structure, and epistemic analysis compared to V1 baseline
  2. Contract scenario regenerates the 341-node, 663-edge graph with 53 conflicts detected — validated against stored baseline
  3. All extractions run through the installed plugin (not raw scripts) — proving the marketplace install path works end-to-end
  4. Both epistemic layers (drug discovery molecular validation + contract conflict detection) produce correct output
  5. A repeatable regression script exists that can re-run all scenarios and diff against baseline snapshots
  6. Graph visualizations for both use cases are demonstration-ready (viewable, navigable, presentable)
  7. Repository is clean: no junk files, no stale artifacts, no large binaries — only production-necessary files are tracked in git
  8. .gitignore is comprehensive: local-only files (extraction output, contract data, node_modules, .planning/, worktrees) are excluded from remote
  9. Feature branch synced with remote main (rebase/merge), pushed, and PR created — closing the v2.0 milestone
**Plans**: 4 plans

Plans:
- [x] 11-01-PLAN.md — Regression infrastructure: V1 baselines, comparison engine, Makefile targets (E2E-05, E2E-01, E2E-02, E2E-04)
- [x] 11-02-PLAN.md — Repo cleanup: gitignore hardening, audit script, npx package.json (REL-01, REL-02)
- [x] 11-03-PLAN.md — Scenario validation: run all scenarios via plugin, validate counts, save V2 baselines (E2E-01, E2E-02, E2E-03, E2E-04, E2E-06)
- [x] 11-04-PLAN.md — Git squash, PR, merge, v2.0.0 tag, GitHub release (REL-03)

## Progress

**Execution Order:**
Phases execute in numeric order: 6 -> 7 -> 8 -> 9 -> 10 -> 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Domain Configuration | v1.0 | 3/3 | Complete | 2026-03-29 |
| 2. Document Ingestion | v1.0 | 2/2 | Complete | 2026-03-29 |
| 3. Entity Extraction and Graph Construction | v1.0 | 2/2 | Complete | 2026-03-29 |
| 4. Cross-Reference Analysis | v1.0 | 3/3 | Complete | 2026-03-31 |
| 5. Interactive Dashboard | v1.0 | 4/4 | Complete | 2026-04-02 |
| 6. Repo Reorganization and Cleanup | v2.0 | 0/3 | Planning | - |
| 7. Testing Framework | v2.0 | 0/3 | Planning | - |
| 8. Domain Creation Wizard | v2.0 | 0/3 | Planning | - |
| 9. Consumer Decoupling and Standalone Install | v2.0 | 0/3 | Planning | - |
| 10. Documentation Refresh | v2.0 | 4/4 | Complete    | 2026-04-04 |
| 11. End-to-End Scenario Validation | v2.0 | 4/4 | Complete    | 2026-04-17 |

### Phase 12: Fix wizard PDF binary read (Bug 3)

**Priority:** P0 CRITICAL
**Goal:** `core/domain_wizard.py` reads PDF sample documents as real extracted text instead of raw `%PDF-1.4` binary. After this phase, `/epistract:domain` produces useful schemas when given PDF samples — which is the most common document format and currently silently broken.

**Problem:** `read_sample_documents()` at `core/domain_wizard.py:63` uses `Path.read_text(errors="replace")`. For PDFs (and any binary format), this reads header bytes and compressed streams rather than extracted text. The 3-pass LLM analysis then runs on `%PDF-1.4\n%\xd0\xd4...` which produces garbage schemas. Surfaced in axmp-compliance build, report at `axmp-compliance-bug-report-2026-04-16.md` Bug 3.

**Fix sketch:** Replace `p.read_text(errors="replace")` with `read_document(p)` from `sift_kg.ingest.reader` (same reader used by the ingestion pipeline). Preserve the `char_count` metric, handle the no-sift-kg case gracefully.

**Requirements:** FIDL-01 — Wizard reads sample documents via sift-kg reader (see `.planning/REQUIREMENTS.md` v3 section).
**Depends on:** Phase 11 (V2 baselines stable).
**Plans:** 4/4 plans complete

**Success criteria sketch:**
1. `/epistract:domain` run on a corpus of 3 PDF samples produces a schema whose entity type names are derived from real document content, not binary headers.
2. Existing text/markdown sample behavior is unchanged (regression).
3. Graceful fallback error message if sift-kg is not installed.

See `.planning/phases/12-*/SCOPE-ADDITIONS.md` Theme A and `axmp-compliance-bug-report-2026-04-16.md` Bug 3.

Plans:
- [x] 12-01-PLAN.md — Add FIDL-01 to REQUIREMENTS.md, fix `read_sample_documents()` to use `sift_kg.ingest.reader.read_document` with `HAS_SIFT_READER` guard, add PDF regression + no-sift-kg fallback tests (FIDL-01)

### Phase 13: Extraction pipeline reliability

**Goal:** Every extraction written by an extractor agent reaches the graph build step. Currently 30% of extractions fail validation in real runs (7/23 in axmp-compliance). After this phase, extraction-load rate is ≥95% on a 20+ doc corpus, and extraction metadata tells the truth about which model ran and what it cost.

**Scope:** Bug 4 + Enh 2 + Enh 3 (extractor prompt enforcement) + Part 1 Item 4 (provenance accuracy). Bug 4 is the observed failure; Enhs 2/3 are the belt-and-suspenders fix; Item 4 rides along since it touches the same `build_extraction.py` file.

**Depends on:** Phase 11 baselines.
**Plans:** 4/5 plans executed

Plans:
- [x] 13-00-PLAN.md — Wave 0 scaffolding: register FIDL-02a/b/c in REQUIREMENTS.md, add 13 test rows to TEST_REQUIREMENTS.md, create 24-file Bug-4 reproducer + 10-file below-threshold fixture corpora (FIDL-02a, FIDL-02b, FIDL-02c)
- [x] 13-01-PLAN.md — Contract enforcement at write time: extend _normalize_fields for schema drift, add sift-kg DocumentExtraction Pydantic validation in build_extraction.py, replace hardcoded claude-opus-4-6/0.0 with --model/--cost flags + EPISTRACT_MODEL env var (FIDL-02c)
- [x] 13-02-PLAN.md — Normalization module: create core/normalize_extractions.py with rename/infer/dedupe/coerce/report + CLI entry-point with --fail-threshold gate (FIDL-02b)
- [x] 13-03-PLAN.md — Agent + command wiring: update agents/extractor.md with Required-Fields block + stdin fallback + fix /scripts/ path bug; insert Step 3.5 in commands/ingest.md + document --fail-threshold flag + EPISTRACT_MODEL export (FIDL-02a)
- [ ] 13-04-PLAN.md — End-to-end regression: FT-009 24-file reproducer ≥95% pass rate + graph builds, FT-010 below-threshold abort before build (FIDL-02b)

### Phase 14: Chunk overlap

**Goal:** Entities and relations that span a chunk boundary are extracted. Currently `core/chunk_document.py` splits without overlap, silently losing recall on every graph.

**Scope:** Part 1 Item 1. Implement character-based or sentence-based sliding window overlap; decide on size (500 char / 3 sentence / etc.) during planning.

**Plans:** 0 plans.

### Phase 15: Format discovery parity with Kreuzberg

**Goal:** Every file format Kreuzberg can parse is actually discovered by `discover_corpus`. Currently only 9 extensions survive the `SUPPORTED_EXTENSIONS` filter; PPTX/EPUB/MD/RTF/ODT/CSV and others are silently skipped.

**Scope:** Part 1 Item 3. Expand allowlist, or query Kreuzberg at runtime if possible.

**Plans:** 0 plans.

### Phase 16: Wizard sample window beyond 8KB

**Goal:** Wizard Pass-1 discovery sees more than the first 8,000 characters of each sample document. After this phase, long documents (contracts, full papers, patents) contribute tail vocabulary to schema design.

**Scope:** Part 1 Item 2. Options: multi-excerpt sampling (head+middle+tail), sliding-window Pass-1, summarize-then-analyze.

**Depends on:** **Phase 12** — wizard must actually read PDFs as text before expanding the window matters.
**Plans:** 0 plans.

### Phase 17: Domain awareness in downstream consumers

**Goal:** When a user passes `--domain <name>` to ingest or dashboard, every downstream consumer (workbench, graph.html, chat system prompt) reflects that domain. Currently they default to drug-discovery branding regardless.

**Scope:** Bug 1 (workbench wrong template), Bug 2 (graph.html empty title), Enh 7 (graph.html entity colors from template), Enh 9 (workbench system prompt domain patterns), Enh 10 (dashboard auto-detect from graph_data.json metadata).

**Plans:** 0 plans.

### Phase 18: Per-domain epistemic & validator extensibility

**Goal:** Domains can ship custom epistemic rules beyond generic term-pair contradictions, and optional validation scripts beyond drug-discovery's molecular validator.

**Scope:** Enh 6 (custom epistemic Python hooks), Enh 8 (per-domain validation/ directory), Part 1 Item 6 (structural-biology doctype — original v2.0 Phase 12 scope, folded in here since it's also an epistemic extensibility item).

**Plans:** 0 plans.

### Phase 19: Wizard & CLI ergonomics

**Goal:** Small bundled polish fixes for wizard and CLI friction points surfaced in axmp-compliance.

**Scope:** Bug 5 (safe slugification in `generate_domain_package`), Enh 1 (wizard emits `workbench/template.yaml`), Enh 4 (`run_sift.py build --domain` name-or-path handling), Enh 5 (`--schema <file.json>` skip-LLM flag).

**Plans:** 0 plans.

### Phase 20: README "Pipeline Capacity & Limits" section

**Goal:** Document the post-fix state of the pipeline so users know exactly what they are getting. Must run after Phases 12–19 so it documents reality rather than aspiration.

**Scope:** Part 1 Item 5. Draft language already written 2026-04-16 analysis — needs to be revised with actual post-fix values before landing.

**Depends on:** Phases 12–19 complete.
**Plans:** 0 plans.
