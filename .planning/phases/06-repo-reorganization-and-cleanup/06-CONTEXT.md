# Phase 6: Repo Reorganization and Cleanup - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the flat `scripts/` codebase into `core/`, `domains/`, `examples/` top-level directories with clean domain-agnostic imports, and remove stale V1 artifacts. After this phase, `import epistract.core` works without domain-specific dependencies, and adding a new domain means only creating files under `domains/<name>/`.

</domain>

<decisions>
## Implementation Decisions

### Core Module Boundary
- **D-01:** Core directory (`core/`) contains: `domain_resolver.py`, `build_extraction.py`, `run_sift.py`, `ingest_documents.py`, `entity_resolution.py`, `chunk_document.py`, `label_communities.py`, and the epistemic dispatcher (`label_epistemic.py`)
- **D-02:** `label_epistemic.py` stays in core as a dispatcher. Each domain provides its own epistemic rules module (e.g., `domains/contracts/epistemic.py`). Core dispatches to whichever domain is active.
- **D-03:** `label_communities.py` is core — the community detection + LLM labeling algorithm is domain-agnostic and works on any graph's community structure.

### Domain Package Layout
- **D-04:** Domain-specific Python modules live inside `domains/<name>/` — co-located with `domain.yaml` and `SKILL.md`. Examples: `domains/contracts/epistemic.py`, `domains/contracts/extract.py`
- **D-05:** Validation scripts (currently `skills/drug-discovery-extraction/validation-scripts/`) move to `domains/drug-discovery/validation/`. The `validate_molecules.py` orchestrator also moves to the drug-discovery domain.
- **D-06:** Each domain directory is self-contained: SKILL.md + domain.yaml + references/ + Python modules + validation scripts (if applicable)

### Stale Artifact Handling
- **D-07:** Remove `paper/`, `medium/`, `poster/` from the repo — publication artifacts don't belong in the framework repo. Can live in a separate repo if needed.
- **D-08:** Remove `epistract-output/` and `docs/analysis/` — add both to `.gitignore`. Generated runtime artifacts shouldn't be in version control.
- **D-09:** Remove `DEVELOPER.md` (34KB V1 dev guide) and `docs/demo/` (demo video materials) — both are V1-specific and will be replaced by Phase 10 documentation.
- **D-10:** Keep `.planning/phases/01-05/` as-is — GSD workflow history is useful context, already collapsed in ROADMAP.md.

### Plugin Interface Mapping
- **D-11:** `commands/` and `agents/` stay at repo root — tiny markdown files, no benefit to moving. Plugin manifest already knows where they are.
- **D-12:** Domains own everything (SKILL.md + domain.yaml + Python + references). `skills/` directory contains symlinks or thin wrappers that point to `domains/`. Plugin interface preserved, single source of truth in `domains/`.

### Claude's Discretion
- Python package structure details (whether core/ uses `__init__.py`, `pyproject.toml`, etc.) — implementation choice for planner
- Import reorganization strategy (how to update imports across scripts) — planner decides approach
- Order of file moves vs. stale artifact removal — sequencing is an implementation detail

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Architecture
- `.planning/PROJECT.md` — Target architecture diagram (core/, domains/, examples/)
- `.planning/REQUIREMENTS.md` — ARCH-01, ARCH-02, ARCH-03, CLEAN-01, CLEAN-02 acceptance criteria
- `.planning/ROADMAP.md` §Phase 6 — Success criteria (5 items)

### Codebase Analysis
- `.planning/codebase/STRUCTURE.md` — Current directory layout and file inventory
- `.planning/codebase/CONVENTIONS.md` — Import patterns, naming, code style to preserve
- `.planning/codebase/ARCHITECTURE.md` — Current data flow and layer dependencies

### Domain Configuration
- `skills/drug-discovery-extraction/domain.yaml` — Drug discovery domain schema (17 entity types, 30 relation types)
- `skills/contract-extraction/domain.yaml` — Contract domain schema (11 entity types, 11 relation types)

### Plugin Interface
- `.claude-plugin/plugin.json` — Plugin manifest (must be updated if skills/ paths change)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/domain_resolver.py` — Already handles dynamic domain loading by name; will be core infrastructure
- `scripts/label_epistemic.py` — Already imports domain-specific modules dynamically; natural dispatcher pattern
- `scripts/__init__.py` — Package marker already exists in scripts/

### Established Patterns
- Domain-specific epistemic modules (`epistemic_biomedical.py`, `epistemic_contract.py`) follow a consistent function interface — can be formalized as a domain contract
- `domain_resolver.py` uses `skills/<domain>/domain.yaml` path convention — needs updating to `domains/<domain>/domain.yaml`
- All scripts use `pathlib.Path` throughout — path changes should be straightforward

### Integration Points
- `scripts/run_sift.py` is the central orchestrator — imports from domain_resolver, label_communities, label_epistemic
- `commands/*.md` reference `scripts/` paths in bash commands — all need path updates
- `skills/` directory is read by Claude Code plugin runtime — symlinks must work for plugin discovery
- `scripts/workbench/` (FastAPI app) will move to `examples/` — import paths need updating

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for the actual file reorganization mechanics.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-repo-reorganization-and-cleanup*
*Context gathered: 2026-04-02*
