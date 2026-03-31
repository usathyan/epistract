---
phase: 5
slug: interactive-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/test_unit.py` (existing) |
| **Quick run command** | `python -m pytest tests/test_dashboard.py -v --timeout=30` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_dashboard.py -v --timeout=30`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | DASH-01 | unit | `python -m pytest tests/test_dashboard.py::test_api_graph_endpoint -v` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | DASH-01 | unit | `python -m pytest tests/test_dashboard.py::test_api_filter_params -v` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | DASH-02 | unit | `python -m pytest tests/test_dashboard.py::test_tabular_endpoint -v` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | DASH-02 | manual | Browser: switch between table/graph views | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_dashboard.py` — stubs for DASH-01, DASH-02
- [ ] FastAPI TestClient fixture in test file
- [ ] `uv pip install fastapi httpx` — if not already installed

*Wave 0 creates test infrastructure before implementation begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Graph renders in browser | DASH-01 | vis.js canvas rendering | Open localhost, verify graph nodes visible |
| Table/graph view toggle | DASH-02 | UI interaction | Click toggle, verify both views display |
| Filter updates graph | DASH-01 | Visual verification | Select vendor filter, verify graph updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
