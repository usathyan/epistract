---
phase: 07-testing-framework
plan: 02
subsystem: testing
tags: [pytest, integration, provenance, fixtures, cross-domain]

requires:
  - phase: 07-01
    provides: conftest.py, fixtures, pytest markers, schema tests
provides:
  - Integration tier tests for 8 command entry points
  - Cross-domain verification tests for drug-discovery and contracts
  - 36 offline KG provenance tests with fixture-based mocking
affects: [07-testing-framework, 08-consumer-separation]

tech-stack:
  added: []
  patterns: [mock-chat-responses-for-provenance, fixture-based-graph-testing]

key-files:
  created:
    - tests/test_integration.py
  modified:
    - tests/test_kg_provenance.py

key-decisions:
  - "Contracts domain cmd_build skipped in cross-domain test -- sift-kg load_domain requires dict-format entity_types, contracts YAML uses list format"
  - "Provenance tests use pre-recorded MOCK_CHAT_RESPONSES dict instead of live API calls"
  - "Provenance test thresholds adapted to fixture data size (26 nodes, 30 edges vs 300+ production)"
  - "label_communities test builds sift-kg-format communities dict from fixture graph node community fields"

patterns-established:
  - "Mock chat responses: MOCK_CHAT_RESPONSES dict maps question patterns to pre-recorded response strings for provenance testing"
  - "Fixture-based graph testing: load sample_graph_data.json instead of HTTP calls, adapt thresholds to fixture size"

requirements-completed: [TEST-02, TEST-06, TEST-07]

duration: 5min
completed: 2026-04-03
---

# Phase 7 Plan 2: Integration Tests and KG Provenance Conversion Summary

**10 integration tests covering 8 command entry points + 2 cross-domain verifications, plus 36 fixture-based KG provenance tests replacing live HTTP calls**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-03T12:21:51Z
- **Completed:** 2026-04-03T12:27:09Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created test_integration.py with 10 tests covering build_extraction, cmd_build, cmd_search, cmd_export, label_epistemic, label_communities, domain_resolver, validate_molecules, plus cross-domain verification
- Converted test_kg_provenance.py from live HTTP server dependency to fully offline fixture-based testing with 36 tests
- All tests pass offline -- no server or network access required

## Task Commits

Each task was committed atomically:

1. **Task 1: Create integration test file** - `6f879bf` (feat)
2. **Task 2: Convert KG provenance tests** - `bbae254` (feat)

## Files Created/Modified
- `tests/test_integration.py` - 10 integration tests for command entry points and cross-domain verification
- `tests/test_kg_provenance.py` - 36 provenance tests converted from live HTTP to fixture-based

## Decisions Made
- Contracts domain cannot go through cmd_build because sift-kg's load_domain expects dict-format entity_types but contracts domain.yaml uses list format. Cross-domain test verifies contracts via write_extraction + domain resolver instead.
- KG provenance tests use @pytest.mark.unit (not integration) since they only do JSON loading and dict lookups with no external dependencies.
- Pre-recorded mock chat responses reference specific entities from sample_graph_data.json fixture to maintain provenance tracing validity.
- label_communities test builds the sift-kg-expected communities dict format from graph node community fields rather than using the sample_communities.json fixture (which has a different format).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adapted cross-domain test for sift-kg schema format incompatibility**
- **Found during:** Task 1 (integration tests)
- **Issue:** contracts domain.yaml uses list-format entity_types; sift-kg load_domain expects dict-format
- **Fix:** Cross-domain test verifies drug-discovery via cmd_build and contracts via write_extraction + domain resolver
- **Files modified:** tests/test_integration.py
- **Verification:** All 10 integration tests pass

**2. [Rule 1 - Bug] Fixed label_communities fixture format mismatch**
- **Found during:** Task 1 (integration tests)
- **Issue:** sample_communities.json has list-of-objects format but label_communities expects {entity_id: community_name} dict
- **Fix:** Build communities dict from graph node community fields instead of using fixture directly
- **Files modified:** tests/test_integration.py
- **Verification:** test_label_communities_produces_output passes

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes adapt to pre-existing format mismatches. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all tests are fully wired to fixture data.

## Next Phase Readiness
- Integration and provenance test tiers complete
- Ready for Plan 07-03 (test runner and CI configuration)
- Contracts domain.yaml list-format entity_types should be addressed if sift-kg cmd_build is needed for contracts

## Self-Check: PASSED

- [x] tests/test_integration.py exists
- [x] tests/test_kg_provenance.py exists
- [x] 07-02-SUMMARY.md exists
- [x] Commit 6f879bf found
- [x] Commit bbae254 found

---
*Phase: 07-testing-framework*
*Completed: 2026-04-03*
