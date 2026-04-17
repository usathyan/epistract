---
phase: 13-extraction-pipeline-reliability
plan: 03
subsystem: extraction-pipeline
tags: [agent-prompt, slash-command, ingest-pipeline, provenance, normalization, pydantic, sift-kg, extraction-contract]

# Dependency graph
requires:
  - phase: 13-extraction-pipeline-reliability
    provides: Write-time Pydantic validation + --model / --cost / EPISTRACT_MODEL contract (Plan 13-01 Wave 1)
  - phase: 13-extraction-pipeline-reliability
    provides: core/normalize_extractions.py CLI + --fail-threshold gate + _normalization_report.json audit artifact (Plan 13-02 Wave 2)
provides:
  - agents/extractor.md Required-Fields block (D-09) — document_id / entities / relations declared REQUIRED top-level
  - agents/extractor.md HOW-to-write block (D-10) — primary --json invocation + stdin-pipe fallback; Write-tool forbidden
  - agents/extractor.md latent path bug fixed — /scripts/build_extraction.py -> /core/build_extraction.py (matches the post-reorg filesystem)
  - commands/ingest.md --fail-threshold argument (default 0.95, range [0.0, 1.0]) — threads into Step 3.5 normalization
  - commands/ingest.md Step 3.5 Normalize Extractions — wires core/normalize_extractions.py into the user-facing pipeline between extract (Step 3) and validate (Step 4)
  - commands/ingest.md provenance threading (D-07 cascade) — BOTH EPISTRACT_MODEL env export AND --model flag documented in dispatch prompt (belt + suspenders)
  - commands/ingest.md Step 7 Report Summary extended — surfaces normalization pass-rate from _normalization_report.json
  - tests/test_unit.py — UT-017 (Required-Fields + Write-tool ban) and UT-018 (stdin fallback + core/ path regression guard)
affects:
  - 13-04-PLAN.md (e2e regression — extractor agents now follow the contract enforced by D-06 write-time raise; Step 3.5 abort is runnable end-to-end)
  - /epistract:ingest user experience — parallel Agent dispatches now carry honest provenance, normalization runs automatically, abort-before-build gate keeps silent-drop 30% bug from recurring

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-path provenance threading: env var (EPISTRACT_MODEL) AND CLI flag (--model) both set unconditionally — agent-dispatch runtimes with unknown env-inheritance semantics still get provenance via the flag per D-07 cascade"
    - "Step 3.5 pipeline insertion point — normalization boundary is an explicit markdown heading inside commands/ingest.md so future dispatcher edits cannot silently break the sequencing between parallel Agent dispatches and downstream build"
    - "Grep-style agent-prompt regression tests (UT-017/018) — pure file-read + substring checks, <1ms each; lock prompt contract into CI so path bugs (/scripts/ vs /core/) or Write-tool escape hatches cannot regress silently"
    - "Belt-and-suspenders defense for extraction contract: prompt tells agents what's required (D-09) + Pydantic validation enforces it at write time (D-06) + normalization catches survivors (D-03) — three layers, each sufficient alone"

key-files:
  created: []
  modified:
    - agents/extractor.md
    - commands/ingest.md
    - tests/test_unit.py

key-decisions:
  - "Kept the original `## Output Format` heading AND inserted `## REQUIRED top-level fields` adjacent to it rather than renaming or merging. Plan Edit C's `old_string`/`new_string` replaced only the `**CRITICAL:**` sentence — preserving `## Output Format` keeps the section header stable for any downstream tools grepping for it, and the Required-Fields block reads naturally as a sub-section immediately below."
  - "Both EPISTRACT_MODEL env export AND --model flag threading documented unconditionally (belt + suspenders). RESEARCH.md §Ingest Pipeline Orchestration lines 233-242 flagged env-var inheritance through Claude Code's Agent tool as LOW confidence. Rather than test-and-flip at runtime, doc prescribes BOTH paths — D-07 cascade (flag > env > null) means flag wins if inherited, flag rescues if not."
  - "UT-017/018 use substring assertions (`in prompt`, `not in prompt`) rather than regex. Plan mandates simple grep-style checks; substring matching tolerates whitespace/formatting drift in the prompt while still catching contract regressions (path bug, missing Required-Fields block, Write-tool escape hatch)."

patterns-established:
  - "Path fix + contract addition colocation: when fixing a latent path bug in a prompt, pair it with a regression test that asserts the WRONG path is absent (`/scripts/build_extraction.py not in prompt`). Prevents rename-drift and silent re-introduction."
  - "Two-heading sub-section pattern in prompts: `## Output Format` followed immediately by `## REQUIRED top-level fields` works fine — adjacent h2s are idiomatic markdown for related-but-separate topics and downstream tools (including the UT-017/018 grep tests) care about heading presence, not nesting."
  - "Agent-prompt regression locks: for every behavioral contract added to agents/*.md, add a grep-style test that asserts the contract text is present. Keeps prompts from silently drifting under future edits."

requirements-completed:
  - FIDL-02a

# Metrics
duration: 3min
completed: 2026-04-17
---

# Phase 13 Plan 03: Extractor Agent + Ingest Pipeline Wiring Summary

**Extractor prompt gains REQUIRED top-level fields block + stdin-pipe fallback + Write-tool ban + /scripts/→/core/ path fix; /epistract:ingest gains --fail-threshold arg, Step 3.5 normalization call, BOTH env-var + --model flag provenance threading, and normalization pass-rate in Step 7 report.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-17T12:34:34Z
- **Completed:** 2026-04-17T12:37:08Z
- **Tasks:** 3
- **Files modified:** 3 (agents/extractor.md, commands/ingest.md, tests/test_unit.py)

## Accomplishments

- Extractor agent contract now explicit: agents know `document_id` / `entities` / `relations` are required, know to write via `build_extraction.py` only (never Write tool), know the stdin-pipe fallback for when Bash permissions deny `--json`, and know to report failure honestly rather than silently falling back to Write.
- Latent path bug fixed: `${CLAUDE_PLUGIN_ROOT}/scripts/build_extraction.py` → `${CLAUDE_PLUGIN_ROOT}/core/build_extraction.py`. Pre-existing documentation regression from the V2 `scripts/` → `core/` reorg (Phase 06) — the extractor prompt still pointed at the old path. UT-018 now guards this.
- /epistract:ingest user-facing pipeline wired end-to-end: `--fail-threshold` argument documented, Step 3.5 inserted between extract and validate, normalization pass-rate surfaced in the Step 7 summary, and provenance threads through the parallel Agent dispatcher via BOTH `EPISTRACT_MODEL=<id>` env export and `--model <id>` literally in the dispatch-prompt Bash invocation.
- Belt-and-suspenders provenance pattern locked in: if Claude Code's Agent tool inherits env vars, the `--model` flag wins the D-07 cascade; if it doesn't, the flag alone still threads provenance. No runtime test-and-flip needed.
- 2 new unit tests (UT-017 + UT-018) pass in 0.12s total. 16 Phase 13 tests still green (UT-012 regression + UT-019..UT-030 from Plans 01/02 + new UT-017/018).

## Task Commits

Each task was committed atomically:

1. **Task 1: Update agents/extractor.md — Required-Fields block, stdin fallback, path fix** — `d4c2c99` (feat)
2. **Task 2: Update commands/ingest.md — Step 3.5 + --fail-threshold + EPISTRACT_MODEL + --model flag threading** — `adf4b6c` (feat)
3. **Task 3: Add UT-017 + UT-018 grep-assertion unit tests** — `92bc09e` (test)

## Files Created/Modified

### Modified
- `agents/extractor.md` — +24 / -5 lines. Added `## REQUIRED top-level fields` block (document_id / entities / relations), `## HOW to write extractions` block (primary `--json` invocation + stdin-pipe fallback), Write-tool ban + honest-failure-report mandate. Fixed path bug on the fallback invocation. Removed the old standalone "Write extraction using stdin pipe..." fence (its content is now inside the HOW block as the labeled fallback).
- `commands/ingest.md` — +29 / -0 lines. Added `--fail-threshold <float>` argument. Added "Provenance threading (BOTH env var AND `--model` flag)" block with example dispatch-prompt Bash line immediately before the parallel-Agent-dispatch instruction. Inserted `### Step 3.5: Normalize Extractions` section between Step 3 and Step 4 with sequencing note, feature summary, invocation block, fail-threshold pass-through instruction, and report-path + abort-before-Step-4 rule. Added Normalization pass-rate bullet to Step 7 summary list.
- `tests/test_unit.py` — +39 lines. New "Phase 13 — FIDL-02a: extractor.md contract" section appended after Plan 02's FIDL-02b block. Added `test_extractor_prompt_required_fields` (UT-017) and `test_extractor_prompt_stdin_fallback` (UT-018). Both are pure file-read + substring-assertion tests under `@pytest.mark.unit`. No skip-if-sift-kg-missing marker needed (neither imports sift-kg).

## Decisions Made

- **Both env-var AND --model flag in dispatch prompt (belt + suspenders).** Plan prescribed this, but the rationale reinforces: RESEARCH.md §Agent dispatcher wiring called env-var inheritance "more robust for parallel dispatch" but known_pitfalls §1 flagged it LOW confidence. Rather than defer a test-and-flip, doc prescribes BOTH unconditionally — D-07 cascade guarantees correctness under either runtime behavior.
- **Kept original `## Output Format` heading adjacent to new `## REQUIRED top-level fields` heading.** Plan Edit C's `old_string` was `**CRITICAL: Use entity_type and relation_type as field names, NOT type.**` — the edit replaces only that line and leaves the surrounding `## Output Format` heading intact. Two adjacent h2s read naturally and preserve the existing section marker for any tool that greps for "Output Format".
- **Grep-style substring tests over regex.** UT-017/018 use `in prompt` / `not in prompt` checks rather than regex. Plan mandates simple grep-style assertions; substring tolerates benign whitespace/format drift while still locking the contract.

## Deviations from Plan

None - plan executed exactly as written. All three tasks' edits applied verbatim from the plan spec; all acceptance criteria for all three tasks pass on first run; both new unit tests pass on first run.

## Issues Encountered

- **Adjacent markdown headings (`## Output Format` → `## REQUIRED top-level fields`) are stylistically slightly awkward.** This is how the plan Edit C is written (the `old_string` is only the `**CRITICAL:**` line, so the preceding `## Output Format` heading stays). Decided to follow the plan literally rather than re-architect the heading hierarchy — both headings are valid top-level concerns (format spec vs required fields) and the downstream grep tests don't care about nesting.

## User Setup Required

None — no external service configuration required. All edits are to prompt/markdown and test files committed to the repo.

## Next Phase Readiness

**Ready for Plan 13-04 (e2e regression tests):**
- Extractor agents now follow the D-09/D-10 contract — failure modes observed in axmp-compliance (variant filenames + missing `document_id`) should not recur in agent-generated JSON going forward.
- `/epistract:ingest` pipeline is fully wired end-to-end: `--fail-threshold` → Step 3.5 → abort-before-build. FT-009 / FT-010 from Plan 13-00 can exercise the ingest command directly.
- Provenance threads end-to-end: extractor agents receive `EPISTRACT_MODEL=<id>` + `--model <id>` in their dispatch Bash invocation, `build_extraction.py` reads both per D-07 cascade, extraction JSON now carries honest `model_used` instead of the old hardcoded `"claude-opus-4-6"` lie.

**No blockers.**

## Known Stubs

None. All additions are concrete documentation/contract — no placeholders, mock values, or TODO markers. The plan's three files are fully wired and testable; the only "stubs" in the system are the intentional honest-null provenance values (`model_used: null` / `cost_usd: null` when flags/env not provided), which are documented design per D-07/D-08 and not stubs.

## Self-Check

**Files verified on disk:**
- FOUND: agents/extractor.md (Required-Fields block line 52, HOW block line 58, Write-tool ban line 74, CRITICAL line 76, Rules section line 101; no /scripts/build_extraction.py references; two /core/build_extraction.py occurrences)
- FOUND: commands/ingest.md (--fail-threshold line 16, Provenance threading line 56, Step 3.5 line 71, Step 7 Normalization pass-rate line 109)
- FOUND: tests/test_unit.py (test_extractor_prompt_required_fields + test_extractor_prompt_stdin_fallback functions in Phase 13 — FIDL-02a section)
- FOUND: .planning/phases/13-extraction-pipeline-reliability/13-03-SUMMARY.md (this file)

**Commits verified:**
- FOUND: d4c2c99 feat(13-03): enforce extraction contract in extractor agent prompt
- FOUND: adf4b6c feat(13-03): wire Step 3.5 normalization + --fail-threshold + provenance threading
- FOUND: 92bc09e test(13-03): add UT-017 + UT-018 to lock extractor.md contract

**Test suite verified:**
- PASS: tests/test_unit.py::test_extractor_prompt_required_fields (UT-017)
- PASS: tests/test_unit.py::test_extractor_prompt_stdin_fallback (UT-018)
- PASS: 16 Phase 13 tests (UT-012 + UT-019..UT-030 + UT-017/018 + UT-022a/b) — no regressions

**Acceptance criteria verified:**
- Agent prompt audit: REQUIRED top-level fields = 1, /scripts/build_extraction = 0, /core/build_extraction = 2, HOW to write extractions = 1, DO NOT fall back to the Write tool = 1, stdin pipe >= 1, silently drops >= 1, duplicate stdin fence = 0
- Ingest command audit: Step 3.5 = 1, --fail-threshold = 4 (>= 3), default: 0.95 = 1, range: [0.0, 1.0] = 1, EPISTRACT_MODEL = 2 (>= 1), --model = 2 (>= 2), belt + suspenders = 1, MUST run AFTER = 1, Normalization pass-rate = 1, _normalization_report.json = 2 (>= 1)
- Unit test functions: test_extractor_prompt_required_fields = 1, test_extractor_prompt_stdin_fallback = 1

## Self-Check: PASSED

---
*Phase: 13-extraction-pipeline-reliability*
*Completed: 2026-04-17*
