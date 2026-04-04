---
phase: 10
slug: documentation-refresh
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.2.1 + shell smoke checks |
| **Config file** | tests/conftest.py |
| **Quick run command** | `python -m pytest tests/test_unit.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run smoke checks (file existence, stale path grep)
- **After every plan wave:** Run full smoke suite + visual review
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-xx | 01 | 1 | DOCS-01 | smoke | `grep -c "knowledge graph framework" README.md` | N/A | ⬜ pending |
| 10-02-xx | 02 | 1 | DOCS-02 | smoke | `ls docs/diagrams/{architecture,data-flow,two-layer-kg,domain-package}.{mmd,svg}` | N/A | ⬜ pending |
| 10-03-xx | 03 | 1 | DOCS-03 | smoke | `grep -c "skills/" docs/ADDING-DOMAINS.md` returns 0 | N/A | ⬜ pending |
| 10-04-xx | 04 | 2 | DOCS-04 | manual | Visual review of paper sections | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. Documentation phase requires no test infrastructure — smoke checks are inline shell commands.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README narrative quality | DOCS-01 | Prose quality cannot be automated | Review framework-first pitch, dual-path quick-start |
| Domain guide wizard walkthrough | DOCS-03 | Tutorial flow requires human assessment | Follow wizard steps in guide, verify accuracy |
| Paper reframing as evolution | DOCS-04 | Academic writing quality is subjective | Read title, abstract, architecture sections for framework framing |
| STA privacy compliance | D-16/D-17 | Privacy leaks require contextual judgment | Search for vendor names, dollar amounts in public docs |

---

## Smoke Check Suite

```bash
# 1. Verify no stale skills/ paths in new docs
grep -r "skills/" README.md docs/ADDING-DOMAINS.md | grep -v "node_modules"

# 2. Verify all 4 diagram pairs exist
for d in architecture data-flow two-layer-kg domain-package; do
  test -f "docs/diagrams/$d.mmd" && test -f "docs/diagrams/$d.svg" && echo "$d: OK" || echo "$d: MISSING"
done

# 3. Verify no STA vendor names leaked
grep -i "marriott\|aramark\|freeman\|convention center" README.md docs/showcases/*.md 2>/dev/null && echo "LEAK DETECTED" || echo "Clean"

# 4. Verify demo video removed
grep -i "youtube\|demo.*video\|7mHbdb0nn3Y" README.md && echo "VIDEO STILL PRESENT" || echo "Video removed"

# 5. Verify framework identity in README
grep -c "knowledge graph framework\|domain-agnostic" README.md
```

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
