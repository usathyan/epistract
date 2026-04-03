# Phase 6: Repo Reorganization and Cleanup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 06-repo-reorganization-and-cleanup
**Areas discussed:** Core module boundary, Stale artifact handling, Plugin interface mapping

---

## Core Module Boundary

### Epistemic Dispatcher Location

| Option | Description | Selected |
|--------|-------------|----------|
| Core dispatcher + domain rules | label_epistemic.py stays in core/ as dispatcher. Each domain provides its own epistemic rules module. Core dispatches to active domain. | ✓ |
| Fully in core with config | Move all epistemic logic to core/ with rule definitions in domain.yaml config. Simpler but less flexible. | |
| Fully in domains | Each domain owns its own full epistemic pipeline. No shared dispatcher. More duplication. | |

**User's choice:** Core dispatcher + domain rules (Recommended)
**Notes:** Clean separation — core handles orchestration, domains provide rules.

### Community Labeling Location

| Option | Description | Selected |
|--------|-------------|----------|
| Core | Algorithm is domain-agnostic — works on any graph's community structure. Keep in core/. | ✓ |
| Domain-specific | Each domain provides its own community labeling logic. Allows domain-specific label styles. | |

**User's choice:** Core (Recommended)
**Notes:** None — straightforward decision.

### Domain-Specific Python Module Location

| Option | Description | Selected |
|--------|-------------|----------|
| Inside domains/<name>/ | Co-located with domain.yaml and SKILL.md. Clean boundary: everything domain-specific in one directory. | ✓ |
| Separate scripts/domains/ dir | Keeps all Python in scripts/ tree but separates by domain. Less disruption to imports. | |

**User's choice:** Inside domains/<name>/ (Recommended)
**Notes:** None.

### Validation Scripts Location

| Option | Description | Selected |
|--------|-------------|----------|
| Move to domains/<name>/ | Co-located with the domain package. validate_molecules.py orchestrator also moves. | ✓ |
| Keep in skills/ | Leave where they are. skills/ already has domain separation. Fewer file moves. | |

**User's choice:** Move to domains/<name>/ (Recommended)
**Notes:** None.

---

## Stale Artifact Handling

### Publication Directories (paper/, medium/, poster/)

| Option | Description | Selected |
|--------|-------------|----------|
| Remove from repo | Delete from framework repo. Can live in a separate epistract-publications repo. Keeps framework repo focused. | ✓ |
| Move to docs/publications/ | Keep in-repo but tuck under docs/. Less disruptive. | |
| Keep as-is | Leave at top level. Part of project history. | |

**User's choice:** Remove from repo (Recommended)
**Notes:** None.

### Runtime Outputs (epistract-output/, docs/analysis/)

| Option | Description | Selected |
|--------|-------------|----------|
| Remove + gitignore | Delete committed outputs, add to .gitignore. Generated artifacts shouldn't be in version control. | ✓ |
| Keep for reference | Shows V1 worked. Keep as committed proof. | |

**User's choice:** Remove + gitignore (Recommended)
**Notes:** None.

### V1 Planning Artifacts (.planning/phases/01-05/)

| Option | Description | Selected |
|--------|-------------|----------|
| Leave as-is | GSD workflow history is useful context. Already collapsed in ROADMAP.md. | ✓ |
| Archive to .planning/archive/v1/ | Move V1 phase dirs into archive subdirectory. | |

**User's choice:** Leave as-is (Recommended)
**Notes:** None.

### DEVELOPER.md and docs/demo/

| Option | Description | Selected |
|--------|-------------|----------|
| Remove both | DEVELOPER.md replaced by Phase 10 docs. Demo materials are V1-specific. Both stale after reorg. | ✓ |
| Keep DEVELOPER.md, remove demo/ | DEVELOPER.md has useful reference even if outdated. | |
| Keep both | Leave until Phase 10 handles them explicitly. | |

**User's choice:** Remove both (Recommended)
**Notes:** None.

---

## Plugin Interface Mapping

### Domain Skill Package Location

| Option | Description | Selected |
|--------|-------------|----------|
| Domains own everything, skills/ has symlinks | domains/ has SKILL.md + domain.yaml + Python. skills/ has symlinks. Plugin interface preserved, single source of truth. | ✓ |
| Split: schema in domains/, prompts in skills/ | domain.yaml + Python in domains/. SKILL.md stays in skills/. | |
| Keep skills/ as-is, domains/ only has Python | skills/ holds SKILL.md + domain.yaml. domains/ only has Python modules. Two locations per domain. | |

**User's choice:** Domains own everything, skills/ has symlinks (Recommended)
**Notes:** None.

### Commands and Agents Location

| Option | Description | Selected |
|--------|-------------|----------|
| Stay at root | Tiny markdown files, no benefit to moving. Plugin manifest already knows where they are. | ✓ |
| Move to .claude-plugin/ | Group all plugin interface files. Cleaner root but requires manifest update. | |

**User's choice:** Stay at root (Recommended)
**Notes:** None.

---

## Claude's Discretion

- Python package structure details (whether core/ uses __init__.py, pyproject.toml)
- Import reorganization strategy
- Order of file moves vs. stale artifact removal

## Deferred Ideas

None — discussion stayed within phase scope.
