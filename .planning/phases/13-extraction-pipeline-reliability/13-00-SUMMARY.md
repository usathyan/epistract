---
phase: 13-extraction-pipeline-reliability
plan: 00
subsystem: testing
tags: [requirements, test-fixtures, normalization, pydantic, document-extraction]

# Dependency graph
requires:
  - phase: 12-extend-epistemic-classifier-with-structural-biology-document-signature
    provides: FIDL-01 v3 requirement precedent + loud-failure posture for extraction contract violations
provides:
  - FIDL-02a/b/c registered in REQUIREMENTS.md (body + v3 traceability table)
  - 11 Phase 13 unit test rows (UT-017..UT-030 with UT-022 split into a/b) in tests/TEST_REQUIREMENTS.md
  - 2 Phase 13 e2e test rows (FT-009, FT-010) in tests/TEST_REQUIREMENTS.md
  - tests/fixtures/normalization/ with 24 JSON files (23 logical docs post-dedupe) covering all Bug-4 failure modes
  - tests/fixtures/normalization_below_threshold/ with 2 survivors + 8 unrecoverable files for --fail-threshold abort coverage
affects:
  - 13-01-PLAN.md (needs FIDL-02c rows + drift fixture)
  - 13-02-PLAN.md (needs FIDL-02b rows + 24-file reproducer corpus)
  - 13-03-PLAN.md (needs FIDL-02a rows + UT-017/018)
  - 13-04-PLAN.md (needs FT-009 + FT-010 fixtures)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Scaffolding-first Wave 0 — requirement rows, traceability rows, and fixtures land before any code changes so parallel downstream plans have shared dependencies already on disk
    - Fixture corpora generated programmatically from a canonical body template so schema drift is introduced surgically in named files rather than hand-edited everywhere
    - UT-022 split into UT-022a (build_extraction._normalize_fields unit) + UT-022b (normalize_extractions module-level) — one requirement, two enforcement layers, two test IDs

key-files:
  created:
    - tests/fixtures/normalization/_README.md
    - tests/fixtures/normalization/good_01.json .. good_16.json (16 good files)
    - tests/fixtures/normalization/variant_raw.json
    - tests/fixtures/normalization/weird_extraction_input.json
    - tests/fixtures/normalization/hyphen-extraction.json
    - tests/fixtures/normalization/missing_id_alpha.json
    - tests/fixtures/normalization/missing_id_beta.json
    - tests/fixtures/normalization/dupe_target.json
    - tests/fixtures/normalization/dupe_target_raw.json
    - tests/fixtures/normalization/drift_bad_field.json
    - tests/fixtures/normalization_below_threshold/_README.md
    - tests/fixtures/normalization_below_threshold/survivor_01.json
    - tests/fixtures/normalization_below_threshold/survivor_02.json
    - tests/fixtures/normalization_below_threshold/bad_01.json .. bad_08.json (8 unrecoverable files)
  modified:
    - .planning/REQUIREMENTS.md
    - tests/TEST_REQUIREMENTS.md

key-decisions:
  - "Duplicate pair (dupe_target + dupe_target_raw) placed in Group D with the richer 8-entity/4-relation body in the _raw variant so the composite score 1000*has_id + len(entities) + len(relations) guarantees the richer version survives dedupe (1012 > 1003)"
  - "drift_bad_field only corrupts entity 0 — entity 1 stays canonical — so the unit test can assert coercion fired on exactly the drifted entity"
  - "bad_02 uses entities=\"not-a-list\" rather than missing entities+relations entirely, because empty-string document_path is a valid Pydantic default — we needed a different failure mode to guarantee unrecoverability"

patterns-established:
  - "Fixture corpora live under tests/fixtures/normalization*/ with _README.md explaining intent — adopted from tests/fixtures/ convention already used for sample_extraction_*.json"
  - "Test IDs for Phase 13 occupy UT-017 onwards, continuing from the v1 UT-001..UT-016 range; e2e tests continue from FT-008 as FT-009/010"
  - "Requirement IDs for v3 use Theme-letter + sequence number (FIDL-01 for Phase 12, FIDL-02a/b/c for Phase 13 to reflect the three-prong split of Bug 4 + Enh 2/3 + Part 1 Item 4)"

requirements-completed:
  - FIDL-02a
  - FIDL-02b
  - FIDL-02c

# Metrics
duration: 4min
completed: 2026-04-17
---

# Phase 13 Plan 00: Wave 0 Scaffolding Summary

**FIDL-02a/b/c registered in REQUIREMENTS + TEST_REQUIREMENTS plus 24-file Bug-4 reproducer and 10-file below-threshold fixture corpora for downstream Plans 01-04 to consume immediately.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-17T12:16Z
- **Completed:** 2026-04-17T12:20Z
- **Tasks:** 4
- **Files modified:** 38 (2 edited + 36 created)

## Accomplishments

- Three v3 requirements (FIDL-02a/b/c) registered in REQUIREMENTS.md with per-row plan traceability (13-01/02/03/04)
- 13 test rows added to TEST_REQUIREMENTS.md — 11 unit + 2 e2e — all traceable to FIDL-02a/b/c
- 24 physical JSON files in `tests/fixtures/normalization/` covering every Bug-4 failure mode observed in the axmp-compliance 23-doc build (variant filenames, missing `document_id`, duplicate `doc_id`, schema drift); 23 logical docs post-dedupe
- 10 JSON files in `tests/fixtures/normalization_below_threshold/` — 2 recoverable survivors + 8 unrecoverable failure modes — giving the `--fail-threshold` abort path deterministic e2e coverage
- UT-022 intentionally split into UT-022a (`build_extraction._normalize_fields` unit) + UT-022b (`normalize_extractions()` module-level) so the two-layer defense (D-06 write-time + D-03 normalize-time) each has an independent test ID

## Task Commits

Each task was committed atomically:

1. **Task 1: Register FIDL-02a/b/c in REQUIREMENTS.md** - `58b6c80` (docs)
2. **Task 2: Register Phase 13 test IDs in tests/TEST_REQUIREMENTS.md** - `6c561ba` (docs)
3. **Task 3: Create normalization fixture corpus (24 files → 23 logical docs)** - `bfa62a7` (test)
4. **Task 4: Create below-threshold fixture corpus** - `7d9526c` (test)

**Plan metadata:** `4bd2fed` (docs: complete Wave 0 scaffolding plan)

## Files Created/Modified

### Modified
- `.planning/REQUIREMENTS.md` — +3 body rows (FIDL-02a/b/c) under new "Extraction Pipeline Reliability (Phase 13)" subsection; +3 traceability rows in v3 table; footer bumped to 2026-04-17
- `tests/TEST_REQUIREMENTS.md` — +89 lines registering Section 5 with UT-017..UT-030 (UT-022 split) + FT-009 + FT-010 before Section 4 Traceability Matrix

### Created
- `tests/fixtures/normalization/` — 24 JSON files + `_README.md` (Group A: good_01..good_16; Group B: variant_raw.json, weird_extraction_input.json, hyphen-extraction.json; Group C: missing_id_alpha.json, missing_id_beta.json; Group D: dupe_target.json + dupe_target_raw.json; Group E: drift_bad_field.json)
- `tests/fixtures/normalization_below_threshold/` — 10 JSON files + `_README.md` (survivor_01.json, survivor_02.json; bad_01..bad_08.json)

## Decisions Made

- **UT-022 split into UT-022a + UT-022b** — Plan text explicitly requires the two-layer defense (build_extraction + normalize_extractions) to each have an independent test ID so future regressions pinpoint which layer regressed. Followed plan as specified.
- **Dedupe composite score** — Followed plan: `has_document_id*1000 + len(entities) + len(relations)`. Group D designed so the richer `dupe_target_raw.json` (score 1012) wins over the canonical-named `dupe_target.json` (score 1003), exercising the tie-break path through the _raw suffix rather than relying on filename preference.
- **bad_02 failure mode** — Plan hinted at "empty-string fallback OK, so make this one fail differently"; implemented as `entities="not-a-list"` (string instead of list). This guarantees Pydantic validation fails with a clear type error that normalization cannot rescue.

## Deviations from Plan

None - plan executed exactly as written. Every acceptance criterion passed on first try (see Self-Check below).

## Issues Encountered

- **`.planning/` gitignored** — First `git add .planning/REQUIREMENTS.md` attempt printed the "ignored by .gitignore" hint, but the file was already tracked so the modification staged correctly on a status re-check. No workaround needed; the file is in the git index from prior phases.
- **Parallel executor commits interleaved** — The orchestrator spawned a parallel 13-01 executor; commits `02a7a52` and `b93ff32` from that plan appear between our task commits. All four 13-00 commits (`58b6c80`, `6c561ba`, `bfa62a7`, `7d9526c`) are intact and in order. This is expected behaviour under `<parallel_execution>`.

## User Setup Required

None - Wave 0 is documentation + fixtures only. No runtime configuration or external services involved.

## Next Phase Readiness

**Ready for Plans 13-01 / 13-02 / 13-03 / 13-04:**
- FIDL-02a/b/c rows exist — acceptance criteria in downstream plans can reference them directly
- TEST_REQUIREMENTS.md has placeholders for every unit + e2e test that Plans 01-04 need to add
- `tests/fixtures/normalization/` is ready for Plan 02 unit tests and Plan 04 FT-009 to load without collecting real corpora
- `tests/fixtures/normalization_below_threshold/` is ready for Plan 04 FT-010 to exercise the `--fail-threshold` abort path

**No blockers.** Downstream plans can proceed in parallel since Wave 0 had no wave dependencies.

## Self-Check

**Files verified on disk:**
- FOUND: .planning/REQUIREMENTS.md (FIDL-02a/b/c body + traceability rows present)
- FOUND: tests/TEST_REQUIREMENTS.md (Section 5 with 11 UT + 2 FT rows present)
- FOUND: tests/fixtures/normalization/ (24 *.json files + _README.md)
- FOUND: tests/fixtures/normalization_below_threshold/ (10 *.json files + _README.md)

**Commits verified:**
- FOUND: 58b6c80 docs(13-00): register FIDL-02a/b/c requirements for Phase 13
- FOUND: 6c561ba docs(13-00): register Phase 13 test IDs in TEST_REQUIREMENTS.md
- FOUND: bfa62a7 test(13-00): add Bug-4 reproducer fixture corpus (24 files → 23 docs)
- FOUND: 7d9526c test(13-00): add --fail-threshold abort fixture corpus

## Self-Check: PASSED

---
*Phase: 13-extraction-pipeline-reliability*
*Completed: 2026-04-17*
