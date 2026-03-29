---
phase: 1
slug: domain-configuration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/test_unit.py (existing) |
| **Quick run command** | `python -m pytest tests/test_unit.py -v --tb=short` |
| **Full suite command** | `python -m pytest tests/test_unit.py -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -v --tb=short`
- **After every plan wave:** Run `python -m pytest tests/test_unit.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DCFG-01 | unit | `python -m pytest tests/test_domain_config.py -v -k "test_resolve_domain"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DCFG-01 | unit | `python -m pytest tests/test_domain_config.py -v -k "test_auto_discover"` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | DCFG-03 | unit | `python -m pytest tests/test_domain_config.py -v -k "test_contract_yaml_loads"` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | DCFG-04 | unit | `python -m pytest tests/test_domain_config.py -v -k "test_contract_entities"` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | DCFG-02 | integration | `python -m pytest tests/test_domain_config.py -v -k "test_biomedical_backward_compat"` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | DCFG-01 | unit | `python -m pytest tests/test_domain_config.py -v -k "test_domain_flag"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_domain_config.py` — stubs for DCFG-01 through DCFG-04
- [ ] Test fixtures for domain YAML loading and validation

*Existing test infrastructure (pytest, test_unit.py) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent reads domain SKILL.md | DCFG-01 | Agent behavior requires Claude runtime | Run `/epistract-ingest` with `--domain contract` on a test document and verify extraction follows contract ontology |
| `--list-domains` output | DCFG-01 | CLI output formatting | Run script with `--list-domains` and verify both domains appear |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
