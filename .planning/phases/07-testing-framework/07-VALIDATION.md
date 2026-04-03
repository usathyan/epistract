---
phase: 7
slug: testing-framework
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.2.1 |
| **Config file** | none — Wave 0 creates pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_unit.py -m unit -v --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -m unit -v --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | TEST-01 | unit | `python -m pytest tests/test_unit.py -m unit -v` | ✅ existing (needs markers) | ⬜ pending |
| 07-01-02 | 01 | 1 | TEST-03 | unit | `python -m pytest tests/test_unit.py -k "domain_yaml" -v` | ✅ partial | ⬜ pending |
| 07-01-03 | 01 | 1 | TEST-04 | unit | `python -m pytest tests/test_unit.py -k "extraction_schema" -v` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | TEST-02 | integration | `python -m pytest tests/test_integration.py -m integration -v` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 2 | TEST-06 | integration | `python -m pytest tests/test_kg_provenance.py -m integration -v` | ✅ existing (needs conversion) | ⬜ pending |
| 07-02-03 | 02 | 2 | TEST-07 | integration | `python -m pytest tests/test_integration.py -k "cross_domain" -v` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 3 | TEST-05 | e2e | `python -m pytest tests/test_e2e.py -m e2e -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures, path setup, availability flags
- [ ] `pyproject.toml` — pytest marker registration, testpaths config
- [ ] `tests/test_integration.py` — integration tier test file stub
- [ ] `tests/test_e2e.py` — E2E tier test file stub
- [ ] `tests/fixtures/contract_graph_data.json` — contract domain graph fixture
- [ ] `tests/fixtures/contract_claims_layer.json` — contract domain claims fixture
- [ ] `tests/fixtures/sample_extraction_drug.json` — pre-recorded drug extraction for E2E
- [ ] `tests/fixtures/sample_extraction_contract.json` — pre-recorded contract extraction for E2E
- [ ] Makefile update — add `test-integration` and `test-all` targets

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `/epistract:view` opens browser | TEST-02 | Opens browser — cannot verify in headless test | Run `/epistract:view` manually, confirm HTML opens |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
