---
phase: 06-repo-reorganization-and-cleanup
plan: 02
subsystem: testing
tags: [pytest, imports, core-independence, ARCH-02]

requires:
  - phase: 06-01
    provides: "Reorganized directory structure with core/, domains/, skills/ symlinks"
provides:
  - "All test files updated to reference new directory layout"
  - "Core import independence verified (ARCH-02)"
  - "resolve_domain API properly consumed by core modules"
affects: [07-domain-wizard, testing]

tech-stack:
  added: []
  patterns: ["resolve_domain returns dict with yaml_path/schema/name keys", "Dynamic domain epistemic loading via importlib.util"]

key-files:
  created: []
  modified:
    - tests/test_unit.py
    - core/build_extraction.py
    - core/run_sift.py

key-decisions:
  - "Skipped test_workbench.py migration to examples/ -- workbench still at scripts/workbench/"
  - "Skipped test_kg_provenance.py updates -- no scripts/ path references found"
  - "Added DRUG_DISCOVERY_DIR constant for validate_molecules.py path resolution"

patterns-established:
  - "resolve_domain() returns dict, not path -- callers extract yaml_path key"
  - "Core modules use from core.domain_resolver import (fully qualified)"

requirements-completed: [ARCH-02]

duration: 3min
completed: 2026-04-03
---

# Phase 06 Plan 02: Test Updates and Core Import Independence Summary

**Updated test imports for reorganized directories and fixed resolve_domain API consumption across core modules (ARCH-02 verified)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T00:35:26Z
- **Completed:** 2026-04-03T00:38:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Updated test_unit.py path constants from skills/scripts to domains/core layout
- Fixed resolve_domain API mismatch in build_extraction.py and run_sift.py (returned dict, consumed as path)
- Verified core modules import cleanly without domain dependencies (ARCH-02)
- All 46 tests collected successfully against reorganized codebase

## Task Commits

Each task was committed atomically:

1. **Task 1: Update test files for new directory structure** - `31a33de` (feat)
2. **Task 2: Verify core import independence and run tests** - `6282a53` (fix)

## Files Created/Modified
- `tests/test_unit.py` - Updated VALIDATION_SCRIPTS, CORE, DOMAIN_YAML, DRUG_DISCOVERY_DIR paths
- `core/build_extraction.py` - Fixed resolve_domain import (bare -> core.domain_resolver) and dict API usage
- `core/run_sift.py` - Fixed cmd_build to extract yaml_path from resolve_domain dict; fixed list_domains usage in __main__

## Decisions Made
- Skipped test_workbench.py migration: workbench remains at scripts/workbench/, not moved to examples/
- Skipped test_kg_provenance.py: no scripts/ references to update
- Added DRUG_DISCOVERY_DIR constant to test_unit.py for validate_molecules.py subprocess path

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed resolve_domain API mismatch in build_extraction.py**
- **Found during:** Task 2 (core import independence verification)
- **Issue:** resolve_domain() returns dict with schema/yaml_path keys, but build_extraction.py called open() on the dict directly
- **Fix:** Extract schema from dict, fall back to loading yaml_path if schema is None
- **Files modified:** core/build_extraction.py
- **Verification:** test_ut012_extraction_adapter passes
- **Committed in:** 6282a53

**2. [Rule 1 - Bug] Fixed resolve_domain API mismatch in run_sift.py**
- **Found during:** Task 2 (core import independence verification)
- **Issue:** cmd_build passed resolve_domain dict directly to load_domain(domain_path=), expecting a Path
- **Fix:** Extract yaml_path from dict and pass Path(yaml_path) to load_domain
- **Files modified:** core/run_sift.py
- **Verification:** Core imports clean, test collection succeeds
- **Committed in:** 6282a53

**3. [Rule 1 - Bug] Fixed list_domains usage in run_sift.py __main__**
- **Found during:** Task 2 (code review)
- **Issue:** list_domains() returns list of strings, but __main__ treated them as dicts with name/version/description keys
- **Fix:** Iterate strings, call resolve_domain for each to get schema details
- **Files modified:** core/run_sift.py
- **Committed in:** 6282a53

---

**Total deviations:** 3 auto-fixed (3x Rule 1 - Bug)
**Impact on plan:** All fixes necessary to correct API contract mismatch from Wave 1 restructuring. No scope creep.

## Issues Encountered
None beyond the auto-fixed API mismatches above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Core import independence confirmed (ARCH-02)
- Test suite collects all 46 tests against reorganized codebase
- Ready for Plan 03 or subsequent phases

## Self-Check

Verified below.

---
*Phase: 06-repo-reorganization-and-cleanup*
*Completed: 2026-04-03*
