---
phase: 8
slug: domain-creation-wizard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_domain_wizard.py -v --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_domain_wizard.py -v --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | WIZD-01 | unit | `python -m pytest tests/test_domain_wizard.py::test_schema_discovery -v` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | WIZD-01 | unit | `python -m pytest tests/test_domain_wizard.py::test_document_analysis -v` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | WIZD-02 | unit | `python -m pytest tests/test_domain_wizard.py::test_package_generation -v` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | WIZD-03 | unit | `python -m pytest tests/test_domain_wizard.py::test_epistemic_rules -v` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 3 | WIZD-04 | integration | `python -m pytest tests/test_domain_wizard.py::test_e2e_pipeline -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_domain_wizard.py` — stubs for WIZD-01, WIZD-02, WIZD-03, WIZD-04
- [ ] Test fixtures: sample documents for wizard input

*Existing conftest.py and test infrastructure from Phase 7 covers shared fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM schema discovery quality | WIZD-01 | LLM output varies per run | Run wizard on sample docs, inspect proposed schema for reasonable entity/relation types |
| Generated SKILL.md prompt quality | WIZD-02 | Prompt quality is subjective | Review generated SKILL.md for extraction guidance completeness |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
