---
phase: 01-domain-configuration
plan: 03
subsystem: pipeline
tags: [domain-resolver, sift-kg, cross-domain, backward-compat]

requires:
  - phase: 01-01
    provides: domain_resolver.py with 5 resolution functions
  - phase: 01-02
    provides: contract domain package (domain.yaml, SKILL.md, references/)
provides:
  - Domain-aware pipeline scripts (run_sift.py, build_extraction.py, validate_molecules.py)
  - Domain-aware commands (ingest.md, build.md) with --domain flag
  - Domain-aware agents (extractor.md, validator.md) referencing SKILL.md dynamically
  - 9 contract domain integration tests
  - --list-domains CLI command
affects: [02-contract-ingestion, 03-knowledge-graph, pipeline-scripts]

tech-stack:
  added: []
  patterns: [domain-name-not-path, graceful-skip-validation, dynamic-skill-loading]

key-files:
  created: []
  modified:
    - scripts/run_sift.py
    - scripts/build_extraction.py
    - scripts/validate_molecules.py
    - commands/ingest.md
    - commands/build.md
    - agents/extractor.md
    - agents/validator.md
    - tests/test_unit.py

key-decisions:
  - "Domain parameter is a name string (not path) throughout the pipeline"
  - "validate_molecules.py exits gracefully with JSON when domain has no validation scripts"
  - "Agents reference domain SKILL.md dynamically with drug-discovery as fallback"

patterns-established:
  - "Domain name convention: pass short names like 'contract' or 'drug-discovery', never paths"
  - "Graceful skip pattern: tools report 'no validation scripts for domain X' and exit 0"
  - "Dynamic agent context: agents read domain SKILL.md at runtime, keep biomedical as fallback"

requirements-completed: [DCFG-01, DCFG-03, DCFG-04]

duration: 7min
completed: 2026-03-29
---

# Phase 01 Plan 03: Pipeline Domain Wiring Summary

**Wired all 6 hardcoded biomedical references to domain resolver, added --list-domains CLI, and 9 contract domain integration tests -- full pipeline is now domain-aware**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-29T21:35:24Z
- **Completed:** 2026-03-29T21:42:20Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Eliminated all hardcoded biomedical paths from scripts/, commands/, and agents/
- run_sift.py supports --domain name and --list-domains, build_extraction.py reads domain_name from YAML
- validate_molecules.py skips gracefully for domains without validators
- Agents reference domain SKILL.md dynamically with drug-discovery defaults as fallback
- 31 total tests pass (22 existing + 9 new contract domain integration tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update pipeline scripts to use domain resolver** - `4de04f5` (feat)
2. **Task 2: Update commands and agents to be domain-aware** - `5b01d92` (feat)
3. **Task 3: Add contract domain integration tests** - `8e8118e` (test)

## Files Created/Modified
- `scripts/run_sift.py` - Domain-aware sift-kg wrapper with --domain and --list-domains
- `scripts/build_extraction.py` - Reads domain_name from domain.yaml dynamically
- `scripts/validate_molecules.py` - Uses get_validation_scripts_dir(), skips when no scripts
- `commands/ingest.md` - Supports --domain flag, no hardcoded paths
- `commands/build.md` - Supports --domain flag
- `agents/extractor.md` - References domain SKILL.md dynamically
- `agents/validator.md` - Skips validation when no validation-scripts exist
- `tests/test_unit.py` - 9 new contract domain integration tests

## Decisions Made
- Domain parameter is a name string (not path) throughout the pipeline -- simpler API, resolver handles path mapping
- validate_molecules.py exits gracefully with JSON output when domain has no validation scripts -- prevents pipeline failures for non-biomedical domains
- Agents keep drug-discovery entity/relation types as fallback defaults when no domain SKILL.md is provided -- ensures backward compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_ut013 keyword argument from domain_path to domain_name**
- **Found during:** Task 1
- **Issue:** Existing test called cmd_build(tmpdir, domain_path=str(DOMAIN_YAML)) but signature changed to domain_name
- **Fix:** Changed to cmd_build(tmpdir, domain_name="drug-discovery") to match new API
- **Files modified:** tests/test_unit.py
- **Verification:** All 22 existing tests pass
- **Committed in:** 4de04f5 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary fix for API signature change. No scope creep.

## Issues Encountered
- PyYAML not available on default Python (3.13 from homebrew) but available on Python 3.11 -- used Python 3.11 for all test runs
- Pre-existing ruff warnings in test_unit.py (unused imports, E402) are not from this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full pipeline is domain-aware: adding a new domain requires only creating a skills/{name}-extraction/ directory
- Contract domain package validated with 9 integration tests
- Ready for Phase 02 (contract ingestion) which will use --domain contract throughout

## Known Stubs
None - all functions are fully wired to the domain resolver.

---
*Phase: 01-domain-configuration*
*Completed: 2026-03-29*
