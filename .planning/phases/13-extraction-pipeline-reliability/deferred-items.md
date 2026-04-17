# Phase 13 — Deferred Items

Items discovered during execution that are out of scope for the current plan.

## Logged during Plan 13-04 execution (2026-04-17)

### UT-013 pre-existing failure (`test_ut013_run_sift_build`)

**Discovered:** During Plan 13-04 Task 2 full regression sweep.

**Location:** `tests/test_unit.py::test_ut013_run_sift_build`

**Symptom:** Test fails with `FileNotFoundError: No extractions found` after calling `write_extraction()` directly then `cmd_build`.

**Root cause:** Same 30% silent-drop bug that Phase 13 addresses, but in a different entry path. Plan 13-01 (commit `a98b6a4`) changed `core/build_extraction.py::write_extraction()` to default `cost_usd=None` / `model_used=None`, writing null to disk per D-07/D-08 honest-null provenance. `sift_kg.graph.builder.load_extractions()` then silently drops files with null for these fields (DocumentExtraction declares them non-nullable float / str defaults).

**Why not fixed in 13-04:**
- Plan 13-04 scope is the acceptance test (FT-009 + FT-010), not module-level fixes
- The `/epistract:ingest` path (Plans 13-02/03) runs `normalize_extractions` between write and build; Plan 13-04's fix in `normalize_extractions` makes the end-to-end user-facing pipeline achieve ≥95% load rate (FT-009 proves this)
- UT-013's direct `write_extraction → cmd_build` path bypasses normalize, so it still demonstrates the bug. This is a Plan 13-01 defect: `write_extraction` should apply the same sift-kg default substitution when writing to disk
- Per execution rules SCOPE BOUNDARY: "Only auto-fix issues DIRECTLY caused by the current task's changes"

**Symmetric fix (for a follow-up plan):**
Apply the same substitution `build_extraction.py::write_extraction` already does during in-memory validation to the on-disk payload too:

```python
# After line 119 (after building `extraction` dict), before write:
if extraction.get("cost_usd") is None:
    extraction["cost_usd"] = 0.0
if extraction.get("model_used") is None:
    extraction["model_used"] = ""
```

This mirrors what Plan 13-04 applied in `core/normalize_extractions.py`.

**Status:** RESOLVED in commit `2898571` (fix(13-01): apply sift-kg defaults on disk in write_extraction). Applied symmetric substitution in `write_extraction` mirroring the fix in `normalize_extractions`. UT-029 / UT-030 updated to assert the new on-disk contract (sift-kg defaults, not null). All 47 unit+e2e tests pass. Option A chosen during phase verification: preserves direct-path backward compatibility over "honest null" on disk.

**Impact (pre-resolution):** The documented user path (`/epistract:ingest`) always ran normalize, so the phase acceptance goal (≥95% load rate) was met end-to-end. Direct `build_extraction` invocation without normalize was broken. Post-resolution, both paths work.
