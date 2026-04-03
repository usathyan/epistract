---
phase: 02-document-ingestion
plan: 01
subsystem: ingestion
tags: [pdf, xlsx, kreuzberg, sift-kg, document-parsing, triage]

# Dependency graph
requires:
  - phase: 01-domain-config
    provides: domain resolver, sift-kg reader infrastructure
provides:
  - "Core ingestion module (discover_corpus, parse_document, sanitize_doc_id, detect_category, ingest_corpus)"
  - "Synthetic test fixtures (2 PDFs, 1 XLSX) for offline testing"
  - "triage.json metadata report format"
  - "9 unit tests for ingestion functions"
affects: [02-02, extraction-pipeline, contract-analysis]

# Tech tracking
tech-stack:
  added: [fpdf2, openpyxl]
  patterns: [sift-kg reader integration, triage.json metadata format, Rich progress bar, conditional reader fallback]

key-files:
  created:
    - scripts/ingest_documents.py
    - tests/fixtures/sample_contract_a.pdf
    - tests/fixtures/sample_contract_b.pdf
    - tests/fixtures/sample_spreadsheet.xlsx
  modified:
    - tests/test_unit.py

key-decisions:
  - "Used lstrip('_') instead of strip('_') for doc IDs to preserve trailing underscores from parenthesized filenames"
  - "Used sift-kg read_document as primary parser with plain-text .txt fallback"
  - "Readiness score uses 3-component heuristic: text density (0.4), structure signals (0.3), length threshold (0.3)"

patterns-established:
  - "Ingestion pattern: discover -> parse -> metadata -> write text -> triage.json"
  - "Conditional sift-kg import with HAS_SIFT_READER availability flag"
  - "KNOWN_CATEGORIES set for folder-based category detection"

requirements-completed: [INGS-05, INGS-06, INGS-07, INGS-09, INGS-10]

# Metrics
duration: 3min
completed: 2026-03-29
---

# Phase 02 Plan 01: Ingestion Core Summary

**Core document ingestion module with corpus scanning, PDF/XLSX parsing via sift-kg reader, category detection, and triage.json metadata output**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-29T23:17:37Z
- **Completed:** 2026-03-29T23:21:19Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created 3 synthetic test fixtures (2 PDF contracts, 1 XLSX vendor summary) for offline development
- Built scripts/ingest_documents.py with 8 exported functions following established script patterns
- Added 9 unit tests covering all core functions, all 23 tests (14 existing + 9 new) passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test fixtures and ingestion unit tests** - `c542e4f` (test) - TDD RED: fixtures + failing tests
2. **Task 2: Create core ingestion module** - `b9840bb` (feat) - TDD GREEN: implementation passing all tests

_Note: TDD task with RED/GREEN commits._

## Files Created/Modified
- `scripts/ingest_documents.py` - Core ingestion pipeline: 8 functions for corpus discovery, parsing, metadata, triage
- `tests/fixtures/sample_contract_a.pdf` - Synthetic catering contract (Aramark, Sample 2026)
- `tests/fixtures/sample_contract_b.pdf` - Synthetic AV contract (PSAV/Encore)
- `tests/fixtures/sample_spreadsheet.xlsx` - Vendor summary spreadsheet (4 vendors)
- `tests/test_unit.py` - Added 9 ingestion tests with HAS_INGEST conditional import

## Decisions Made
- Used lstrip('_') instead of strip('_') for sanitize_doc_id to preserve trailing underscores from parenthesized filenames (e.g., "PCC Rental Agreement (2026).PDF" -> "pcc_rental_agreement__2026_")
- sift-kg read_document as primary parser; plain-text fallback for .txt files when sift-kg unavailable
- Readiness score is a 3-component heuristic (density 0.4, structure 0.3, length 0.3) -- tunable thresholds for real contract corpus

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sanitize_doc_id trailing underscore behavior**
- **Found during:** Task 2 (core ingestion module)
- **Issue:** Plan expected trailing underscore preserved for parenthesized filenames, but strip("_") removed it
- **Fix:** Changed to lstrip("_") to only remove leading underscores
- **Files modified:** scripts/ingest_documents.py
- **Verification:** test_ingest_sanitize_doc_id_parens passes
- **Committed in:** b9840bb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minor behavioral fix to match expected doc ID format. No scope creep.

## Issues Encountered
- fpdf2 and openpyxl not pre-installed -- installed via `uv pip install --system` (dev dependencies for fixture generation)

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all functions are fully implemented with real sift-kg reader integration.

## Next Phase Readiness
- Ingestion module ready for Plan 02 (triage pipeline, extraction orchestration)
- parse_document successfully reads synthetic PDFs via sift-kg reader
- triage.json format established for downstream consumption
- Real contract corpus can be ingested once available at configured path

---
*Phase: 02-document-ingestion*
*Completed: 2026-03-29*
