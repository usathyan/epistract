# Phase 1: Domain Configuration - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Epistract supports multiple domains via pluggable configuration. A contract domain ontology (entity types, relation types, extraction prompts) is ready for use in downstream extraction phases. Existing biomedical scenarios 1-6 continue to work unchanged.

</domain>

<decisions>
## Implementation Decisions

### Domain Config Structure
- **D-01:** New domains live as skill directories inside `skills/` — e.g., `skills/contract-extraction/` mirrors `skills/drug-discovery-extraction/`
- **D-02:** Each domain.yaml is fully independent (no shared base schema, no inheritance). If two domains share an entity type, they each define it independently.
- **D-03:** Every domain must be a full package: `domain.yaml` + `SKILL.md` + `references/` directory. All three are required for a valid domain.
- **D-04:** Strict validation on load — validate YAML structure (entity types exist, relation source/target types reference defined entities, required fields present). Fail fast with clear error if schema is malformed.
- **D-05:** Version field in domain.yaml for documentation (already exists in current YAML) but no enforcement or migration checks.
- **D-06:** Auto-discovery — scan `skills/` for directories containing `domain.yaml`. No explicit registry needed. New domains become available by dropping in a directory.

### Contract Ontology Design
- **D-07:** Start with the 7 entity types from requirements (Party, Obligation, Deadline, Cost, Clause, Service, Venue) and iterate after running extraction on real contracts.
- **D-08:** Start with the 6 relation types from requirements (OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS) and iterate after real extraction.
- **D-09:** Include detailed extraction_hints per entity and relation type, specific to contract language (e.g., "Look for shall, must, agrees to, is required to" for OBLIGATION).
- **D-10:** Fallback relation: `RELATED_TO` for contract associations that don't fit the 6 specific types.
- **D-11:** Contract-specific confidence calibration: 0.9+ for explicit "shall/must" obligations, 0.7-0.89 for implied obligations, 0.5-0.69 for inferred from context.
- **D-12:** Contract-specific disambiguation rules (OBLIGATION vs CLAUSE, COST vs PENALTY, SERVICE vs VENUE).

### Domain Selection Mechanism
- **D-13:** Domain selected via `--domain <name>` flag. System resolves name to `skills/{name}-extraction/domain.yaml`.
- **D-14:** Default domain is `drug-discovery` when no `--domain` flag is provided (backward compatibility).
- **D-15:** Add `--list-domains` command that scans `skills/` and shows available domains with descriptions.

### Biomedical Compatibility
- **D-16:** Biomedical becomes a domain config — the existing `skills/drug-discovery-extraction/` IS the biomedical domain. Pipeline learns dynamic domain resolution instead of hardcoding the path. No migration needed.
- **D-17:** Agents (extractor.md, validator.md) become domain-aware in Phase 1 — they read the selected domain's SKILL.md for extraction guidance instead of hardcoded biomedical instructions.
- **D-18:** Validation scripts are optional per domain. Biomedical keeps its validators. Contract domain has none initially. Pipeline skips validation if no validation-scripts/ exist for the domain.

### Claude's Discretion
- Implementation details of YAML validation (Pydantic model, manual checks, or sift-kg's built-in validation)
- Naming convention for domain skill directories (confirmed pattern: `{domain-name}-extraction/`)
- Internal domain resolution function design

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Domain Schema
- `skills/drug-discovery-extraction/domain.yaml` — Current biomedical domain schema (17 entity types, 30 relation types). Reference implementation for contract domain YAML structure.
- `skills/drug-discovery-extraction/SKILL.md` — Biomedical extraction prompt. Reference for contract SKILL.md structure.

### Pipeline Integration
- `scripts/run_sift.py` — sift-kg wrapper with existing `--domain` flag and `load_domain()` usage. Must be updated for dynamic domain resolution.
- `scripts/build_extraction.py` — Extraction JSON builder. Must work with any domain's entity/relation types.

### Agent Definitions
- `agents/extractor.md` — Extraction agent. Must become domain-aware (read domain SKILL.md).
- `agents/validator.md` — Validation agent. Must handle optional validation scripts per domain.

### Requirements
- `.planning/REQUIREMENTS.md` — DCFG-01 through DCFG-04 define Phase 1 acceptance criteria.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/drug-discovery-extraction/` — Complete reference implementation of a domain package (YAML + SKILL.md + references/ + validation-scripts/)
- `run_sift.py`'s `load_domain()` call via sift-kg — Already supports loading domain from a path; needs thin wrapper for name-to-path resolution
- sift-kg's `load_domain(domain_path=Path(...))` API — Underlying library already supports arbitrary domain YAML paths

### Established Patterns
- Domain schema structure: `name`, `version`, `description`, `system_context`, `fallback_relation`, `entity_types`, `relation_types` fields in YAML
- Entity type structure: `description` + `extraction_hints` list
- Relation type structure: `description` + `source_types` + `target_types` + optional `symmetric`, `review_required`, `extraction_hints`
- CLI flag pattern: `sys.argv` parsing with `--flag value` (no argparse)

### Integration Points
- `run_sift.py` line 37 — hardcoded default domain path, needs to use `resolve_domain()` instead
- `commands/*.md` — Plugin commands need `--domain` argument support
- `agents/extractor.md` — Agent prompt references biomedical concepts, needs to load domain SKILL.md dynamically

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-domain-configuration*
*Context gathered: 2026-03-29*
