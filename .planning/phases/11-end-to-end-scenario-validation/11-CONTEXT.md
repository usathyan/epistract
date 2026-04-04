# Phase 11: End-to-End Scenario Validation and v2.0 Release - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate that the V2 framework produces correct knowledge graphs for both domains (drug discovery + contracts), create a repeatable regression suite with automated baseline comparison, clean the repository for public release, and ship v2.0 to remote with PR, tag, and GitHub release.

</domain>

<decisions>
## Implementation Decisions

### Validation Scope
- **D-01:** All 6 drug discovery scenarios (PICALM, KRAS, Rare Disease, Immuno-Oncology, Cardiovascular, GLP-1) must be re-run through the V2 plugin pipeline. Full coverage, ~90 documents total.
- **D-02:** Contract scenario re-runs the full 62-contract STA corpus (not a synthetic subset). Requires private contract data available locally.
- **D-03:** Threshold-based comparison — V2 must produce >=80% of V1 entity/relation counts. Allows natural LLM variation while catching regressions.
- **D-04:** All validation runs through `/epistract:*` plugin commands only (ingest, build, view, validate, epistemic). No raw Python scripts. Proves the marketplace install path works end-to-end.
- **D-05:** Epistemic validation checks key markers: drug discovery molecular validation runs with SMILES/sequences flagged; contracts conflict count >=40 (baseline 53) with obligations and deadlines detected. Spot-check a few entries per domain.
- **D-06:** Graph visualizations regenerated for all scenarios + contracts via `/epistract:view`. Screenshots captured as demonstration artifacts.
- **D-07:** Screenshots and demonstration artifacts stored in `docs/showcases/` (not tests/scenarios/screenshots/).
- **D-08:** After validation passes threshold, save V2 counts as new canonical baselines. V1 baselines archived for reference.

### Regression Suite Design
- **D-09:** Regression script runs as `make regression` Makefile target. Orchestrates: run all scenarios via plugin, diff against baselines, report pass/fail. Consistent with existing Makefile convention.
- **D-10:** Regression validates both graph structure (node/edge/community counts) AND epistemic layer output (molecular validation, conflict detection, epistemic status labels).
- **D-11:** Regression suite includes plugin install test: fresh `claude plugin install epistract` -> run a scenario -> verify output. Proves the full user journey.
- **D-12:** Support both install paths: `claude plugin install epistract` (marketplace) AND npx-style one-shot global install (e.g., `npx epistract` or `bunx epistract`). Document both in README.

### Claude's Discretion
- Baseline storage mechanism (JSON files vs inline in script) for comparison data
- Specific threshold percentages per metric (nodes, edges, communities, conflicts)
- Regression script internal architecture and error reporting format
- npx/bunx package configuration details for one-shot install

### Repo Cleanup Criteria
- **D-13:** Full audit of repository before push: scan for large binaries, `.planning/` artifacts, worktree dirs, `node_modules`, `.venv`, `__pycache__`, stale test output. Verify nothing sensitive slips through.
- **D-14:** `.planning/` directory gitignored — GSD workflow artifacts are development-only, not included in remote repo.
- **D-15:** Git history squashed to ~5-10 commits grouped by milestone phase. One commit per major phase for clean, navigable history.

### Release Workflow
- **D-16:** Integration method: Claude's discretion (rebase + squash merge or merge commit — cleanest approach for 202-commit branch).
- **D-17:** Create GitHub release tagged `v2.0.0` with comprehensive changelog: full breakdown per phase, new features, architecture changes, breaking changes, migration notes.
- **D-18:** PR description: comprehensive changelog with multi-section body covering what changed per phase, key features, architecture, and breaking changes.
- **D-19:** Feature branch `feature/cross-domain-kg-framework` deleted after successful merge.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/ROADMAP.md` §Phase 11 — 9 success criteria defining validation, cleanup, and release gates
- `.planning/REQUIREMENTS.md` — All v2 requirements (ARCH, WIZD, INST, DOCS, CONS, TEST, CLEAN) for cross-reference
- `.planning/STATE.md` — Current progress, velocity metrics

### Prior Phase Decisions
- `.planning/phases/09-consumer-decoupling-and-standalone-install/09-CONTEXT.md` — D-07 (marketplace install), D-08 (pre-built domains bundled), D-09 (pluginignore)
- `.planning/phases/10-documentation-refresh/10-CONTEXT.md` — D-16 (STA privacy), D-17 (.gitignore rules), D-04 (demo video removed)
- `.planning/phases/06-repo-reorganization-and-cleanup/06-CONTEXT.md` — D-04 (self-contained domains), D-06 (domain directory layout)

### Existing Test Infrastructure
- `tests/test_e2e.py` — Existing end-to-end test suite
- `tests/test_unit.py` — Unit test suite
- `tests/TEST_REQUIREMENTS.md` — Test traceability specification
- `tests/VALIDATION_RESULTS.md` — V1 baseline validation data (node/edge counts per scenario)

### V1 Baseline Data
- `tests/corpora/01_picalm_alzheimers/output/` — S1 baseline: 149 nodes, 457 edges, 6 communities
- `tests/corpora/02_kras_g12c_landscape/output/` — S2 baseline: 108 nodes, 307 edges, 4 communities
- `tests/corpora/03_rare_disease/output/` — S3 baseline: 94 nodes, 229 edges, 4 communities
- `tests/corpora/04_immunooncology/output/` — S4 baseline
- `tests/corpora/05_cardiovascular/output/` — S5 baseline
- `tests/corpora/06_glp1_landscape/output/` — S6 baseline

### Scenario Documentation
- `tests/scenarios/scenario-01-picalm-alzheimers.md` through `scenario-06-glp1-landscape.md` — Scenario specifications

### Repository
- `.gitignore` — Current exclusion rules (STA data, extraction output, demo recordings)
- `Makefile` — Existing targets (help, setup, test, lint, format, clean)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Makefile` with standard targets — regression target extends this naturally
- `tests/test_e2e.py` — existing E2E pipeline test framework, can be extended for regression
- `tests/corpora/*/output/` — V1 baseline data with node/edge/community counts
- `tests/VALIDATION_RESULTS.md` — structured validation data with per-scenario tables
- `core/run_sift.py` — sift-kg wrapper with build/view/export/search/info commands

### Established Patterns
- All pipeline operations go through `/epistract:*` commands (plugin-first architecture)
- JSON output with `indent=2` for all structured data
- Threshold-based validation aligns with existing confidence scoring (0.5-1.0 range)
- `docs/showcases/` established by Phase 10 for scenario documentation

### Integration Points
- `make regression` integrates with existing `make test` flow
- Plugin install test needs Claude Code CLI (`claude plugin install`)
- npx/bunx install needs package.json with bin entry
- GitHub release creation via `gh release create`
- PR creation via `gh pr create`

</code_context>

<specifics>
## Specific Ideas

- User wants npx-style one-shot install alongside marketplace install — two paths to first use
- Squash 202 commits into ~5-10 phase-grouped commits for clean history
- V2 baselines replace V1 as canonical after validation passes
- Comprehensive PR changelog covering all phases of the v2.0 rewrite
- docs/showcases/ for demonstration screenshots (not tests/scenarios/screenshots/)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-end-to-end-scenario-validation*
*Context gathered: 2026-04-04*
