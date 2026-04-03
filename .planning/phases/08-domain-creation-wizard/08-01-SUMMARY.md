---
phase: 08-domain-creation-wizard
plan: 01
subsystem: core/epistemic-dispatcher
tags: [epistemic, dispatcher, wizard, fixtures]
dependency_graph:
  requires: [core/domain_resolver.py, domains/contracts/epistemic.py, domains/drug-discovery/epistemic.py]
  provides: [convention-based epistemic dispatch, wizard test fixtures]
  affects: [core/label_epistemic.py, tests/test_unit.py]
tech_stack:
  added: []
  patterns: [convention-based function lookup, inspect.signature for parameter detection]
key_files:
  created:
    - tests/fixtures/wizard/sample_lease_1.txt
    - tests/fixtures/wizard/sample_lease_2.txt
    - tests/fixtures/wizard/sample_lease_3.txt
  modified:
    - core/label_epistemic.py
    - tests/test_unit.py
decisions:
  - Used DOMAIN_ALIASES from domain_resolver instead of duplicating alias map in label_epistemic
  - Added inspect.signature() to detect master_doc_path parameter support per-function
  - Added generic analyze_epistemic() fallback for domains that don't use slug naming
metrics:
  duration: ~3min
  completed: 2026-04-03
---

# Phase 08 Plan 01: Generalize Epistemic Dispatcher + Wizard Test Fixtures Summary

Convention-based epistemic dispatcher replacing hard-coded domain branching, plus 3 lease document fixtures for wizard testing.

## What Was Done

### Task 1: Generalize epistemic dispatcher to convention-based lookup

Refactored `core/label_epistemic.py` in two places:

1. **`_load_domain_epistemic()`**: Replaced hard-coded `dir_map` dict with `DOMAIN_ALIASES` import from `core.domain_resolver`. Falls back to using domain name directly as directory for wizard-generated domains.

2. **`analyze_epistemic()` dispatch**: Replaced `if effective_domain == "contract"` branching with convention-based `analyze_<slug>_epistemic()` lookup using `getattr()`. Uses `inspect.signature()` to detect whether the function accepts `master_doc_path`. Includes fallback chain: slug-named function -> generic `analyze_epistemic()` -> built-in biomedical analysis.

**Commit:** baa7d05

### Task 2: Create wizard test fixtures and dispatcher unit tests

Created 3 sample lease documents in `tests/fixtures/wizard/`:
- `sample_lease_1.txt` -- Residential lease (25 lines)
- `sample_lease_2.txt` -- Commercial lease (27 lines)
- `sample_lease_3.txt` -- Lease amendment (22 lines)

Added 5 unit tests to `tests/test_unit.py`:
- `test_epistemic_dispatcher_generic_contract` -- contract domain loads and has expected function
- `test_epistemic_dispatcher_generic_biomedical` -- drug-discovery domain loads correctly
- `test_epistemic_dispatcher_alias_resolution` -- "biomedical" alias resolves to drug-discovery
- `test_epistemic_dispatcher_unknown_domain_returns_none` -- graceful None for unknown domains
- `test_wizard_fixtures_exist` -- fixture files present with sufficient content

**Commit:** 7d9095b

## Verification

- All 5 new tests pass
- Full unit test suite: 19/19 pass, no regressions
- `dir_map` removed from label_epistemic.py (0 occurrences)
- `getattr(domain_mod, func_name)` present in label_epistemic.py

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- All 6 key files verified present on disk
- Both commit hashes (baa7d05, 7d9095b) found in git log
