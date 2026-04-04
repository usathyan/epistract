---
phase: 09-consumer-decoupling-and-standalone-install
plan: 01
subsystem: ui
tags: [pydantic, yaml, fastapi, template-system, workbench]

requires:
  - phase: 06-repo-reorganization-and-cleanup
    provides: "domains/ directory structure and domain_resolver.py"
provides:
  - "WorkbenchTemplate Pydantic model for domain template validation"
  - "load_template() function with domain discovery and generic fallback"
  - "auto_generate_starters() for entity-type-based starter questions"
  - "Domain template.yaml files for contracts and drug-discovery"
  - "/api/template endpoint returning domain config as JSON"
  - "Template-driven system_prompt.py (persona from template, not hardcoded)"
affects: [09-02-frontend-generalization, 09-03-telegram-bot]

tech-stack:
  added: [pydantic WorkbenchTemplate model]
  patterns: [template-driven configuration, domain-specific workbench/template.yaml convention]

key-files:
  created:
    - examples/workbench/template_schema.py
    - examples/workbench/template_loader.py
    - domains/contracts/workbench/template.yaml
    - domains/drug-discovery/workbench/template.yaml
  modified:
    - examples/workbench/server.py
    - examples/workbench/system_prompt.py
    - examples/workbench/api_chat.py
    - tests/test_workbench.py

key-decisions:
  - "Template loader imports WorkbenchTemplate for validation but remains self-contained (no core/ imports)"
  - "DOMAINS_DIR resolved via CLAUDE_PLUGIN_ROOT env var with fallback to repo-relative path"
  - "Persona moved verbatim from system_prompt.py to contracts template.yaml"

patterns-established:
  - "Domain workbench config: domains/{name}/workbench/template.yaml"
  - "Template loading: load_template(domain) -> dict with Pydantic validation and generic fallback"

requirements-completed: [CONS-01, INST-02]

duration: 4min
completed: 2026-04-04
---

# Phase 09 Plan 01: Domain Template System & Backend Generalization Summary

**Pydantic-validated template system loading domain-specific workbench config from template.yaml with generic fallback, replacing all hardcoded STA content in Python backend**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-04T12:28:23Z
- **Completed:** 2026-04-04T12:32:40Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Created WorkbenchTemplate and DashboardConfig Pydantic models for template validation
- Built template loader with domain discovery (domains/*/workbench/template.yaml) and generic fallback
- Extracted STA persona, 13 starter questions, and entity colors into contracts template.yaml
- Created drug-discovery template.yaml with biomedical persona and starter questions
- Generalized server.py, system_prompt.py, api_chat.py -- zero STA strings in Python backend
- Added /api/template endpoint serving domain config as JSON
- 21 of 22 workbench tests pass (1 pre-existing failure unrelated to this plan)

## Task Commits

Each task was committed atomically:

1. **Task 1: Template schema, loader, and domain template.yaml files** - `f3aed39` (feat)
2. **Task 2: Generalize server.py, system_prompt.py, api_chat.py with template API** - `4b7c083` (feat)

## Files Created/Modified
- `examples/workbench/template_schema.py` - WorkbenchTemplate and DashboardConfig Pydantic models
- `examples/workbench/template_loader.py` - load_template() and auto_generate_starters() functions
- `domains/contracts/workbench/template.yaml` - STA contract domain template with persona and 13 starters
- `domains/drug-discovery/workbench/template.yaml` - Drug discovery domain template with biomedical persona
- `examples/workbench/server.py` - Accepts domain param, loads template, serves /api/template
- `examples/workbench/system_prompt.py` - Uses template persona instead of hardcoded PERSONA_PROMPT
- `examples/workbench/api_chat.py` - Passes template to build_system_prompt
- `tests/test_workbench.py` - 9 new tests (7 template + 2 template API)

## Decisions Made
- Template loader uses Pydantic for validation but stays self-contained (no core/ imports) per research pitfall 5
- DOMAINS_DIR uses CLAUDE_PLUGIN_ROOT env var for plugin install compatibility with repo-relative fallback
- PERSONA_PROMPT constant removed entirely; persona text moved verbatim to contracts template.yaml

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- System Python (3.13.12) lacked pydantic; tests needed to run via venv Python (/Users/umeshbhatt/code/epistract/.venv/bin/python)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Template system ready for Plan 02 (frontend generalization) to consume /api/template
- Plan 03 (telegram bot) can use load_template() for bot persona configuration
- Both pre-built domains have workbench templates; new domains just need workbench/template.yaml

---
*Phase: 09-consumer-decoupling-and-standalone-install*
*Completed: 2026-04-04*

## Self-Check: PASSED
