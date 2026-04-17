---
phase: 13-extraction-pipeline-reliability
plan: 04
subsystem: testing
tags: [e2e, normalization, sift-kg, pydantic, fail-threshold, bug-4-reproducer, document-extraction]

# Dependency graph
requires:
  - phase: 13-extraction-pipeline-reliability
    provides: 24-file Bug-4 reproducer + 10-file below-threshold fixtures (Plan 13-00 Wave 0)
  - phase: 13-extraction-pipeline-reliability
    provides: normalize_extractions public API + CLI --fail-threshold (Plan 13-02 Wave 2)
  - phase: 13-extraction-pipeline-reliability
    provides: /epistract:ingest Step 3.5 wiring + extractor.md contract (Plan 13-03 Wave 3)
provides:
  - FT-009 test_e2e_bug4_normalization_95pct — 24-file Bug-4 reproducer flows through normalize_extractions -> sift_kg.build at >=95% pass rate with non-empty graph
  - FT-010 test_e2e_fail_threshold_aborts — below-threshold fixture aborts the pipeline (exit 1) BEFORE graph_data.json is created
  - Loader-compatible on-disk provenance defaults in normalize_extractions.py — substitutes sift-kg defaults (0.0 / "") for null cost_usd / model_used so canonical extractions actually reach sift-kg's graph builder (closes the 30% silent-drop bug end-to-end)
  - Phase 13 acceptance target met end-to-end: >=95% load rate on 20+ doc corpus AND abort-before-build on unrecoverable corpora
affects:
  - Phase 13 complete — all five plans shipped
  - /epistract:ingest operational guarantees: users now get either >=95% load rate OR a clean abort before silent-garbage graphs are built
  - Future phases can treat the extraction contract as settled; focus moves to Phase 14+ (chunk overlap, format parity, graph fidelity)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "End-to-end acceptance test pattern — copy fixture corpus into tmp_path/extractions/, run normalize + build, assert pass_rate threshold AND graph_data.json existence. Reusable for future corpus-scale regression tests."
    - "CLI subprocess regression test pattern — invoke core/normalize_extractions.py as subprocess with --fail-threshold, assert exit code + stderr content + absence-of-build-artifact. Simulates the /epistract:ingest abort path without requiring full pipeline infrastructure."
    - "Asymmetric honest-null contract: agents WRITE null (D-07/D-08 honest-null provenance) but normalize-time on-disk output substitutes sift-kg-compatible defaults before the canonical write. Validation reconciliation (in-memory) and loader reconciliation (on-disk) are separate concerns; this plan added the second."

key-files:
  created:
    - .planning/phases/13-extraction-pipeline-reliability/13-04-SUMMARY.md
    - .planning/phases/13-extraction-pipeline-reliability/deferred-items.md
  modified:
    - tests/test_e2e.py
    - core/normalize_extractions.py

key-decisions:
  - "Applied sift-kg default substitution (cost_usd: 0.0 / model_used: '') to the on-disk canonical file write inside normalize_extractions, not just in-memory validation. Discovered via FT-009 RED step: sift_kg.graph.builder.load_extractions silently drops any file with null provenance (DocumentExtraction declares them non-nullable), so the 24-file reproducer had a 0/23 load rate despite normalization reporting 100% pass_rate. This is Rule 1 (bug) auto-fix — the phase acceptance target (>=95% load rate) was unreachable without it."
  - "Kept the FT-009 and FT-010 test bodies identical to the plan spec — plan-prescribed code verbatim. Only deviation was in core/normalize_extractions.py (the GREEN step for FT-009)."
  - "UT-013 pre-existing failure documented in deferred-items.md rather than auto-fixed. It exercises the direct write_extraction -> cmd_build path (no normalize) and fails for the same root cause. Per SCOPE BOUNDARY: only fix issues directly caused by the current plan's changes. UT-013 was broken by Plan 13-01 commit a98b6a4 and slipped through that plan's self-check. Logged symmetric fix recipe for a follow-up plan."

patterns-established:
  - "TDD-style e2e acceptance tests expose integration gaps that unit tests miss. FT-009 RED revealed that Plan 13-02's in-memory validation reconciliation did NOT include on-disk reconciliation — the unit tests (UT-019..UT-023) all passed because they used the normalize_extractions return value, not the on-disk files + downstream loader."
  - "deferred-items.md as first-class artifact for out-of-scope discoveries during execution. Captures root cause + fix recipe + why-deferred + impact assessment so a future plan can consume it without rediscovery."
  - "Goal-backward verification: phase acceptance target is tested end-to-end with canonical fixtures, not assumed from unit-test green. This caught a symptom that Plans 13-01..13-03 each individually passed but collectively didn't deliver."

requirements-completed:
  - FIDL-02b

# Metrics
duration: 5min
completed: 2026-04-17
---

# Phase 13 Plan 04: Bug-4 Reproducer End-to-End Summary

**Two e2e tests close the Phase 13 acceptance loop: FT-009 proves the 24-file Bug-4 reproducer achieves >=95% load rate through normalize_extractions -> sift_kg.build with a non-empty graph; FT-010 proves the below-threshold fixture aborts the pipeline (exit 1) before graph_data.json is created. The plan also auto-fixed a discovered pipeline-level silent-drop (sift-kg loader rejected null provenance) by substituting sift-kg defaults in normalize_extractions' on-disk write — the only code path remaining between the normalized-in-memory dict and the graph builder.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-17T12:40:34Z
- **Completed:** 2026-04-17T12:45:41Z
- **Tasks:** 2
- **Files modified:** 2 (tests/test_e2e.py, core/normalize_extractions.py)

## Accomplishments

- **FT-009 passes**: 24-file Bug-4 reproducer (the canonical axmp-compliance failure corpus shape) goes end-to-end at >=95% pass rate AND produces a non-empty graph. Without the deviation fix in normalize_extractions, load rate was 0/23 (100% silent drop). After fix: 23/23 loaded, graph built with 11+ nodes.
- **FT-010 passes**: below-threshold fixture (2 survivors + 8 unrecoverable, pass_rate = 0.20) aborts the pipeline with exit code 1, writes the normalization report with `above_threshold: false`, and critically does NOT create graph_data.json. The --fail-threshold gate works end-to-end.
- **Pipeline-level silent-drop bug found + fixed**: FT-009's RED step surfaced a subtle integration gap between Plans 13-01/13-02's in-memory validation reconciliation and the actual on-disk output. normalize_extractions now substitutes sift-kg defaults (0.0 / "") for null provenance at write time, so the canonical extraction JSON is accepted by sift_kg.graph.builder.load_extractions. Phase 13 acceptance target is now reachable for the first time.
- **All 17 Phase 13 tests pass**: UT-017..UT-030 + FT-009 + FT-010. 50/51 full-suite tests pass; the one failure (UT-013) is pre-existing and documented in deferred-items.md.
- **Phase 13 complete**: All five plans (13-00..13-04) shipped. Acceptance target ">=95% load rate on 20+ doc corpus" met end-to-end via FT-009, with abort-before-build confirmed via FT-010.

## Task Commits

Each task was committed atomically:

1. **Task 1 (TDD RED->GREEN): FT-009 e2e test + normalize_extractions on-disk provenance fix** — `ed8ccb1` (test)
2. **Task 2: FT-010 --fail-threshold abort e2e test** — `0eadc34` (test)

## Files Created/Modified

### Created
- `.planning/phases/13-extraction-pipeline-reliability/13-04-SUMMARY.md` — this file
- `.planning/phases/13-extraction-pipeline-reliability/deferred-items.md` — documents pre-existing UT-013 failure (symmetric build_extraction fix) with root cause + recipe + why-deferred

### Modified
- `tests/test_e2e.py` (+117 lines) — two new test functions appended:
  - `test_e2e_bug4_normalization_95pct` (FT-009): stage 24-file fixture, run normalize_extractions, assert pass_rate >= 0.95, run cmd_build, assert graph_data.json exists with >0 nodes
  - `test_e2e_fail_threshold_aborts` (FT-010): stage 10-file fixture, invoke normalize_extractions CLI via subprocess with --fail-threshold 0.95, assert exit 1 + ABORT in stderr + report.above_threshold=False + graph_data.json absent
- `core/normalize_extractions.py` (+12 lines; 3 lines of logic + 9 lines of explanation) — before the canonical on-disk write (line ~230), substitute `record["cost_usd"] = 0.0` and `record["model_used"] = ""` when they are None. Mirror of the in-memory reconciliation already applied during validation; extends the honest-null contract boundary to "before canonical write" instead of "before validation only."

## Decisions Made

- **On-disk provenance substitution in normalize_extractions, not build_extraction** — The deviation fix was scoped to Plan 13-04's module (normalize_extractions) because its mandate is to "standardize extractions so they reach the graph builder." The symmetric fix in build_extraction.py (same 3-line substitution in write_extraction) is required for the direct write_extraction -> cmd_build path that UT-013 exercises, but that path is pre-existing-broken (Plan 13-01 regression) and out of scope per SCOPE BOUNDARY. Fix recipe logged in deferred-items.md.
- **TDD RED phase caught a cross-plan integration gap** — All of Plan 13-02's UT-019..UT-023 passed because they only asserted the normalize_extractions return value, not the on-disk file as consumed by sift-kg's loader. Plan 13-03's UT-017..UT-018 are grep tests, also not integration. FT-009 was the first test in the phase to actually chain normalize_extractions output through sift_kg.graph.builder.load_extractions — and it failed, proving goal-backward e2e coverage was missing and the plan pack's self-checks were insufficient.
- **Pre-existing UT-013 failure documented, not fixed** — Verified via git stash + re-run that UT-013 was failing before Plan 13-04 touched anything. The root cause is the same as FT-009's RED cause (null provenance not substituted at write time), but in build_extraction.write_extraction, not normalize_extractions. Per the deviation rules scope boundary, this is a Plan 13-01 defect; fix recipe in deferred-items.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] normalize_extractions wrote loader-incompatible null provenance to disk**
- **Found during:** Task 1 (FT-009 TDD RED phase)
- **Issue:** normalize_extractions wrote canonical files with `cost_usd: null` and `model_used: null` per D-07/D-08 honest-null contract. But `sift_kg.extract.models.DocumentExtraction` declares `cost_usd: float = 0.0` and `model_used: str = ""` (non-nullable). `sift_kg.graph.builder.load_extractions` silently catches the Pydantic validation error and continues (`logger.warning; continue` at builder.py:313) — every single normalized file was dropped. The 24-file reproducer had pass_rate=100% from normalize_extractions' perspective but 0/23 documents actually reached the graph builder. Phase 13 acceptance target (>=95% load rate) was unreachable.
- **Fix:** Added 3-line substitution in normalize_extractions.py immediately before the canonical file write (after validation success, before `canonical_path.write_text(...)`):
  ```python
  if record.get("cost_usd") is None:
      record["cost_usd"] = 0.0
  if record.get("model_used") is None:
      record["model_used"] = ""
  ```
  This mirrors the in-memory validation reconciliation already established by Plan 13-01 in `build_extraction.write_extraction` and by Plan 13-02 in `normalize_extractions._validate`. The on-disk canonical file is now loader-compatible; agents still WRITE null per D-07/D-08, but normalize_extractions rescues into loadable form at the write boundary.
- **Files modified:** `core/normalize_extractions.py` (+12 lines — 3 lines of logic + 9 lines of explanatory comment)
- **Verification:** FT-009 passes (pass_rate=100%, graph has 11+ nodes from drug-discovery domain). All 6 normalize unit tests (UT-019..UT-023, UT-022b) still pass — they operate on the return value, not on-disk files, so are unaffected. 17 total Phase 13 tests green.
- **Committed in:** `ed8ccb1` (Task 1 commit, bundled with the FT-009 test addition as the TDD GREEN step)

**Rationale for Rule 1 classification:** The phase goal is "Extraction-load rate >=95% on 20+ doc corpora." Without the fix, the normalize step produced output that the graph builder silently rejected — the explicit scenario Phase 13 was created to fix. This is classic correctness bug territory: code that looks right (100% normalize pass_rate reported) but produces wrong downstream behavior (0% graph load rate). Not architectural (Rule 4) — the fix is a 3-line mirror of an existing reconciliation pattern used in two other modules.

---

**Total deviations:** 1 auto-fixed (Rule 1 - correctness bug).
**Impact on plan:** Deviation is essential for the phase to actually achieve its acceptance goal. Not scope creep — the fix is in the same module Plan 13-04 was supposed to be validating (normalize_extractions), and it closes the same 30% silent-drop loophole Phase 13 exists to eliminate. Without it, FT-009 could not pass and the phase goal would be unmet.

## Issues Encountered

- **UT-013 pre-existing failure discovered during regression sweep.** Plan's `<verification>` block includes `python3 -m pytest tests/test_unit.py tests/test_e2e.py -v  # Regression — no existing tests broken` which turned up UT-013 failing. Verified via `git stash` that this was failing on HEAD before Plan 13-04's changes. Root cause is a Plan 13-01 regression: `build_extraction.write_extraction` also writes null provenance to disk, and UT-013's direct `write_extraction -> cmd_build` path (no normalize) exhibits the same silent-drop as FT-009 did. Symmetric fix recipe logged in `deferred-items.md`; out of scope per SCOPE BOUNDARY.
- **FT-009 first run produced a misleading early trace.** The test failed at `cmd_build` raising `FileNotFoundError: No extractions found`, which looks like a fixture staging bug but was actually the silent-drop symptom: load_extractions returned an empty list because all 23 files failed Pydantic validation, then `run_build` raised the FileNotFoundError on empty list. Understanding required tracing into sift-kg's internal `load_extractions` behavior — the `WARNING  sift_kg.graph.builder:builder.py:313 Failed to load good_01.json` lines in the captured log were the real signal.

## User Setup Required

None — test-only and module-internal changes. No external service configuration, environment variables, or runtime dependencies added.

## Next Phase Readiness

**Phase 13 complete.** All five plans shipped; all three requirements (FIDL-02a/b/c) marked complete. Acceptance target met:

- **Load rate**: FT-009 proves 24-file Bug-4 reproducer (23 logical docs) achieves 100% load rate (>=95% gate passed)
- **Abort gate**: FT-010 proves below-threshold fixture (pass_rate=0.20) aborts pipeline before graph build
- **Two-layer defense in place**: extractor.md prompt contract (D-09) + Pydantic write-time validation (D-06) + normalize-time coercion + rescue (D-03) + loader-compatible on-disk format (this plan)

**Ready for Phase 14+:**
- Chunk overlap (Phase 14) can safely assume extraction contract is enforced
- Format discovery parity (Phase 15) can reuse the normalize-pattern for its own validation boundary
- Graph fidelity work (Phase 16-18+) can trust the input contract

**Deferred items for future plans:**
- Symmetric fix in `core/build_extraction.py::write_extraction` (recipe in `.planning/phases/13-extraction-pipeline-reliability/deferred-items.md`) — fixes UT-013 and closes the direct write_extraction path to sift-kg. Small (~3 lines). Candidate for Phase 14's wave-0 housekeeping.

**No blockers.**

## Known Stubs

None. All additions are concrete tests or a 3-line production fix. No placeholders, mock data, or TODO/FIXME markers introduced. The only null-ish values remaining in the codebase are the intentional honest-null provenance in agent-written extractions per D-07/D-08, which are no longer loader-incompatible because normalize_extractions rescues them at the canonical write boundary.

## Self-Check

**Files verified on disk:**
- FOUND: tests/test_e2e.py (test_e2e_bug4_normalization_95pct at line 125, test_e2e_fail_threshold_aborts at line 180)
- FOUND: core/normalize_extractions.py (contains `if record.get("cost_usd") is None` substitution pre-write)
- FOUND: .planning/phases/13-extraction-pipeline-reliability/deferred-items.md (UT-013 logged)
- FOUND: .planning/phases/13-extraction-pipeline-reliability/13-04-SUMMARY.md (this file)

**Commits verified:**
- FOUND: ed8ccb1 test(13-04): add FT-009 e2e test + fix loader-incompat null provenance
- FOUND: 0eadc34 test(13-04): add FT-010 e2e test for --fail-threshold abort

**Test suite verified:**
- PASS: tests/test_e2e.py::test_e2e_bug4_normalization_95pct (FT-009) — 0.91s
- PASS: tests/test_e2e.py::test_e2e_fail_threshold_aborts (FT-010) — 1.43s
- PASS: 6 normalize unit tests (UT-019..UT-023 + UT-022b) — 0.05s; no regression from on-disk substitution change
- PASS: 17 Phase 13 tests total (UT-017..UT-030 + FT-009 + FT-010)
- PASS: 50/51 full-suite (tests/test_unit.py + tests/test_e2e.py); only failure is pre-existing UT-013 documented in deferred-items.md

**Acceptance criteria verified (Task 1):**
- grep 'def test_e2e_bug4_normalization_95pct' tests/test_e2e.py = 1
- grep 'pass_rate >= 0\.95' tests/test_e2e.py = 2
- grep 'FIXTURES_DIR / "normalization"' tests/test_e2e.py = 1
- grep 'from normalize_extractions import normalize_extractions' tests/test_e2e.py = 1
- FT-009 exits 0: PASS

**Acceptance criteria verified (Task 2):**
- grep 'def test_e2e_fail_threshold_aborts' tests/test_e2e.py = 1
- grep 'normalization_below_threshold' tests/test_e2e.py = 2
- grep 'result.returncode == 1' tests/test_e2e.py = 1
- grep 'not graph_path.exists' tests/test_e2e.py = 1
- FT-010 exits 0: PASS

## Self-Check: PASSED

---
*Phase: 13-extraction-pipeline-reliability*
*Completed: 2026-04-17*
