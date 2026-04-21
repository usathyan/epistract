---
phase: 16-wizard-sample-window-beyond-8kb
plan: 02
subsystem: domain-wizard
tags: [wizard, schema-discovery, acceptance-fixture, tiktoken, FIDL-05]
dependency_graph:
  requires:
    - "Plan 16-01: core.domain_wizard._build_excerpts + constants + conditional build_schema_discovery_prompt landed"
    - "Plan 16-01: docs/known-limitations.md Domain Wizard section (with <TOKEN_COUNT_PLACEHOLDER>)"
    - "Plan 16-01: UT-042 GREEN, UT-043 RED (fixture-dependent)"
    - "Phase-8 wizard fixtures: tests/fixtures/wizard/sample_lease_{1,2,3}.txt"
  provides:
    - "tests/fixtures/wizard_sample_window/long_contract.txt: deterministic 60200-char ASCII fixture with head/middle/tail sentinels"
    - "UT-043 (test_multi_excerpt_prompt_contains_markers) GREEN — RED→GREEN handoff from Plan 16-01"
    - "FT-016 (test_ft016_long_doc_captures_all_three_sentinels) — prompt-level sentinel coverage e2e"
    - "FT-017 (test_ft017_short_doc_prompt_is_strict_superset_of_pre_phase16) — D-12 strict-superset regression gate"
    - "docs/known-limitations.md: concrete measured input-token count (2631 tokens, tiktoken cl100k_base, 2026-04-21) replacing placeholder"
  affects:
    - "Phase-16 wrap-up will flip FIDL-05 row from Pending to Complete and amend plan list to `16-01, 16-02`"
    - "Phase 20 README Pipeline Capacity section now has a concrete input-token figure to quote"
tech_stack:
  added: []
  patterns:
    - "Phase 14 deterministic synthetic fixture precedent (tests/fixtures/<phase>/*.txt, hard invariants enforced at generation)"
    - "Phase 15 FT-013..FT-015 test naming + traceability-matrix row pattern"
    - "Measurement-only optional dependency pattern (tiktoken) with len/4 fallback, no pyproject.toml change (D-09)"
    - "Strict-superset regression gate pattern (assert old structural substrings present AND no new-feature leakage into old path)"
key_files:
  created:
    - tests/fixtures/wizard_sample_window/long_contract.txt
  modified:
    - tests/test_unit.py
    - tests/TEST_REQUIREMENTS.md
    - docs/known-limitations.md
    - .planning/phases/16-wizard-sample-window-beyond-8kb/deferred-items.md
decisions:
  - "TOTAL_LEN = 60200 chosen for clean slice arithmetic: len//2 == 30100, middle slice [28100, 32100), tail slice [56200, 60200). FT-016's exact-literal marker assertions depend on this."
  - "Token measurement one-shot: tiktoken cl100k_base ran locally and yielded 2631 tokens. No measurement script committed — the integer in docs/known-limitations.md is the final artifact (D-09)."
  - "Soft-budget headroom revised 5× → 9×: the pre-Phase-16 `~5×` estimate was a design-time guess; measured headroom is 24000 // 2631 = 9×."
  - "Pre-existing ruff format/lint drift in tests/test_unit.py remains deferred (matches Plan 16-01 deferred-items.md decision). New FT-016/FT-017 code follows Plan 16-01's `assert cond, (msg)` convention — no new lint errors introduced by Phase 16."
metrics:
  duration: ~15min
  completed: 2026-04-21
  commits: 3
  tasks: 3
  files_touched: 4
---

# Phase 16 Plan 02: Wizard Sample Window Beyond 8KB — Acceptance, Regression & Token Measurement Summary

One-liner: Created the deterministic 60,200-char synthetic `long_contract.txt` fixture with three sentinel phrases at head/middle/tail regions, added FT-016 (e2e sentinel coverage) and FT-017 (D-12 short-doc strict-superset regression) to `tests/test_unit.py`, and replaced the `<TOKEN_COUNT_PLACEHOLDER>` in `docs/known-limitations.md` with the measured 2,631 input-token count via `tiktoken cl100k_base` — flipping Plan 16-01's RED UT-043 to GREEN and closing all FIDL-05 acceptance/regression/documentation gates.

## What Changed

1. **Synthetic 60,200-char fixture** (`857a07c`)
   - `tests/fixtures/wizard_sample_window/long_contract.txt` — deterministic ASCII-only contract generated to exact length 60,200 chars.
   - `PARTY_SENTINEL_HEAD` at char 111 (head slice `[0, 4000)`).
   - `OBLIGATION_SENTINEL_MIDDLE` at char 28,111 (middle slice `[28100, 32100)`).
   - `TERMINATION_SENTINEL_TAIL` at char 56,211 (tail slice `[56200, 60200)`).
   - Hard invariants enforced at generation time: exact length 60,200; sentinel count == 1 per sentinel; sentinel position falls within the expected `_build_excerpts` slice; pure ASCII (`all(ord(c) < 128 for c in payload)`).
   - Plan 16-01's UT-043 `test_multi_excerpt_prompt_contains_markers` flips RED → GREEN on fixture creation (handoff completed).

2. **FT-016 sentinel coverage + FT-017 strict-superset regression** (`5fa5fec`)
   - `tests/test_unit.py::test_ft016_long_doc_captures_all_three_sentinels` — reads the fixture, calls `build_schema_discovery_prompt(fixture_text, "Synthetic long contract domain for Phase 16 FT-016")`, asserts exactly 1 occurrence of each sentinel + the exact literal markers `[EXCERPT 1/3 — chars 0 to 4000 (head)]`, `[EXCERPT 2/3 — chars 28100 to 32100 (middle)]`, `[EXCERPT 3/3 — chars 56200 to 60200 (tail)]`, plus the plural `**Document excerpts:**` header and the preface, with the singular `**Document text:**` leak-check.
   - `tests/test_unit.py::test_ft017_short_doc_prompt_is_strict_superset_of_pre_phase16` — for each of `sample_lease_{1,2,3}.txt` (all ≤1.3K chars → short-doc branch), asserts the full `text` appears verbatim in the prompt, all 8 pre-Phase-16 structural substrings are preserved (task name, domain description interpolation, `**Document text:**`, instructions list, 5-15/5-20 count directive, SCREAMING_SNAKE_CASE, `Output format (JSON):`, `Return ONLY the JSON object, no commentary.`), and none of the long-doc markers (`[EXCERPT `, `three excerpts from a larger document`, `**Document excerpts:**`) leak into the short-doc path.
   - `tests/TEST_REQUIREMENTS.md` — FT-016 / FT-017 spec blocks + traceability-matrix rows appended after UT-043.
   - `.planning/phases/16-wizard-sample-window-beyond-8kb/deferred-items.md` — updated to record that Plan 16-02 preserves the Plan 16-01 scope-boundary decision on pre-existing ruff format drift.

3. **Concrete token-cost measurement** (`2701763`)
   - One-shot measurement of `build_schema_discovery_prompt(fixture_text, "Synthetic long contract domain for Phase 16 FT-016")` — rendered prompt is 13,498 chars; tiktoken cl100k_base encoding yields **2,631 input tokens**.
   - `docs/known-limitations.md` — replaced `<TOKEN_COUNT_PLACEHOLDER>` bullet with the concrete integer + method annotation `Method: tiktoken cl100k_base. Soft budget 24,000 tokens → headroom ≈ 9× the measured cost.`
   - Updated the downstream "Soft budget" bullet from the stale `~5×` design-time estimate to the measured `~9×` headroom.
   - Updated footer: `Last updated: 2026-04-21 — Phase 16 FIDL-05 (Wizard Sample Window) initial entry; token cost measured.`
   - tiktoken is NOT added to `pyproject.toml` — D-09 (measurement-only, `len(prompt) // 4` fallback preserved for environments without tiktoken).

## Reference Patterns Followed

- **Phase 14 deterministic synthetic fixture** — `tests/fixtures/phase14_boundary_straddle.txt` precedent: fixture generation uses a one-shot script whose invariants are enforced at build time (length, sentinel positions, pure ASCII). The fixture — not the generator — is committed. Same pattern applied for `long_contract.txt`.
- **Phase 15 FT-013..FT-015 naming/traceability** — `FT-016` / `FT-017` continue the FT-N sequence; each test gets a spec block in `tests/TEST_REQUIREMENTS.md §7 Phase 16 Tests` and a row in the `§4 Traceability Matrix`.
- **Phase 14 D-14 measurement-only-not-runtime pattern** — `sentence-transformers` was optional in Phase 14 for local semantic clustering; Phase 16 applies the same idea to `tiktoken` — measurement-only, fallback is explicit, no new runtime dep.
- **Phase 8 prompt-builder test layering** — `test_wizard_schema_discovery_prompt` (24-char input → short-doc branch) remains untouched; FT-017 adds the fixture-based regression layer on top rather than replacing the existing test. Both tests pass in the same run.

## FIDL-05 Status Progression

- **Before Plan 16-02:** `| FIDL-05 | Phase 16 | 16-01 | Pending |`. Acceptance tests UT-042 GREEN, UT-043 RED (fixture-dependent). `<TOKEN_COUNT_PLACEHOLDER>` present.
- **After Plan 16-02 (functionally complete):**
  - UT-042 GREEN, UT-043 GREEN, FT-016 GREEN, FT-017 GREEN, `test_wizard_schema_discovery_prompt` GREEN — all in the same pytest run.
  - Placeholder replaced with measured 2,631-token integer.
  - Regression gate (FT-017) proves no Phase-8 caller loses content or structural cues on the short-doc path.
- **Phase-level wrap-up (NOT done in this plan):** flip REQUIREMENTS.md row to `| FIDL-05 | Phase 16 | 16-01, 16-02 | Complete |` and mark the `- [ ] **FIDL-05**` checkbox `- [x]` in `§v3`. Deliberately deferred to phase-wrap-up per 16-02-PLAN.md success criterion #8.

## Non-Obvious Decisions

1. **60,200 chars, not 60,000.** `TOTAL_LEN = 60200` was chosen so `len // 2 == 30100` (even midpoint, no fractional slice math) and `tail_start = 56200` lands cleanly on a 200-char offset. FT-016's marker-literal assertions — `[EXCERPT 2/3 — chars 28100 to 32100 (middle)]` and `[EXCERPT 3/3 — chars 56200 to 60200 (tail)]` — are exact-match and would fail for any other total length.

2. **Sentinels are not exactly at char 0 / char mid / char end.** They're positioned *inside* their respective slices (char 111 for head, 28,111 for middle, 56,211 for tail) with prose-style padding on both sides. This models a real document where the sentinel phrase appears in context, not as a magic marker at the first or last byte.

3. **FT-017's 8 structural substrings deliberately include `**Document text:**`.** That substring is the signal that the short-doc branch is active. Its presence in the short-doc prompt and absence in the long-doc prompt is the cleanest way to verify branch dispatch without reproducing the entire prompt template in the test.

4. **tiktoken cl100k_base returned 2,631 tokens — lower than the pre-measurement estimate of ~4,500.** Plan 16-01's design-time estimate assumed denser prose; the synthetic fixture's padding uses highly repetitive Lorem-ipsum-esque boilerplate, which the cl100k_base BPE collapses efficiently. The measured value is still representative of "long fixture Pass-1 cost in this project's prompt shape"; real-world natural-language corpora will likely measure 3K-5K tokens.

5. **Pre-existing ruff format drift preserved, not auto-fixed.** `ruff format --check tests/test_unit.py` wants to reformat ~40 sites, all in code predating Phase 16 (including Plan 16-01's UT-042/UT-043 block, which shipped with the same `assert cond, (msg)` style). Auto-fixing would inflate the Phase 16 diff across 1,200+ unrelated lines. Decision: document in `deferred-items.md` (same call Plan 16-01 made) and log as an Observation below.

## Deviations from Plan

### Auto-fixed Issues

None — no bugs encountered during execution.

### Architectural Decisions

None — no Rule 4 escalations.

### Observations

- **Soft-budget headroom revised 5× → 9× based on measurement.** The Plan 16-01 `docs/known-limitations.md` bullet said "Headroom: ~5× the measured value." After measurement yielded 2,631 tokens (not the ~4,500 design estimate), I updated the "Soft budget" bullet to reflect the measured headroom (`24000 // 2631 = 9`). This is a content correctness adjustment, not a scope expansion — the bullet previously referenced "the measured value" and there was no concrete measurement; it now references the real number.
- **Pre-existing `ruff format --check tests/test_unit.py` failure is unchanged.** The plan's Task-2 acceptance criteria listed `ruff format --check tests/test_unit.py` exit 0. That criterion is failing on `main` (pre-Phase-16) and is explicitly scope-deferred per `deferred-items.md` (Plan 16-01's scope-boundary decision, carried forward). Phase 16 additions pass default `ruff check` cleanly and introduce no new lint errors.
- **Full-suite `pytest tests/test_unit.py` shows 9 pre-existing failures (chonkie import errors).** Verified via `git stash && pytest tests/test_unit.py` — the 9 failures are environment-level (`ModuleNotFoundError: chonkie`) and pre-date all Phase 16 work. Out of scope; not in Phase 16's dependency graph.

## Commits

| # | Commit  | Message                                                                                      |
| - | ------- | -------------------------------------------------------------------------------------------- |
| 1 | 857a07c | test(16-02): add synthetic 60200-char long_contract.txt fixture (FIDL-05 D-10)               |
| 2 | 5fa5fec | test(16-02): add FT-016 sentinel coverage + FT-017 strict-superset regression (FIDL-05)      |
| 3 | 2701763 | docs(16-02): record measured 2631 input tokens for Pass-1 prompt (FIDL-05 D-08, D-09)        |

## Test Status

| Test                                                                    | Status                                            |
| ----------------------------------------------------------------------- | ------------------------------------------------- |
| UT-042 `test_build_excerpts`                                            | GREEN (unchanged from Plan 16-01)                 |
| UT-043 `test_multi_excerpt_prompt_contains_markers`                     | GREEN (RED→GREEN via Task 1 fixture)              |
| FT-016 `test_ft016_long_doc_captures_all_three_sentinels`               | GREEN (new in Plan 16-02)                         |
| FT-017 `test_ft017_short_doc_prompt_is_strict_superset_of_pre_phase16`  | GREEN (new in Plan 16-02)                         |
| `test_wizard_schema_discovery_prompt` (Phase 8)                         | GREEN (unchanged; backward compat preserved)      |
| All 17 wizard + FIDL-05 tests (same pytest -k run)                      | 17/17 passed                                      |
| Chonkie-dependent tests (UT-031..UT-038)                                | 9 failed — pre-existing env issue, out of scope   |

## Acceptance vs Plan Success Criteria

| Criterion                                                                               | Status |
| --------------------------------------------------------------------------------------- | ------ |
| 1. FIDL-05 D-10: synthetic 60200-char fixture with 3 sentinels in correct slices        | MET    |
| 2. FIDL-05 D-11: prompt-level acceptance (UT-043 + FT-016) — no LLM calls               | MET    |
| 3. FIDL-05 D-12: strict-superset regression (FT-017) across 3 Phase-8 wizard fixtures   | MET    |
| 4. FIDL-05 D-08: soft budget 24K tokens documented with measured headroom               | MET    |
| 5. FIDL-05 D-09: tiktoken measurement-only, fallback allowed, method annotated          | MET    |
| 6. FIDL-05 D-14: known-limitations doc finalized (no placeholder)                       | MET    |
| 7. Plan-16-01 UT-043 unblocked (RED→GREEN)                                              | MET    |
| 8. Scope discipline: no core/domain_wizard.py changes; no pyproject.toml changes        | MET    |
| 9. FIDL-05 row at `| FIDL-05 | Phase 16 | 16-01 | Pending |` — flip deferred to wrap-up | MET    |

## Known Stubs

None. Plan 16-01's sole cross-plan placeholder (`<TOKEN_COUNT_PLACEHOLDER>`) is now replaced with the concrete measured integer. No new stubs introduced by Plan 16-02.

## Deferred / Out of Scope

- See `.planning/phases/16-wizard-sample-window-beyond-8kb/deferred-items.md` for pre-existing ruff format/lint drift in `tests/test_unit.py` (unchanged by Plan 16-02) and unrelated portions of `core/domain_wizard.py`.
- 9 chonkie-dependent tests (UT-031..UT-038) fail due to missing `chonkie` module in this environment — pre-existing, unrelated to Phase 16. Not touched.
- Phase-wrap-up step to flip FIDL-05 row to `Complete` and amend plan list to `16-01, 16-02` is deliberately deferred to phase-level wrap-up per 16-02-PLAN.md success criterion #8.

## Self-Check: PASSED

Verified files exist:
- `/Users/umeshbhatt/code/epistract/tests/fixtures/wizard_sample_window/long_contract.txt` — FOUND (60200 chars)
- `/Users/umeshbhatt/code/epistract/tests/test_unit.py` — modified (FT-016 + FT-017 added)
- `/Users/umeshbhatt/code/epistract/tests/TEST_REQUIREMENTS.md` — modified (FT-016 + FT-017 spec + traceability rows)
- `/Users/umeshbhatt/code/epistract/docs/known-limitations.md` — modified (2631-token measurement replaces placeholder)
- `/Users/umeshbhatt/code/epistract/.planning/phases/16-wizard-sample-window-beyond-8kb/deferred-items.md` — modified (Plan 16-02 update appended)

Verified commits exist in git history:
- 857a07c — FOUND
- 5fa5fec — FOUND
- 2701763 — FOUND
