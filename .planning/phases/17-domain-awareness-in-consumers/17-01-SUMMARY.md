---
phase: 17-domain-awareness-in-consumers
plan: 01
subsystem: "domain metadata propagation (workbench + launcher + cmd_build)"
tags: [FIDL-06, domain-awareness, metadata, resolve_domain, phase-17]
requires: []
provides:
  - "graph_data.json.metadata.domain field (additive, str | null)"
  - "resolve_domain(output_dir, explicit_domain) -> (str | None, str) helper"
  - "auto-detect domain in workbench when --domain omitted"
affects:
  - core/run_sift.py
  - examples/workbench/template_loader.py
  - examples/workbench/server.py
  - scripts/launch_workbench.py
  - commands/dashboard.md
  - tests/test_unit.py
  - tests/TEST_REQUIREMENTS.md
  - .planning/REQUIREMENTS.md
tech-stack:
  added: []
  patterns:
    - "post-process graph_data.json after sift-kg's run_build (single-source-of-truth metadata pattern)"
    - "pure helper factoring — resolve_domain mirrors Phase 14 __getattr__ / Phase 15 _install_hint / Phase 16 _build_excerpts (single-purpose stateless helper consumed by both server + launcher)"
    - "idempotent double-call (create_app + launcher both call resolve_domain) — each layer self-contained, cost is one extra file read"
key-files:
  created:
    - .planning/phases/17-domain-awareness-in-consumers/17-01-SUMMARY.md
    - .planning/phases/17-domain-awareness-in-consumers/deferred-items.md
  modified:
    - core/run_sift.py (cmd_build post-processes graph_data.json with metadata.domain)
    - examples/workbench/template_loader.py (added resolve_domain helper + json/sys imports)
    - examples/workbench/server.py (create_app calls resolve_domain before load_template)
    - scripts/launch_workbench.py (banner uses resolved domain + source)
    - commands/dashboard.md (--domain bullet documents FIDL-06 precedence rule)
    - tests/test_unit.py (+116 lines: UT-044 + UT-045)
    - tests/TEST_REQUIREMENTS.md (Phase 17 FIDL-06 section + matrix rows)
    - .planning/REQUIREMENTS.md (FIDL-06 row UPDATED in place: — → 17-01)
decisions:
  - "D-01/D-02: post-process graph_data.json in cmd_build rather than monkey-patching sift-kg KnowledgeGraph.save() — keeps us decoupled from sift_kg internals; additive metadata.domain preserves all 7 pre-existing keys"
  - "D-03/D-07/D-09 precedence codified in resolve_domain: explicit > metadata > fallback (with stderr warning when metadata.domain absent on existing graph)"
  - "D-08 legacy: graph without metadata.domain loads generic with visible stderr warning; UT-045 Branch 3 is the regression guard"
  - "D-14: resolve_domain is a NEW helper — load_template signature and behavior unchanged, so test_workbench.py byte-identical regression path holds"
  - "D-15: FIDL-06 traceability row UPDATED in place (— → 17-01), never duplicated; Plan 17-02 will flip to `17-01, 17-02 | Complete`"
metrics:
  duration: "approx 12 min"
  tasks_completed: 2
  files_modified: 8
  files_created: 2
  tests_added: 2
  commits: 3
  completed: "2026-04-21"
---

# Phase 17 Plan 1: Domain Metadata Persistence + Consumer Auto-Detection Summary

Establish `graph_data.json.metadata.domain` as the single source of truth for build-time domain, and wire the workbench launch path (server + launcher) to auto-detect via a new `resolve_domain` precedence helper — fixing the `/epistract:dashboard <dir>` (no `--domain`) falling-through-to-generic-template bug.

## What Changed

- `core/run_sift.cmd_build(output_dir, domain_name)` now post-processes `graph_data.json` immediately after sift-kg's `run_build` returns, injecting `metadata.domain` (str or None) while preserving all 7 pre-existing sift-kg metadata keys byte-identically. Graceful non-fatal error path (OSError/JSONDecodeError) prints a warning but lets the build succeed — consumers fall back via `resolve_domain`'s D-08 legacy branch.
- `examples/workbench/template_loader.resolve_domain(output_dir, explicit_domain) -> (resolved, source)` is the new precedence helper implementing D-03/D-07/D-09. Source is one of `"explicit"`, `"metadata"`, or `"fallback"`. Visible stderr warning when `graph_data.json` exists but `metadata.domain` is absent (D-08 legacy-graph guard).
- `examples/workbench/server.create_app(output_dir, domain=None)` calls `resolve_domain` before `load_template`, so a contracts-built graph auto-loads the contracts template even when `domain=None` — closing Bug 1 + Enh 10 from the axmp-compliance report. Explicit `domain="drug-discovery"` still wins (D-09). App state carries `_domain_name` (resolved) and `_domain_source` for debugging.
- `scripts/launch_workbench.py` calls `resolve_domain` to build a banner line like `Domain: contracts (metadata)` or `Domain: (generic — fallback)`, so console + browser tab + API all agree on the same resolution. Idempotent double-call pattern (both `create_app` and launcher call `resolve_domain`) costs one extra file read and keeps each layer self-contained.
- `commands/dashboard.md` `--domain` bullet documents FIDL-06 precedence rule (explicit > metadata > fallback), including the "flag wins even against a differently-built graph" experimenter intent.
- Two new unit tests (UT-044 + UT-045) pin the behavior RED-first (KeyError / ImportError), then GREEN after Sub-steps A-E land. Neither test requires sift-kg — UT-044 stubs `_import_sift` to inject a fake `run_build` that writes a minimal valid `graph_data.json`; UT-045 is pure file I/O.
- `.planning/REQUIREMENTS.md` FIDL-06 row UPDATED in place (`—` → `17-01`) and footer rewritten — `grep -c "^| FIDL-06 |" .planning/REQUIREMENTS.md` remains exactly 1 (D-15 UPDATE-in-place gate).

## Reference Patterns Followed

- **Phase 14 `__getattr__` / Phase 15 `_install_hint()` / Phase 16 `_build_excerpts` helper-factoring pattern:** `resolve_domain` is the Phase 17 equivalent — a single-purpose pure helper that both the server and the launcher consume. Keeps precedence logic in one place; no conditional logic scattered across call sites.
- **Phase 15/16 UPDATE-in-place pre-registered traceability row pattern (D-15):** FIDL-06 row is UPDATED from `—` to `17-01` rather than appended. Plan 17-02 will flip to `17-01, 17-02 | Complete` by editing the same line — `grep -c "^| FIDL-06 |" REQUIREMENTS.md` stays at 1 forever.
- **RED-first TDD precedent from Phase 13/14/16:** Two-commit sequence — test commit (RED: `KeyError`, `ImportError`) → feat commit (GREEN). Clean bisect path.

## FIDL-06 Status Progression

Current state: `| FIDL-06 | Phase 17 | 17-01 | Pending |`

Plan 17-02 will add:
- Bug 2 fix: `graph.html` `<h1>` populated from metadata via pyvis template (D-04)
- Enh 7 fix: `entity_colors` from `domains/<name>/workbench/template.yaml` injected into pyvis rendering (D-05)
- Enh 9 fix: per-domain `analysis_patterns` block in each template.yaml; `build_system_prompt` reads it instead of hardcoding contracts vocabulary (D-06, UT-046)
- FT-018 end-to-end test: build contracts graph → GET /api/template returns contracts template; build drug-discovery graph → same → drug-discovery (D-13)
- `docs/known-limitations.md` "Domain awareness propagation" section append (D-16)
- FIDL-06 status flip → `| FIDL-06 | Phase 17 | 17-01, 17-02 | Complete |`

## Non-obvious Decisions

- **Post-process graph_data.json instead of monkey-patching sift-kg's `KnowledgeGraph.save()`** (D-01 "simplest intervention"): sift-kg's `export()` builds metadata as a hardcoded dict with no extensibility hook. Monkey-patching `save()` would be fragile across sift-kg upgrades; subclassing would mean threading a custom class through `run_build`. Post-processing the emitted JSON is the minimal, upgrade-safe choice.
- **`resolve_domain` is a NEW helper, not a rewrite of `load_template`:** keeping `load_template(domain_name)` domain-name-pure means the 4 existing `test_workbench.py::test_template_loading_*` tests (lines 270-300) pass byte-identically. D-14 regression gate held without editing those tests.
- **Idempotent double-call in launcher + server** (both call `resolve_domain`): costs one extra file read of `graph_data.json`; benefit is both layers self-contained. Matches "each consumer reads metadata itself" pattern from D-01's single-source-of-truth design.
- **Warning fires on both "metadata dict missing domain key" and "metadata.domain explicitly null":** at this layer we cannot distinguish "user never specified a domain" from "legacy graph predates Phase 17." Warning message ("Rebuild with --domain <name>") is correct advice for both cases.

## Deferred to Plan 17-02

- `graph.html` `<h1>` post-processing in `cmd_view` (Bug 2)
- `entity_colors` from template.yaml injected into pyvis output (Enh 7)
- `domains/drug-discovery/workbench/template.yaml` adds new `analysis_patterns` block; contracts template gets one extracted from existing hardcoded `system_prompt.py` contracts vocabulary
- `build_system_prompt` reads `template.analysis_patterns` instead of hardcoding "CROSS-CONTRACT REFERENCES"
- FT-018 end-to-end (build → workbench → `GET /api/template` per domain)
- `docs/known-limitations.md` "Domain awareness propagation" section
- UT-046 (`build_system_prompt` analysis_patterns load + fallback-with-warning)
- FIDL-06 final status flip to Complete

## Deferred Issues (Out of Scope for 17-01)

- `tests/test_workbench.py::test_schema_expansion` — pre-existing failure referencing `skills/contract-extraction/domain.yaml` (Phase 6 reorg legacy). Verified pre-existing via `git stash && pytest`. Logged in `.planning/phases/17-domain-awareness-in-consumers/deferred-items.md` with recommendation to delete or realign to `domains/contracts/domain.yaml`. Not caused by Phase 17; not in FIDL-06 critical path.
- Pre-existing ruff lint warnings in `tests/test_unit.py` (5 errors at lines 138, 926, 976, 1099, 1154 — all pre-date our additions at line 1625+). Pre-existing ruff format drift in the 4 modified non-test files. Verified both pre-existing via `git stash`. Out of scope per plan's SCOPE BOUNDARY rule.

## Self-Check

Verifying claimed artifacts and commits exist:

- [x] `core/run_sift.py` — `grep 'metadata\["domain"\] = domain_name'` = 1 (FOUND)
- [x] `examples/workbench/template_loader.py` — `grep '^def resolve_domain'` = 1 (FOUND)
- [x] `examples/workbench/server.py` — `grep 'resolve_domain(Path(output_dir), domain)'` = 1 (FOUND)
- [x] `scripts/launch_workbench.py` — `grep 'resolve_domain(output_dir, domain)'` = 1 (FOUND)
- [x] `commands/dashboard.md` — `grep 'FIDL-06'` = 1 (FOUND)
- [x] `.planning/REQUIREMENTS.md` — `grep '^| FIDL-06 |'` = 1, updated to `17-01 | Pending` (FOUND, UPDATE-in-place preserved)
- [x] `tests/TEST_REQUIREMENTS.md` — UT-044 + UT-045 sections + matrix rows (FOUND)
- [x] `tests/test_unit.py` — `test_cmd_build_writes_domain_metadata` + `test_resolve_domain_precedence` present, both PASS in `.venv/bin/python` (GREEN)
- [x] Workbench regression: 21 of 22 pass (1 pre-existing unrelated failure `test_schema_expansion` documented in deferred-items.md)
- [x] No FIDL-01..05 unit tests regress (16 wizard/discover/ingest tests all PASS)
- [x] Commit `adc41de` (docs Task 1), `1c98c70` (test RED), `017fc1a` (feat GREEN) all present in `git log --oneline`

## Self-Check: PASSED
