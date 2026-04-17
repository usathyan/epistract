---
phase: 13-extraction-pipeline-reliability
plan: 02
subsystem: extraction-pipeline
tags: [normalization, dedupe, pydantic, cli, sift-kg, document-extraction]

# Dependency graph
requires:
  - phase: 13-extraction-pipeline-reliability
    provides: FIDL-02b requirement row + 24-file Bug-4 reproducer fixture (Plan 13-00 Wave 0)
  - phase: 13-extraction-pipeline-reliability
    provides: Extended _normalize_fields coercion + HAS_SIFT_EXTRACTION_MODEL pattern (Plan 13-01 Wave 1)
provides:
  - Post-extraction normalization module core/normalize_extractions.py (D-03 rules)
  - normalize_extractions(output_dir, fail_threshold=0.95) -> dict public API
  - CLI entry-point with --fail-threshold, exit codes 0/1/2, stderr usage on no-args
  - Extractions dedupe archive convention (_dedupe_archive/) + report (_normalization_report.json)
  - 5 new unit tests: UT-019, UT-020, UT-021, UT-022b, UT-023
affects:
  - 13-03-PLAN.md (extractor.md — belt-and-suspenders: module is the second line of defense behind write-time Pydantic)
  - 13-04-PLAN.md (e2e — FT-009 / FT-010 will drive this module against the 24-file + 10-file fixture corpora)
  - commands/ingest.md (Plan 13-03 will wire normalize_extractions() between Step 3 extract and Step 4 validate)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - HAS_SIFT_EXTRACTION_MODEL guard mirrored from core/build_extraction.py (Plan 01) — optional sift-kg import stays uniform across core modules
    - sys.path bootstrap for PROJECT_ROOT + core/ mirrors build_extraction.py — script can be invoked via absolute path (agent-dispatch style) or module import
    - Composite dedupe score (has_document_id*1000 + len(entities) + len(relations)) locked in with lexicographic filename tie-break
    - sift-kg default substitution during validation (None -> 0.0 / "") — preserves honest-null provenance on disk while still enforcing required-field contract

key-files:
  created:
    - core/normalize_extractions.py
  modified:
    - tests/test_unit.py

key-decisions:
  - "Validation path substitutes sift-kg defaults (0.0/\"\") for None provenance fields, identical to the fix Plan 13-01 applied in build_extraction.write_extraction. Same model, same reconciliation: validation enforces document_id / entity_type / required scalars; honest-null provenance is a separate on-disk contract."
  - "Added sys.path bootstrap (PROJECT_ROOT + core/) so `python3 core/normalize_extractions.py <output_dir>` works as a plain script. Matches the agent-dispatch invocation pattern Plan 13-01 established for build_extraction.py."
  - "Added `not isinstance(record, dict)` guard in _load_and_coerce to handle below-threshold fixture files that contain raw JSON arrays or strings — Plan 13-04 will exercise these via FT-010, so failing loudly at load time (not at _normalize_fields) gives a cleaner report."

patterns-established:
  - "Extractions post-processing lives under extractions/_* prefixed files: _dedupe_archive/ for moved losers, _normalization_report.json for audit."
  - "Variant-filename regex is single-pass and idempotent: `^(.+?)(_raw|_extraction_input|-extraction)$` applied to Path.stem, re-runs on already-canonical files are no-ops."
  - "Composite dedupe score gives document_id presence a 1000-weight dominance over entity/relation counts so a lossy record with richer body never beats an intact-but-smaller record."

requirements-completed:
  - FIDL-02b

# Metrics
duration: 3min
completed: 2026-04-17
---

# Phase 13 Plan 02: normalize_extractions Module Summary

**Post-extraction normalization module + 5 unit tests. Walks output_dir/extractions/, renames variant filenames, infers missing document_id from stem, dedupes same-doc_id via composite score, validates against sift-kg DocumentExtraction, and emits _normalization_report.json with per-file actions. CLI entry-point aborts at pass_rate < --fail-threshold.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-17T12:28:13Z
- **Completed:** 2026-04-17T12:31:09Z
- **Tasks:** 2
- **Files modified:** 2 (1 created + 1 edited)

## Accomplishments

- Belt-and-suspenders second line of defense against the axmp-compliance 30% silent-drop bug — surfaces extraction-contract violations at a known step with explicit per-file actions, replacing `sift_kg/graph/builder.py:308-313`'s `logger.warning; continue`.
- Single-entry-point public API: `normalize_extractions(output_dir, fail_threshold=0.95) -> dict` returning `{pass_rate, report_path, total, passed, recovered, unrecoverable, actions}`.
- All 6 D-03 rules implemented in one pass: rename variants, infer document_id, dedupe duplicates, coerce schema drift (via delegation), validate against Pydantic, write audit report.
- CLI wrapper matching Phase 13 conventions: `python3 core/normalize_extractions.py <output_dir> [--fail-threshold 0.95]`, stderr usage + exit 2 on no-args, exit 1 on below-threshold, exit 0 on success.
- 5 unit tests (UT-019..UT-023, UT-022b) green in 0.05s — well under the plan's 10-second fast-tier budget.
- Plan 13-01 regression tests (UT-022a + UT-024..UT-030) still green — nothing leaked.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build normalize_extractions core module** — `b405a88` (feat)
2. **Task 2: Add UT-019..UT-023 unit tests** — `347d2df` (test)

## Files Created/Modified

### Created
- `core/normalize_extractions.py` (320 lines) — module with `normalize_extractions` public API, `_canonical_stem`, `_score`, `_load_and_coerce`, `_validate` helpers, `_VARIANT_SUFFIX_RE` regex, `_DEDUPE_ARCHIVE` / `_REPORT_NAME` constants, HAS_SIFT_EXTRACTION_MODEL guard, sys.path bootstrap, CLI entry-point.

### Modified
- `tests/test_unit.py` (+145 lines) — new "Phase 13 — FIDL-02b" section:
  - `_write_extraction_file` helper (synthesizes tmp-path fixture JSON)
  - `test_normalize_renames_variant_filenames` (UT-019)
  - `test_normalize_infers_document_id` (UT-020)
  - `test_normalize_dedupes_keeps_richer` (UT-021)
  - `test_normalize_coerces_schema_drift_via_module` (UT-022b)
  - `test_normalize_writes_report` (UT-023)

## Decisions Made

- **sift-kg default substitution during validation** — Same problem Plan 13-01 hit in `build_extraction.write_extraction`: sift-kg's `DocumentExtraction` declares `cost_usd: float = 0.0` and `model_used: str = ""` as non-nullable. The plan contract and Plan 13-01's write path produce honest `null` on disk. Chose the same fix: build a sanitized `payload = dict(record)` and substitute defaults only during `DocumentExtraction(**payload)`. The on-disk file still has null values when unknown. Kept symmetric with Plan 13-01 so any future sift-kg update to allow `Optional` fields applies to both modules identically.
- **Dict-type guard in `_load_and_coerce`** — Plan 13-00's below-threshold fixture includes `bad_03.json` (raw JSON array `[1,2,3]`) and similar malformed files. Without the `isinstance(record, dict)` check, `record.get(...)` would raise `AttributeError` from `_normalize_fields`. Adding the guard classifies these as `unrecoverable_load` with a clear reason (`not_a_json_object: got list`) instead of a stack trace. Plan 13-04's FT-010 will exercise these paths; the guard is belt-and-suspenders.
- **Additional `core/` on sys.path** — `build_extraction.py` only adds PROJECT_ROOT; normalize_extractions also needs `core/` on sys.path so the `from build_extraction import _normalize_fields` resolves when invoked as a plain script (`python3 core/normalize_extractions.py ...`). Module-import path is unaffected (path already present in conftest.py for tests).
- **Followed plan-prescribed code verbatim** for the module body and all five tests. Two minor additions (dict-guard, extra sys.path entry) are documented as deviations below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical] Added `isinstance(record, dict)` guard in `_load_and_coerce`**
- **Found during:** Task 1 module construction (anticipating Plan 13-04 FT-010 fixture)
- **Issue:** Plan spec's `_load_and_coerce` assumes every parseable JSON is a dict. But the below-threshold fixture corpus (Plan 13-00, `tests/fixtures/normalization_below_threshold/bad_03.json`) contains a raw JSON array. Without a type guard, `record.get(...)` would raise `AttributeError` at `_normalize_fields` entry, masking the classification.
- **Fix:** Added early-return path: `if not isinstance(record, dict): return None, f"not_a_json_object: got {type(record).__name__}"`. Matches the error-string style of the existing `unparseable_json` path.
- **Files modified:** `core/normalize_extractions.py` (5 lines)
- **Verification:** All 5 unit tests still pass. Plan 13-04's FT-010 will verify the below-threshold classification works as expected.
- **Committed in:** `b405a88` (Task 1 commit)

**2. [Rule 3 - Blocking] Added `core/` to sys.path bootstrap**
- **Found during:** Task 1 module authoring (comparing to build_extraction.py preamble)
- **Issue:** Plan code adds only PROJECT_ROOT to sys.path (identical to build_extraction.py). But `normalize_extractions.py` imports `from build_extraction import _normalize_fields` — a sibling import. When invoked as `python3 core/normalize_extractions.py <dir>`, Python prepends the script's dir to sys.path, so this works. But when invoked from an arbitrary CWD via absolute path (`python3 /plugin-root/core/normalize_extractions.py ...`), sibling import resolves via sys.path only. Belt-and-suspenders: add `core/` dir explicitly.
- **Fix:** Added 3 more lines after the PROJECT_ROOT bootstrap: `_CORE_DIR = Path(__file__).resolve().parent; if str(_CORE_DIR) not in sys.path: sys.path.insert(0, str(_CORE_DIR))`.
- **Files modified:** `core/normalize_extractions.py` (3 lines)
- **Verification:** Module imports cleanly from tests (conftest already has core/ on sys.path) and from CLI smoke test in /tmp CWD.
- **Committed in:** `b405a88` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 Rule 2 defensive, 1 Rule 3 blocking — both to ensure agent-style CLI invocation works reliably).

**Impact on plan:** Both fixes are defensive hardening discovered while implementing. Neither changes the plan's stated behavior; they only make edge cases (malformed non-dict JSON, absolute-path CLI invocation) behave per the plan's spirit rather than crashing with a stack trace.

## Issues Encountered

- **Plan spec suggested "at least 100 lines"** — Final file is 320 lines. The extra lines come from: the docstring block (30 lines of documentation exactly as specified), the CLI block (50 lines of sys.argv parsing + error handling), and the two sys.path bootstraps. No scope creep; every line matches the plan body.
- **Parallel executor interleaving not observed this run** — 13-02 executor ran to completion with no interference; both task commits (`b405a88`, `347d2df`) are sequential in git log.

## User Setup Required

None — module is self-contained with a graceful sift-kg-missing fallback (`_validate` returns None when `HAS_SIFT_EXTRACTION_MODEL` is False, per plan spec). No external services or environment variables required.

## Next Phase Readiness

**Ready for Plan 13-03 (commands/ingest.md Step 3.5 wiring):**
- Public API is stable: `normalize_extractions(output_dir, fail_threshold=0.95) -> dict`. Plan 13-03's ingest.md update can call this directly or via CLI with `--fail-threshold`.
- Return dict provides `pass_rate` for caller gating and `report_path` for log linkage.
- CLI exits 0/1/2 per RESEARCH.md pattern — plan 03 can chain `python3 core/normalize_extractions.py "$OUT" --fail-threshold "$FT" || exit $?` directly.

**Ready for Plan 13-04 (e2e regression FT-009 / FT-010):**
- 24-file reproducer fixture (`tests/fixtures/normalization/`) can be copied to `tmp/extractions/` and normalized — expected 23 logical docs at 100% pass_rate.
- 10-file below-threshold fixture (`tests/fixtures/normalization_below_threshold/`) — expected 2 survivors / 8 unrecoverable → pass_rate ≈ 20% → exit 1 with ABORT message.
- Dict-guard handles malformed non-dict JSON classified as `unrecoverable_load`.

**No blockers.**

## Known Stubs

None. The module has no placeholder values, hardcoded mock data, or TODO/FIXME markers. All behavior is wired to real fixtures; Plan 13-04 will extend coverage to the 24-file and 10-file corpora.

## Self-Check

**Files verified on disk:**
- FOUND: core/normalize_extractions.py (320 lines, normalize_extractions public API, _VARIANT_SUFFIX_RE, _dedupe_archive, _normalization_report.json, HAS_SIFT_EXTRACTION_MODEL, from __future__ import annotations, has_doc_id * 1000 score, CLI with --fail-threshold)
- FOUND: tests/test_unit.py (contains all 5 test function defs + _write_extraction_file helper)
- FOUND: .planning/phases/13-extraction-pipeline-reliability/13-02-SUMMARY.md

**Commits verified:**
- FOUND: b405a88 feat(13-02): add normalize_extractions module
- FOUND: 347d2df test(13-02): add UT-019..UT-023 for normalize_extractions

**Test suite verified:**
- PASS: tests/test_unit.py::test_normalize_renames_variant_filenames (UT-019)
- PASS: tests/test_unit.py::test_normalize_infers_document_id (UT-020)
- PASS: tests/test_unit.py::test_normalize_dedupes_keeps_richer (UT-021)
- PASS: tests/test_unit.py::test_normalize_coerces_schema_drift_via_module (UT-022b)
- PASS: tests/test_unit.py::test_normalize_writes_report (UT-023)

**CLI smoke tests verified:**
- PASS: no-arg invocation prints `Usage:` and exits 2
- PASS: valid invocation prints `Normalized 1 files: 1 pass, 0 recovered, 0 unrecoverable (pass_rate=100.00%)` and exits 0

**Plan 13-01 regression verified:**
- PASS: 8 Plan 13-01 tests (UT-022a + UT-024..UT-030) still green — no regressions introduced.

## Self-Check: PASSED

---
*Phase: 13-extraction-pipeline-reliability*
*Completed: 2026-04-17*
