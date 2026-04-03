---
phase: 3
slug: entity-extraction-and-graph-construction
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | none (uses defaults, per existing pattern) |
| **Quick run command** | `python -m pytest tests/test_unit.py -v -k "ut03" -x` |
| **Full suite command** | `python -m pytest tests/test_unit.py -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -v -k "ut03" -x`
- **After every plan wave:** Run `python -m pytest tests/test_unit.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | EXTR-01 | unit | `python -m pytest tests/test_unit.py::test_ut030_chunk_document_clause_split -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 0 | EXTR-01 | unit | `python -m pytest tests/test_unit.py::test_ut031_chunk_document_fallback -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 0 | EXTR-01 | integration | `python -m pytest tests/test_unit.py::test_ut032_extraction_from_chunks -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 0 | EXTR-02 | unit | `python -m pytest tests/test_unit.py::test_ut033_legal_suffix_stripping -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 0 | EXTR-02 | unit | `python -m pytest tests/test_unit.py::test_ut034_alias_resolution -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 0 | EXTR-02 | integration | `python -m pytest tests/test_unit.py::test_ut035_entity_dedup_integration -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 0 | GRPH-01 | integration | `python -m pytest tests/test_unit.py::test_ut036_graph_build_contracts -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 0 | GRPH-02 | unit | `python -m pytest tests/test_unit.py::test_ut037_graph_node_attributes -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 0 | GRPH-02 | smoke | `python -m pytest tests/test_unit.py::test_ut038_visualization_renders -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_unit.py` — Add UT-030 through UT-038 test functions
- [ ] `tests/fixtures/sample_contract_text.txt` — Synthetic contract text with known entities for deterministic testing
- [ ] `tests/fixtures/sample_contract_unstructured.txt` — Free-form text (no section headers) for fallback chunking test

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| pyvis HTML renders contract graph with distinguishable entity types | GRPH-02 | Browser visual inspection needed | Open generated HTML, verify entity type colors/labels visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
