---
phase: 08-domain-creation-wizard
plan: 02
subsystem: core/domain-wizard
tags: [wizard, yaml, epistemic, code-generation, templates]
dependency_graph:
  requires:
    - phase: 08-01
      provides: convention-based epistemic dispatch, wizard test fixtures
  provides:
    - domain wizard analysis and generation module (core/domain_wizard.py)
    - 12 functions covering full wizard pipeline
    - 10 unit tests validating generation correctness
  affects: [core/domain_wizard.py, tests/test_unit.py, domains/]
tech_stack:
  added: []
  patterns: [template-based code generation, ast.parse + importlib validation, multi-pass LLM prompt design]
key_files:
  created:
    - core/domain_wizard.py
  modified:
    - tests/test_unit.py
key_decisions:
  - "Used textwrap.dedent f-strings for epistemic.py code generation instead of Jinja2 templates"
  - "Validation uses tempfile + importlib.util for isolated import testing of generated code"
  - "generate_domain_package writes to DOMAINS_DIR / domain_name convention"
patterns-established:
  - "Template-based Python code generation with ast.parse validation"
  - "Multi-pass LLM prompt pattern: discovery -> consolidation -> finalization"
requirements-completed: [WIZD-01, WIZD-02, WIZD-03]
duration: 4min
completed: 2026-04-03
---

# Phase 08 Plan 02: Domain Wizard Core Module Summary

**12-function domain wizard module generating complete domain packages (YAML, SKILL.md, epistemic.py, references) with AST-validated epistemic code generation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-03T21:23:18Z
- **Completed:** 2026-04-03T21:27:43Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `core/domain_wizard.py` (810 lines) with full wizard pipeline: document reading, 4 prompt builders, schema generation, package writing, validation
- Generated epistemic.py code passes AST syntax check, importlib import check, function existence check, and dry-run with empty graph data
- 10 new unit tests covering all generation functions -- all pass alongside existing 19 tests (29 total, 23 pass, 6 skip optional deps)

## Task Commits

1. **Task 1: Build core/domain_wizard.py with analysis and generation functions** - `619bd7f` (feat)
2. **Task 2: Unit tests for wizard generation functions** - `a996950` (test)

## Files Created/Modified

- `core/domain_wizard.py` -- Domain wizard with 12 functions: read_sample_documents, build_schema_discovery_prompt, build_consolidation_prompt, build_final_schema_prompt, build_epistemic_prompt, check_domain_exists, generate_domain_yaml, generate_skill_md, generate_epistemic_py, generate_reference_docs, validate_generated_epistemic, write_domain_package, analyze_documents, generate_domain_package
- `tests/test_unit.py` -- Added 10 wizard tests (read docs, too-few error, YAML gen, SKILL.md gen, epistemic gen, validation good/bad, reference docs, domain collision, prompt content)

## Decisions Made

- Used `textwrap.dedent` f-strings for epistemic.py code generation rather than introducing a Jinja2 dependency -- keeps the module self-contained with stdlib only
- Validation pipeline writes to a tempfile and uses `importlib.util.spec_from_file_location` for isolated module testing, cleaned up in finally block
- `generate_domain_package()` derives directory name from domain_name via `lower().replace(" ", "-")` -- consistent with existing domain naming convention

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed PyYAML for Python 3.13**
- **Found during:** Task 1 verification
- **Issue:** System python (3.13) did not have PyYAML installed; `import yaml` failed
- **Fix:** Installed via `python3.13 -m pip install pyyaml --break-system-packages`
- **Files modified:** none (system package)
- **Verification:** `from core.domain_wizard import generate_domain_yaml` succeeds

**2. [Rule 3 - Blocking] Installed pytest for Python 3.13**
- **Found during:** Task 2 test execution
- **Issue:** `python -m pytest` failed with "No module named pytest"
- **Fix:** Installed via `python3.13 -m pip install pytest --break-system-packages`
- **Files modified:** none (system package)
- **Verification:** All 29 tests run successfully

**3. [Rule 1 - Bug] Removed unused `import re`**
- **Found during:** Task 1 lint check
- **Issue:** `ruff check` flagged F401 unused import for `re`
- **Fix:** Removed the import
- **Files modified:** core/domain_wizard.py
- **Verification:** `ruff check core/domain_wizard.py` passes clean

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 bug)
**Impact on plan:** All auto-fixes necessary for execution environment correctness. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations above.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- `core/domain_wizard.py` ready for Plan 03 (CLI integration via `/epistract:domain` command)
- All prompt builders return strings ready for LLM invocation
- `analyze_documents()` and `generate_domain_package()` provide the high-level API

---
*Phase: 08-domain-creation-wizard*
*Completed: 2026-04-03*
