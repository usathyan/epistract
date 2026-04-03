# Phase 7: Testing Framework - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Comprehensive test suite that locks down V1 regression coverage and validates every V2 capability from install through extraction. This is the quality gate before wizard (Phase 8), standalone install (Phase 9), and documentation (Phase 10) phases. No CI setup — local test execution only.

</domain>

<decisions>
## Implementation Decisions

### Test Tiers
- **D-01:** Three-tier test structure: Unit (fast, no external deps) → Integration (needs sift-kg/RDKit but no servers) → E2E (needs running workbench/LLM). Pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`) control which tier runs.
- **D-02:** Makefile targets: `make test` = unit only, `make test-integration` = integration tier, `make test-all` = everything.
- **D-03:** KG provenance tests (32 existing) converted to fixture-based mocking — load graph_data.json + claims_layer.json from fixtures, mock HTTP calls. Tests run offline and fast. No live server required.

### Test Data Strategy
- **D-04:** Shared fixtures directory at `tests/fixtures/` with domain-labeled files (e.g., `sample_graph_data.json` for drug-discovery, `contract_graph_data.json` for contracts). Both domains share the same fixture loading pattern.
- **D-05:** E2E pipeline test (TEST-05) uses pre-recorded extraction JSON files as golden outputs. Pipeline runs graph-build → epistemic → export starting from pre-extracted data. No LLM calls — deterministic and fast.

### Command & Skill Testing
- **D-06:** Command coverage (TEST-02) defined as testing the underlying Python entry points that each `/epistract:*` command invokes. Every Python function a command would call (e.g., `run_sift.py build`, `run_sift.py export`, `build_extraction.py`, `label_epistemic.py`) runs without error against test fixtures.
- **D-07:** Agent coverage (TEST-04) uses Pydantic schema validation. Create DocumentExtraction Pydantic models and validate existing extraction JSON fixtures against the schema. Proves format correctness without invoking agents.
- **D-08:** Skill coverage (TEST-03) validates that domain YAML schemas load correctly and that extraction prompt templates produce valid output format.

### CI & Execution
- **D-09:** Local execution only for this phase. No GitHub Actions CI setup — that's future scope. Focus on getting the test suite correct and comprehensive.
- **D-10:** Optional dependencies (RDKit, Biopython) handled with `pytest.mark.skipif` markers. Unit tier runs without optional deps. Integration tier requires sift-kg. RDKit/Biopython tests are bonus — skip if not installed, pass if installed. `make test` always succeeds regardless of installed optional deps.

### Claude's Discretion
- Test file organization (single file vs multiple test files per tier)
- conftest.py fixture design and shared helpers
- Exact pytest marker names and grouping
- Whether to add `pyproject.toml` pytest config or keep Makefile-only
- Test naming convention (keep existing `test_ut{NNN}_` pattern or adopt new scheme)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Success Criteria
- `.planning/REQUIREMENTS.md` — TEST-01 through TEST-07 acceptance criteria
- `.planning/ROADMAP.md` §Phase 7 — 6 success criteria defining "done"

### Existing Test Infrastructure
- `tests/test_unit.py` — 14 existing unit tests (1118 lines), import patterns, skip decorators
- `tests/test_kg_provenance.py` — 32 provenance tests (472 lines), graph tracing logic to convert to fixture-based
- `tests/test_workbench.py` — 260 lines, workbench API tests
- `tests/TEST_REQUIREMENTS.md` — Existing traceability spec (UT-001 through UT-014)
- `tests/fixtures/` — Existing fixture files (graph data, communities, claims layer, contract samples)

### Codebase Analysis
- `.planning/codebase/TESTING.md` — Current test patterns, conventions, run commands
- `.planning/codebase/STRUCTURE.md` — Directory layout after Phase 6 reorganization
- `.planning/codebase/CONVENTIONS.md` — Code style and import patterns to follow

### Code Under Test
- `core/` — Domain-agnostic pipeline (10 Python modules): build_extraction, run_sift, label_communities, label_epistemic, domain_resolver, etc.
- `domains/drug-discovery/` — Drug discovery domain (domain.yaml, SKILL.md, validation scripts)
- `domains/contracts/` — Contract domain (domain.yaml, SKILL.md, epistemic rules)
- `commands/` — 10 slash commands (setup, ingest, build, query, export, view, validate, epistemic, ask, dashboard)
- `agents/` — 2 agents (extractor.md, validator.md)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/test_unit.py` — 14 existing tests with established patterns (skipif decorators, temp dirs, availability flags). Foundation for unit tier.
- `tests/fixtures/` — Sample graph data, communities, claims layer, contract PDFs/text already available. Sufficient for integration tests.
- `tests/test_kg_provenance.py` — 32 provenance tests with graph tracing logic. Core logic reusable; HTTP mocking layer needs to be added.
- `core/build_extraction.py` — `write_extraction()` function already used as test helper for creating fixture data.

### Established Patterns
- Conditional imports with availability flags (`HAS_SIFTKG`, `HAS_RDKIT`, `HAS_BIOPYTHON`) at module level
- `pytest.mark.skipif` for optional dependency gating
- Path setup via `sys.path.insert(0, ...)` for project imports (no installed package)
- Section separators with `# ====` comment blocks and UT-NNN IDs
- Assertions with f-string messages: `assert condition, f"Expected X, got {actual}"`

### Integration Points
- `core/run_sift.py` — Main entry point for build/view/export/search/info commands. All command tests route through here.
- `core/domain_resolver.py` — Resolves which domain to use. Cross-domain test (TEST-07) exercises this.
- Makefile `test` target — Currently runs `python -m pytest tests/test_unit.py -v`. Needs expansion for tiers.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for test organization and implementation.

</specifics>

<deferred>
## Deferred Ideas

- GitHub Actions CI setup — future phase after test suite is stable
- Test coverage reporting (coverage.py) — not in scope, no coverage targets defined
- Docker-based test environment — deferred, local execution sufficient
- Live LLM integration tests — too expensive/non-deterministic for automated suite

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-testing-framework*
*Context gathered: 2026-04-03*
