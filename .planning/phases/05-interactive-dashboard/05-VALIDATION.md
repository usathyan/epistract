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
| **Quick run command** | `python -m pytest tests/test_workbench.py -v --timeout=30` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_workbench.py -v --timeout=30`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | DASH-01 | unit | `python -c "import yaml; d=yaml.safe_load(open('skills/contract-extraction/domain.yaml')); assert 'COMMITTEE' in d['entity_types']"` | N/A (inline) | pending |
| 05-01-02 | 01 | 1 | DASH-02 | unit | `python -c "import json; d=json.load(open('tests/fixtures/sample_graph_data.json')); assert len(d['nodes'])>=20"` | N/A (inline) | pending |
| 05-02-01 | 02 | 1 | DASH-01 | unit | `python -m pytest tests/test_workbench.py::test_graph_api -v` | W0 | pending |
| 05-02-02 | 02 | 1 | DASH-02 | unit | `python -m pytest tests/test_workbench.py::test_entity_filter -v` | W0 | pending |
| 05-02-03 | 02 | 1 | DASH-02 | unit | `python -m pytest tests/test_workbench.py::test_sources_list -v` | W0 | pending |
| 05-03-01 | 03 | 2 | DASH-01 | unit | `python -c "from scripts.workbench.system_prompt import build_system_prompt; print('OK')"` | N/A (inline) | pending |
| 05-03-02 | 03 | 2 | DASH-01 | unit | `python -c "from scripts.workbench.api_chat import router, ChatRequest; print('OK')"` | N/A (inline) | pending |
| 05-03-03 | 03 | 2 | DASH-02 | unit | `python -m pytest tests/test_workbench.py::test_chat_stream_mock -v` | W0 | pending |
| 05-04-01 | 04 | 2 | DASH-01 | file | `python -c "from pathlib import Path; assert Path('scripts/workbench/static/index.html').exists()"` | N/A (inline) | pending |
| 05-04-02 | 04 | 2 | DASH-01 | file | `python -c "from pathlib import Path; g=Path('scripts/workbench/static/graph.js').read_text(); assert 'vis.Network' in g or 'vis.DataSet' in g"` | N/A (inline) | pending |
| 05-04-03 | 04 | 2 | DASH-02 | manual | Browser: full workbench visual + functional verification | N/A | pending |

*Status: pending | green | red | flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_workbench.py` — stubs for DASH-01, DASH-02 (created in Plan 02 Task 2)
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
| Severity filter applies | DASH-01 | Visual verification | Select severity level, verify graph filters nodes |
| Chat streams response | DASH-01 | SSE + Claude API | Type question, verify streaming markdown response |
| Citation links open sources | DASH-02 | Cross-panel navigation | Click citation in chat, verify source panel opens |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
