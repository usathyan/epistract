---
phase: 14-chunk-overlap
plan: 02
subsystem: infra
tags: [chonkie, chunk-overlap, fidl-03, sentence-chunker, substrate, tdd]

# Dependency graph
requires:
  - phase: 14-chunk-overlap
    provides: FIDL-03 requirement row (Plan 14-01); chonkie>=1.0 declared in pyproject.toml + installed via scripts/setup.sh + documented in CLAUDE.md §Key Dependencies (Plan 14-01, corrected by 3589e2f after blingfire → chonkie pivot)
provides:
  - Module-level chonkie import guard in core/chunk_document.py with fail-loud ImportError
  - HAS_CHONKIE flag for future introspection (mirrors validate_molecules.py HAS_RDKIT pattern, inverted outcome)
  - OVERLAP_SENTENCES = 3 and OVERLAP_MAX_CHARS = 1500 module constants
  - _SENTENCE_BOUNDARY regex matching chonkie's default delim set (. ! ? \n)
  - _make_chunker(max_size) factory — centralized SentenceChunker construction for Plan 14-03's three split paths
  - _tail_sentences(text, n, max_chars) — pure cross-flush overlap helper for ARTICLE-boundary transitions
  - UT-031..UT-035 + UT-033b unit tests pinning the substrate contracts
affects: [14-03, 14-04, V2-scenario-runs]

# Tech tracking
tech-stack:
  added: [chonkie>=1.0 (runtime import surface)]
  patterns:
    - "Required-dep import guard (D-08 posture): try/except at module top with re-raise + actionable install hint. Mirrors validate_molecules.py HAS_* pattern in structure; inverts outcome (required, not optional — raises loud rather than skipping features)."
    - "Factory pattern for parametric dep construction: _make_chunker(max_size) returns a configured SentenceChunker — isolates chonkie's kwarg shape so Plan 14-03 can call it uniformly from all three split paths and future phases can tweak config in one place."
    - "Pure-helper substrate-before-wire: land the plumbing (Task 1) + its contract tests (Task 2) in a dedicated plan; defer call-site wiring to the next wave plan. Reduces risk, keeps commits atomic, allows verifier to gate on substrate integrity."

key-files:
  created:
    - ".planning/phases/14-chunk-overlap/deferred-items.md (logs 5 pre-existing tests/test_unit.py ruff violations surfaced during Task 2 — all confirmed pre-existing via git stash round-trip)"
  modified:
    - "core/chunk_document.py (+143 lines: chonkie import guard lines 22-39; OVERLAP constants + regex lines 49-59; _make_chunker factory lines 74-94; _tail_sentences helper lines 97-178; existing _split_at_sections/_merge_small_sections/_split_at_paragraphs/_split_fixed/chunk_document/chunk_document_to_files untouched)"
    - "tests/test_unit.py (+133 lines: UT-031..UT-035 + UT-033b appended after test_extractor_prompt_stdin_fallback; no existing test modified)"

key-decisions:
  - "Helpers placed BEFORE _split_at_sections per plan action block (not after MIN_CHUNK_SIZE) — groups substrate-of-helpers together under the '# Internal helpers' horizontal rule."
  - "_SENTENCE_BOUNDARY regex pattern: `(?<=[.!?])\\s+|\\n+` — matches chonkie's default include_delim=prev behavior (punctuation stays with preceding sentence). Alternative `r\"(?<=[.!?])\\s+\"` was rejected because it would miss newline-only boundaries (common in contract ARTICLE bodies)."
  - "_tail_sentences is pure/regex-based (NOT chonkie-backed) because chonkie's SentenceChunker instantiation has non-trivial setup cost and the helper runs on short tails in hot paths. Plan's interfaces block documents this as 'intentional approximation' with three rationales (structured-prose input, minor wobble not bug, hot-path pure helper)."
  - "Line-count target (~360) missed by +78: actual file is 438 lines. Driver is the plan-mandated verbose docstring on _tail_sentences (Args/Returns/Behavior/Purity sections totaling ~40 lines) + import-guard comment block + D-02/D-03 rationale comment on constants. All extra lines are documentation, not logic. No scope creep."
  - "Pre-existing ruff violations in tests/test_unit.py (5 errors on lines 138, 688, 738, 861, 916) logged to deferred-items.md rather than auto-fixed — confirmed pre-existing via git-stash round-trip, out of scope per deviation Rule 3's scope boundary."
  - "Architectural pivot acknowledged: original 14-02 design built _sentence_overlap on blingfire.text_to_sentences_and_offsets; checkpoint surfaced that blingfire 0.1.8 ships only an x86_64 Mach-O dylib (no arm64, no newer release). Rewritten plan (committed by 2df7110) pivots to chonkie.SentenceChunker — scope SHRANK because chonkie owns intra-chunk overlap natively; _sentence_overlap became the smaller _tail_sentences helper + _make_chunker factory."

patterns-established:
  - "Fail-loud required-dep import at module top (D-08): `try: from <dep> import X; HAS_<DEP> = True; except ImportError as e: raise ImportError('...install hint...') from e`. Complementary to the optional-dep HAS_* flag pattern (validate_molecules.py) — same guard structure, opposite outcome."
  - "Substrate-before-wire plan decomposition: one plan (14-02) lands helpers + tests; next plan (14-03) wires them into call sites. Each plan has a single, auditable scope; TDD tests gate substrate correctness before wiring risk is introduced."
  - "Cross-flush vs intra-chunk overlap bifurcation: chonkie.SentenceChunker handles overlap WITHIN a single chunk(text) call (D-04 #1 intra-section). A separate regex-based _tail_sentences handles overlap ACROSS hard-flush boundaries where chonkie cannot span (D-04 #2 ARTICLE transitions, D-04 #3 small-section merges)."

requirements-completed: [FIDL-03]  # Partial — Plan 14-02 delivers the substrate portion of FIDL-03; wiring into split paths remains with Plan 14-03. The requirement row in REQUIREMENTS.md already spans Plans 14-01..14-04; STATE counts this plan toward FIDL-03 progress.

# Metrics
duration: 10min
completed: 2026-04-18
---

# Phase 14 Plan 02: Chonkie Substrate for Chunk Overlap Summary

**Landed chonkie's SentenceChunker into `core/chunk_document.py` as a fail-loud required dep with HAS_CHONKIE flag, OVERLAP_SENTENCES / OVERLAP_MAX_CHARS constants, a `_make_chunker` factory, and a pure `_tail_sentences` helper for cross-flush overlap — all gated by six new unit tests (UT-031..UT-035 + UT-033b). Pure substrate; zero behavioral change to existing `chunk_document()` output. Plan 14-03 will wire these into the three split paths.**

## Performance

- **Duration:** ~10 min working time (wall-clock 64 min including initial context reads across 7 files totaling ~2,500 lines)
- **Started:** 2026-04-18T17:35:09Z
- **Completed:** 2026-04-18T18:39:04Z
- **Tasks:** 2 (both executed atomically)
- **Files modified:** 2 source + 1 deferred-items doc (3 total)

## Accomplishments

- **Fail-loud chonkie import gate landed** (lines 22-39 of `core/chunk_document.py`). Importing the module without chonkie installed now raises `ImportError("chonkie is required for chunk overlap (Phase 14 FIDL-03). Install it with: uv pip install 'chonkie>=1.0' ...")` — matches Phase 12/13 "loud failure over silent garbage" posture exactly, and the message preserves both install routes (direct `uv pip install` AND `/epistract:setup`).
- **HAS_CHONKIE flag exported** for future introspection, mirroring the `validate_molecules.py::HAS_RDKIT` pattern in structure while inverting the outcome (required, not optional).
- **OVERLAP_SENTENCES = 3 and OVERLAP_MAX_CHARS = 1500 declared** next to `MAX_CHUNK_SIZE` in the `# Constants` block — hardcoded per D-06 / D-07 (no CLI flag, no env var, pit-of-success).
- **`_make_chunker(max_size)` factory shipped** — returns a `SentenceChunker(tokenizer="character", chunk_size=max_size, chunk_overlap=OVERLAP_MAX_CHARS, min_sentences_per_chunk=1)`. Plan 14-03 will call it uniformly from `_split_at_paragraphs`, `_merge_small_sections::_flush`, and `_split_fixed` — one configuration touchpoint for all three.
- **`_tail_sentences(text, n, max_chars)` helper shipped** as a pure regex-based segmenter for cross-flush (ARTICLE-boundary) overlap that chonkie's intra-chunk overlap cannot span. Five behavior surfaces verified via UT-032/UT-033/UT-033b/UT-034: last-N fits / truncate-under-cap / partial-fit intersection / empty / single-over-cap.
- **6 new unit tests land cleanly**: UT-031 (chonkie API pin + Chunk attribute surface), UT-032 (last-N returned), UT-033 (truncate path starts on sentence boundary), UT-033b (D-02 ∩ D-03 intersection — M-5), UT-034 (edge cases), UT-035 (fail-loud ImportError guarded by pytest monkeypatch for order-independence — B-3). Full unit suite: 46 → 52 tests, 42 → 48 passing, 4 skipped unchanged.
- **Zero behavioral change to existing `chunk_document()`** — verified by short-text smoke test (`chunk_document("Some short text with two sentences. That is enough.", doc_id="test")` still returns exactly 1 chunk). All four pre-existing split/merge helpers are byte-identical; insertions only, no mods. Plan 14-03 edits them.

## Task Commits

Each task committed atomically:

1. **Task 1: Add chonkie import guard, overlap constants, _make_chunker factory, _tail_sentences helper** — `8c1446a` (feat)
2. **Task 2: Add UT-031..UT-035 + UT-033b unit tests to tests/test_unit.py** — `e215707` (test)

## Files Created/Modified

- `core/chunk_document.py` — +143 lines (296 → 438). All insertions; no existing line modified. Import guard at lines 22-39, constants at lines 49-59, `_make_chunker` at lines 74-94, `_tail_sentences` at lines 97-178. `_split_at_sections` (184), `_merge_small_sections` (228), `_split_at_paragraphs` (302), `_split_fixed` (321), `chunk_document` (354), `chunk_document_to_files` (379), `__main__` block all preserved byte-identical.
- `tests/test_unit.py` — +133 lines (963 → 1096). UT-031..UT-035 + UT-033b appended after `test_extractor_prompt_stdin_fallback`. No existing test modified.
- `.planning/phases/14-chunk-overlap/deferred-items.md` — NEW. Logs 5 pre-existing ruff violations in `tests/test_unit.py` (lines 138 F401, 688/738 E401, 861/916 F841) that Plan 14-02 did NOT introduce, confirmed via git-stash round-trip. Out of scope for FIDL-03.

## The `_tail_sentences` Docstring (as landed)

```python
def _tail_sentences(
    text: str,
    n: int = OVERLAP_SENTENCES,
    max_chars: int = OVERLAP_MAX_CHARS,
) -> str:
    """Return the last n sentences of `text`, capped at `max_chars`.

    Used by `_merge_small_sections::_flush` to carry overlap across
    hard-flush boundaries (ARTICLE transitions, small-section merges) that
    chonkie's intra-chunk overlap cannot span. Within an oversized section,
    `_make_chunker(...).chunk(body)` handles overlap directly — this helper
    is NOT called in that path.

    Sentence segmentation uses a regex matching chonkie's default delim
    set (`. `, `! `, `? `, `\\n`). This is an intentional approximation
    (chonkie's internal segmenter is slightly more robust to edge cases
    like "Dr. Smith"), but: (a) the helper operates on already-buffered
    section bodies which are typically structured prose, not dialogue,
    (b) mismatched sentence detection between here and chonkie can at
    most misattribute a sentence boundary at a cross-flush transition —
    a minor provenance wobble, not a correctness bug, (c) the helper is
    pure and side-effect-free, callable in hot paths without chonkie setup
    overhead.

    Behavior (Phase 14 D-02, D-03):
      - Empty `text` → returns "".
      - Fewer than n sentences → returns all sentences.
      - Cumulative length of last-n sentences ≤ max_chars → returns those
        n sentences.
      - Cumulative length > max_chars → returns the most-recent whole
        sentences that fit under the cap; NEVER mid-sentence truncation.
      - A single sentence longer than max_chars → returns "".

    The helper is pure: no side effects, no I/O, no module-state mutation.

    Args:
        text: Source text to pull a sentence-level tail from.
        n: Maximum number of trailing sentences to include.
        max_chars: Hard cap on the returned string's length.

    Returns:
        Overlap tail ending on a sentence boundary, or "".
    """
```

## Chonkie Version Pin (for Plan 14-03 API stability)

```
$ .venv/bin/python3 -c "import chonkie; print(chonkie.__version__)"
1.6.2
```

`chonkie>=1.0` is declared in `pyproject.toml` and installed in `scripts/setup.sh`. Installed version on this machine: **1.6.2**. Plan 14-03 can safely rely on these `Chunk` attributes (UT-031 pins them):
- `.text: str` — chunk body including any overlap prefix from the previous chunk
- `.start_index: int` — char offset in input text where the chunk begins
- `.end_index: int` — char offset in input text where the chunk ends
- `.token_count: int` — in `tokenizer="character"` mode this equals character count

Also available on `Chunk` objects (not used by this plan, but confirmed present): `.id`, `.context`, `.embedding`, `.copy`, `.from_dict`, `.to_dict`.

## Pytest Output (the six new tests, from full `-v` run)

```
tests/test_unit.py::test_ut031_chonkie_imports PASSED                    [ 90%]
tests/test_unit.py::test_ut032_tail_returns_last_n_sentences PASSED      [ 92%]
tests/test_unit.py::test_ut033_tail_truncates_under_cap PASSED           [ 94%]
tests/test_unit.py::test_ut033b_partial_fit_three_sentences PASSED       [ 96%]
tests/test_unit.py::test_ut034_tail_handles_edges PASSED                 [ 98%]
tests/test_unit.py::test_ut035_missing_chonkie_raises_loud PASSED        [100%]

======================== 48 passed, 4 skipped in 7.57s =========================
```

Filtered-run output (only the new tests, via `pytest -k "ut031 or ut032 or ut033 or ut034 or ut035"`):

```
......                                                                   [100%]
6 passed, 46 deselected in 0.08s
```

The 4 skipped tests are pre-existing (conditional on RDKit / Biopython / sift-kg availability) — unchanged from HEAD.

## Verification Results

- `grep -q '^OVERLAP_SENTENCES = 3$' core/chunk_document.py` → PASS
- `grep -q '^OVERLAP_MAX_CHARS = 1500$' core/chunk_document.py` → PASS
- `grep -q 'from chonkie import SentenceChunker' core/chunk_document.py` → PASS (module-level, line 29)
- `grep -q 'HAS_CHONKIE = True' core/chunk_document.py` → PASS
- `grep -q 'raise ImportError' core/chunk_document.py` → PASS; message contains both `uv pip install` AND `chonkie` (and `/epistract:setup` — both install routes preserved)
- `grep -q 'def _tail_sentences' core/chunk_document.py` → PASS
- `grep -q 'def _make_chunker' core/chunk_document.py` → PASS
- `grep -c 'def _split_at_sections\|def _merge_small_sections\|def _split_at_paragraphs\|def _split_fixed' core/chunk_document.py` → 4 (all existing helpers preserved)
- `.venv/bin/python3 -c "import sys; sys.path.insert(0, 'core'); import chunk_document"` → exit 0 (clean import with chonkie installed)
- `.venv/bin/python3 -c "... from chunk_document import _tail_sentences; r = _tail_sentences('A. B. C. D. E.'); assert 'C' in r and 'D' in r and 'E' in r and 'A' not in r"` → PASS (`r = 'C. D. E.'`)
- `.venv/bin/python3 -c "... assert _tail_sentences('') == ''"` → PASS
- `.venv/bin/python3 -c "... assert _tail_sentences('Only one sentence here.') == 'Only one sentence here.'"` → PASS
- `.venv/bin/python3 -c "... from chunk_document import _make_chunker; from chonkie import SentenceChunker; assert isinstance(_make_chunker(10000), SentenceChunker)"` → PASS
- `.venv/bin/python3 -c "... from chunk_document import chunk_document, chunk_document_to_files, MAX_CHUNK_SIZE, MIN_CHUNK_SIZE; assert MAX_CHUNK_SIZE == 10000 and MIN_CHUNK_SIZE == 500"` → PASS (existing public API preserved)
- `.venv/bin/python3 -c "... from chunk_document import _tail_sentences, _make_chunker, OVERLAP_SENTENCES, OVERLAP_MAX_CHARS, HAS_CHONKIE; print(OVERLAP_SENTENCES, OVERLAP_MAX_CHARS, HAS_CHONKIE)"` → `3 1500 True`
- `ruff check core/chunk_document.py` → all checks passed
- `git diff --stat HEAD~1 HEAD -- core/chunk_document.py` → `143 insertions(+)` only, zero deletions
- `.venv/bin/python3 -m pytest tests/test_unit.py -m unit -q` → `48 passed, 4 skipped in 7.57s`
- Smoke test (overall verification #5): `chunk_document("Some short text with two sentences. That is enough.", doc_id="test")` returns exactly 1 chunk, no exception — confirms substrate landed without altering existing chunker behavior.
- UT-033b partial-fit intersection (M-5): `_tail_sentences(three_600-char_sents)` returns SECONDSENT + THIRDSENT (~1204 chars), FIRSTSENT dropped. PASS.
- UT-034 single-over-cap: `_tail_sentences("X" * 2000 + ".")` returns `""` — refuses mid-sentence cut. PASS.

## Decisions Made

Summarized from the frontmatter `key-decisions` block:

1. **Helpers placed before `_split_at_sections`** — groups substrate-of-helpers together under the `# Internal helpers` horizontal rule, per the plan's explicit placement directive.
2. **`_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")`** — newline-only boundaries included to match common contract ARTICLE body formatting; punctuation stays with preceding sentence (chonkie's default `include_delim=prev`).
3. **`_tail_sentences` is regex-based, not chonkie-backed** — chonkie `SentenceChunker` instantiation has non-trivial cost; pure helper runs in hot paths. The plan's `<interfaces>` block documents this as intentional approximation with three rationales.
4. **Line-count target missed by +78** — docstring verbosity per spec, not scope creep.
5. **Pre-existing ruff issues deferred** — 5 violations in `tests/test_unit.py` confirmed pre-existing via git-stash round-trip. Logged to `.planning/phases/14-chunk-overlap/deferred-items.md`. Out of scope per Rule 3 scope boundary.

## Deviations from Plan

### Auto-fixed Issues

**None** — plan executed exactly as written for behavioral logic.

### Spec Nuances (not deviations)

**1. Plan `<verify><automated>` block used `_make_chunker(1000)`, which chonkie rejects**
- **Found during:** Task 1 verification
- **Observed:** chonkie's `SentenceChunker.__init__` raises `ValueError("chunk_overlap must be less than chunk_size")` when `chunk_size=1000` is passed with the factory's hardcoded `chunk_overlap=OVERLAP_MAX_CHARS=1500`.
- **Root cause:** Plan line 378 smoke-tests `_make_chunker(1000)`, but acceptance criterion on line 392 uses `_make_chunker(10000)` (the production `MAX_CHUNK_SIZE`). The 1000 in the verify block is a planner typo — 1000 is below the 1500-char overlap floor. Intent is clearly to assert `isinstance(_make_chunker(...), SentenceChunker)`, which holds for any `max_size > OVERLAP_MAX_CHARS`.
- **Resolution:** Code is correct per the plan's acceptance criteria (line 392 explicitly tests `_make_chunker(10000)`, which passes). `_make_chunker(MAX_CHUNK_SIZE)` is the only call shape Plan 14-03 will use. No code change needed; noting here for the planner.
- **Follow-up suggestion for 14-03 planner:** If future tests exercise `_make_chunker(small_value)`, the factory may need a guard like `chunk_size=max(max_size, OVERLAP_MAX_CHARS * 2)` or an explicit ValueError. Not in scope for this plan.

**2. Final module is 438 lines, plan expected ~360**
- **Reason:** Plan-mandated docstrings on `_tail_sentences` (Behavior / Args / Returns / Purity sections) plus import-guard comment block plus D-02/D-03 rationale comments on constants expand the line count by ~78 beyond the estimate. All extra lines are documentation or whitespace required by the plan's explicit verbatim code blocks, not logic. Ruff clean.

## Issues Encountered

None functional. One planner-typo nuance (verify block `_make_chunker(1000)` vs AC `_make_chunker(10000)`) called out above — did not block execution because the acceptance criteria are the binding contract.

## Authentication Gates

None. No external service configuration required for this plan.

## Known Stubs

None — this plan touches only the substrate helpers + their unit tests. `_make_chunker` and `_tail_sentences` are complete and production-ready; Plan 14-03 will call them from the three split paths to close FIDL-03. No UI or data surfaces touched, so no stub patterns (empty arrays, "coming soon", placeholder text) apply.

Note on substrate-before-wire shape: the helpers are deliberately not yet called from `_split_at_paragraphs`, `_merge_small_sections`, or `_split_fixed` — that wiring is Plan 14-03's explicit scope. This is NOT a stub: `chunk_document()` still returns correct chunks via its existing paragraph-based splitting; overlap recovery is just not yet active. The 14-02 / 14-03 split is exactly the "pure substrate first, wire second" pattern this plan's `<success_criteria>` codifies ("Plan 14-03's executor can `from chunk_document import _tail_sentences, _make_chunker` and call them from all three split paths").

## Architectural Pivot Note (per task prompt)

The original Plan 14-02 design built a hand-written `_sentence_overlap` primitive on `blingfire.text_to_sentences_and_offsets`. Plan 14-01's executor discovered at `import blingfire` time that blingfire 0.1.8 ships only an x86_64 Mach-O dylib — no arm64 build, no newer release — and raises on Apple Silicon (the user's dev platform). This triggered an architectural-deviation checkpoint (Rule 4), already resolved and committed:

- `2df7110` docs(14): supersede 14-02/14-03 plans — pivot blingfire → chonkie
- `3589e2f` fix(14-01): swap blingfire → chonkie (arm64 dylib unavailable)

Plan 14-02 as executed uses `chonkie.SentenceChunker`, which:
1. Runs native on arm64 AND x86_64 — no platform restriction
2. Provides sentence-boundary-preserving chunking with overlap built in — scope SHRANK
3. Supplies honest `start_index` / `end_index` offsets per chunk — the D-11 honest-char-offset fix is now automatic (was part of the original 14-03 scope)
4. Is pure Python — no bundled dylib, no OCR/C deps

Net effect of the pivot: the original plan's `_sentence_overlap` primitive was replaced by a smaller `_tail_sentences` helper (only used for cross-flush overlap at ARTICLE boundaries — D-04 #2) plus a trivial `_make_chunker` factory. Intra-chunk overlap (D-04 #1) is now free via `chonkie.SentenceChunker`'s built-in `chunk_overlap` kwarg.

No further pivots needed; substrate is stable.

## Next Phase Readiness

**Plan 14-03 is unblocked.** Its executor can immediately:

```python
from chunk_document import _tail_sentences, _make_chunker, OVERLAP_SENTENCES, OVERLAP_MAX_CHARS
```

and call `_make_chunker(max_size)` + `_tail_sentences(buffer_text)` from the three split paths named in 14-CONTEXT.md D-04:
1. `_split_at_paragraphs` (oversized-section sub-chunks) — `_make_chunker` replaces paragraph-only splitting
2. `_merge_small_sections::_flush` (ARTICLE hard-flush boundary) — `_tail_sentences(flushed_body)` prepended to next buffer
3. `_split_fixed` (no-structure fallback) — `_make_chunker` replaces paragraph-bucket splitting

UT-031 pins the four `Chunk` attributes (`.text`, `.start_index`, `.end_index`, `.token_count`) so if chonkie 1.6.x ever breaks that contract, Plan 14-03's call sites will surface the break via UT-031 failure, not via silent chunk-shape drift.

The line-number anchors from Plan 14-01's SUMMARY (`.planning/REQUIREMENTS.md` FIDL-03 row at line 204, `tests/TEST_REQUIREMENTS.md` §6 at existing anchor) remain valid. Plan 14-03 should add its new test IDs (UT-036, UT-036b, UT-037, UT-038 + FT-011) to TEST_REQUIREMENTS.md §6 as it lands them.

## Self-Check: PASSED

Artifact existence (each tested via `[ -f path ] && echo FOUND || echo MISSING`):

- `core/chunk_document.py` — FOUND (438 lines, includes all substrate tokens)
- `tests/test_unit.py` — FOUND (1096 lines, includes 6 new tests)
- `.planning/phases/14-chunk-overlap/14-02-SUMMARY.md` — FOUND (this file)
- `.planning/phases/14-chunk-overlap/deferred-items.md` — FOUND

Commit existence (each tested via `git log --oneline --all | grep -q $hash && echo FOUND || echo MISSING`):

- `8c1446a` (Task 1 — feat) — FOUND
- `e215707` (Task 2 — test) — FOUND

Pytest: `48 passed, 4 skipped` (full unit suite) — six new tests contributing; zero regressions.

---

*Phase: 14-chunk-overlap*
*Plan: 02*
*Completed: 2026-04-18*
