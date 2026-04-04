---
phase: 09-consumer-decoupling-and-standalone-install
plan: 02
subsystem: ui
tags: [javascript, html, template-api, dynamic-rendering, workbench]

requires:
  - phase: 09-consumer-decoupling-and-standalone-install
    provides: "Template API endpoint (/api/template), template_loader.py, domain template.yaml files"
provides:
  - "Generic index.html shell with zero hardcoded domain content"
  - "Template-driven app.js populating title, sidebar, welcome, starters, dashboard, legend"
  - "Dynamic entity toggle buttons and legend from /api/graph/entity-types"
  - "Dashboard API endpoint (/api/dashboard) serving domain HTML or auto-generated stats"
  - "Contracts dashboard.html preserving full V1 richness (vendor tables, financials, decisions, key persons)"
affects: [09-03-telegram-bot]

tech-stack:
  added: []
  patterns: [template-driven frontend rendering, dynamic entity color assignment with palette fallback]

key-files:
  created:
    - domains/contracts/workbench/dashboard.html
  modified:
    - examples/workbench/static/index.html
    - examples/workbench/static/app.js
    - examples/workbench/static/chat.js
    - examples/workbench/static/graph.js
    - examples/workbench/static/style.css
    - examples/workbench/server.py

key-decisions:
  - "Dashboard content served via /api/dashboard endpoint (domain HTML file or auto-generated stats)"
  - "Entity colors resolved via template.entity_colors with PALETTE array fallback for unknown types"
  - "Starter card click handlers wired in app.js after dynamic creation (not chat.js static query)"

patterns-established:
  - "Domain dashboard override: domains/{name}/workbench/dashboard.html"
  - "Dynamic entity toggle/legend: fetch /api/graph/entity-types, render with template colors + palette fallback"

requirements-completed: [CONS-01]

duration: 3min
completed: 2026-04-04
---

# Phase 09 Plan 02: Frontend Generalization Summary

**Template-driven workbench frontend dynamically loading all domain content from API, with contracts dashboard preserved as domain-specific HTML fragment**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-04T12:37:52Z
- **Completed:** 2026-04-04T12:41:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Removed all hardcoded STA content from index.html, app.js, chat.js, graph.js, and style.css
- Extracted rich contracts dashboard (vendor tables, financials, decisions, key persons) to domains/contracts/workbench/dashboard.html
- Added /api/dashboard endpoint serving domain-specific HTML or auto-generated entity summary stats
- All entity toggles, legend items, starter questions, page title, loading message now load from template API
- Dynamic entity color assignment with getEntityColor() using template colors + PALETTE fallback

## Task Commits

Each task was committed atomically:

1. **Task 1: Generalize index.html and extract contracts dashboard** - `f03b2a8` (feat)
2. **Task 2: Generalize chat.js, graph.js, and app.js for template-driven rendering** - `9d0e074` (feat)

## Files Created/Modified
- `domains/contracts/workbench/dashboard.html` - Full STA contract dashboard HTML fragment (vendor tables, financials, decisions, key persons)
- `examples/workbench/static/index.html` - Generic shell with empty containers for dynamic content
- `examples/workbench/static/app.js` - Template fetch on init, populates page title, sidebar, welcome, starters, dashboard, legend
- `examples/workbench/static/chat.js` - Accepts template in opts, uses template.loading_message
- `examples/workbench/static/graph.js` - Dynamic ENTITY_COLORS from template, getEntityColor() with palette fallback, dynamic toggle buttons
- `examples/workbench/static/style.css` - Removed STA reference from file comment
- `examples/workbench/server.py` - Added /api/dashboard endpoint, stored _domain_name in app.state

## Decisions Made
- Dashboard content delivered via dedicated /api/dashboard endpoint rather than embedding in /api/template (keeps template lightweight)
- Entity color assignment uses template.entity_colors first, then alphabetical PALETTE index fallback for unknown types
- CSS comment updated to generic "Epistract Workbench" to ensure zero STA references in workbench directory

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed STA reference from style.css comment**
- **Found during:** Task 2 (final verification grep)
- **Issue:** CSS file header comment still said "Sample Contract Analysis Workbench"
- **Fix:** Changed to "Epistract Workbench - Design System"
- **Files modified:** examples/workbench/static/style.css
- **Verification:** `grep -r "STA" examples/workbench/` returns zero results
- **Committed in:** 9d0e074 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial comment fix to meet zero-STA verification requirement. No scope creep.

## Issues Encountered
- 1 pre-existing test failure (test_schema_expansion -- expects COMMITTEE/PERSON/EVENT/STAGE/ROOM entity types in contracts domain.yaml, unrelated to this plan)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Frontend fully generalized, ready for any domain's graph data
- Plan 03 (Telegram bot) can use the same template system for bot persona configuration
- New domains only need workbench/template.yaml (and optionally workbench/dashboard.html) to get a customized UI

---
*Phase: 09-consumer-decoupling-and-standalone-install*
*Completed: 2026-04-04*

## Self-Check: PASSED
