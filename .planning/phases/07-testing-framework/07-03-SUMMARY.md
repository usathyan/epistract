---
phase: 07-testing-framework
plan: 03
subsystem: testing
tags: [pytest, e2e, makefile, sift-kg, pipeline]

# Dependency graph
requires:
  - phase: 07-01
    provides: conftest.py with fixtures, path setup, HAS_SIFTKG flag, pyproject.toml markers
provides:
  - E2E pipeline tests proving full extraction-to-export lifecycle
  - Tiered Makefile test targets (unit, integration, e2e, all)
affects: [testing, ci, domains]

# Tech tracking
tech-stack:
  added: []
  patterns: [e2e pipeline test pattern using tmp_path and fixture extractions]

key-files:
  created: [tests/test_e2e.py]
  modified: [Makefile, domains/contracts/domain.yaml]

key-decisions:
  - "Fixed contracts domain.yaml from list to dict format for sift-kg compatibility"
  - "E2E tests call cmd_build and analyze_epistemic directly rather than subprocess"

patterns-established:
  - "E2E test pattern: copy fixture extraction -> cmd_build -> analyze_epistemic -> cmd_export"
  - "Tiered test execution: make test (unit) / make test-integration / make test-e2e / make test-all"

requirements-completed: [TEST-05, TEST-01]

# Metrics
duration: 3min
completed: 2026-04-03
---

# Phase 07 Plan 03: E2E Pipeline Tests and Makefile Targets Summary

**E2E pipeline tests for drug-discovery and contracts domains with tiered Makefile test targets**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T12:23:00Z
- **Completed:** 2026-04-03T12:26:09Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- E2E pipeline tests prove full lifecycle (extraction -> graph build -> epistemic -> export) for both domains
- Makefile has 4 tiered test targets: test (unit), test-integration, test-e2e, test-all
- Fixed contracts domain.yaml schema format incompatibility with sift-kg

## Task Commits

Each task was committed atomically:

1. **Task 1: Create E2E pipeline test** - `faba71e` (feat)
2. **Task 2: Update Makefile with tiered test targets** - `aae043d` (chore)

## Files Created/Modified
- `tests/test_e2e.py` - 3 E2E tests: drug-discovery pipeline, contract pipeline, graph metadata verification
- `Makefile` - Tiered test targets and updated lint/format to include core/
- `domains/contracts/domain.yaml` - Fixed entity_types/relation_types from list to dict format

## Decisions Made
- Fixed contracts domain.yaml format during E2E test creation -- sift-kg load_domain expects dict-style entity_types (e.g., `PARTY: {description: ...}`) not list-style (e.g., `- name: PARTY`)
- E2E tests import and call Python functions directly (cmd_build, analyze_epistemic) rather than spawning subprocesses, matching the existing test patterns

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed contracts domain.yaml schema format**
- **Found during:** Task 1 (E2E pipeline test)
- **Issue:** contracts/domain.yaml used list format for entity_types and relation_types (`- name: PARTY`) but sift-kg's load_domain expects dict format (`PARTY: {description: ...}`), causing AttributeError
- **Fix:** Converted both entity_types and relation_types from list-of-dicts to dict-of-dicts format
- **Files modified:** domains/contracts/domain.yaml
- **Verification:** test_e2e_contract_pipeline passes with 3/3 E2E tests green
- **Committed in:** faba71e (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix was necessary for contract pipeline E2E test to work. The schema format was incompatible with sift-kg since it was created.

## Issues Encountered
None beyond the domain.yaml format fix documented above.

## Known Stubs
None -- all tests exercise real pipeline functions with actual sift-kg calls.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 plans in Phase 07 complete (01: infrastructure, 02: integration tests, 03: E2E + Makefile)
- Test framework ready for CI integration
- make test runs unit tier cleanly on any machine

---
*Phase: 07-testing-framework*
*Completed: 2026-04-03*
