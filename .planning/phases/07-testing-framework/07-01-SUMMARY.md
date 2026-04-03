---
phase: 07-testing-framework
plan: 01
subsystem: testing
tags: [pytest, pydantic, fixtures, conftest, markers]

requires:
  - phase: 06-repo-reorganization
    provides: core/, domains/ directory structure with domain.yaml files
provides:
  - conftest.py with centralized path setup, availability flags, and shared fixtures
  - pyproject.toml with pytest marker registration (unit, integration, e2e)
  - Pydantic DocumentExtraction model for schema validation
  - Contract domain test fixtures (graph data, claims layer, extraction)
  - Drug-discovery test extraction fixture
affects: [07-02, 07-03, integration-tests, e2e-tests]

tech-stack:
  added: [pydantic (test schemas)]
  patterns: [conftest-centralized-setup, pytest-marker-tiers, fixture-driven-testing]

key-files:
  created:
    - tests/conftest.py
    - tests/test_schemas.py
    - pyproject.toml
    - tests/fixtures/contract_graph_data.json
    - tests/fixtures/contract_claims_layer.json
    - tests/fixtures/sample_extraction_drug.json
    - tests/fixtures/sample_extraction_contract.json
  modified:
    - tests/test_unit.py

key-decisions:
  - "Handled both dict-keyed (drug-discovery) and list-of-dict (contracts) YAML entity_type formats in schema tests"
  - "Pydantic DocumentExtraction model defined in test_schemas.py (not core/) since it serves test validation only"

patterns-established:
  - "conftest.py centralizes all sys.path manipulation and availability flags"
  - "All test functions use @pytest.mark.unit decorator for tiered execution"
  - "Domain YAML tests handle polymorphic entity_type/relation_type formats"

requirements-completed: [TEST-01, TEST-03, TEST-04]

duration: 3min
completed: 2026-04-03
---

# Phase 07 Plan 01: Test Infrastructure and Unit Tier Summary

**Pytest conftest.py with centralized path setup, 4 cross-domain fixture files, Pydantic DocumentExtraction schema validation, and @pytest.mark.unit on all 24 unit-tier tests.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T12:16:15Z
- **Completed:** 2026-04-03T12:19:19Z
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments

### Task 1: conftest.py, pyproject.toml, and fixture files
- Created `tests/conftest.py` centralizing PROJECT_ROOT, FIXTURES_DIR, sys.path setup, and HAS_SIFTKG/HAS_RDKIT/HAS_BIOPYTHON availability flags
- Created `pyproject.toml` with `[tool.pytest.ini_options]` registering unit/integration/e2e markers
- Created 4 new fixture files: contract_graph_data.json (5 nodes, 4 edges, metadata), contract_claims_layer.json (3 claims: asserted/conditional/obligatory), sample_extraction_drug.json (drug-discovery DocumentExtraction), sample_extraction_contract.json (contract DocumentExtraction)

### Task 2: Unit markers and schema validation tests
- Added `@pytest.mark.unit` to all 14 existing test functions in test_unit.py
- Removed duplicated sys.path and availability flag setup from test_unit.py (now imports from conftest)
- Created `tests/test_schemas.py` with 10 tests: 4 Pydantic DocumentExtraction validation tests and 6 domain YAML/SKILL.md coverage tests
- All 24 unit-tier tests pass (14 existing + 10 new)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Handled polymorphic domain YAML formats**
- **Found during:** Task 2
- **Issue:** Drug-discovery domain.yaml uses dict keys for entity_types (e.g., `COMPOUND: {description: ...}`), while contracts domain.yaml uses list-of-dicts (e.g., `[{name: PARTY, description: ...}]`)
- **Fix:** Schema tests detect format type and validate accordingly with isinstance checks
- **Files modified:** tests/test_schemas.py
- **Commit:** 234ccfb

## Verification Results

- `python -m pytest tests/test_unit.py -m unit -v`: 14 passed
- `python -m pytest tests/test_schemas.py -m unit -v`: 10 passed
- `python -m pytest tests/ -m unit --co -q`: 24 tests collected, no marker warnings
- All 4 new fixture files parse as valid JSON

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | e24ac8a | feat(07-01): create conftest.py, pyproject.toml, and fixture files |
| 2 | 234ccfb | feat(07-01): add unit markers to existing tests and create schema validation tests |
