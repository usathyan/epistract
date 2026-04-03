# Phase 3: Entity Extraction and Graph Construction - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract contract entities from all ingested documents using domain-configured prompts, deduplicate entity variants, and assemble into a queryable NetworkX knowledge graph with domain-specific attributes. Covers: clause-aware chunking, extraction agent dispatch, entity resolution, graph construction, and basic visualization verification. Does NOT include cross-reference analysis (Phase 4) or interactive dashboard (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Extraction Strategy
- **D-01:** Clause-aware chunking via a Python pre-processor script (e.g., `scripts/chunk_document.py`). Splits ingested text at section/clause boundaries (Article, Section, numbered clauses) to keep legal context intact.
- **D-02:** Fallback to fixed ~10K character chunks at paragraph boundaries when no clause structure is detected (e.g., free-form emails, XLS files).
- **D-03:** Chunk output stored as intermediate files (e.g., `ingested/<doc_id>_chunks/`) for debuggability and re-run without re-chunking.
- **D-04:** Parallel agent dispatch (4+ concurrent) — one extraction agent per document, matching the existing pattern from `commands/ingest.md` Step 3.
- **D-05:** One merged extraction JSON per document (`extractions/<doc_id>.json`), matching existing `build_extraction.py` pattern.
- **D-06:** Full contract SKILL.md passed as context to each extraction agent (Phase 1 D-17 pattern).
- **D-07:** Cross-references between contract sections extracted as attributes (e.g., "per Section 4.2") and resolved during graph construction when all sections are available. No overlap or neighboring-section inclusion during chunking.
- **D-08:** Reuse existing `agents/extractor.md` — it's already domain-aware. No new contract-specific agent needed.
- **D-09:** Pipeline is corpus-agnostic — processes whatever documents exist in the corpus directory. Not hardcoded to any specific document count.

### Entity Resolution
- **D-10:** Research-first approach — phase researcher MUST investigate existing contract/legal ontologies (LKIF, FIBO, ContractML, etc.), open-source contract review tools, and established taxonomies for obligations, parties, and clauses. Scope: general contract analysis frameworks + event/venue contract examples.
- **D-11:** If research finds established ontologies, adapt their concepts into the existing domain.yaml format (Phase 1 pattern). Don't adopt external formats directly — preserve the pluggable domain config system.
- **D-12:** SemHash fuzzy dedup as baseline implementation (case normalization, legal suffix stripping). Research findings inform upgrades to the resolution strategy.
- **D-13:** Extraction agents capture defined-term aliases during extraction — e.g., when a contract says "hereinafter referred to as 'Contractor'", extract both the formal name AND the alias. Store as `aliases` attribute on PARTY entities.

### Graph Attributes
- **D-14:** Structured typed attributes per entity type:
  - COST: `{amount, currency, unit, frequency, conditions, raw_text}`
  - DEADLINE: `{date, what_is_due, penalty_for_miss, raw_text}`
  - PARTY: `{role, aliases, contact, legal_name}`
  - OBLIGATION: `{action, responsible_party, conditions, raw_text}`
  - CLAUSE: `{section_number, clause_type, raw_text}`
  - SERVICE: `{description, provider, scope, raw_text}`
  - VENUE: `{name, capacity, location, restrictions, raw_text}`
- **D-15:** Clause-level provenance on all graph edges — each relation stores the source contract, section/clause number. Enables drill-down in Phase 5 dashboard and audit trails.
- **D-16:** COST entities store both parsed numeric amounts (for filtering/math) and original contract text (for audit/display). E.g., `{amount: 45.00, currency: "USD", unit: "per person", raw_text: "$45 per person"}`.

### Quality & Testing
- **D-17:** Synthetic contract fixtures in `tests/fixtures/` for deterministic testing — extend the Phase 2 pattern with small contracts containing known entities and relations that can be validated against expected extraction output.
- **D-18:** Basic sift-kg visualization verified in Phase 3 — confirm the existing pyvis HTML viewer renders the contract graph with distinguishable entity types. Not a dashboard, just the existing viewer working with contract data.

### Claude's Discretion
- Validation strategy for extraction quality (schema validation, confidence thresholds, LLM review — pick what works best)
- Internal design of the clause-aware chunker (regex patterns for section detection, handling edge cases)
- Exact attribute schemas beyond the types specified above
- SemHash configuration parameters (similarity thresholds, normalization rules)
- How to structure the merged extraction when combining chunk-level outputs

### Folded Todos
None.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Domain Schema & Extraction Guidance
- `skills/contract-extraction/domain.yaml` -- Contract domain schema (7 entity types, 7 relation types, confidence calibration, disambiguation rules)
- `skills/contract-extraction/SKILL.md` -- Full extraction prompt with naming standards, disambiguation rules, confidence calibration
- `skills/contract-extraction/references/entity-types.md` -- Detailed entity type reference
- `skills/contract-extraction/references/relation-types.md` -- Detailed relation type reference

### Existing Pipeline (reuse patterns)
- `agents/extractor.md` -- Domain-aware extraction agent. Reuse as-is for contract extraction.
- `scripts/build_extraction.py` -- Extraction JSON builder. Produces merged `extractions/<doc_id>.json`.
- `scripts/run_sift.py` -- sift-kg wrapper for graph building (`cmd_build`), viewing (`cmd_view`), export.
- `scripts/ingest_documents.py` -- Phase 2 ingestion script. Produces `ingested/<doc_id>.txt` and `triage.json`.
- `scripts/domain_resolver.py` -- Domain name-to-path resolution.

### Prior Phase Context
- `.planning/phases/01-domain-configuration/01-CONTEXT.md` -- Domain config decisions (D-01 through D-18)
- `.planning/phases/02-document-ingestion/02-CONTEXT.md` -- Ingestion decisions (D-01 through D-16)

### Requirements
- `.planning/REQUIREMENTS.md` -- EXTR-01, EXTR-02, GRPH-01, GRPH-02 define Phase 3 acceptance criteria

### Research Targets (for phase researcher)
- Existing contract/legal ontologies: LKIF (Legal Knowledge Interchange Format), FIBO (Financial Industry Business Ontology), ContractML, OASIS LegalDocumentML
- Open-source contract analysis tools and repos
- Event/venue contract analysis patterns
- Entity normalization approaches for legal entities

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agents/extractor.md` -- Domain-aware extraction agent, reads SKILL.md for guidance. Ready for contract use.
- `scripts/build_extraction.py` -- Writes extraction JSON with field normalization (`_normalize_fields`). Handles domain resolution.
- `scripts/run_sift.py` `cmd_build()` -- Builds graph from extractions, runs community labeling. Direct entry point for graph construction.
- `scripts/label_communities.py` -- Auto-labels graph communities. Works with any domain.
- SemHash dependency -- Already in project for fuzzy string deduplication.
- Rich progress bar -- Already used in `ingest_documents.py` for batch processing.

### Established Patterns
- CLI: `sys.argv` parsing with `--flag value` (no argparse). All scripts follow this.
- Error handling: return error dicts, don't raise. Log and continue.
- Path handling: `pathlib.Path` throughout.
- JSON output: `json.dumps(data, indent=2)` with ISO timestamps.
- Optional dependencies: try/except at module level with availability flags.

### Integration Points
- `ingested/<doc_id>.txt` -- Input from Phase 2. Chunker reads these.
- `triage.json` -- Document metadata from Phase 2. Can inform extraction prioritization.
- `extractions/<doc_id>.json` -- Output from extraction. Input to `run_sift.py build`.
- `graph_data.json` -- Output from graph construction. Input to Phase 4 cross-reference analysis.
- `commands/ingest.md` Steps 2-5 -- Chunking, extraction, validation, and graph building steps that Phase 3 implements.

</code_context>

<specifics>
## Specific Ideas

- Entity resolution should follow the same philosophy as biomedical: leverage established domain ontologies rather than inventing ad-hoc deduplication. The phase researcher should investigate what exists for legal/contract analysis.
- The framework should be domain-agnostic in its approach -- whatever resolution strategy works for contracts should be generalizable to other domains via the plugin architecture.
- Extraction readiness score from triage.json can inform extraction strategy (prioritize high-quality documents).

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 03-entity-extraction-and-graph-construction*
*Context gathered: 2026-03-29*
