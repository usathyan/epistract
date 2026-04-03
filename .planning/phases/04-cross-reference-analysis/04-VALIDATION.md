---
phase: 4
slug: cross-reference-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/test_unit.py (existing) |
| **Quick run command** | `python -m pytest tests/test_unit.py -v -k "ut039 or ut040 or ut041 or ut042 or ut043 or ut044 or ut045 or ut046"` |
| **Full suite command** | `python -m pytest tests/test_unit.py -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -v -k "ut039 or ut040 or ut041 or ut042 or ut043 or ut044 or ut045 or ut046"`
- **After every plan wave:** Run `python -m pytest tests/test_unit.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 04-01-01 | 01 | 1 | XREF-01, XREF-02 | unit | `python -m pytest tests/test_unit.py -v -k "ut039 or ut045"` | pending |
| 04-01-02 | 01 | 1 | XREF-02 | unit | `python -m pytest tests/test_unit.py -v -k "ut042"` | pending |
| 04-02-01 | 02 | 2 | XREF-01, XREF-02 | behavioral | `python3 -c "import sys; sys.path.insert(0,'scripts'); from epistemic_contract import find_cross_contract_entities, detect_conflicts; ..."` | pending |
| 04-02-02 | 02 | 2 | XREF-03, XREF-04 | behavioral | `python3 -c "import sys; sys.path.insert(0,'scripts'); from epistemic_contract import analyze_contract_epistemic, score_risks; ..."` | pending |
| 04-02-03 | 02 | 2 | XREF-01..04 | unit | `python -m pytest tests/test_unit.py -v -k "ut040 or ut041 or ut043 or ut044 or ut046"` | pending |
| 04-03-01 | 03 | 3 | XREF-01..04 | integration | `python3 -c "import sys; sys.path.insert(0,'scripts'); from extract_contracts import extract_and_build; ..."` | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] Tests UT-039, UT-042, UT-045 created in Plan 01 Task 2 (in `tests/test_unit.py`)
- [ ] Test fixtures for sample graph_data.json with multi-contract entities

*Existing infrastructure covers framework setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cross-contract visual linking in graph viewer | XREF-01 | Requires browser inspection | Open graph HTML, verify multi-source nodes show contract labels |
| Risk report readability | XREF-04 | Subjective formatting | Review generated risk report for clarity and actionability |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
