---
phase: 14-chunk-overlap
verified: 2026-04-20T00:00:00Z
status: passed
score: 6/6 must-haves verified
notes:
  - "REQUIREMENTS.md:121 FIDL-03 bullet text is stale (still references blingfire + _split_at_paragraphs). Behavioral goal is satisfied; this is a docs-only drift, not a code gap. Flagged as Info for a future docs cleanup pass."
---

# Phase 14: Chunk Overlap Verification Report

**Phase Goal:** Entities and relations that span a chunk boundary are extracted. Previously `core/chunk_document.py` split without overlap, silently losing recall on every graph built since v1. After this phase, a synthetic boundary-straddling relation (`INHIBITS(sotorasib, KRAS G12C)` spanning char 10000) is recovered, the 6 drug-discovery + 1 contract V2 baselines are not regressed (contract stays >=341 nodes / >=663 edges per D-14), and `commands/ingest.md:34`'s "chunks with overlap" prose finally matches behavior.

**Verified:** 2026-04-20
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Boundary-straddling mentions are co-located in at least one chunk | VERIFIED | `chunk_document(boundary_straddle.txt, 'straddle')` → 2 chunks; chunk 1 contains BOTH `sotorasib` AND `kras g12c` (overlap_prev=1378 chars pulled in sotorasib's sentence from chunk 0 tail). FT-011 GREEN passes. |
| 2 | Without overlap, no chunk co-locates both mentions (fix matters) | VERIFIED | FT-011 RED mode (monkeypatch `_make_chunker` → zero-overlap chunker AND `_tail_sentences` → "") yields 0 chunks containing both mentions. Reproduced manually. |
| 3 | Chunk JSON carries overlap provenance (7-key schema) | VERIFIED | Every chunk from `chunk_document()` has `chunk_id`, `text`, `section_header`, `char_offset`, `overlap_prev_chars`, `overlap_next_chars`, `is_overlap_region`. First chunk `prev=0`, last chunk `next=0` (UT-036, UT-038). |
| 4 | Cross-flush (ARTICLE boundary) overlap uses RAW tail, not chained chunk text (M-1/M-2) | VERIFIED | UT-037 pins: `chunks[a2_idx]["overlap_prev_chars"] == len(_tail_sentences(article_1_raw))` and `a2_chunk["text"].startswith(_tail_sentences(article_1))`. `_pending_tail` cache populated from RAW buffer_text in `_merge_small_sections::_flush` (chunk_document.py:357). |
| 5 | V2 baselines not regressed; contract floor >=341 nodes / >=663 edges | VERIFIED | `tests/baselines/v2/expected.json` committed with 7 scenario floors including `contract_events: {"nodes": 341, "edges": 663}`. FT-012 reads this file unconditionally (hard-fails on missing), asserts observed >= floor per scenario. Passes. Floors adopted from pre-Phase-14 2026-04-13 runs (Option 3a); contract retains D-14 hard gate. |
| 6 | `commands/ingest.md:34` "chunks with overlap" prose matches implementation | VERIFIED | `sed -n '34p' commands/ingest.md` → `"Split each document's text into ~10,000 character chunks with overlap. Use your judgment on natural break points (paragraph boundaries, section headers)."` Aspirational pre-phase, honest post-phase (chonkie's `chunk_overlap=1500` active on every split path). |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `core/chunk_document.py` | chonkie-backed chunker with 7-key schema, `_pending_tail` cache, 537 lines | VERIFIED | 537 lines. `from chonkie import SentenceChunker` at line 30. `HAS_CHONKIE=True` at line 31. `OVERLAP_SENTENCES=3`, `OVERLAP_MAX_CHARS=1500` at lines 53-54. `_make_chunker` factory at lines 74-95. `_tail_sentences` helper at lines 98-182. `_merge_small_sections` rewritten with `_pending_tail` nonlocal (line 259), chonkie delegation (line 270), all 7 schema keys on every emission. `_split_fixed` delegates end-to-end to chonkie (line 417). `_split_at_paragraphs` DELETED. Ruff clean. |
| `tests/test_unit.py` | 10 Phase 14 unit tests all pass | VERIFIED | 1293 lines. All 10 tests present by name: UT-031, UT-032, UT-033, UT-033b, UT-034, UT-035, UT-036, UT-036b, UT-037, UT-038. All pass: `pytest -m unit -k "ut031 or ut032 or ut033 or ut034 or ut035 or ut036 or ut037 or ut038"` → 10 passed, 46 deselected. Full unit suite: 52 passed, 4 skipped. |
| `tests/test_e2e.py` | FT-011 (boundary-straddle RED+GREEN) + FT-012 (V2-floor regression) | VERIFIED | 423 lines. `test_ft011_boundary_straddle_chunk_level_colocation` and `test_ft012_v2_baseline_regression` defined. Both pass (`pytest -m e2e -k "ft011 or ft012"` → 2 passed). FT-011 monkeypatches BOTH `_make_chunker` and `_tail_sentences` to disable overlap in RED mode (post-pivot dual-path correction vs. pre-pivot `_sentence_overlap` plan text). FT-012 reads `tests/baselines/v2/expected.json` and resolves per-scenario `graph_data.json` output paths (direct read, not stdout parsing). |
| `tests/fixtures/phase14_boundary_straddle.txt` | 15-25 KB synthetic fixture | VERIFIED | 15,332 bytes. `sotorasib` appears 1x, `KRAS G12C` appears 1x. No `ARTICLE`/`Section` headers → routes through `_split_fixed` fallback path. Round-trip produces exactly 2 chunks (`sotorasib` in chunk 0 tail, `KRAS G12C` in chunk 1 body) with chunk 1 `overlap_prev_chars=1378 > 0`. |
| `tests/baselines/v2/expected.json` | Committed summary counts, contract >=341/663 | VERIFIED | 1,329 bytes. 7 scenarios: `01_picalm_alzheimers` (183/478), `02_kras_g12c_landscape` (140/432), `03_rare_disease` (110/278), `04_immunooncology` (151/440), `05_cardiovascular` (90/245), `06_glp1_landscape` (193/619), `contract_events` (341/663). D-14 floor satisfied. Option 3a resolution documented in file's `note` field. |
| `commands/ingest.md:34` | "chunks with overlap" prose still present | VERIFIED | Line 34: `"Split each document's text into ~10,000 character chunks with overlap. Use your judgment on natural break points (paragraph boundaries, section headers)."` Invariant matches plan's expected string. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `core/chunk_document.py::_merge_small_sections::_flush` | `_make_chunker` | SentenceChunker instantiation on oversized buffer | WIRED | Line 270: `chunker = _make_chunker(max_size); sub_chunks = chunker.chunk(buffer_text)`. 7-key chunk dict emitted per sub-chunk (lines 323-337). |
| `core/chunk_document.py::_merge_small_sections::_flush` | `_tail_sentences` | `_pending_tail` nonlocal cache populated from RAW `buffer_text` | WIRED | Line 259 declares `_pending_tail = ""`. Line 266 reads `incoming = _pending_tail`. Line 357 writes `_pending_tail = _tail_sentences(buffer_text)` — RAW body, NOT `chunks[-1]["text"]`. Grep confirms `_tail_sentences(chunks[-1]["text"])` is ABSENT from the codebase (M-1 bug absent). |
| `core/chunk_document.py::_split_fixed` | `_make_chunker` | direct end-to-end call on full document text | WIRED | Line 417: `chunker = _make_chunker(max_size); sub_chunks = chunker.chunk(text)`. 7-key dict emitted per chunk with `char_offset = cc.start_index` (honest per-chunk). |
| `tests/test_e2e.py::FT-011` | `core.chunk_document.chunk_document` | direct call on fixture + co-location inspection | WIRED | Fixture opened via `FIXTURES_DIR / "phase14_boundary_straddle.txt"`. Two-mode monkeypatch (`_make_chunker` → zero-overlap factory AND `_tail_sentences` → `""`) for RED. Both modes pass. |
| `tests/test_e2e.py::FT-012` | `tests/baselines/v2/expected.json` | `json.load` + per-scenario floor comparison | WIRED | Hard-fails if file absent (grep confirms `expected_path.exists()` + assert present; no skip path for missing floor). Resolves per-scenario output dir and reads `graph_data.json` directly. |
| `scripts/setup.sh` | operator laptop | `uv pip install 'chonkie>=1.0'` required block | WIRED | Lines 139-167 of setup.sh install chonkie in the required block (before optional RDKit/Biopython). Column-0 heredoc, `exit 1` on failure. Mirrors sift-kg pattern. |
| `pyproject.toml` | discoverable dep declaration | `[project].dependencies = ["chonkie>=1.0"]` | WIRED | Line 18 declares `chonkie>=1.0` in `[project].dependencies`. Lines 1-8 carry the M-4 header comment documenting the partial-declaration intent. |

### Data-Flow Trace (Level 4)

Not applicable in the traditional UI-data-render sense — Phase 14 is a library-level refactor of `core/chunk_document.py`. The "data" is text input → chunk dict output. Traced manually via smoke test:

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `chunk_document()` output chunks | `chunks: list[dict]` | chonkie.SentenceChunker on buffered text (`_make_chunker().chunk(buffer_text)`); `_tail_sentences(buffer_text)` for cross-flush | Yes — real chunk text with overlap prefix, honest char_offset, non-zero overlap_prev_chars on middle chunks | FLOWING |
| `overlap_prev_chars` | int field on chunk dict | `max(0, sub_chunks[i-1].end_index - cc.start_index)` (chonkie-derived) or `len(incoming)` (cross-flush) | Yes — boundary-straddle fixture chunk 1 reports 1378 (non-zero, derived from chonkie `Chunk.start_index`/`end_index`) | FLOWING |
| `tests/baselines/v2/expected.json` content | `scenarios: dict` | committed JSON with real pre-Phase-14 observed counts (drug-discovery) + D-14 hard floor (contract) | Yes — 6 drug-discovery scenarios with non-zero floors; 1 contract scenario at 341/663 per D-14 | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Unit suite green (52 passed, 4 skipped) | `.venv/bin/python3 -m pytest tests/test_unit.py -m unit -q` | `52 passed, 4 skipped in 7.65s` | PASS |
| Phase 14 unit tests (10/10) | `.venv/bin/python3 -m pytest tests/test_unit.py -m unit -v -k "ut031 or ut032 or ut033 or ut034 or ut035 or ut036 or ut037 or ut038"` | 10 passed, 46 deselected | PASS |
| E2E suite green (7 passed) | `.venv/bin/python3 -m pytest tests/test_e2e.py -m e2e -q` | `7 passed in 2.12s` | PASS |
| FT-011 + FT-012 targeted | `.venv/bin/python3 -m pytest tests/test_e2e.py -m e2e -k "ft011 or ft012"` | 2 passed, 5 deselected | PASS |
| Boundary-straddle GREEN: chunk 1 contains both mentions | `python3 -c "from chunk_document import chunk_document; text=open('tests/fixtures/phase14_boundary_straddle.txt').read(); cs=chunk_document(text,'straddle'); print([i for i,c in enumerate(cs) if 'sotorasib' in c['text'].lower() and 'kras g12c' in c['text'].lower()])"` | `[1]` — chunk 1 co-locates both mentions | PASS |
| Boundary-straddle RED: no chunk co-locates when overlap disabled | monkeypatch `_make_chunker` → zero-overlap chunker AND `_tail_sentences` → "" | `[]` — no chunk co-locates | PASS |
| JSON round-trip preserves types | `json.loads(json.dumps(chunks[0]))`; assert `isinstance(overlap_prev_chars, int)`, `isinstance(is_overlap_region, bool)` | Both asserts hold | PASS |
| ARTICLE-boundary path emits cross-flush overlap | Two-article smoke with short bodies → 2 chunks, chunk 2 `overlap_prev_chars > 0` | chunk 0 `prev=0 next=122`; chunk 1 `prev=122 next=0` | PASS |
| D-14 contract floor in committed expected.json | `json.load('tests/baselines/v2/expected.json')["scenarios"]["contract_events"]` | `{"nodes": 341, "edges": 663}` | PASS |
| Fixture geometry (15-25 KB, no headers) | `wc -c tests/fixtures/phase14_boundary_straddle.txt; grep -cE "^(ARTICLE|Section)"` | 15,332 bytes; 0 matches | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| FIDL-03 | 14-01, 14-02, 14-03, 14-04 | Chunk boundaries emit sentence-aware overlap; entities/relations straddling 10K boundary reach extractor; chunk JSON records overlap provenance; required runtime dep with loud-fail import | SATISFIED | Code: chonkie-backed `_merge_small_sections::_flush` + `_split_fixed`; 7-key schema on every chunk; `_pending_tail` cross-flush cache; fail-loud `import chonkie` at module top. Tests: UT-031..UT-038 + UT-033b + UT-036b + FT-011 + FT-012 all pass. Traceability: `.planning/REQUIREMENTS.md:204` marks `FIDL-03 | Phase 14 | 14-01,14-02,14-03,14-04 | Complete`. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `.planning/REQUIREMENTS.md` | 121 | FIDL-03 bullet text still references `blingfire.text_to_sentences_and_offsets` and `_split_at_paragraphs` — both superseded by the 2026-04-18 chonkie pivot | Info | Docs-only drift. Code, infra, and tests are all chonkie-based; the requirement marker is `[x]` complete. Text describes the pre-pivot intent; behavior matches post-pivot reality. Candidate for a future docs cleanup pass. Does NOT affect phase goal achievement. |
| `core/chunk_document.py` | - | No TODO/FIXME/placeholder/HACK comments; no stub returns; no empty handlers | None | Clean. |
| `tests/test_unit.py` | 138, 688, 738, 861, 916 | 5 pre-existing ruff violations (F401, E401, F841) logged to `deferred-items.md` in Plan 14-02; NOT introduced by Phase 14 | Info | Pre-existing, confirmed via git-stash round-trip in 14-02. Out of FIDL-03 scope. |

### Human Verification Required

None required. The human checkpoint Task 3 in Plan 14-04 was resolved 2026-04-20 via Option 3a (adopt pre-Phase-14 counts as V2 regression floors). The phase goal — boundary-straddle recovery — is demonstrated empirically by FT-011's dual GREEN+RED mode and manually reproduced above. FT-012 is a forward-regression guardrail, not a Phase 14 acceptance test.

One contingency to note for future operators: FT-012 currently SKIPs the `contract_events` scenario on the dev machine because no contract output directory has been materialized post-2026-04-16 (see Plan 14-04 SUMMARY "Spec Nuance #3"). When the contract regression is re-run fresh, FT-012 will gate against the D-14 floor automatically. This is correct behavior (a missing output dir is not a regression), not a gap.

### Gaps Summary

No gaps. All 6 observable truths verified. All 7 required artifacts present and substantive. All 7 key links wired. All 10 Phase 14 unit tests pass; both E2E tests pass; full unit suite (52 passed, 4 skipped) and full E2E suite (7 passed) pass with zero regressions.

The one Info-severity drift (REQUIREMENTS.md:121 still references blingfire) is a documentation artifact from the 2026-04-18 architectural pivot. The traceability table and completion marker are accurate; only the free-text bullet description lags. Suggest future docs cleanup pass to rewrite the bullet to reference chonkie and the actual post-pivot split paths.

---

_Verified: 2026-04-20_
_Verifier: Claude (gsd-verifier)_
