---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Graph Fidelity & Honest Limits
status: executing
stopped_at: Completed 15-01-PLAN.md (FIDL-04 discover_corpus delegation + warnings[] field)
last_updated: "2026-04-21T12:36:54.297Z"
last_activity: 2026-04-21
progress:
  total_phases: 15
  completed_phases: 9
  total_plans: 32
  completed_plans: 31
  percent: 58
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-02)

**Core value:** Extract knowledge, not information. Any corpus, any domain -- plug in a schema, get a knowledge graph with epistemic layer.
**Current focus:** Phase 15 — format-discovery-parity

## Current Position

Phase: 15 (format-discovery-parity) — EXECUTING
Plan: 2 of 2
Status: Ready to execute
Last activity: 2026-04-21

Progress: [█████░░░░░] 58%

## Performance Metrics

**Velocity:**

- Total plans completed: 14 (v1)
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
| Phase 14 P01 | 4min | 2 tasks | 5 files |
| Phase 14 P02 | 10min | 2 tasks | 2 files |
| Phase 14 P03 | 85min | 3 tasks | 2 files |
| Phase 14-chunk-overlap P04 | 75min | 3 tasks | 3 files |
| Phase 15-format-discovery-parity P01 | 6min | 3 tasks | 5 files |

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
- [Phase 14]: [Phase 14-01]: pyproject.toml [project].dependencies is PARTIAL (only blingfire>=0.1.8); canonical install path remains scripts/setup.sh per M-4 header comment. Full dep-graph declaration in pyproject.toml is post-v3.0 migration work.
- [Phase 14]: [Phase 14-01]: blingfire install NOT gated on INSTALL_ALL — required dep (unlike RDKit/Biopython). Mirrors sift-kg required-install pattern: column-0 heredoc, fail-loud exit 1 on install failure.
- [Phase 14]: [Phase 14-02]: Pivoted from blingfire to chonkie.SentenceChunker — blingfire 0.1.8 ships x86_64-only dylib (no arm64). chonkie is pure Python, owns intra-chunk overlap natively, supplies honest start_index/end_index per sub-chunk (D-11 fix becomes free). Original _sentence_overlap primitive shrank to _tail_sentences (cross-flush only) + _make_chunker factory.
- [Phase 14]: [Phase 14-02]: Substrate-before-wire plan decomposition — Plan 14-02 lands helpers + contract tests; Plan 14-03 wires them into _split_at_paragraphs / _merge_small_sections::_flush / _split_fixed. Helpers live in core/chunk_document.py under '# Internal helpers' before _split_at_sections. UT-031 pins the four Chunk attributes Plan 14-03 will consume (.text, .start_index, .end_index, .token_count).
- [Phase 14]: [Phase 14-02]: _tail_sentences is pure regex-based (not chonkie-backed) — chonkie SentenceChunker instantiation has non-trivial cost; helper runs on short tails in hot paths. Intentional approximation documented in docstring with three rationales (structured-prose input, minor wobble not bug, hot-path pure helper). UT-033b pins the D-02 ∩ D-03 partial-fit intersection boundary.
- [Phase 14]: [Phase 14-03]: Wired chonkie.SentenceChunker into _merge_small_sections::_flush (oversized-clause path) and _split_fixed (fallback) via _make_chunker factory. Cross-flush overlap (ARTICLE boundaries) carried by nonlocal _pending_tail cache populated from RAW buffer_text via _tail_sentences — NOT chunks[-1]['text'] (M-1/M-2 invariant pinned by UT-037).
- [Phase 14]: [Phase 14-03]: Deleted _split_at_paragraphs entirely (dead code after chonkie adoption). Two-commit atomic split: Task 1 left the symbol in place as dead-code-in-transition so the intermediate commit stayed green; Task 2 rewrote _split_fixed and removed the symbol atomically.
- [Phase 14]: [Phase 14-03]: Extended chunk JSON schema with overlap_prev_chars, overlap_next_chars, is_overlap_region + honest per-sub-chunk char_offset (D-10, D-11). Final chunk post-loop correction: chunks[-1]['overlap_next_chars'] = 0. Plan 14-04's e2e gates can assume 7-key shape on both split paths.
- [Phase 14]: [Phase 14-03]: Chunk count on tests/fixtures/sample_contract_text.txt unchanged (4 → 4) — same boundaries, same IDs, same char_offsets; only new provenance fields differ. Plan 14-04's V2 baseline regression gate can assume structural equivalence; node/edge counts should hold or increase (boundary-straddling entities/relations newly recoverable).
- [Phase 14]: [Phase 14-03]: Chonkie 1.6.2 collapses highly-repeated identical sentences into one chunk regardless of input size (verified: 'Sentence. ' * 5000 → 1 chunk at chunk_size=10000). Tests exercising oversized-split must use varied sentence content. Documented in UT-036 inline comment.
- [Phase 14-chunk-overlap]: [Phase 14-04]: FT-011 GREEN/RED proof uses monkey-patch of BOTH _make_chunker (zero-overlap chonkie) AND _tail_sentences (cross-flush). Single patch of either would leave one overlap path active post-chonkie pivot. Plan drafted pre-pivot assumed _sentence_overlap was the sole overlap primitive; current code has both chonkie-native (intra-chunk) and _tail_sentences (cross-flush) — both must be disabled for the RED assertion to be honest.
- [Phase 14-chunk-overlap]: [Phase 14-04]: FT-012 reads graph_data.json directly per-scenario (via tests/corpora/*/output-v2 resolution mirroring run_regression.py::_resolve_output_dir) rather than subprocess-ing run_regression.py and parsing stdout. Deliberate deviation from plan: actual runner output format (label N1/N2 E1/E2) does not match plan's assumed 'label: N nodes, E edges'. Direct graph_data.json reading is more robust, equivalent in intent, and avoids stdout-parsing fragility.
- [Phase 14-chunk-overlap]: [Phase 14-04]: FT-011 RED mode monkey-patches BOTH _make_chunker (chonkie intra-chunk overlap) AND _tail_sentences (cross-flush overlap). Post-pivot topology has two orthogonal overlap paths; patching either alone leaves one active.
- [Phase 14-chunk-overlap]: [Phase 14-04]: FT-012 reads graph_data.json directly per scenario (mirroring run_regression.py::_resolve_output_dir) rather than subprocess-ing run_regression.py and parsing stdout. Runner's actual output format (label N1/N2 E1/E2) does not match plan's assumed 'label: N nodes, E edges'. Direct graph read is equivalent in intent, more robust, avoids stdout-parsing fragility.
- [Phase 14-chunk-overlap]: [Phase 14-04]: Human checkpoint resolved 2026-04-20 via Option 3a — adopt pre-Phase-14 observed counts (from 2026-04-13 tests/corpora/*/output-v2/graph_data.json artifacts) as V2 regression floors. Contract scenario keeps D-14 hard floor (341/663). Rationale: Phase 14 acceptance is proven by unit tests UT-031..UT-038 + UT-033b + UT-036b and E2E test FT-011; FT-012 is a forward-regression guardrail, not a Phase 14 acceptance test.
- [Phase 15-format-discovery-parity]: [Phase 15-01]: PEP 562 __getattr__ idiom over functools.lru_cache for SUPPORTED_EXTENSIONS — transparent back-compat with 'from core.ingest_documents import SUPPORTED_EXTENSIONS' consumers, no caller rewrites required.
- [Phase 15-format-discovery-parity]: [Phase 15-01]: Tuple-cache (text_class, ocr_class) in single module-level var — one computation serves both OCR modes via set-difference over the Kreuzberg-supported extension set.
- [Phase 15-format-discovery-parity]: [Phase 15-01]: Runtime set is 29 text-class extensions on sift-kg 0.9.x (Kreuzberg's 37 minus 1 zip minus 8 images); UT-039 asserts >=28 for forward-compat tolerance, not the literal 29 (CONTEXT.md said >=29 — corrected to >=28 against the actual set).
- [Phase 15-format-discovery-parity]: [Phase 15-01]: ingest_corpus wraps discover_corpus in try/ImportError so CLI users see a clean error-dict path; raw traceback never surfaces. Aligns with existing print(..., file=sys.stderr) error convention in the same function.
- [Phase 15-format-discovery-parity]: [Phase 15-01]: triage.json warnings[] field is additive — no schema version bump. examples/workbench/data_loader.py reads documents[] keys it knows about; new field is invisible to existing consumers.

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

Last session: 2026-04-21T12:36:54.293Z
Stopped at: Completed 15-01-PLAN.md (FIDL-04 discover_corpus delegation + warnings[] field)
Resume file: None
