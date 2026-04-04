# Phase 11: End-to-End Scenario Validation and v2.0 Release - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 11-end-to-end-scenario-validation
**Areas discussed:** Validation scope, Regression suite design, Repo cleanup criteria, Release workflow

---

## Validation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All 6 scenarios | Re-run PICALM, KRAS, Rare Disease, Immuno-Oncology, Cardiovascular, GLP-1 — full coverage | ✓ |
| Representative subset (3) | Pick 3 diverse scenarios to prove pipeline works | |
| Just contracts + 1 drug | Minimal cross-domain proof | |

**User's choice:** All 6 scenarios
**Notes:** Full coverage required for complete validation

---

| Option | Description | Selected |
|--------|-------------|----------|
| Threshold-based (>=80%) | Allows natural LLM variation while catching regressions | ✓ |
| Exact match | Very strict, may fail due to LLM non-determinism | |
| Qualitative review | Manual judgment only | |

**User's choice:** Threshold-based
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Plugin-only | All validation through /epistract:* commands | ✓ |
| Plugin + scripts hybrid | Plugin for ingest/build, scripts for comparison | |
| You decide | Claude picks approach | |

**User's choice:** Plugin-only
**Notes:** Success criterion #3 requires proving marketplace install path

---

| Option | Description | Selected |
|--------|-------------|----------|
| Key markers present | Spot-check molecular validation, conflict counts | ✓ |
| Full audit | Every epistemic annotation reviewed | |
| You decide | Claude determines depth | |

**User's choice:** Key markers present
**Notes:** Drug discovery: SMILES/sequences flagged. Contracts: conflict count >=40

---

| Option | Description | Selected |
|--------|-------------|----------|
| Regenerate all | Run /epistract:view for every scenario, capture screenshots | ✓ |
| Spot-check 2-3 | Verify command works on a couple scenarios | |
| Command works = sufficient | Just prove it launches without error | |

**User's choice:** Regenerate all
**Notes:** Screenshots stored in docs/showcases/

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full 62 contracts | Re-run complete STA corpus | ✓ |
| Synthetic subset | Use 3 existing synthetic test fixtures | |
| Both paths | Synthetic for automated, full for manual | |

**User's choice:** Full 62 contracts
**Notes:** Requires private contract data available locally

---

| Option | Description | Selected |
|--------|-------------|----------|
| Capture new V2 baselines | Save V2 counts as new canonical baselines | ✓ |
| Keep V1 as canonical | V1 numbers remain gold standard | |
| You decide | Claude determines approach | |

**User's choice:** Capture new V2 baselines
**Notes:** V1 baselines archived for reference

---

## Regression Suite Design

| Option | Description | Selected |
|--------|-------------|----------|
| Makefile target | `make regression` orchestrates full suite | ✓ |
| Standalone Python script | scripts/run_regression.py with argparse | |
| pytest suite extension | Extend tests/test_e2e.py with parametrized tests | |

**User's choice:** Makefile target
**Notes:** Consistent with existing Makefile convention

---

| Option | Description | Selected |
|--------|-------------|----------|
| JSON baseline files | Store baselines as JSON, script compares | |
| Inline in Makefile/script | Hardcode expected ranges | |
| You decide | Claude picks maintainable approach | ✓ |

**User's choice:** You decide
**Notes:** Claude's discretion on baseline storage mechanism

---

| Option | Description | Selected |
|--------|-------------|----------|
| Graph + epistemic | Validate both graph structure AND epistemic markers | ✓ |
| Graph structure only | Just node/edge/community counts | |
| You decide | Claude determines depth | |

**User's choice:** Graph + epistemic
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include install test | Fresh plugin install -> run scenario -> verify output | ✓ |
| Manual install verification | Tested manually once | |
| You decide | Claude determines practicality | |

**User's choice:** Yes, include install test
**Notes:** Proves full user journey

---

| Option | Description | Selected |
|--------|-------------|----------|
| claude plugin install | Standard marketplace install | |
| npx-style shortcut | One-shot global install | |
| Both paths | Support both marketplace and npx/bunx | ✓ |

**User's choice:** Both paths
**Notes:** User specifically requested npx-type install for one-shot global plugin install

---

## Repo Cleanup Criteria

| Option | Description | Selected |
|--------|-------------|----------|
| Squash to ~5-10 commits | Group by milestone phase | ✓ |
| Squash to single commit | One big v2.0 commit | |
| Keep full history | All 202 commits | |
| You decide | Claude picks strategy | |

**User's choice:** Squash to ~5-10 commits
**Notes:** One commit per major phase for clean history

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full audit needed | Scan for all sensitive/large files | ✓ |
| .planning/ exclusion only | Main concern is .planning/ | |
| Audit + size check | Full audit plus >1MB file check | |

**User's choice:** Full audit needed
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Gitignore .planning/ | Development-only, excluded from remote | ✓ |
| Include .planning/ | Preserve for audit trail | |
| Partial — keep ROADMAP only | Gitignore most, keep key docs | |

**User's choice:** Gitignore .planning/
**Notes:** Success criterion #8 explicitly lists .planning/ as excluded

---

## Release Workflow

| Option | Description | Selected |
|--------|-------------|----------|
| Rebase + squash merge | Clean linear history | |
| Merge commit | Shows branch topology | |
| You decide | Cleanest approach | ✓ |

**User's choice:** You decide
**Notes:** Claude's discretion for 202-commit branch integration

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, create v2.0.0 release | Tag + GitHub release with changelog | ✓ |
| Tag only, no release | Reference tag only | |
| No tag needed | Version via commit history | |

**User's choice:** Yes, create v2.0.0 release
**Notes:** Standard open-source practice

---

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive changelog | Full breakdown per phase | ✓ |
| High-level summary | Brief summary + link to README | |
| You decide | Claude drafts appropriate content | |

**User's choice:** Comprehensive changelog
**Notes:** Multi-section PR body for major rewrite

---

| Option | Description | Selected |
|--------|-------------|----------|
| Delete after merge | Clean up feature branch | ✓ |
| Keep branch | Preserve for reference | |
| You decide | Claude handles lifecycle | |

**User's choice:** Delete after merge
**Notes:** Standard practice

## Claude's Discretion

- Baseline storage mechanism (JSON files vs inline)
- Specific threshold percentages per metric
- Regression script architecture and error reporting
- npx/bunx package configuration details
- Git integration method (rebase + squash vs merge)

## Deferred Ideas

None — discussion stayed within phase scope
