---
phase: 05
plan: 04
subsystem: workbench
status: checkpoint_pending
checkpoint_task: 4
checkpoint_type: human-verify
tags: [fastapi, httpx, async-cache, openrouter, javascript, optgroup, workbench, model-selector]

dependency_graph:
  requires: [05-03]
  provides: [live-openrouter-model-browser]
  affects: [examples/workbench/server.py, examples/workbench/static/chat.js, examples/workbench/static/index.html, examples/workbench/static/style.css]

tech_stack:
  added: [httpx async client for OpenRouter fetch, module-level TTL cache dict]
  patterns:
    - "Module-level TTL cache for external HTTP fetches with graceful stale/static fallback (no new deps)"
    - "Pure filter/group function separable from async fetcher for deterministic unit tests"
    - "Extended response schema with optional fields (group, input_cost, ...) preserves existing id/label contract — frontend detects by field presence"
    - "Frontend <optgroup> rendering with category-ordered rebuild on sort-toggle; localStorage for both selection and view mode"

key_files:
  modified:
    - examples/workbench/server.py
    - examples/workbench/static/chat.js
    - examples/workbench/static/index.html
    - examples/workbench/static/style.css
    - tests/test_unit.py
  created: []

key_decisions:
  - "Filter on architecture.output_modalities == ['text'], NOT architecture.modality == 'text->text', because the latter drops all Anthropic models (Pitfall 1)"
  - "Strip leading ~ from id prefix before CATEGORY_MAP lookup so alias models group correctly (Pitfall 3)"
  - "Sort button hidden when response has no grouped data — Anthropic/Foundry look unchanged (Pitfall 6)"
  - "Cache reset in tests via direct srv._or_models_cache assignment rather than a new clear_cache() helper — keeps production API minimal (Pitfall 4)"

requirements_completed: []

metrics:
  tasks_total: 4
  tasks_completed: 3
  tasks_pending: 1
  duration_estimate: "~45 min for Tasks 1-3"
  completed_date: "2026-04-24"
---

# Phase 05 Plan 04: Live OpenRouter Model Browser Summary

**One-liner:** Live OpenRouter model fetch with 1-hour TTL cache, provider-grouped optgroup `<select>`, and cost-sort toggle button persisted to localStorage.

## Status: CHECKPOINT PENDING

Tasks 1, 2, and 3 are complete and committed. Task 4 (human smoke test) requires manual verification before the plan can be marked complete.

## What Was Built

### Task 1 — TDD RED: 6 Failing Tests (commit `3adfd07`)

Added 6 new `@pytest.mark.unit` tests to `tests/test_unit.py` in the workbench model-selector section:
- `test_filter_or_models_text_only` — pure function drops non-text output_modalities
- `test_filter_or_models_excludes_routers` — pure function drops openrouter/ prefix, -1 pricing, expired models
- `test_filter_or_models_grouping` — correct CATEGORY_MAP lookup including tilde-alias (~anthropic/) handling
- `test_filter_or_models_label_format` — label contains `($X.XX/M)` or `(free)`, provider prefix stripped
- `test_get_models_openrouter_live` — mocked httpx fetch returns grouped models via TestClient
- `test_get_models_openrouter_fallback` — ConnectError causes fallback to PROVIDER_MODELS['openrouter']

### Task 2 — TDD GREEN: Backend (commit `7603e5e`)

Updated `examples/workbench/server.py`:
- Module-level `_or_models_cache` dict + `_OR_CACHE_TTL = 3600` + `_OPENROUTER_DEFAULT_MODEL`
- `CATEGORY_MAP`: 12 provider prefixes mapped to optgroup category labels
- `_filter_and_group_or_models(raw)`: pure function filtering text-only models, excluding openrouter/ prefix, negative pricing, and expired dates; attaches group, input_cost, output_cost, context_length, free fields; strips tilde prefix before CATEGORY_MAP lookup
- `_fetch_or_models()`: async TTL-cached fetch from openrouter.ai/api/v1/models; falls back to PROVIDER_MODELS['openrouter'] on any network error
- `get_models()` OpenRouter branch: now `await _fetch_or_models()` instead of static list; Anthropic and Foundry branches are byte-identical to Plan 03

All 6 new tests green. Full suite: 106 passed / 2 skipped.

### Task 3 — Frontend (commit `c7bbd61`)

- `examples/workbench/static/index.html`: Added `<button id="model-sort-btn" class="model-sort-btn">` before `<select id="model-select">`, hidden by default
- `examples/workbench/static/style.css`: Added `.model-sort-btn` and `.model-sort-btn:hover` rules after `.model-select option` block
- `examples/workbench/static/chat.js`: Rewrote `loadModelSelector()` with `CATEGORY_ORDER` constant, `buildGroupedOptions()`, `buildCostSortedOptions()` helpers; sort toggle persists `localStorage.epistract_model_sort`; `sendMessage()` backward compat preserved

chat.js: 300 lines (under 350 limit), braces balanced, 0 console.log statements.

### Task 4 — Human Smoke Test (PENDING)

Automated verification: 6/6 pytest tests pass. Human verification of the 11-step smoke test procedure required before this plan is complete.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `3adfd07` | test(05-04): add failing tests for live OpenRouter model browser |
| 2 | `7603e5e` | feat(05-04): add live OpenRouter model fetch with TTL cache + grouping |
| 3 | `c7bbd61` | feat(05-04): render live models in optgroups + cost sort toggle |

## Deviations from Plan

None — plan executed exactly as written for Tasks 1-3.

Pre-existing ruff lint issues in `tests/test_unit.py` (lines 139, 965, 1015, 1138, 1193) are out of scope. The 6 new test functions have no lint errors.

## Known Stubs

None. The live OpenRouter fetch is fully wired; the 5-item static fallback is intentional behavior on network failure, not a stub.

## Threat Flags

No new security surface beyond the plan's threat model. Frontend uses DOM property assignment only — no innerHTML with untrusted data (T-05-04-05 mitigated).

## Self-Check: PASSED

- `tests/test_unit.py` — all 6 new test functions present and passing
- `examples/workbench/server.py` — `_or_models_cache`, `_OR_CACHE_TTL`, `CATEGORY_MAP`, `_filter_and_group_or_models`, `_fetch_or_models`, `await _fetch_or_models()` all present
- `examples/workbench/static/index.html` — `id="model-sort-btn"` present (1 match)
- `examples/workbench/static/style.css` — `.model-sort-btn` rule present
- `examples/workbench/static/chat.js` — `buildGroupedOptions`, `buildCostSortedOptions`, `CATEGORY_ORDER`, `epistract_model_sort` all present
- Commits `3adfd07`, `7603e5e`, `c7bbd61` confirmed in git log
