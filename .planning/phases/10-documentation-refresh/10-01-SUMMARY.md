---
phase: 10-documentation-refresh
plan: 01
subsystem: docs
tags: [mermaid, svg, diagrams, gitignore, architecture]

# Dependency graph
requires: []
provides:
  - Four architecture diagrams (mermaid + SVG) for README and domain guide embedding
  - STA data safety rules in .gitignore
affects: [10-02, 10-03]

# Tech tracking
tech-stack:
  added: ["@mermaid-js/mermaid-cli (npx, not installed)"]
  patterns: ["Mermaid source + SVG render pairs in docs/diagrams/"]

key-files:
  created:
    - docs/diagrams/two-layer-kg.mmd
    - docs/diagrams/two-layer-kg.svg
    - docs/diagrams/domain-package.mmd
    - docs/diagrams/domain-package.svg
  modified:
    - docs/diagrams/architecture.mmd
    - docs/diagrams/architecture.svg
    - docs/diagrams/data-flow.mmd
    - docs/diagrams/data-flow.svg
    - .gitignore

key-decisions:
  - "Used @mermaid-js/mermaid-cli via npx instead of beautiful-mermaid (beautiful-mermaid had no bin entry point)"
  - "drug-discovery/ name kept in architecture.mmd as domain label, not biomedical jargon"

patterns-established:
  - "Diagram workflow: edit .mmd source, render with npx @mermaid-js/mermaid-cli -i X.mmd -o X.svg"

requirements-completed: [DOCS-02]

# Metrics
duration: 4min
completed: 2026-04-04
---

# Phase 10 Plan 01: Architecture Diagrams & Gitignore Summary

**Four framework architecture diagrams (three-layer, two-layer KG, data-flow, domain-package) as Mermaid + SVG pairs, plus STA data safety gitignore rules**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-04T17:10:15Z
- **Completed:** 2026-04-04T17:14:26Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Replaced biomedical-specific architecture diagram with three-layer framework diagram (core/domains/examples)
- Created two-layer KG diagram showing brute facts + epistemic super-domain with domain-agnostic emphasis
- Updated data-flow diagram to show domain-agnostic pipeline with core script labels and domain.yaml input
- Created domain package anatomy diagram showing structure of a pluggable domain directory
- Added explicit STA contract data exclusion rules to .gitignore

## Task Commits

Each task was committed atomically:

1. **Task 1: Create four Mermaid architecture diagrams and render to SVG** - `085725f` (feat)
2. **Task 2: Audit and update .gitignore for STA data safety** - `aa87263` (chore)

## Files Created/Modified
- `docs/diagrams/architecture.mmd` - Three-layer framework diagram (core/domains/examples)
- `docs/diagrams/architecture.svg` - Rendered three-layer diagram
- `docs/diagrams/two-layer-kg.mmd` - Two-layer KG: brute facts + epistemic super-domain
- `docs/diagrams/two-layer-kg.svg` - Rendered two-layer KG diagram
- `docs/diagrams/data-flow.mmd` - Domain-agnostic pipeline flow with core script labels
- `docs/diagrams/data-flow.svg` - Rendered data flow diagram
- `docs/diagrams/domain-package.mmd` - Domain package anatomy (domain.yaml, SKILL.md, epistemic.py, etc.)
- `docs/diagrams/domain-package.svg` - Rendered domain package diagram
- `.gitignore` - Added STA data exclusion rules, demo recording exclusions

## Decisions Made
- Used @mermaid-js/mermaid-cli via npx instead of beautiful-mermaid — the beautiful-mermaid package had no bin entry point and produced no output
- Kept "drug-discovery/" as a domain name label in architecture.mmd — it is the name of a pluggable domain, not biomedical-specific language

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched from beautiful-mermaid to @mermaid-js/mermaid-cli**
- **Found during:** Task 1 (SVG rendering)
- **Issue:** beautiful-mermaid package had no bin entry in package.json; running it directly produced no output
- **Fix:** Used `npx @mermaid-js/mermaid-cli -i X.mmd -o X.svg` which rendered all four diagrams successfully
- **Files modified:** None (tooling change only)
- **Verification:** All four SVG files generated, non-empty (18-25KB each)
- **Committed in:** 085725f (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal — alternative rendering tool produced identical SVG output. No scope creep.

## Issues Encountered
None beyond the beautiful-mermaid tool issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four diagram SVGs ready for embedding in README (Plan 02) and Domain Guide (Plan 03)
- .gitignore secured against STA data leakage

---
*Phase: 10-documentation-refresh*
*Completed: 2026-04-04*
