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
| **Quick run command** | `python -m pytest tests/test_unit.py -v -k "xref"` |
| **Full suite command** | `python -m pytest tests/test_unit.py -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -v -k "xref"`
- **After every plan wave:** Run `python -m pytest tests/test_unit.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | XREF-01 | unit | `python -m pytest tests/test_unit.py -v -k "cross_contract_linking"` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | XREF-02 | unit | `python -m pytest tests/test_unit.py -v -k "conflict_detection"` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | XREF-03 | unit | `python -m pytest tests/test_unit.py -v -k "coverage_gap"` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 2 | XREF-04 | unit | `python -m pytest tests/test_unit.py -v -k "risk_flag"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_xref.py` — stubs for XREF-01 through XREF-04
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
