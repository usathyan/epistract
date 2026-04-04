# Phase 11: End-to-End Scenario Validation and v2.0 Release - Research

**Researched:** 2026-04-04
**Domain:** E2E validation, regression testing, git release workflow
**Confidence:** HIGH

## Summary

Phase 11 is the capstone: re-run all 7 scenarios (6 drug discovery + 1 contracts) through the V2 plugin pipeline, validate output against V1 baselines, build a repeatable regression suite, clean the repo, squash 198 feature-branch commits into ~5-10, and ship v2.0 via PR + GitHub release.

The project is in solid shape. All V1 baseline data exists in `tests/corpora/*/output/` with exact node/edge/community counts. The plugin infrastructure (`commands/*.md`, `.claude-plugin/plugin.json`) is complete. The core pipeline (`core/`) and both domain packages (`domains/drug-discovery/`, `domains/contracts/`) are functional. The primary risk is the git history squash of 198 commits -- this is destructive and must be done carefully.

**Primary recommendation:** Structure as 4 waves: (1) baseline capture + regression script, (2) scenario validation runs, (3) repo cleanup + gitignore hardening, (4) git squash + PR + release.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** All 6 drug discovery scenarios (PICALM, KRAS, Rare Disease, Immuno-Oncology, Cardiovascular, GLP-1) must be re-run through the V2 plugin pipeline. Full coverage, ~90 documents total.
- **D-02:** Contract scenario re-runs the full 62-contract STA corpus (not a synthetic subset). Requires private contract data available locally.
- **D-03:** Threshold-based comparison -- V2 must produce >=80% of V1 entity/relation counts. Allows natural LLM variation while catching regressions.
- **D-04:** All validation runs through `/epistract:*` plugin commands only (ingest, build, view, validate, epistemic). No raw Python scripts. Proves the marketplace install path works end-to-end.
- **D-05:** Epistemic validation checks key markers: drug discovery molecular validation runs with SMILES/sequences flagged; contracts conflict count >=40 (baseline 53) with obligations and deadlines detected. Spot-check a few entries per domain.
- **D-06:** Graph visualizations regenerated for all scenarios + contracts via `/epistract:view`. Screenshots captured as demonstration artifacts.
- **D-07:** Screenshots and demonstration artifacts stored in `docs/showcases/` (not tests/scenarios/screenshots/).
- **D-08:** After validation passes threshold, save V2 counts as new canonical baselines. V1 baselines archived for reference.
- **D-09:** Regression script runs as `make regression` Makefile target. Orchestrates: run all scenarios via plugin, diff against baselines, report pass/fail. Consistent with existing Makefile convention.
- **D-10:** Regression validates both graph structure (node/edge/community counts) AND epistemic layer output (molecular validation, conflict detection, epistemic status labels).
- **D-11:** Regression suite includes plugin install test: fresh `claude plugin install epistract` -> run a scenario -> verify output. Proves the full user journey.
- **D-12:** Support both install paths: `claude plugin install epistract` (marketplace) AND npx-style one-shot global install (e.g., `npx epistract` or `bunx epistract`). Document both in README.
- **D-13:** Full audit of repository before push: scan for large binaries, `.planning/` artifacts, worktree dirs, `node_modules`, `.venv`, `__pycache__`, stale test output. Verify nothing sensitive slips through.
- **D-14:** `.planning/` directory gitignored -- GSD workflow artifacts are development-only, not included in remote repo.
- **D-15:** Git history squashed to ~5-10 commits grouped by milestone phase. One commit per major phase for clean, navigable history.
- **D-16:** Integration method: Claude's discretion (rebase + squash merge or merge commit -- cleanest approach for 202-commit branch).
- **D-17:** Create GitHub release tagged `v2.0.0` with comprehensive changelog: full breakdown per phase, new features, architecture changes, breaking changes, migration notes.
- **D-18:** PR description: comprehensive changelog with multi-section body covering what changed per phase, key features, architecture, and breaking changes.
- **D-19:** Feature branch `feature/cross-domain-kg-framework` deleted after successful merge.

### Claude's Discretion
- Baseline storage mechanism (JSON files vs inline in script) for comparison data
- Specific threshold percentages per metric (nodes, edges, communities, conflicts)
- Regression script internal architecture and error reporting format
- npx/bunx package configuration details for one-shot install

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## V1 Baseline Data (Canonical Reference)

These are the exact V1 counts that V2 must match at >=80%:

| Scenario | Documents | Nodes | Edges | Communities |
|----------|-----------|-------|-------|-------------|
| S1: PICALM/Alzheimer's | 15 | 149 | 457 | 6 |
| S2: KRAS G12C | 16 | 108 | 307 | 4 |
| S3: Rare Disease | 15 | 94 | 229 | 4 |
| S4: Immuno-Oncology | 16 | 132 | 361 | 5 |
| S5: Cardiovascular | 15 | 94 | 246 | 5 |
| S6: GLP-1 CI | 34 | 206 | 630 | 9 |
| Contracts (STA) | 62 | 341 | 663 | -- |

**Source:** `tests/corpora/*/output/graph_data.json` (verified by direct file read).

### 80% Threshold Targets

| Scenario | Min Nodes | Min Edges |
|----------|-----------|-----------|
| S1 | 119 | 366 |
| S2 | 86 | 246 |
| S3 | 75 | 183 |
| S4 | 106 | 289 |
| S5 | 75 | 197 |
| S6 | 165 | 504 |
| Contracts | 273 | 530 |

## Architecture Patterns

### Regression Script Design

**Recommendation:** JSON baseline files stored alongside each scenario, Python script for comparison.

```
tests/
  baselines/
    v1/                           # Archived V1 baselines
      s01_picalm.json
      ...
    v2/                           # Canonical V2 baselines (after validation)
      s01_picalm.json
      ...
  regression/
    run_regression.py             # Main regression runner
    compare_baselines.py          # Diff logic
```

Each baseline JSON:
```json
{
  "scenario": "01_picalm_alzheimers",
  "version": "v1",
  "nodes": 149,
  "edges": 457,
  "communities": 6,
  "epistemic": {
    "claims_layer_exists": true,
    "hedging_count_min": 0,
    "molecular_validation": true
  }
}
```

**Why JSON over inline:** Easier to update, version-controllable, machine-readable for CI.

### Threshold Percentages (Recommendation)

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Nodes | >=80% | LLM variation in entity detection |
| Edges | >=80% | Relation extraction varies with entity changes |
| Communities | >=50% | Community detection is algorithmic and sensitive to graph topology |
| Conflicts (contracts) | >=75% (>=40) | Per D-05 baseline of 53 |

Communities get a lower threshold because small node count changes can significantly alter Louvain community detection output.

### Makefile Integration

```makefile
regression: ## Run regression suite against baselines
	python tests/regression/run_regression.py --baselines tests/baselines/v2/

regression-update: ## Update baselines from current output
	python tests/regression/run_regression.py --update-baselines
```

### Plugin-First Validation Pattern

Per D-04, all runs must go through `/epistract:*` commands. The regression script should:
1. Invoke `claude` CLI with the appropriate `/epistract:ingest` command
2. Wait for output to appear in the designated output directory
3. Parse `graph_data.json`, `communities.json`, `claims_layer.json`
4. Compare against baselines

**Practical concern:** Running all 7 scenarios through Claude Code plugin commands is expensive (LLM API calls for ~90+ documents). The regression script should support `--skip-extraction` mode that only validates existing output against baselines, for quick checks.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git history squash | Manual interactive rebase | `git rebase --onto` or `git reset --soft` + single commit per phase | 198 commits, interactive rebase impractical |
| GitHub release | Manual notes | `gh release create v2.0.0 --title "v2.0.0" --notes-file CHANGELOG.md` | Handles tag creation + release notes |
| PR creation | Manual GitHub UI | `gh pr create --title ... --body ...` | Scripted, repeatable |
| Baseline comparison | Ad-hoc shell scripts | Python with structured JSON diff | Need threshold logic, reporting |

## Common Pitfalls

### Pitfall 1: Git Squash Destroys Unsaved Work
**What goes wrong:** `git reset --soft` or force-push destroys commits if not backed up.
**Why it happens:** 198 commits being squashed is destructive.
**How to avoid:** Create a backup branch before any squash: `git branch backup/pre-squash-v2`. Never force-push without confirming backup exists.
**Warning signs:** No backup branch exists before starting squash.

### Pitfall 2: STA Contract Data Not Available
**What goes wrong:** Contract scenario needs private STA corpus that may not be in the expected location.
**Why it happens:** STA data is gitignored (correctly) and must exist locally.
**How to avoid:** Check for STA data existence before starting contract validation. Script should fail early with clear message.
**Warning signs:** `sample-contracts/` directory missing or empty.

### Pitfall 3: LLM Variation Below Threshold
**What goes wrong:** V2 extraction produces significantly different counts due to LLM non-determinism.
**Why it happens:** Different Claude model version, different chunking, or temperature variation.
**How to avoid:** 80% threshold provides buffer. If consistently below, investigate extraction pipeline changes, don't just re-run.
**Warning signs:** Multiple scenarios failing threshold simultaneously.

### Pitfall 4: .planning/ Tracked in Git History
**What goes wrong:** `.planning/` is currently tracked (not gitignored). Adding it to `.gitignore` only prevents future additions -- existing tracked files remain.
**Why it happens:** `.planning/` was committed during development workflow.
**How to avoid:** Must `git rm -r --cached .planning/` to untrack, THEN add to `.gitignore`. This must happen before the squash.
**Warning signs:** `git ls-files .planning/` returns results.

### Pitfall 5: Large Binary Screenshots in Git
**What goes wrong:** Screenshot PNGs (up to 1MB) bloat the repo.
**Current state:** `tests/scenarios/screenshots/scenario-06-graph.png` is 1.08MB. Six scenario screenshots plus graph HTMLs are tracked.
**How to avoid:** Per D-07, new screenshots go to `docs/showcases/`. Old `tests/scenarios/screenshots/` should be evaluated -- keep if needed for regression reference, or remove and rely on `docs/showcases/`.
**Warning signs:** `git ls-files | grep -E '\.(png|jpg)$'` returns many large files.

### Pitfall 6: Squash Merge vs Rebase Confusion
**What goes wrong:** Squash to ~5-10 commits requires `git reset --soft` approach, not GitHub squash merge (which creates 1 commit).
**Why it happens:** D-15 says "~5-10 commits grouped by milestone phase" but D-16 says "Claude's discretion."
**How to avoid:** Use `git reset --soft <merge-base>` then make targeted commits per phase group. This is the only approach that gives fine-grained control over commit grouping.
**Warning signs:** Using `git rebase -i` with 198 commits (impractical without editor).

## Git Squash Strategy (Recommended)

Given 198 commits on `feature/cross-domain-kg-framework` ahead of `main` (merge base: `8c8f800`):

**Approach: Soft reset + phased recommit**

```bash
# 1. Create safety backup
git branch backup/pre-squash-v2

# 2. Soft reset to merge base (keeps all changes staged)
git reset --soft 8c8f80069c85f8935f06a71cc3038c5412dcb9f5

# 3. Make targeted commits per phase group
# (selectively stage files per phase using git add)
git add core/ domains/ ...
git commit -m "feat: restructure to three-layer architecture (Phase 6)"
# ... repeat for each phase group
```

**Suggested commit groups (~8 commits):**

| Commit | Content | Phases |
|--------|---------|--------|
| 1 | Three-layer architecture + cleanup | 6 |
| 2 | Test infrastructure | 7 |
| 3 | Domain wizard | 8 |
| 4 | Consumer decoupling + standalone install | 9 |
| 5 | Documentation refresh | 10 |
| 6 | Regression suite + baselines | 11 (validation) |
| 7 | Repo cleanup + gitignore | 11 (cleanup) |
| 8 | Release prep | 11 (release) |

## Repo Cleanup Checklist

### Currently Tracked Files That Need Review

| Item | Status | Action |
|------|--------|--------|
| `.planning/` | Tracked, 90+ files | `git rm -r --cached`, add to `.gitignore` |
| `tests/scenarios/screenshots/*.png` | 6 files, ~1MB largest | Move to `docs/showcases/` per D-07, or remove |
| `tests/fixtures/sample_contract_a.pdf`, `sample_contract_b.pdf` | Tracked PDFs | Keep if needed for tests, else remove |
| `tests/corpora/*/output/` | V1 baseline data | Keep -- needed for regression baselines |
| `docs/diagrams/*.svg` | 5 SVGs | Keep -- documentation assets |
| `.claude/worktrees/` | Untracked | Already not tracked, verify in `.gitignore` |

### .gitignore Additions Needed

```gitignore
# GSD workflow artifacts (development-only)
.planning/

# Claude worktrees
.claude/worktrees/

# Kreuzberg cache
.kreuzberg/
```

## npx/bunx Install Path

Per D-12, the plugin needs an npx-style one-shot install alongside marketplace. This requires:

1. A `package.json` at repo root (currently missing)
2. A `bin` entry pointing to an install/setup script
3. Publishing to npm registry

**Minimal package.json:**
```json
{
  "name": "epistract",
  "version": "2.0.0",
  "description": "Cross-domain knowledge graph framework",
  "bin": {
    "epistract": "./scripts/npx-install.sh"
  },
  "files": [
    "core/",
    "domains/",
    "commands/",
    ".claude-plugin/",
    "scripts/npx-install.sh"
  ]
}
```

**Note:** The deleted `package.json` and `package-lock.json` in the current git status may indicate previous attempts. This is a new creation, not a restoration.

**Alternative:** If npm publishing is out of scope for v2.0, document the npx path as "coming soon" and focus on the marketplace path which is already functional. The planner should evaluate scope.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Core pipeline | TBD (check at execution) | -- | -- |
| gh CLI | PR + release creation | Yes | 2.89.0 | -- |
| claude CLI | Plugin install test | Yes | -- | -- |
| git | Squash + push | Yes | -- | -- |
| sift-kg | Graph building | TBD (check at execution) | -- | -- |
| STA corpus | Contract validation | TBD (must check locally) | -- | Skip contracts |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | None explicit (uses conftest.py conventions) |
| Quick run command | `python -m pytest tests/ -m unit -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map

Since no formal requirement IDs were provided for Phase 11, mapping against the 9 success criteria:

| Criteria | Behavior | Test Type | Automated Command | Exists? |
|----------|----------|-----------|-------------------|---------|
| SC-1 | Drug discovery scenarios regenerate graphs >=80% baseline | manual + regression | `make regression` | Wave 0 |
| SC-2 | Contract scenario regenerates ~341/663 graph | manual + regression | `make regression` | Wave 0 |
| SC-3 | All extractions via plugin commands | manual | Claude plugin invocation | Manual-only |
| SC-4 | Epistemic layers correct output | regression | `make regression` (epistemic check) | Wave 0 |
| SC-5 | Repeatable regression script exists | smoke | `make regression --dry-run` | Wave 0 |
| SC-6 | Graph visualizations demo-ready | manual | Visual inspection | Manual-only |
| SC-7 | Repo clean (no junk) | smoke | `scripts/audit_repo.sh` | Wave 0 |
| SC-8 | .gitignore comprehensive | smoke | `git status` after cleanup | Wave 0 |
| SC-9 | Branch synced, PR created | manual | `gh pr view` | Manual |

### Wave 0 Gaps
- [ ] `tests/regression/run_regression.py` -- regression runner (SC-1, SC-2, SC-4, SC-5)
- [ ] `tests/regression/compare_baselines.py` -- baseline comparison logic
- [ ] `tests/baselines/v1/*.json` -- extracted from current `tests/corpora/*/output/`
- [ ] `scripts/audit_repo.sh` -- repo cleanliness checker (SC-7)
- [ ] `make regression` target in Makefile

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -m unit -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green + `make regression` passes

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| V1 raw scripts | V2 plugin commands | Phase 9 | All validation via `/epistract:*` |
| Screenshots in tests/ | Screenshots in docs/showcases/ | Phase 10 (D-07) | Cleaner repo structure |
| Manual baseline checking | Automated regression suite | Phase 11 | Repeatable validation |

## Open Questions

1. **npx/bunx publishing scope**
   - What we know: D-12 requests both marketplace and npx install paths
   - What's unclear: Whether npm publishing is feasible within v2.0 timeline (needs npm account, package naming, etc.)
   - Recommendation: Create package.json structure but defer npm publish to post-release if time-constrained. Document as "coming soon."

2. **Contract data availability**
   - What we know: STA corpus is private, gitignored, needed for D-02
   - What's unclear: Whether it exists on the current machine
   - Recommendation: Regression script must check for data and skip gracefully with clear messaging if absent.

3. **Squash granularity**
   - What we know: D-15 says ~5-10 commits, D-16 gives Claude discretion on method
   - What's unclear: Exact file-to-phase mapping for selective staging after soft reset
   - Recommendation: Use 8 commits as outlined in Git Squash Strategy section. The soft-reset approach allows precise control.

4. **Plugin install test automation (D-11)**
   - What we know: `claude plugin install epistract` is the marketplace path
   - What's unclear: Whether this can be automated in CI (requires Claude Code runtime + auth)
   - Recommendation: Document as a manual test step in regression suite. Automate the post-install validation (run scenario, check output) but not the install itself.

## Sources

### Primary (HIGH confidence)
- Direct file reads of `tests/corpora/*/output/graph_data.json` -- V1 baseline counts verified
- Direct file reads of `tests/corpora/*/output/communities.json` -- community counts verified
- `.gitignore`, `Makefile`, `tests/test_e2e.py` -- current project infrastructure
- `git log --oneline main..HEAD` -- 198 commits on feature branch
- `git remote -v` -- origin at `https://github.com/usathyan/epistract.git`

### Secondary (MEDIUM confidence)
- Git squash strategy based on standard git workflows for large feature branches
- Regression suite design based on common Python testing patterns

## Metadata

**Confidence breakdown:**
- Baseline data: HIGH -- verified by direct file read
- Git workflow: HIGH -- standard git operations, gh CLI confirmed available
- Regression architecture: MEDIUM -- design recommendation, not verified against existing patterns
- npx install: LOW -- no existing package.json, unclear if npm publishing is in scope

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stable -- project-specific, not library-dependent)
