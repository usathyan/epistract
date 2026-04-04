---
phase: 9
slug: consumer-decoupling-and-standalone-install
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_unit.py -v -x` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -v -x`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | CONS-01 | integration | `python -m pytest tests/ -k "workbench_template" -v` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | CONS-01 | integration | `python -m pytest tests/ -k "workbench_generic" -v` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | CONS-02 | integration | `python -m pytest tests/ -k "telegram_bot" -v` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 3 | INST-01 | manual | See manual section | — | ⬜ pending |
| 09-03-02 | 03 | 3 | INST-02 | integration | `python -m pytest tests/ -k "prebuilt_domain" -v` | ❌ W0 | ⬜ pending |
| 09-03-03 | 03 | 3 | INST-03 | manual | See manual section | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_workbench_template.py` — stubs for CONS-01 (template loading, generic fallback)
- [ ] `tests/test_telegram_bot.py` — stubs for CONS-02 (bot initialization, domain-agnostic queries)
- [ ] `tests/test_standalone_install.py` — stubs for INST-01, INST-02, INST-03 (plugin packaging, domain bundling)

*Existing test infrastructure (conftest.py, fixtures) covers shared needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fresh machine install | INST-01 | Requires clean environment without repo clone | 1. `claude plugin install epistract` 2. Run `/epistract:setup` 3. Verify sift-kg installs 4. Verify domains available |
| Plugin package size | INST-03 | Requires inspecting actual plugin cache contents | 1. Check `~/.claude/plugins/cache/epistract/` 2. Verify no `tests/`, `.planning/`, `docs/` directories 3. Verify `domains/` present with both pre-built domains |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
