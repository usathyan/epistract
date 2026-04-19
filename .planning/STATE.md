---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Framework Architecture & Domain Developer Experience
status: verifying
stopped_at: Phase 999.1 context gathered
last_updated: "2026-04-19T02:39:36.504Z"
last_activity: 2026-04-19
progress:
  total_phases: 16
  completed_phases: 12
  total_plans: 41
  completed_plans: 46
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-02)

**Core value:** Extract knowledge, not information. Any corpus, any domain -- plug in a schema, get a knowledge graph with epistemic layer.
**Current focus:** Phase 13 — Extraction Pipeline Reliability

## Current Position

Phase: 999.1
Plan: Not started
Status: Phase complete — ready for verification
Last activity: 2026-04-19

Progress: [████████░░] 85%

## Performance Metrics

**Velocity:**

- Total plans completed: 24 (v1)
- Average duration: ~4min
- Total execution time: ~56 min

**By Phase (v1):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 01 | 3 | 18min | 6min |
| Phase 02 | 2 | 7min | 3.5min |
| Phase 03 | 2 | 11min | 5.5min |
| Phase 04 | 3 | 11min | 3.7min |
| Phase 05 | 4 | 16min | 4min |
| 21 | 4 | - | - |
| 999.1 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: 5min, 3min, 3min, 5min, 2min
- Trend: Stable

| Phase 06 P03 | 2min | 2 tasks | 43 files |
| Phase 06 P01 | 5min | 3 tasks | 25 files |
| Phase 06 P02 | 3min | 2 tasks | 3 files |
| Phase 07 P01 | 3min | 2 tasks | 8 files |
| Phase 07 P02 | 5min | 2 tasks | 2 files |
| Phase 07 P03 | 3min | 2 tasks | 3 files |
| Phase 08 P01 | 3min | 2 tasks | 5 files |
| Phase 08 P02 | 4min | 2 tasks | 2 files |
| Phase 08 P03 | 3min | 2 tasks | 2 files |
| Phase 09 P01 | 4min | 2 tasks | 8 files |
| Phase 09 P02 | 3min | 2 tasks | 7 files |
| Phase 09 P03 | 4min | 2 tasks | 7 files |
| Phase 10 P04 | 3min | 2 tasks | 6 files |
| Phase 10 P01 | 4min | 2 tasks | 9 files |
| Phase 10 P03 | 2min | 1 tasks | 1 files |
| Phase 10 P02 | 6min | 2 tasks | 4 files |
| Phase 11 P02 | 2min | 2 tasks | 3 files |
| Phase 12 P01 | 3min | 2 tasks | 3 files |
| Phase 13 P00 | 4 | 4 tasks | 38 files |
| Phase 13 P01 | 6min | 3 tasks | 2 files |
| Phase 13 P02 | 3min | 2 tasks | 2 files |
| Phase 13 P03 | 3min | 3 tasks | 3 files |
| Phase 13 P04 | 5min | 2 tasks | 2 files |

## Accumulated Context

### Roadmap Evolution

- Phase 11 added: End-to-End Scenario Validation and v2.0 Release — regenerate all graphs, validate both use cases, repeatable regression, git sync + push
- Backlog items 999.1 (docs refresh — superseded by Phase 10) and 999.2 (git sync — absorbed into Phase 11) removed
- Phase 1000 (incorrectly numbered) removed
- Phase 12 added (2026-04-13): Extend epistemic classifier with structural biology document signature — surfaced during Phase 11 S2 KRAS run where `structural_sotorasib.txt` registered as `document_type: unknown`. gsd-tool bug note: `phase add` assigned 11 instead of 12 on first attempt because the scanner missed the existing 11-end-to-end-scenario-validation dir; renamed manually.

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v2.0]: Phase numbering continues from 6 (v1 ended at Phase 5)
- [v2.0]: ARCH + CLEAN grouped in Phase 6 (cleanup depends on knowing new structure)
- [v2.0]: CONS + INST grouped in Phase 8 (standalone install needs clean consumer separation)
- [v2.0]: DOCS last (Phase 9) -- documents the final state after all structural changes
- [Phase 06]: Expanded INGS-01..10 range to individual requirement lines for accurate traceability
- [Phase 06]: Created domain_resolver.py from scratch with DOMAINS_DIR, aliases, YAML loading
- [Phase 06]: Created contracts domain package from scratch (9 entity types, 9 relation types)
- [Phase 06]: Skipped workbench move and missing script moves (files do not exist in branch)
- [Phase 06]: resolve_domain returns dict (not path) -- callers extract yaml_path key
- [Phase 06]: Skipped workbench test migration -- scripts/workbench not yet moved to examples/
- [Phase 07]: Pydantic DocumentExtraction model in test_schemas.py; conftest.py centralizes all path setup
- [Phase 07]: Contracts domain cmd_build skipped in cross-domain test due to sift-kg schema format incompatibility
- [Phase 07]: KG provenance tests use pre-recorded mock chat responses and @pytest.mark.unit marker
- [Phase 07]: Fixed contracts domain.yaml from list to dict format for sift-kg compatibility
- [Phase 08]: Convention-based epistemic dispatch via getattr + DOMAIN_ALIASES instead of hard-coded dir_map
- [Phase 08]: Used textwrap.dedent f-strings for epistemic.py code generation instead of Jinja2
- [Phase 08]: Validation uses tempfile + importlib.util for isolated import testing of generated code
- [Phase 08]: Tests use resolve_domain()[schema][entity_types] path since resolver returns nested dict
- [Phase 09]: Template loader self-contained (no core/ imports), uses CLAUDE_PLUGIN_ROOT for plugin install compat
- [Phase 09]: PERSONA_PROMPT removed from system_prompt.py; persona text moved verbatim to contracts template.yaml
- [Phase 09]: Dashboard content via /api/dashboard endpoint (domain HTML or auto-generated stats)
- [Phase 09]: Entity colors: template.entity_colors first, PALETTE array fallback for unknown types
- [Phase 09]: Used telegram_bot (underscore) directory for Python module import compat; bot handlers in HAS_TELEGRAM guard
- [Phase 10]: Paper title: Domain-Agnostic Framework for Agentic KG Construction from Document Corpora
- [Phase 10]: Used @mermaid-js/mermaid-cli via npx for SVG rendering (beautiful-mermaid had no bin entry)
- [Phase 10]: Domain guide wizard-first structure per D-11; real code from both domains per D-12
- [Phase 10]: README opens with domain-agnostic pitch; biomedical content only in Showcase and Pre-built Domains
- [Phase 10]: CLAUDE.md Architecture reframed as three-layer: core/domains/examples with domain resolver
- [Phase 11]: package.json bin entry deferred (scripts/npx-install.sh) until npm account setup
- [Phase 12]: [Phase 12]: Wizard read_sample_documents now routes through sift_kg.ingest.reader.read_document (HAS_SIFT_READER guard mirrors core/ingest_documents.py:20-25). Dropped errors='replace' fallback entirely — binary-as-text IS the bug.
- [Phase 12]: [Phase 12]: When sift-kg is missing, wizard skips non-.txt inputs rather than silently reading binary; caller hits MIN_SAMPLE_DOCS ValueError — loud failure over silent-garbage schemas.
- [Phase 13]: [Phase 13 Plan 00]: FIDL-02a/b/c registered. Plan IDs mapped — 02a→13-03, 02b→13-02+13-04, 02c→13-01.
- [Phase 13]: [Phase 13 Plan 00]: UT-022 split into UT-022a (build_extraction._normalize_fields unit) + UT-022b (normalize_extractions module-level) — one requirement, two enforcement layers, two test IDs.
- [Phase 13]: [Phase 13-01]: Substituted sift-kg defaults (0.0 / "") for None provenance during Pydantic validation; on-disk JSON preserves honest null per D-07/D-08. Validation enforces required fields, not provenance nullability.
- [Phase 13]: [Phase 13-01]: Added sys.path bootstrap to core/build_extraction.py so extractor agents can invoke it as a plain script via absolute path — pre-existing latent bug surfaced by Task 3 subprocess tests.
- [Phase 13]: [Phase 13-02]: normalize_extractions reuses sift-kg default substitution (0.0/"") during Pydantic validation — same reconciliation as Plan 13-01. Ensures honest-null provenance on disk while enforcing required-field contract.
- [Phase 13]: [Phase 13-02]: Composite dedupe score (has_document_id*1000 + len(entities) + len(relations)) with lexicographic filename tie-break; 1000-weight dominance guarantees intact-but-smaller records always beat lossy-but-richer ones.
- [Phase 13]: [Phase 13-02]: Added isinstance(record, dict) guard in _load_and_coerce so malformed non-dict JSON (arrays, strings) classifies as unrecoverable_load instead of crashing _normalize_fields — belt-and-suspenders for Plan 13-04 below-threshold fixture.
- [Phase 13]: [Phase 13-03]: Dual-path provenance threading — BOTH EPISTRACT_MODEL env export AND --model flag literally in dispatch-prompt Bash. D-07 cascade (flag > env > null) guarantees correctness under either Agent-tool env-inheritance behavior; no runtime test-and-flip needed.
- [Phase 13]: [Phase 13-03]: Fixed latent path bug in agents/extractor.md — /scripts/build_extraction.py -> /core/build_extraction.py (post-reorg drift from Phase 06). UT-018 now asserts the old path is absent to guard against regression.
- [Phase 13]: [Phase 13-03]: Grep-style agent-prompt regression tests (UT-017/018) use pure file-read + substring assertions. Runs in <1ms each; locks the prompt contract into CI so Write-tool escape hatches or path-bug regressions fail fast.
- [Phase 13]: [Phase 13-04]: FT-009 RED phase surfaced integration gap — normalize_extractions wrote null provenance to disk but sift_kg.graph.builder.load_extractions silently rejects null cost_usd / model_used (DocumentExtraction non-nullable defaults). Applied 3-line substitution pre-canonical-write (mirror of Plan 13-01/13-02 in-memory reconciliation). Phase 13 acceptance target (>=95% load rate) was unreachable without this.
- [Phase 13]: [Phase 13-04]: UT-013 pre-existing failure (direct write_extraction -> cmd_build path, same null-provenance root cause in build_extraction.py) logged to deferred-items.md with symmetric fix recipe rather than auto-fixed. Verified pre-existing on HEAD via git stash. Plan 13-01 regression slipped through that plan's self-check.
- [Phase 13]: [Phase 13-04]: Goal-backward e2e acceptance test pattern established — copy fixture corpus, run full normalize -> build chain, assert both pass_rate AND graph_data.json existence + node count. FT-009 caught a silent-drop symptom that Plans 13-01..13-03 individually passed but collectively did not deliver, validating the separate-acceptance-plan approach.

### Pending Todos

- [2026-04-13] Auto-approve permissions for V2 scenario runs and document the recipe (`tooling`) — capture Bash/Write/Edit command patterns per scenario, harden `.claude/settings.local.json` incrementally, document recipe in `docs/showcases/drug-discovery-v2.md`

### Blockers/Concerns

- Repo reorganization (Phase 6) is the critical path -- everything else depends on it
- Domain wizard (Phase 7) needs the new `domains/` structure to exist before generating into it
- Backward compatibility with biomedical scenarios must be preserved through reorganization

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260416-fkc | Fix rdkit-pypi -> rdkit (Py3.13+) and bypass SOCKS proxy in workbench api_chat.py | 2026-04-16 | 2fef783 | [260416-fkc-fix-rdkit-pypi-to-rdkit-python-3-13-and-](./quick/260416-fkc-fix-rdkit-pypi-to-rdkit-python-3-13-and-/) |

## Session Continuity

Last session: 2026-04-18T13:07:02.772Z
Stopped at: Phase 999.1 context gathered
Resume file: .planning/phases/999.1-v2-docs-artifacts-refresh/999.1-CONTEXT.md
