---
phase: 21-clinicaltrials-pubchem-domain
plan: "00"
subsystem: testing
tags: [wave-0, stubs, fixtures, clinicaltrials, pubchem, tdd-red]
dependency_graph:
  requires: []
  provides:
    - "tests/fixtures/clinicaltrials/ — 4 fixture files for CT.gov + PubChem mocks"
    - "tests/test_unit.py — 12 CTDM Wave 0 stub tests (red)"
    - ".planning/phases/21-clinicaltrials-pubchem-domain/21-VALIDATION.md — nyquist_compliant=true"
  affects:
    - "tests/test_unit.py"
    - "tests/fixtures/clinicaltrials/"
tech_stack:
  added: []
  patterns:
    - "unittest.mock.patch + MagicMock for HTTP stub tests"
    - "importlib.import_module for domain-local module import in tests"
key_files:
  created:
    - tests/fixtures/clinicaltrials/sample_ct_protocol.txt
    - tests/fixtures/clinicaltrials/mock_ctgov_NCT04303780.json
    - tests/fixtures/clinicaltrials/mock_pubchem_remdesivir.json
    - tests/fixtures/clinicaltrials/mock_pubchem_notfound.json
    - .planning/phases/21-clinicaltrials-pubchem-domain/21-VALIDATION.md (updated)
  modified:
    - tests/test_unit.py
decisions:
  - "Wave 0 stubs use importlib.import_module('enrich') so domain-local enrich.py can be imported without adding clinicaltrials to conftest sys.path at module load time — keeps test isolation clean until Plan 21-02 lands the file"
  - "FIXTURES_DIR added to conftest import in test_unit.py (was already exported from conftest.py but not imported in test_unit.py)"
  - "21-VALIDATION.md lives in git-ignored .planning/ — updated on filesystem in both worktree and main repo location; orchestrator owns any git tracking"
metrics:
  duration: "5 minutes"
  completed: "2026-04-18"
  tasks_completed: 3
  files_changed: 6
requirements: [CTDM-01, CTDM-02, CTDM-03, CTDM-04, CTDM-05, CTDM-06]
---

# Phase 21 Plan 00: ClinicalTrials + PubChem Wave 0 Test Scaffolding Summary

**One-liner:** Wave 0 red-test scaffold — 12 CTDM stub tests in test_unit.py plus 4 verified CT.gov/PubChem fixture files — gives Plans 21-01 and 21-02 a concrete failing definition of done.

---

## What Was Built

### Task 1: Clinicaltrials Test Fixtures (commit `88ea2c5`)

Four fixture files created under `tests/fixtures/clinicaltrials/`:

| File | Purpose |
|------|---------|
| `sample_ct_protocol.txt` | Realistic CT protocol prose (CodeBreaK 200 / NCT04303780); contains `NCT04303780`, `remdesivir`, `ibuprofen`, `Phase 3`, `Amgen` |
| `mock_ctgov_NCT04303780.json` | Verified CT.gov v2 response shape: `protocolSection.designModule.phases=["PHASE3"]`, `enrollmentInfo.count=345`, `overallStatus="ACTIVE_NOT_RECRUITING"` |
| `mock_pubchem_remdesivir.json` | PubChem PUG REST response with `ConnectivitySMILES` key (not `CanonicalSMILES`) — Pitfall 2 guard; CID=121304016, MolecularFormula=C27H35N6O8P |
| `mock_pubchem_notfound.json` | PubChem 404 body: `{"Fault": {"Code": "PUGREST.NotFound", ...}}` |

### Task 2: Wave 0 CTDM Stub Tests (commit `633c6bb`)

12 stub tests appended to `tests/test_unit.py`, organized by requirement:

| Tests | Requirement | What They Check (when green) |
|-------|-------------|------------------------------|
| `test_ctdm01_*` (3) | CTDM-01 | domain.yaml loads with 12 entity/10 relation types; `list_domains()` returns "clinicaltrials"; "clinicaltrial" alias resolves |
| `test_ctdm02_*` (1) | CTDM-02 | SKILL.md exists and contains "NCT" + "Phase" strings |
| `test_ctdm03_*` (2) | CTDM-03 | Epistemic dispatcher finds `analyze_clinicaltrials_epistemic`; function returns claims layer dict with required keys |
| `test_ctdm04_*` (2) | CTDM-04 | `_fetch_ct_gov` parses CT.gov v2 response; 404 returns None |
| `test_ctdm05_*` (2) | CTDM-05 | `_fetch_pubchem` reads `ConnectivitySMILES` into `canonical_smiles`; 404 returns None |
| `test_ctdm06_*` (2) | CTDM-06 | `enrich_graph` writes `_enrichment_report.json`; `ConnectionError` returns None without raising |

All 12 tests **fail (red)** today — the implementation does not exist yet. That is the correct Wave 0 state.

### Task 3: Mark Wave 0 Complete in 21-VALIDATION.md (filesystem only — .planning/ is gitignored)

- `nyquist_compliant: false` → `nyquist_compliant: true`
- `wave_0_complete: false` → `wave_0_complete: true`
- Both Wave 0 requirement checkboxes marked `[x]`
- Approval updated to: `approved — Wave 0 tests landed in Plan 21-00 on 2026-04-18`

---

## Verification Results

```
$ python3 -m pytest tests/test_unit.py -k "ctdm" --collect-only -q
12/58 tests collected

$ python3 -m pytest tests/test_unit.py -k "ctdm" -v
12 FAILED — all red (expected Wave 0 state)
```

All 4 fixture files present and JSON-validated:
- `ConnectivitySMILES` key verified in PubChem mock
- `protocolSection.designModule.enrollmentInfo.count == 345` verified in CT.gov mock
- `Fault.Code == "PUGREST.NotFound"` verified in 404 mock
- `NCT04303780`, `remdesivir`, `ibuprofen` verified in protocol text

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] FIXTURES_DIR not imported in test_unit.py**
- **Found during:** Task 2
- **Issue:** `FIXTURES_DIR` was exported from `conftest.py` but not imported in `test_unit.py` — required by stub tests using `CT_FIXTURES = FIXTURES_DIR / "clinicaltrials"`
- **Fix:** Added `FIXTURES_DIR` to the `from conftest import ...` line and added `from unittest.mock import patch, MagicMock`
- **Files modified:** `tests/test_unit.py`
- **Commit:** `633c6bb`

**2. [Rule 3 - Blocking issue] Phase 21 planning files not in worktree git history**
- **Found during:** Task 3
- **Issue:** `.planning/phases/21-clinicaltrials-pubchem-domain/` exists in the main repo filesystem but was never committed (`.planning/` is gitignored). The worktree branches from the committed state, so the directory was absent.
- **Fix:** Created the directory in the worktree, copied VALIDATION.md from main repo, edited it, then copied updated version back to main repo location. No git commit needed (gitignored).
- **Files modified:** `.planning/phases/21-clinicaltrials-pubchem-domain/21-VALIDATION.md` (filesystem only)

---

## Known Stubs

All 12 CTDM tests are intentional stubs — they exercise paths that do not exist until Plans 21-01 and 21-02. This is the designed Wave 0 state (red), not an error. Each stub's failure message clearly identifies the missing component:
- CTDM-01..03: `FileNotFoundError` / `AssertionError` — `domains/clinicaltrials/` absent
- CTDM-04..06: `ModuleNotFoundError` — `domains/clinicaltrials/enrich.py` absent

---

## Threat Flags

None — this plan creates only static test fixtures (public registry data) and stub test functions. No new network endpoints, auth paths, or schema changes introduced.

---

## Self-Check

### Created files exist:

```
tests/fixtures/clinicaltrials/sample_ct_protocol.txt ............. FOUND
tests/fixtures/clinicaltrials/mock_ctgov_NCT04303780.json ........ FOUND
tests/fixtures/clinicaltrials/mock_pubchem_remdesivir.json ....... FOUND
tests/fixtures/clinicaltrials/mock_pubchem_notfound.json ......... FOUND
```

### Commits exist:

```
88ea2c5 feat(21-00): create clinicaltrials test fixtures
633c6bb test(21-00): add Wave 0 CTDM-01..CTDM-06 stub tests (red)
```

### Test collection:

```
12/58 tests collected with -k "ctdm"
12 FAILED (all red — expected Wave 0 state)
```

## Self-Check: PASSED
