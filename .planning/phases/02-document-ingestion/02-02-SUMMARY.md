---
phase: 02-document-ingestion
plan: 02
subsystem: ingestion
tags: [integration-tests, triage, cli, error-handling, pytest]

# Dependency graph
requires:
  - phase: 02-document-ingestion
    provides: core ingestion module (discover_corpus, parse_document, ingest_corpus)
provides:
  - "6 integration tests covering triage.json output, D-08 metadata, error handling, empty corpus"
  - "Hardened CLI entry point with --help, exit codes, path validation"
  - "is_dir() validation in ingest_corpus"
affects: [extraction-pipeline, contract-analysis]

# Tech tracking
tech-stack:
  added: []
  patterns: [integration test with tmp_path fixtures, shutil.copy for category-folder test setup]

key-files:
  created: []
  modified:
    - tests/test_unit.py
    - scripts/ingest_documents.py

key-decisions:
  - "Normalized whitespace comparison in txt content fidelity test (reader may strip trailing spaces non-deterministically)"
  - "CLI path validation moved to __main__ block for proper exit code 1 on nonexistent paths"

patterns-established:
  - "Integration test naming: test_ingest_integration_* prefix"
  - "Category-folder test setup: copy fixtures into Hotel/AV subdirs under tmp_path"

requirements-completed: [INGS-01, INGS-02, INGS-03, INGS-04, INGS-08]

# Metrics
duration: 4min
completed: 2026-03-29
---

# Phase 02 Plan 02: Ingestion Integration Tests and CLI Hardening Summary

**6 integration tests validating triage.json output, D-08 metadata fields, error handling for corrupt files, and hardened CLI entry point with --help and exit codes**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-29T23:24:48Z
- **Completed:** 2026-03-29T23:28:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added 6 integration tests covering triage.json structure, all 10 D-08 metadata fields, corrupt file handling, empty corpus, text file output, and content fidelity
- Fixed CLI to handle --help flag (exit 0), nonexistent paths (exit 1), and file-not-directory validation
- All 28 tests pass (1 pre-existing failure in UT-013 unrelated to ingestion)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add integration tests for triage output and error handling** - `93b5aab` (test) - 6 integration tests with TDD approach
2. **Task 2: Validate CLI entry point and end-to-end run** - `1c89847` (feat) - CLI hardening, ruff fixes, e2e verification

## Files Created/Modified
- `tests/test_unit.py` - Added 6 integration tests (test_ingest_integration_*) with shutil-based fixture setup
- `scripts/ingest_documents.py` - Fixed CLI --help handling, exit codes, added is_dir() check, output_dir creation

## Decisions Made
- Normalized whitespace in txt content fidelity test to handle potential trailing space differences from sift-kg reader
- Moved corpus path existence check to __main__ block so CLI exits with code 1 (ingest_corpus still returns error dict for programmatic use)
- Added explicit output_dir.mkdir() before ingested/ subdirectory creation for robustness

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CLI --help treated as corpus path**
- **Found during:** Task 2
- **Issue:** --help flag was passed to Path() as a corpus path, resulting in "path does not exist" error
- **Fix:** Added --help check before path parsing in __main__ block
- **Files modified:** scripts/ingest_documents.py
- **Committed in:** 1c89847

**2. [Rule 1 - Bug] Nonexistent corpus path exited with code 0**
- **Found during:** Task 2
- **Issue:** ingest_corpus returned error dict but __main__ continued to exit 0
- **Fix:** Moved path existence check to __main__ block with sys.exit(1)
- **Files modified:** scripts/ingest_documents.py
- **Committed in:** 1c89847

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** CLI edge case fixes necessary for correct operation. No scope creep.

## Issues Encountered
- Pre-existing test failure (UT-013: cmd_build() API change) unrelated to ingestion -- not fixed (out of scope)

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all tests and functions are fully implemented.

## Next Phase Readiness
- Ingestion pipeline fully tested with 15 unit + integration tests
- triage.json format validated end-to-end with all D-08 fields
- CLI ready for real corpus ingestion
- Phase 2 complete -- ready for Phase 3 (entity extraction)

---
*Phase: 02-document-ingestion*
*Completed: 2026-03-29*
