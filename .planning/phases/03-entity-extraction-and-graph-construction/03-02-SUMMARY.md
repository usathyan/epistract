---
phase: 03-entity-extraction-and-graph-construction
plan: 02
subsystem: extraction-pipeline
tags: [sift-kg, networkx, pyvis, contract-extraction, community-labeling, graph-construction]

# Dependency graph
requires:
  - phase: 03-01
    provides: chunk_document, entity_resolution functions (chunking + merge + normalize)
  - phase: 01-domain-configuration
    provides: contract domain.yaml schema, domain_resolver
provides:
  - extract_contracts.py orchestrator chaining chunk -> merge -> resolve -> graph build
  - contract-aware community labeling (PARTY/VENUE-anchored labels)
  - integration tests UT-036 through UT-038 validating graph construction and visualization
affects: [04-cross-reference-analysis, 05-dashboard-and-chat]

# Tech tracking
tech-stack:
  added: []
  patterns: [contract community labeling heuristics, extraction pipeline orchestration]

key-files:
  created: [scripts/extract_contracts.py]
  modified: [scripts/label_communities.py, tests/test_unit.py]

key-decisions:
  - "Contract entity types added alongside biomedical types in label_communities.py (additive, no removal)"
  - "UT-037 requires at least one relation for sift-kg to include entities in graph (isolated entities get no nodes)"
  - "Fixed pre-existing UT-013 bug: domain_path kwarg changed to domain_name after Phase 1 API update"

patterns-established:
  - "Contract community labels anchored by PARTY (priority 0) and VENUE (priority 1)"
  - "Pipeline orchestrator pattern: chunk -> merge -> resolve -> build with skip flags"

requirements-completed: [EXTR-01, GRPH-01, GRPH-02]

# Metrics
duration: 6min
completed: 2026-03-30
---

# Phase 3 Plan 2: Graph Construction & Pipeline Orchestration Summary

**Contract extraction pipeline wired end-to-end: orchestrator chains chunking through sift-kg graph build, community labels use PARTY/VENUE anchors, and pyvis visualization renders contract entity types with typed attributes**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-30T14:07:18Z
- **Completed:** 2026-03-30T14:13:45Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Contract-aware community labeling: PARTY and VENUE anchor labels, with service/obligation/cost/deadline heuristics
- extract_contracts.py orchestrator chains 4 pipeline steps with Rich progress and skip flags
- Integration tests prove graph nodes carry typed attributes (COST amount/currency, PARTY role/aliases)
- Pyvis HTML visualization confirmed rendering for contract entity graphs
- All 38 tests pass (full suite green, 9 Phase 3 tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update label_communities.py for contract entity types** - `fcbf256` (feat)
2. **Task 2: Create extract_contracts.py orchestrator and integration tests** - `d35ea6a` (feat)

## Files Created/Modified
- `scripts/extract_contracts.py` - End-to-end pipeline orchestrator: chunk -> merge -> resolve -> graph build
- `scripts/label_communities.py` - Added contract entity type priorities and labeling heuristics
- `tests/test_unit.py` - Added UT-036, UT-037, UT-038; fixed UT-013 domain_path bug

## Decisions Made
- Contract entity types added alongside biomedical types (additive change preserves backward compat)
- sift-kg requires at least one relation to include entities as graph nodes; UT-037 includes a COSTS relation
- Fixed UT-013 pre-existing bug where domain_path kwarg no longer matches cmd_build(domain_name=) signature

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed UT-013 domain_path -> domain_name**
- **Found during:** Task 2 (test investigation)
- **Issue:** After Phase 1 refactored cmd_build to use domain_name instead of domain_path, UT-013 was calling cmd_build(tmpdir, domain_path=str(DOMAIN_YAML)) which raises TypeError
- **Fix:** Changed to cmd_build(tmpdir, domain_name="drug-discovery")
- **Files modified:** tests/test_unit.py
- **Verification:** UT-013 passes
- **Committed in:** d35ea6a (Task 2 commit)

**2. [Rule 1 - Bug] Fixed UT-037 missing relation for entity visibility**
- **Found during:** Task 2 (test creation)
- **Issue:** sift-kg only creates graph nodes for entities that participate in at least one relation; plan's UT-037 had 0 relations causing COST node assertion to fail
- **Fix:** Added a COSTS relation between the two entities
- **Files modified:** tests/test_unit.py
- **Verification:** UT-037 passes, COST node has expected attributes
- **Committed in:** d35ea6a (Task 2 commit)

**3. [Rule 1 - Bug] Fixed stdout parsing in UT-036**
- **Found during:** Task 2 (test creation)
- **Issue:** label_communities prints JSON to stdout before cmd_build's result JSON, causing json.loads to fail with "Extra data"
- **Fix:** Parse last line of stdout instead of entire buffer
- **Files modified:** tests/test_unit.py
- **Verification:** UT-036 passes
- **Committed in:** d35ea6a (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 bugs)
**Impact on plan:** All fixes necessary for test correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## Known Stubs
None - all pipeline steps are wired to real implementations. Step 2 (extraction) is intentionally a passthrough that merges agent-produced chunk extractions rather than calling LLMs directly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full extraction pipeline operational: chunk -> merge -> resolve -> graph build -> visualize
- Ready for Phase 4 cross-reference analysis (graph_data.json with typed contract entities available)
- Entity extraction is dispatched by Claude agents (agents/extractor.md), not by extract_contracts.py directly

---
*Phase: 03-entity-extraction-and-graph-construction*
*Completed: 2026-03-30*
