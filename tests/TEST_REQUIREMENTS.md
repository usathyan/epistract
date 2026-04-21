# Epistract Test Requirements Specification

**Traceability:** Each requirement has a unique ID (REQ-XXX) traceable from:
- Domain spec → Entity/Relation types → Unit tests → Functional tests → User acceptance tests

---

## 1. Unit Tests (UT)

Unit tests validate individual components in isolation.

### UT-001: Domain YAML Loads Successfully
- **Traces to:** Domain spec Section 3 (Entity Types)
- **Test:** Load `domain.yaml` via sift-kg DomainLoader, verify 17 entity types and 30 relation types
- **Pass criteria:** No errors, correct counts

### UT-002: Pattern Scanner Detects SMILES
- **Traces to:** Domain spec Section 16.6 (Regex Patterns)
- **Test:** Feed text containing known SMILES `CC(=O)Oc1ccccc1C(=O)O` to scan_patterns.scan_text()
- **Pass criteria:** Returns match with pattern_type="smiles"

### UT-003: Pattern Scanner Detects NCT Numbers
- **Traces to:** Domain spec Section 16.6
- **Test:** Feed text containing `NCT04303780` to scan_patterns.scan_text()
- **Pass criteria:** Returns match with pattern_type="nct_number"

### UT-004: Pattern Scanner Detects DNA Sequences
- **Traces to:** Domain spec Section 16.6
- **Test:** Feed text containing `ATCGATCGATCGATCG` (≥15 chars)
- **Pass criteria:** Returns match with pattern_type="dna_sequence"

### UT-005: Pattern Scanner Detects CAS Numbers
- **Traces to:** Domain spec Section 16.6
- **Test:** Feed text containing `2252403-56-6` (sotorasib CAS)
- **Pass criteria:** Returns match with pattern_type="cas_number"

### UT-006: SMILES Validator Returns Properties
- **Traces to:** Domain spec Section 16.7 (Validation Pipeline)
- **Test:** validate_smiles("CC(=O)Oc1ccccc1C(=O)O") → valid, MW ~180, canonical form
- **Pass criteria:** valid=True, molecular_weight present, canonical_smiles present
- **Dependency:** RDKit installed

### UT-007: SMILES Validator Rejects Invalid SMILES
- **Traces to:** Domain spec Section 16.7
- **Test:** validate_smiles("not_a_smiles") → valid=False
- **Pass criteria:** valid=False, error message present
- **Dependency:** RDKit installed

### UT-008: SMILES Validator Graceful Without RDKit
- **Traces to:** Design spec Section 16.7
- **Test:** With RDKit not importable, validate_smiles returns valid=None
- **Pass criteria:** valid=None, error mentions "not installed"

### UT-009: Sequence Validator Validates DNA
- **Traces to:** Domain spec Section 16.7
- **Test:** validate_sequence("ATCGATCGATCGATCG") → valid=True, type=DNA, gc_content present
- **Pass criteria:** valid=True, type="DNA"
- **Dependency:** Biopython installed

### UT-010: Sequence Validator Validates Protein
- **Traces to:** Domain spec Section 16.7
- **Test:** validate_sequence("MTEYKLVVVGAGGVGKSALT") → valid=True, type=protein
- **Pass criteria:** valid=True, type="protein", molecular_weight present
- **Dependency:** Biopython installed

### UT-011: Sequence Validator Auto-Detects Type
- **Traces to:** Domain spec Section 16.7
- **Test:** detect_type("ATCGATCG") → "DNA", detect_type("AUGCUAGC") → "RNA", detect_type("MTEYKLVVV") → "protein"
- **Pass criteria:** Correct type for each

### UT-012: Extraction Adapter Writes Valid JSON
- **Traces to:** Design spec Section 3 (Claude-as-Extractor)
- **Test:** Call build_extraction.write_extraction() with sample data, load resulting JSON, verify it matches sift-kg DocumentExtraction schema
- **Pass criteria:** JSON loads, all required fields present, entities/relations are lists

### UT-013: run_sift.py Build Command Works
- **Traces to:** Design spec Section 8 (Scripts)
- **Test:** Create test extraction JSONs, run `python run_sift.py build <dir>`, verify graph_data.json created
- **Pass criteria:** graph_data.json exists with entities > 0

### UT-014: Validation Orchestrator Scans Extractions
- **Traces to:** Design spec Section 16.9
- **Test:** Create extraction JSON with SMILES in context, run validate_molecules.py, verify results.json created
- **Pass criteria:** results.json exists, identifiers_found > 0

### UT-015: Extraction Adapter Normalizes Field Names
- **Traces to:** Bug fix — agents may use `type` instead of `entity_type`/`relation_type`
- **Test:** Call build_extraction.write_extraction() with entities using `type` field, verify output uses `entity_type`
- **Pass criteria:** Output JSON has `entity_type` on all entities, `relation_type` on all relations, no `type` keys

### UT-016: Community Labeling Generates Descriptive Names
- **Traces to:** scripts/label_communities.py
- **Test:** Build graph from 01_picalm_alzheimers corpus, run label_communities, verify communities have descriptive labels
- **Pass criteria:** No community label starts with "Community " (numbered), all labels are descriptive strings

---

## 2. Functional Tests (FT)

Functional tests validate end-to-end pipeline behavior.

### FT-001: Full Pipeline — Single Document
- **Traces to:** Design spec Section 9 (Workflow)
- **Test:** Ingest single PubMed abstract → extract → build → verify graph has entities and relations
- **Pass criteria:** graph_data.json has ≥5 entities and ≥3 relations

### FT-002: Full Pipeline — Multiple Documents
- **Traces to:** Design spec Section 9
- **Test:** Ingest 5 KRAS G12C abstracts → extract → build → verify graph merges cross-document entities
- **Pass criteria:** Entity count < sum of per-document entities (dedup working), relations span documents

### FT-003: Entity Type Coverage
- **Traces to:** Domain spec Section 3
- **Test:** Extract from mixed corpus (oncology + clinical trial report), verify ≥8 of 13 entity types present
- **Pass criteria:** ≥8 distinct entity_type values in graph nodes

### FT-004: Relation Type Coverage
- **Traces to:** Domain spec Section 4
- **Test:** Extract from KRAS corpus, verify TARGETS, INHIBITS, INDICATED_FOR, EVALUATED_IN all present
- **Pass criteria:** All 4 relation types found in graph edges

### FT-005: Export Formats
- **Traces to:** Design spec Section 5 (/epistract-export)
- **Test:** Build graph, export to JSON, GraphML, SQLite, CSV — verify all produce valid output
- **Pass criteria:** All files created, SQLite queryable, CSV has headers

### FT-006: Molecular Validation Integration
- **Traces to:** Domain spec Section 16.9
- **Test:** Ingest document containing known SMILES, run validation, verify SMILES detected and (if RDKit available) validated
- **Pass criteria:** validation/results.json has smiles_found ≥ 1

### FT-007: Community Detection and Labeling
- **Traces to:** sift-kg graph/communities.py, scripts/label_communities.py
- **Test:** Build graph from 15 documents, verify communities detected and auto-labeled
- **Pass criteria:** communities.json has ≥2 communities, all community values are descriptive labels (not "Community N")

### FT-008: Interactive Viewer Generates HTML
- **Traces to:** sift-kg visualize.py
- **Test:** Build graph, run view command, verify graph.html created
- **Pass criteria:** graph.html exists, contains <script> tags, file size > 10KB

---

## 3. User Acceptance Tests (UAT) — PhD Scientist Questions

These are real research questions a PhD scientist would ask. Each tests whether the knowledge graph can provide a meaningful, scientifically accurate answer through graph traversal.

### Topic 1: PICALM / Alzheimer's Disease

#### UAT-101: What genes are associated with Alzheimer's disease risk?
- **Expected:** PICALM, APOE, BIN1, CLU, CR1, CD33, ABCA7, and others extracted as GENE entities with IMPLICATED_IN → DISEASE(Alzheimer's disease)
- **Graph traversal:** DISEASE(Alzheimer) ← IMPLICATED_IN ← GENE
- **Acceptance:** ≥3 risk genes identified with GWAS evidence

#### UAT-102: What biological pathways does PICALM participate in?
- **Expected:** Endocytosis, clathrin-mediated vesicle trafficking, amyloid precursor protein processing
- **Graph traversal:** GENE/PROTEIN(PICALM) → PARTICIPATES_IN → PATHWAY
- **Acceptance:** ≥1 pathway linked to PICALM

#### UAT-103: What is the relationship between PICALM and amyloid beta?
- **Expected:** PICALM modulates endocytosis affecting APP processing and Aβ clearance
- **Graph traversal:** PROTEIN(PICALM) → relations → PROTEIN(APP) or PATHWAY(endocytosis) → IMPLICATED_IN → DISEASE
- **Acceptance:** A traceable path from PICALM to amyloid biology

#### UAT-104: What therapeutic approaches target PICALM-related pathways?
- **Expected:** Compounds targeting endocytosis or APP processing
- **Graph traversal:** PATHWAY ← PARTICIPATES_IN ← PROTEIN(PICALM); PATHWAY ← INHIBITS/ACTIVATES ← COMPOUND
- **Acceptance:** If any compounds are mentioned in the literature, they should be extracted

### Topic 2: KRAS G12C Inhibitor Landscape

#### UAT-201: What drugs target KRAS G12C?
- **Expected:** sotorasib (AMG 510), adagrasib (MRTX849), and emerging compounds
- **Graph traversal:** GENE(KRAS G12C) ← TARGETS/INHIBITS ← COMPOUND
- **Acceptance:** Both sotorasib and adagrasib extracted and linked

#### UAT-202: What clinical trials evaluate KRAS G12C inhibitors?
- **Expected:** CodeBreaK 100, CodeBreaK 200, KRYSTAL-1, KRYSTAL-7
- **Graph traversal:** COMPOUND(sotorasib/adagrasib) → EVALUATED_IN → CLINICAL_TRIAL
- **Acceptance:** ≥2 named trials with phase and results attributes

#### UAT-203: What resistance mechanisms exist for KRAS G12C inhibitors?
- **Expected:** Secondary KRAS mutations (G12D/V/R, Y96C), MET amplification, MAPK reactivation
- **Graph traversal:** COMPOUND(sotorasib) ← CONFERS_RESISTANCE_TO ← GENE/PROTEIN
- **Acceptance:** ≥1 resistance mechanism extracted

#### UAT-204: What combination strategies are being explored?
- **Expected:** KRAS G12C inhibitors + anti-PD-1, + SHP2 inhibitors, + SOS1 inhibitors, + MEK inhibitors
- **Graph traversal:** COMPOUND(sotorasib) → COMBINED_WITH → COMPOUND
- **Acceptance:** ≥1 combination partner identified

#### UAT-205: What is the mechanism of action of sotorasib?
- **Expected:** Covalent, irreversible KRAS G12C inhibitor that locks KRAS in inactive GDP-bound state
- **Graph traversal:** COMPOUND(sotorasib) → HAS_MECHANISM → MECHANISM_OF_ACTION; COMPOUND → INHIBITS → PROTEIN(KRAS)
- **Acceptance:** Mechanism described with covalent/irreversible attributes

### Topic 3: Rare Disease Therapeutics

#### UAT-301: What is the approach to treating PKU?
- **Expected:** Pegvaliase (enzyme substitution with PEGylated phenylalanine ammonia lyase)
- **Graph traversal:** COMPOUND(pegvaliase) → INDICATED_FOR → DISEASE(phenylketonuria); COMPOUND → HAS_MECHANISM → MOA
- **Acceptance:** Pegvaliase linked to PKU with mechanism

#### UAT-302: What is vosoritide's target and mechanism?
- **Expected:** C-type natriuretic peptide analog targeting FGFR3 pathway to promote bone growth
- **Graph traversal:** COMPOUND(vosoritide) → TARGETS → PROTEIN; COMPOUND → HAS_MECHANISM → MOA
- **Acceptance:** Target pathway identified, achondroplasia indication linked

#### UAT-303: What gene therapy approaches exist for hemophilia A?
- **Expected:** Valoctocogene roxaparvovec (AAV5-FVIII gene therapy)
- **Graph traversal:** COMPOUND(valoctocogene roxaparvovec) → INDICATED_FOR → DISEASE(hemophilia A)
- **Acceptance:** Gene therapy compound extracted with correct indication

### Topic 4: Immuno-Oncology Combinations

#### UAT-401: What checkpoint combinations have been developed?
- **Expected:** nivolumab + ipilimumab (PD-1 + CTLA-4), nivolumab + relatlimab (PD-1 + LAG-3)
- **Graph traversal:** COMPOUND(nivolumab) → COMBINED_WITH → COMPOUND; each → TARGETS → PROTEIN(checkpoint)
- **Acceptance:** Both combinations identified with correct targets

#### UAT-402: What are the key clinical trials for nivolumab combinations?
- **Expected:** CheckMate-067 (melanoma), CheckMate-227 (NSCLC), RELATIVITY-047 (melanoma with relatlimab)
- **Graph traversal:** COMPOUND(nivolumab) → EVALUATED_IN → CLINICAL_TRIAL
- **Acceptance:** ≥2 named trials extracted

#### UAT-403: What immune-related adverse events are associated with checkpoint inhibitors?
- **Expected:** Colitis, hepatitis, pneumonitis, thyroiditis, dermatitis, myocarditis
- **Graph traversal:** COMPOUND(nivolumab/ipilimumab) → CAUSES → ADVERSE_EVENT
- **Acceptance:** ≥2 irAEs extracted

#### UAT-404: What biomarkers predict response to nivolumab?
- **Expected:** PD-L1 expression (TPS), TMB, MSI-H
- **Graph traversal:** BIOMARKER → PREDICTS_RESPONSE_TO → COMPOUND(nivolumab)
- **Acceptance:** ≥1 predictive biomarker linked

### Topic 5: Cardiovascular & Inflammation

#### UAT-501: What is mavacamten's mechanism of action?
- **Expected:** Selective cardiac myosin inhibitor that reduces cardiac hypercontractility
- **Graph traversal:** COMPOUND(mavacamten) → HAS_MECHANISM → MOA; COMPOUND → TARGETS → PROTEIN(cardiac myosin)
- **Acceptance:** Mechanism and target identified

#### UAT-502: What clinical evidence supports mavacamten for HCM?
- **Expected:** EXPLORER-HCM (Phase 3), VALOR-HCM trials, LVOT gradient reduction
- **Graph traversal:** COMPOUND(mavacamten) → EVALUATED_IN → CLINICAL_TRIAL; COMPOUND → INDICATED_FOR → DISEASE(HCM)
- **Acceptance:** ≥1 trial with results

#### UAT-503: What is deucravacitinib's target and indication?
- **Expected:** Selective TYK2 inhibitor for moderate-to-severe plaque psoriasis
- **Graph traversal:** COMPOUND(deucravacitinib) → INHIBITS → PROTEIN(TYK2); COMPOUND → INDICATED_FOR → DISEASE(psoriasis)
- **Acceptance:** TYK2 target and psoriasis indication linked

---

## 5. Phase 13 Tests (Extraction Pipeline Reliability)

### UT-017: Extractor Prompt Declares Required Fields
- **Traces to:** FIDL-02a
- **Test:** grep agents/extractor.md for `document_id`, `entities`, `relations` declared as REQUIRED top-level fields and "build_extraction.py" instruction
- **Pass criteria:** All three field names appear in a block labeled REQUIRED; Write tool ban text present

### UT-018: Extractor Prompt Documents Stdin Fallback
- **Traces to:** FIDL-02a
- **Test:** grep agents/extractor.md for stdin-pipe invocation AND "report failure" instruction
- **Pass criteria:** Both primary `--json` path AND stdin fallback `echo '<json>' | python3 ...` path are documented

### UT-019: normalize_extractions Renames Variant Filenames
- **Traces to:** FIDL-02b
- **Test:** Fixture dir contains `foo_raw.json`, `bar_extraction_input.json`, `baz-extraction.json` with valid bodies; after normalize, only `foo.json`, `bar.json`, `baz.json` remain (or are returned in the report as renamed)
- **Pass criteria:** All three variant filenames mapped to canonical `<doc_id>.json`

### UT-020: normalize_extractions Infers Missing document_id
- **Traces to:** FIDL-02b
- **Test:** Fixture JSON with no `document_id` field but filename `my_doc_42.json` → output has `document_id: "my_doc_42"`
- **Pass criteria:** Inferred value equals filename stem

### UT-021: normalize_extractions Dedupes Keeping Richer Version
- **Traces to:** FIDL-02b
- **Test:** Two files for same doc_id (one with 3 entities, one with 10) → survivor has 10 entities; loser moved to `_dedupe_archive/`
- **Pass criteria:** Survivor file has richer content; archived file exists under `extractions/_dedupe_archive/`

### UT-022a: build_extraction._normalize_fields Coerces Schema Drift
- **Traces to:** FIDL-02c
- **Test:** Unit test `test_normalize_coerces_schema_drift` in tests/test_unit.py exercises `build_extraction._normalize_fields` directly: entity using `type` (not `entity_type`) + string `"0.9"` confidence + missing `context`/`attributes` → all coerced
- **Pass criteria:** Output entity has `entity_type` field, numeric confidence, empty-string context, empty-dict attributes

### UT-022b: normalize_extractions Module-Level Coerces Schema Drift
- **Traces to:** FIDL-02b
- **Test:** Unit test `test_normalize_coerces_schema_drift_via_module` in tests/test_unit.py exercises the `normalize_extractions()` entry-point end-to-end on a drift fixture; confirms delegation to `_normalize_fields` and write-back of coerced record
- **Pass criteria:** File on disk has `entity_type` field + numeric confidence after module-level normalize; `result["pass_rate"] == 1.0`

### UT-023: normalize_extractions Writes _normalization_report.json
- **Traces to:** FIDL-02b
- **Test:** After normalize run, `extractions/_normalization_report.json` exists with per-file action entries and aggregate pass/recovered/unrecoverable counts
- **Pass criteria:** File exists with `indent=2` JSON and records every input file

### UT-024: DocumentExtraction Pydantic Model Rejects Missing document_id
- **Traces to:** FIDL-02c
- **Test:** Directly instantiate `sift_kg.extract.models.DocumentExtraction(document_path="x.pdf", entities=[], relations=[])` (omitting `document_id`) — must raise `pydantic.ValidationError` mentioning `document_id`. Also verify `write_extraction` wraps this into a `ValueError` when called with a dict payload (via `**record`) that lacks `document_id`.
- **Pass criteria:** Direct `DocumentExtraction(**payload)` raises ValidationError; `write_extraction` wraps into ValueError with both "DocumentExtraction" AND "document_id" in message

### UT-025: build_extraction Raises on Invalid Entity Shape
- **Traces to:** FIDL-02c
- **Test:** Call `write_extraction` with entity using `type` field bypassing `_normalize_fields` → Pydantic validation raises
- **Pass criteria:** Raises ValueError mentioning `entity_type`

### UT-026: build_extraction Threads --model Flag Into Output
- **Traces to:** FIDL-02c
- **Test:** Run `python3 core/build_extraction.py doc1 <tmp> --model claude-sonnet-4-5 --json '...'` → output JSON has `model_used: "claude-sonnet-4-5"`
- **Pass criteria:** `model_used` matches flag value

### UT-027: build_extraction Reads EPISTRACT_MODEL Env Var
- **Traces to:** FIDL-02c
- **Test:** Run without `--model` but with `EPISTRACT_MODEL=claude-opus-4-7` in env → output JSON has `model_used: "claude-opus-4-7"`
- **Pass criteria:** `model_used` matches env var value

### UT-028: build_extraction Threads --cost Flag Into Output
- **Traces to:** FIDL-02c
- **Test:** Run with `--cost 0.0123` → output JSON has `cost_usd: 0.0123` (use `pytest.approx` for float compare)
- **Pass criteria:** `cost_usd == pytest.approx(0.0123)` returns True

### UT-029: build_extraction model_used Defaults to null (not hardcoded)
- **Traces to:** FIDL-02c
- **Test:** Run without `--model` flag and without `EPISTRACT_MODEL` env → output `model_used` is null (JSON null, not the string "claude-opus-4-6")
- **Pass criteria:** `data["model_used"] is None`; the literal string `"claude-opus-4-6"` does NOT appear in any build_extraction.py output

### UT-030: build_extraction cost_usd Defaults to null (not hardcoded)
- **Traces to:** FIDL-02c
- **Test:** Run without `--cost` flag → output `cost_usd` is null
- **Pass criteria:** `data["cost_usd"] is None`; the literal `0.0` fallback is not inserted

### FT-009: 20+ Doc Normalization Achieves ≥95% Pass Rate (e2e)
- **Traces to:** FIDL-02b
- **Test:** Load `tests/fixtures/normalization/` (24 physical files → 23 logical docs post-dedupe), run normalize + graph build; confirm ≥95% load rate
- **Pass criteria:** `_normalization_report.json` reports `pass_rate >= 0.95`; `graph_data.json` has nodes from all recovered docs

### FT-010: --fail-threshold Aborts Before Build When Below Threshold (e2e)
- **Traces to:** FIDL-02b
- **Test:** Load `tests/fixtures/normalization_below_threshold/` (10 files: 2 survivors + 8 unrecoverable), run with `--fail-threshold 0.95`; confirm pipeline exits nonzero BEFORE run_sift.py build runs
- **Pass criteria:** Subprocess exit code ≠ 0; `graph_data.json` is NOT created; error message mentions `--fail-threshold` and the observed pass-rate

---

## 6. Phase 14 Tests (Chunk Overlap)

### UT-031: blingfire imports and tokenizes at module load
- **Traces to:** FIDL-03
- **Test:** `import blingfire; blingfire.text_to_sentences_and_offsets("One. Two. Three.")` returns a 2-tuple (text_with_newlines, offset_array) with 3 sentences.
- **Pass criteria:** Import succeeds; result contains 3 sentence spans.

### UT-032: Overlap primitive returns last-N sentences under cap
- **Traces to:** FIDL-03 (D-02, D-03)
- **Test:** Unit test invokes the `core/chunk_document.py` overlap helper on a 10-sentence fixture; asserts the returned overlap contains exactly the last 3 sentences when their total length is ≤1500 chars.
- **Pass criteria:** Overlap string equals concatenation of last 3 sentences (order preserved); `len(overlap) <= 1500`.

### UT-033: Overlap primitive truncates on 1500-char cap
- **Traces to:** FIDL-03 (D-03)
- **Test:** Feed a fixture where the last 3 sentences total > 1500 chars. Helper returns the most-recent sentences whose cumulative length fits under 1500; never mid-sentence truncation.
- **Pass criteria:** `len(overlap) <= 1500`; overlap starts on a sentence boundary (begins a new sentence produced by blingfire, not mid-word).

### UT-033b: Overlap primitive — partial fit (2 of 3 last sentences fit under cap) (M-5)
- **Traces to:** FIDL-03 (D-02 ∩ D-03 intersection)
- **Test:** Build a fixture with 3 sentences of ~600 chars each (total ~1800, over the 1500 cap, but the last 2 fit at ~1200). Assert the primitive returns exactly the last 2 sentences — the oldest (first) is dropped, the two most-recent are preserved. This pins the interior walk (right-to-left accumulate) behavior in between "all 3 fit" (UT-032) and "none fit" (UT-033 edge where a single sentence > cap).
- **Pass criteria:** Overlap contains the content of sentences 2 and 3 (the most-recent two); does NOT contain sentence 1's distinguishing content; `len(overlap) <= 1500`.

### UT-034: Overlap primitive handles fewer-than-N sentences
- **Traces to:** FIDL-03
- **Test:** Feed a fixture with exactly 1 sentence; helper returns that sentence (not error, not empty). Feed empty text; helper returns "".
- **Pass criteria:** 1-sentence input → 1-sentence overlap; empty input → empty overlap.

### UT-035: Missing blingfire raises loud ImportError
- **Traces to:** FIDL-03 (D-08)
- **Test:** Use pytest's `monkeypatch.setitem(sys.modules, "blingfire", None)` + `monkeypatch.delitem(sys.modules, "chunk_document", raising=False)` and `importlib.import_module("chunk_document")`; assert ImportError whose message mentions both `blingfire` and the install hint (`uv pip install blingfire` or `/epistract:setup`). Monkeypatch restores state automatically at teardown — no manual try/finally, safe under pytest-randomly / pytest-xdist.
- **Pass criteria:** ImportError raised with install hint substring present; no test ordering interference.

### UT-036: Chunk JSON contains overlap_prev_chars / overlap_next_chars / is_overlap_region / char_offset + section_header (cont.) invariant
- **Traces to:** FIDL-03 (D-10, D-11, D-12)
- **Test:** Run `chunk_document()` on a fixture that produces ≥3 chunks. Every chunk dict has all four keys. First chunk has `overlap_prev_chars == 0`. Last chunk has `overlap_next_chars == 0`. Non-boundary chunks have `overlap_prev_chars > 0`. `is_overlap_region` is always `False` at the chunk level (reserved flag per D-10). `char_offset` strictly increases across sub-chunks of the same merged section (D-11 — honest per-sub-chunk offsets). Additionally (m-7 fix): sub-chunks after the first of an oversized section have `section_header` ending in `(cont.)` — pins D-12.
- **Pass criteria:** All four keys present on every chunk; `overlap_prev_chars[0] == 0`, `overlap_next_chars[-1] == 0`, middle chunks `> 0`; `is_overlap_region` always False; sub-chunk offsets strictly increasing within a merged section; at least one chunk[1:] has `section_header.endswith("(cont.)")`.

### UT-036b: char_offset stays honest across whitespace-only paragraph gaps (M-6)
- **Traces to:** FIDL-03 (D-11)
- **Test:** Fixture where paragraphs are separated by triple/quadruple blank lines (whitespace-only paragraphs in between). Pin that for each emitted chunk, `original_text[chunk["char_offset"] : chunk["char_offset"] + 30]` aligns with the corresponding chunk body text (after stripping any overlap prefix that was prepended and the `\n\n` separator). Proves the paragraph-skip branch in `_split_at_paragraphs` does not cause `current_start` to lag by the blank-paragraph's length — i.e., `char_offset` marks where the FIRST real paragraph starts, not the spurious earlier whitespace block.
- **Pass criteria:** Offset slice of original text matches chunk body for every chunk; no off-by-N drift attributable to blank-paragraph skip.

### UT-037: Overlap emitted at ARTICLE boundary flush (cross-flush tail cache — M-1/M-2)
- **Traces to:** FIDL-03 (D-04 #2)
- **Test:** Fixture with two ARTICLE sections, each > MIN_CHUNK_SIZE but < MAX_CHUNK_SIZE (so each gets its own chunk without internal splitting). The overlap prefix on ARTICLE II must equal `_sentence_overlap(article_1_raw_text)` — NOT `_sentence_overlap(chunks[0]["text"])`. This pins the correct invariant: cross-flush overlap is computed from the RAW outgoing tail (cached in a nonlocal `_pending_tail` inside `_merge_small_sections`), not from the previous chunk's emitted text (which may itself already carry an overlap prefix — chaining those overlaps would accumulate).
- **Pass criteria:** Chunk 2 `text` starts with `_sentence_overlap(article_1_raw_text)` verbatim; `overlap_prev_chars` equals that tail length; no chained accumulation across multiple flushes.

### UT-038: Overlap emitted at _split_fixed fallback
- **Traces to:** FIDL-03 (D-05 — one primitive, reused)
- **Test:** Fixture with no section headers (falls through `_split_at_sections` → `_split_fixed`), ≥3 paragraphs, total length > MAX_CHUNK_SIZE. Chunks 2..N have non-zero `overlap_prev_chars` populated by the same helper as the clause-aware path.
- **Pass criteria:** Chunks 2..N all have `overlap_prev_chars > 0`; chunk 1 has `overlap_prev_chars == 0`.

### FT-011: Chunk-level co-location of boundary-straddling mentions (M-3 — weaker spec)
- **Traces to:** FIDL-03 (D-13 #1)
- **Test:** Synthetic text fixture where `sotorasib` ends chunk 1 and `KRAS G12C` starts chunk 2 (the "INHIBITS(sotorasib, KRAS G12C)" relation that spans char ~9999/10001). The test is CHUNK-LEVEL (co-location of both mention strings in at least one chunk's text) — a necessary precondition for graph-level extraction. Without a real LLM we cannot assert the relation itself appears in the final graph, but co-location of both entity strings in a single chunk is the CAUSE the fix addresses; extraction failure is the downstream effect. The test is structured as a single function with GREEN mode (real overlap — both mentions co-locate in at least one chunk) and RED mode (monkeypatch `_sentence_overlap` → `""`, no chunk co-locates both mentions). One test function, two modes — no git-stash choreography.
- **Pass criteria:** GREEN: at least one chunk contains both `sotorasib` and `kras g12c` (case-insensitive). RED: with overlap disabled, no chunk contains both.

### FT-012: V2 baseline diff — drug-discovery and contract scenarios ≥ V2 (B-2: file-backed floor, FAIL not SKIP)
- **Traces to:** FIDL-03 (D-13 #2, D-14)
- **Test:** Read `tests/baselines/v2/expected.json` (a committed summary-counts file, format `{"scenarios": {"<scenario>": {"nodes": N, "edges": E}, ...}}`). Re-run the 6 drug-discovery regression scenarios + 1 contract scenario via `python tests/regression/run_regression.py`. For each scenario, assert post-run `nodes >= expected.nodes` AND `edges >= expected.edges`. If `tests/baselines/v2/expected.json` does NOT exist, the test FAILS (not skips) with an instructional message pointing to how to regenerate it (`make regression-update` then record the numbers into `expected.json`). The full `graph_data.json` dumps remain gitignored; only the small summary counts file is committed. The contract scenario's floor (≥663 edges, ≥341 nodes) is pinned in `expected.json` per D-14.
- **Pass criteria:** `expected.json` exists (enforced; missing → FAIL). All 7 scenarios satisfy nodes≥expected AND edges≥expected. Contract scenario ≥663 edges, ≥341 nodes.

### UT-039: discover_corpus delegates to sift-kg (runtime extension set)
- **Traces to:** FIDL-04 (D-01, D-09)
- **Test:** Create a tmpdir containing files with suffixes `.pdf .pptx .md .epub .rtf .odt .csv .xml .json .yaml .log .ipynb .bib .fb2 .msg` (15 varied, all text-class), plus `.zip` and `.png` (must be excluded in default call). Call `discover_corpus(tmpdir)`. Assert the returned list is sorted, length == 15 (no .zip, no .png). Then assert the runtime-resolved extension set (via module-level `SUPPORTED_EXTENSIONS`) has `len(...) >= 28` and that it is a subset of `sift_kg.ingest.create_extractor(backend="kreuzberg").supported_extensions()` minus `{".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}`.
- **Pass criteria:** `discover_corpus` returns exactly the 15 text-class files, skipping .zip and .png; `len(SUPPORTED_EXTENSIONS) >= 28`; set-subset assertion holds.
- **Dependency:** sift-kg installed (skip if HAS_SIFTKG is False).

### UT-040: OCR flag gates image extensions in discover_corpus
- **Traces to:** FIDL-04 (D-04)
- **Test:** Create a tmpdir containing `sample.png`, `sample.jpg`, `sample.pdf`. Call `discover_corpus(tmpdir)` (ocr defaulted False) — assert only `sample.pdf` is returned. Call `discover_corpus(tmpdir, ocr=True)` — assert `sample.pdf`, `sample.png`, `sample.jpg` are all returned.
- **Pass criteria:** Default call returns 1 file; `ocr=True` call returns 3 files.
- **Dependency:** sift-kg installed (skip if HAS_SIFTKG is False).

### UT-041: Missing sift-kg raises ImportError in discover_corpus (no silent fallback)
- **Traces to:** FIDL-04 (D-02)
- **Test:** Use `unittest.mock.patch.object(core.ingest_documents, "HAS_SIFT_READER", False)`, then call `discover_corpus(some_dir)`. Assert `pytest.raises(ImportError)` with a `match` pointing to `/epistract:setup` or `sift-kg`. ALSO assert `core.ingest_documents.SUPPORTED_EXTENSIONS` access under the same patch raises ImportError with the same install hint (D-02: no silent 9-extension fallback).
- **Pass criteria:** Both `discover_corpus(dir)` and `SUPPORTED_EXTENSIONS` access raise `ImportError` whose message contains "sift-kg" or "/epistract:setup".
- **Dependency:** None (pure mock test, runs without sift-kg paths executed).

### FT-013: New-format ingest round-trip — markdown (.md) discovered and extracted end-to-end
- **Traces to:** FIDL-04 (D-01, D-09)
- **Test:** Copy `tests/fixtures/format_parity/sample.md` into a tmp corpus, run `ingest_corpus(corpus, output)`, assert discovery found 1 file, extraction succeeded, `parse_type="text"`, `warnings==[]`, the ingested `.txt` exists and contains the phrase `Phase 15 FT-013`, and `triage.json` reflects the clean result.
- **Pass criteria:** `total_files==1, successful==1, failed==0`; `documents[0].warnings==[]`; ingested text file contains `Phase 15 FT-013`.
- **Dependency:** sift-kg installed (skipped otherwise).

### FT-014: Corrupted file discovered, extraction-failure recorded in triage warnings[]
- **Traces to:** FIDL-04 (D-06, D-07)
- **Test:** Copy `tests/fixtures/format_parity/corrupted.pptx` into a tmp corpus, run `ingest_corpus(corpus, output)`, assert discovery found 1 file (pure extension-match), warnings[] has an entry starting with `extraction_failed` OR equal to `empty_text` (parse_document return-shape disjunction per revised plan — both satisfy D-06/D-07 as long as the failure is SURFACED in warnings[]), and `triage.json` persists the warning.
- **Pass criteria:** `total_files==1`; `documents[0].warnings` contains at least one element satisfying `startswith("extraction_failed") or == "empty_text"`; triage.json on disk reflects the warning.
- **Dependency:** sift-kg installed (skipped otherwise).

### FT-015: V2 baseline floor holds after FIDL-04 discovery-layer change (D-13)
- **Traces to:** FIDL-04 (D-13), Phase 14 D-14
- **Test:** Read `tests/baselines/v2/expected.json`. For each scenario whose output directory exists (resolved via the same logic as tests/test_e2e.py FT-012), assert `graph_data.json` nodes ≥ floor AND edges ≥ floor. If `contract_events` has an output directory, assert nodes ≥341 AND edges ≥663 (Phase 14 D-14 hard floor). `expected.json` missing is a HARD FAILURE.
- **Pass criteria:** All resolvable scenarios satisfy their committed floor; contract floor 341/663 is absolute when its output exists; missing `expected.json` fails (not skips).
- **Dependency:** `tests/baselines/v2/expected.json` present (guaranteed by Phase 14 commit).

---

## 7. Phase 16 Tests (Wizard Sample Window Beyond 8KB)

### UT-042: _build_excerpts returns [] for short docs and 3-slice list for long docs
- **Traces to:** FIDL-05 (D-01, D-02, D-03)
- **Test:** Call `core.domain_wizard._build_excerpts("x" * 11999)` — assert the result is `[]` (short-doc branch — len ≤ MULTI_EXCERPT_THRESHOLD). Call `_build_excerpts("x" * 12001)` — assert the result is a list of 3 strings, each ≤ 4000 chars. Call `_build_excerpts(("a" * 30000))` (exactly 30000 chars) — assert `len(result) == 3`, `result[0] == "a" * 4000` (head is first 4000 chars, D-01), `result[1] == "a" * 4000` (middle slice len == 4000, per D-03: `len//2 - 2000` to `len//2 + 2000` = chars 13000..17000), and `result[2] == "a" * 4000` (tail is last 4000 chars, D-01). Call `_build_excerpts(payload)` where payload is a deterministic string `"HEAD" + "." * 20000 + "MID" + "." * 20000 + "TAIL"` (approx 40007 chars) — assert `"HEAD" in result[0]`, `"MID" in result[1]`, `"TAIL" in result[2]`.
- **Pass criteria:** All four assertions hold; `_build_excerpts` raises no exceptions for any of the four inputs.
- **Dependency:** None (pure function test, no I/O, no LLM call).

### UT-043: build_schema_discovery_prompt emits 3 excerpt markers + 3 sentinels for long docs; full-text preserved for short docs
- **Traces to:** FIDL-05 (D-04, D-05, D-10, D-11)
- **Test:** Read `tests/fixtures/wizard_sample_window/long_contract.txt` (synthetic ~60K-char fixture created in Plan 16-02 Task 1 — RED until that task lands; GREEN once 16-02 Task 1 completes). Call `build_schema_discovery_prompt(fixture_text, "Synthetic long contract domain")`. Assert:
  1. Prompt contains the literal substring `[EXCERPT 1/3 — chars 0 to 4000 (head)]` on its own line.
  2. Prompt contains the literal substring `[EXCERPT 2/3 — chars ` (opening of middle marker; the full marker includes computed m0/m1 values).
  3. Prompt contains the literal substring `[EXCERPT 3/3 — chars ` (opening of tail marker).
  4. Prompt contains the preface sentence: `The following are three excerpts from a larger document. Treat them as non-contiguous samples of the same document, not as a single continuous passage.`.
  5. Prompt contains the plural header `**Document excerpts:**` and does NOT contain the singular `**Document text:**` (long-doc path uses the plural wording per D-05).
  6. Prompt contains all three sentinel phrases from the fixture: `PARTY_SENTINEL_HEAD`, `OBLIGATION_SENTINEL_MIDDLE`, `TERMINATION_SENTINEL_TAIL`.
  7. Prompt contains `Synthetic long contract domain` (domain description interpolated).
  Second assertion block (short-doc path): Call `build_schema_discovery_prompt("Sample lease text here...", "Real estate lease agreements")` (24-char input). Assert prompt CONTAINS the singular `**Document text:**` header, CONTAINS `Sample lease text here...` verbatim, and does NOT contain `[EXCERPT` or `three excerpts from a larger document`. This pins the short-doc backward-compat shape (D-02).
- **Pass criteria:** All 7 long-doc assertions hold; all 3 short-doc assertions hold; no exceptions.
- **Dependency:** Plan 16-02 Task 1 fixture `tests/fixtures/wizard_sample_window/long_contract.txt` exists. Until then this test FAILS with `FileNotFoundError` — that is the expected RED state for Plan 16-01, flipped to GREEN by Plan 16-02 Task 1.

### FT-016: Long-doc Pass-1 prompt contains all 3 sentinels + all 3 excerpt markers (e2e)
- **Traces to:** FIDL-05 (D-10, D-11)
- **Test:** Read `tests/fixtures/wizard_sample_window/long_contract.txt` (60200-char fixture with sentinels at head/middle/tail). Call `build_schema_discovery_prompt(fixture_text, "Synthetic long contract domain for Phase 16 FT-016")`. Assert the rendered prompt contains exactly 1 occurrence each of `PARTY_SENTINEL_HEAD`, `OBLIGATION_SENTINEL_MIDDLE`, `TERMINATION_SENTINEL_TAIL`; the exact literal markers `[EXCERPT 1/3 — chars 0 to 4000 (head)]`, `[EXCERPT 2/3 — chars 28100 to 32100 (middle)]`, `[EXCERPT 3/3 — chars 56200 to 60200 (tail)]`; the plural header `**Document excerpts:**`; and the preface `The following are three excerpts from a larger document.`. Assert the prompt does NOT contain `**Document text:**`.
- **Pass criteria:** All 10 substring assertions hold; sentinel counts are exactly 1.
- **Dependency:** Fixture present (created by Plan 16-02 Task 1).

### FT-017: Short-doc Pass-1 prompt is strict superset of pre-Phase-16 shape (D-12 regression gate)
- **Traces to:** FIDL-05 (D-12)
- **Test:** For each Phase-8 wizard fixture (`sample_lease_1.txt`, `sample_lease_2.txt`, `sample_lease_3.txt` — all ~1.3K chars, flow through the short-doc branch), call `build_schema_discovery_prompt(text, "Real estate lease agreements")`. Assert: (a) full `text` appears verbatim in the prompt; (b) all 8 structural substrings (task name, domain description interpolation, singular header, instructions, entity-type count directive, SCREAMING_SNAKE_CASE mention, JSON format header, return-only directive) are present; (c) none of `[EXCERPT `, `three excerpts from a larger document`, `**Document excerpts:**` leak in.
- **Pass criteria:** All three fixtures pass all three assertion families.
- **Dependency:** Phase-8 wizard fixtures (already committed in `tests/fixtures/wizard/`).

---

## Phase 17 — Domain Awareness in Consumers (FIDL-06)

### UT-044: cmd_build persists domain into graph_data.json metadata
- **Traces to:** FIDL-06 (D-01, D-02, D-10)
- **Test:** Monkeypatch `core.run_sift._import_sift` to return a stub `run_build` that writes a minimal valid `graph_data.json` (with `metadata` dict containing `created_at`, `updated_at`, `entity_count`, `relation_count`) and a stub `load_domain`. Call `cmd_build(tmp_output_dir, domain_name="contracts")`. Read `graph_data.json` and assert `metadata["domain"] == "contracts"`. Also assert all pre-existing metadata keys (`created_at`, `updated_at`, `entity_count`, `relation_count`) are preserved byte-identically (D-02 additive guarantee). Then call `cmd_build(tmp_output_dir2, domain_name=None)` and assert `metadata["domain"] is None` (explicit None → None in file, not the string `"None"`).
- **Pass criteria:** graph_data.json.metadata.domain equals the passed domain_name for both "contracts" and None; all other metadata keys unchanged.
- **Dependency:** None — uses a stub run_build via monkeypatch so sift-kg's real extraction pipeline is not invoked.

### UT-045: resolve_domain honors explicit > metadata > fallback precedence
- **Traces to:** FIDL-06 (D-03, D-07, D-08, D-09, D-11)
- **Test:** Three sub-assertions in a single parametrized or straight-line test:
  1. **Explicit wins over metadata** (D-09): Write a stub `graph_data.json` with `metadata.domain = "contracts"` into tmp_output_dir. Call `resolve_domain(tmp_output_dir, explicit_domain="drug-discovery")`. Assert the return is `("drug-discovery", "explicit")`.
  2. **Metadata used when no explicit** (D-03 happy path): Same tmp_output_dir. Call `resolve_domain(tmp_output_dir, explicit_domain=None)`. Assert return is `("contracts", "metadata")`.
  3. **Fallback on missing metadata.domain** (D-08 legacy): Write a second stub `graph_data.json` with metadata lacking the `domain` key. Call `resolve_domain(tmp2, explicit_domain=None)`. Assert return is `(None, "fallback")` AND that a warning was emitted (capture via `capsys` or `caplog` — match the substring `graph_data.json` and `domain`).
  4. **Fallback on absent graph_data.json** (extra robustness): Call `resolve_domain(empty_tmpdir, explicit_domain=None)`. Assert return is `(None, "fallback")` — no warning required for this branch since the missing-graph case is also covered by the launcher's existing "Warning: No graph_data.json found" path.
- **Pass criteria:** All four branches return the expected (resolved_domain, source) tuple; branch 3 emits a warning to stderr or log.
- **Dependency:** None — pure stub JSON, no sift-kg.

### UT-046: build_system_prompt reads analysis_patterns from template with fallback-plus-warning
- **Traces to:** FIDL-06 (D-06)
- **Test:** Four branches (see tests/test_unit.py::test_build_system_prompt_loads_analysis_patterns):
  1. Contracts template → cross-references section uses "CROSS-CONTRACT REFERENCES"
  2. Drug-discovery template → same section uses "CROSS-STUDY REFERENCES"
  3. Legacy template with no analysis_patterns → falls back to "CROSS-CONTRACT REFERENCES" AND emits a one-shot stderr warning mentioning `analysis_patterns`
  4. Claims layer with no cross_references → section is omitted entirely regardless of template.
- **Pass criteria:** All four branches produce the expected prompt substring. Warning is emitted exactly in branch 3.
- **Dependency:** None — uses a minimal _StubData class; no sift-kg, no FastAPI.

### FT-018: End-to-end domain auto-detection through /api/template
- **Traces to:** FIDL-06 (D-03, D-07, D-08, D-09, D-13)
- **Test:** Four sub-tests (all in tests/test_workbench.py):
  1. `test_ft018_domain_autodetect_through_api_contracts`: build stub graph_data.json with metadata.domain="contracts"; create_app(out, domain=None); GET /api/template; assert title == "Sample Contract Analysis Workbench" AND analysis_patterns.cross_references_heading == "CROSS-CONTRACT REFERENCES".
  2. `test_ft018_domain_autodetect_through_api_drug_discovery`: same pattern with metadata.domain="drug-discovery"; assert "Drug Discovery" in title AND analysis_patterns.cross_references_heading == "CROSS-STUDY REFERENCES".
  3. `test_ft018_explicit_beats_metadata`: metadata.domain="contracts" + create_app(out, domain="drug-discovery") → title reflects drug-discovery (D-09).
  4. `test_ft018_legacy_graph_no_metadata_domain`: metadata.domain is null → title is generic "Knowledge Graph Explorer" (D-08 fallback).
- **Pass criteria:** All four sub-tests pass; existing /api/template endpoint behavior preserved (D-14 — no regression on test_template_api_endpoint or test_template_api_generic).
- **Dependency:** FastAPI TestClient (already used by other tests in test_workbench.py), no sift-kg, no external LLM.

---

## 4. Traceability Matrix

| Requirement | Domain Spec Section | Entity Types Tested | Relation Types Tested | Test Corpus |
|---|---|---|---|---|
| UT-001 | 3 | All 17 | All 30 | N/A (schema test) |
| UT-002–005 | 16.6 | CHEMICAL_STRUCTURE, CLINICAL_TRIAL | N/A | Synthetic text |
| UT-006–008 | 16.7 | CHEMICAL_STRUCTURE | HAS_STRUCTURE | Synthetic SMILES |
| UT-009–011 | 16.7 | NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE | HAS_SEQUENCE | Synthetic sequences |
| UT-012–014 | Design spec 3, 8, 16.9 | All | All | Synthetic extraction |
| UT-015 | Bug fix | All | All | Synthetic extraction |
| UT-016 | label_communities.py | N/A | N/A | 01_picalm_alzheimers |
| FT-001–008 | Design spec 9 | All | All | PubMed abstracts |
| UAT-101–104 | 3, 4 | GENE, PROTEIN, DISEASE, PATHWAY | IMPLICATED_IN, PARTICIPATES_IN | 01_picalm_alzheimers |
| UAT-201–205 | 3, 4 | COMPOUND, GENE, CLINICAL_TRIAL, MOA | TARGETS, INHIBITS, EVALUATED_IN, CONFERS_RESISTANCE_TO, COMBINED_WITH, HAS_MECHANISM | 02_kras_g12c_landscape |
| UAT-301–303 | 3, 4 | COMPOUND, DISEASE, PROTEIN, MOA | INDICATED_FOR, HAS_MECHANISM, TARGETS | 03_rare_disease |
| UAT-401–404 | 3, 4 | COMPOUND, CLINICAL_TRIAL, ADVERSE_EVENT, BIOMARKER | COMBINED_WITH, EVALUATED_IN, CAUSES, PREDICTS_RESPONSE_TO | 04_immunooncology |
| UAT-501–503 | 3, 4 | COMPOUND, PROTEIN, DISEASE, CLINICAL_TRIAL | HAS_MECHANISM, TARGETS, INHIBITS, EVALUATED_IN, INDICATED_FOR | 05_cardiovascular |
| UT-039 | FIDL-04 (D-01, D-09) | N/A (discovery layer) | N/A | Synthetic tmpdir |
| UT-040 | FIDL-04 (D-04) | N/A | N/A | Synthetic tmpdir |
| UT-041 | FIDL-04 (D-02) | N/A | N/A | Synthetic tmpdir |
| FT-013 | FIDL-04 (D-01, D-09) | N/A (ingest-layer) | N/A | tests/fixtures/format_parity/sample.md |
| FT-014 | FIDL-04 (D-06, D-07) | N/A | N/A | tests/fixtures/format_parity/corrupted.pptx |
| FT-015 | FIDL-04 (D-13), Phase 14 D-14 | All (existing V2 scenarios) | All | tests/baselines/v2/expected.json |
| UT-042 | FIDL-05 (D-01, D-02, D-03) | N/A (prompt-builder layer) | N/A | Inline synthetic strings |
| UT-043 | FIDL-05 (D-04, D-05, D-10, D-11) | N/A | N/A | tests/fixtures/wizard_sample_window/long_contract.txt |
| FT-016 | FIDL-05 (D-10, D-11) | N/A (prompt-layer) | N/A | tests/fixtures/wizard_sample_window/long_contract.txt |
| FT-017 | FIDL-05 (D-12) | N/A | N/A | tests/fixtures/wizard/sample_lease_{1,2,3}.txt |
| UT-044 | FIDL-06 (D-01, D-02, D-10) | N/A (metadata write) | N/A | Stub graph_data.json |
| UT-045 | FIDL-06 (D-03, D-07, D-08, D-09, D-11) | N/A (resolver) | N/A | Stub graph_data.json |
| UT-046 | FIDL-06 (D-06) | N/A (system prompt) | N/A | Stub WorkbenchData |
| FT-018 | FIDL-06 (D-03, D-07, D-08, D-09, D-13) | N/A (e2e) | N/A | Stub graph_data.json |
