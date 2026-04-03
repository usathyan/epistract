# Phase 8: Domain Creation Wizard - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Auto-generate complete, working domain packages from sample documents via `/epistract:domain`. A domain developer points the wizard at 2-5 sample documents, provides a brief domain description, and gets a full domain package (domain.yaml, SKILL.md, epistemic.py, references/) written to `domains/<name>/` — ready to use with the standard pipeline without code changes.

</domain>

<decisions>
## Implementation Decisions

### Document Analysis Strategy
- **D-01:** LLM multi-pass analysis — Pass 1 extracts candidate entity/relation types from each doc, Pass 2 consolidates and deduplicates across docs, Pass 3 proposes the final schema
- **D-02:** Minimum 2 sample documents required, recommend 3-5. Wizard warns if only 1 provided
- **D-03:** User provides a 1-2 sentence domain description as required input (e.g., "Real estate lease agreements"). Gives LLM context for schema discovery and naming conventions
- **D-04:** Accept any format Kreuzberg handles (PDF, DOCX, HTML, TXT, etc.) — reuse the existing ingestion pipeline in `core/ingest_documents.py`

### Schema Generation Quality
- **D-05:** Generated domain.yaml targets contracts-level quality — entity types with descriptions + relation types with descriptions. Not drug-discovery-level (no extraction_hints, disambiguation rules). User can manually enrich later
- **D-06:** Generated SKILL.md uses a template with domain-specific sections: system_context from user's description, entity type extraction guidance derived from sample docs, relation extraction rules, confidence calibration section. Modeled after contracts SKILL.md complexity
- **D-07:** Auto-generate `references/entity-types.md` and `references/relation-types.md` with descriptions and examples from sample documents. Keeps package structure consistent with both existing domains
- **D-08:** No validation scripts generated. Validation (like RDKit for chemistry) is too domain-specific for auto-generation. User adds manually if their domain has validatable identifiers

### Epistemic Rules Generation
- **D-09:** Generic template + LLM customization approach. Base template includes all four patterns: contradiction detection, confidence calibration, gap analysis, cross-document linking
- **D-10:** LLM customizes via pattern injection — template has placeholder sections where the LLM injects domain-specific regex patterns, entity type pairs for conflict checking, and gap detection rules
- **D-11:** Generated epistemic.py is a working Python module following the existing pattern — an `analyze_<domain>_epistemic()` function that `core/label_epistemic.py` dispatches to
- **D-12:** Dry-run validation — run generated epistemic.py against a small extraction from sample docs to verify it produces valid output (no crashes, reasonable claim counts). Fix errors before writing final files

### Wizard Interaction Flow
- **D-13:** Guided 3-step flow: (1) User provides domain name + description + sample doc paths, (2) Wizard analyzes and presents proposed schema summary in chat, (3) User approves/edits, wizard generates the full package
- **D-14:** Schema review happens in chat — display proposed entity types, relation types, and key epistemic rules as a formatted summary. User says "looks good" or suggests changes
- **D-15:** Write generated package directly to `domains/<name>/` where `domain_resolver.py` discovers it. Immediately usable with the pipeline
- **D-16:** Create only — no update support. If domain already exists, warn and ask to overwrite or pick a new name. Updating existing domains is a manual editing task

### Claude's Discretion
- Implementation details of the multi-pass LLM analysis (prompt engineering, chunking strategy for large sample docs)
- Exact template structure for the epistemic.py base template
- Error handling and recovery when LLM produces poor schema proposals
- How to format the schema summary for in-chat review

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Domain Package Structure
- `domains/contracts/domain.yaml` — Reference for target domain.yaml quality level (contracts-level)
- `domains/contracts/SKILL.md` — Reference for target SKILL.md complexity level
- `domains/contracts/epistemic.py` — Reference for epistemic.py function signature and dispatch pattern
- `domains/drug-discovery/domain.yaml` — Reference for richer domain.yaml (extraction_hints, nomenclature) — NOT the target quality but useful as upper bound
- `domains/drug-discovery/SKILL.md` — Reference for full-featured SKILL.md
- `domains/drug-discovery/epistemic.py` — Reference for alternative epistemic analysis patterns

### Core Infrastructure
- `core/domain_resolver.py` — Domain discovery and loading. Generated domains must be discoverable by this module
- `core/label_epistemic.py` — Epistemic dispatcher. Generated epistemic.py must match the dispatch interface
- `core/ingest_documents.py` — Document ingestion pipeline to reuse for reading sample documents

### Reference Docs
- `domains/contracts/references/entity-types.md` — Reference for generated entity-types.md format
- `domains/contracts/references/relation-types.md` — Reference for generated relation-types.md format

### Requirements
- `.planning/REQUIREMENTS.md` §Domain Wizard — WIZD-01 through WIZD-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/domain_resolver.py` — Domain discovery. Generated domains auto-discovered if placed in `domains/<name>/` with a `domain.yaml`
- `core/ingest_documents.py` — Kreuzberg-based document parsing. Reuse for reading sample documents during wizard analysis
- `core/build_extraction.py` — DocumentExtraction JSON format. Useful for the dry-run validation step
- `core/label_epistemic.py` — Epistemic dispatcher with domain-based routing. Generated epistemic.py must match its interface

### Established Patterns
- Domain packages: `domain.yaml` + `SKILL.md` + `epistemic.py` + `references/` — two working examples to template from
- Epistemic dispatch: `label_epistemic.py` imports `domains/<name>/epistemic.py` and calls `analyze_<domain>_epistemic()`
- Domain YAML structure: `name`, `version`, `description`, `system_context`, `entity_types` (dict of dicts), `relation_types` (dict of dicts)
- SKILL.md format: Detailed extraction instructions for Claude agents, entity-by-entity guidance

### Integration Points
- `/epistract:domain` command entry point — new command in `commands/` directory
- `domains/` directory — where generated packages land
- `core/domain_resolver.py` — must discover generated domains (already works via directory scan)
- Test infrastructure — Phase 7 tests can validate generated domains work with pipeline

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-domain-creation-wizard*
*Context gathered: 2026-04-03*
