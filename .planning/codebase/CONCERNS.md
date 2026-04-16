# Codebase Concerns

**Analysis Date:** 2026-03-29

## Tech Debt

### Missing Dependency Management System

**Issue:** No `pyproject.toml`, `requirements.txt`, or `setup.py` found at project root. Python validation scripts require optional dependencies (RDKit, Biopython) but installation mechanism is undocumented.

**Files:**
- `skills/drug-discovery-extraction/validation-scripts/validate_smiles.py` — requires RDKit
- `skills/drug-discovery-extraction/validation-scripts/validate_sequences.py` — requires Biopython
- `scripts/validate_molecules.py` — orchestrates both validators

**Impact:**
- No automated CI/CD dependency enforcement
- Graceful degradation exists (functions return `unvalidated` state) but this is silent — errors hidden in validation stats
- Cannot specify version pins; external libraries may introduce breaking changes
- New contributors have no documented installation instructions

**Fix approach:**
1. Create `pyproject.toml` with optional dependency groups: `[project.optional-dependencies]` for `dev = ["rdkit>=2023.9", "biopython>=1.83"]`
2. Document installation: `uv pip install -e ".[dev]"` or `uv sync`
3. Update CI/CD to verify dependencies are available during test runs
4. Consider switching from graceful degradation to explicit validation: fail fast if validator is called without dependencies installed

---

### Pattern Matching False Positives on Non-Molecular Text

**Issue:** Sequence pattern matching is overly permissive. Amino acid regex `\b[ACDEFGHIKLMNPQRSTVWY]{10,}\b` matches any 10+ character word using those letters, not just peptides.

**Files:** `skills/drug-discovery-extraction/validation-scripts/scan_patterns.py` (lines 77-79)

**Evidence from memory:**
- Scenario 4: "RELATIVITY" (10 characters, all valid amino acid codes) matched as `PEPTIDE_SEQUENCE` despite being a clinical trial name
- Scenario 6: 114 false-positive SMILES matches from parenthesized text like "(PD-1-blocking antibody)"

**Current mitigation:** RDKit validation filters 114 SMILES false positives in post-processing. But sequence false positives slip through as "valid" hits.

**Fix approach:**
1. Raise minimum sequence length from 10 to 15 characters for amino acids
2. Add contextual filters: skip matches in quoted passages, bracket notation (`[RELATIVITY]`), or surrounded by clinical trial keywords
3. Cross-reference against known clinical trial registry (e.g., reject if match == known trial acronym)
4. Document known triggers in `scan_patterns.py` comments

**Priority:** Medium — affects data quality but caught during manual review (as per S4 manual validation)

---

### Incomplete Manual Validation Workflow

**Issue:** All 6 scenarios have validation status "PENDING MANUAL REVIEW" with no clear ownership, deadline, or sign-off criteria.

**Files:**
- `tests/VALIDATION_RESULTS.md` — master sign-off document with empty reviewer/date fields
- `tests/corpora/*/output/VALIDATION_RESULTS.md` — per-scenario docs also pending

**Impact:**
- No way to track which entities/relations have been verified vs. flagged
- Validation findings (e.g., S4 RELATIVITY peptide) recorded in memory but not applied to test outputs
- Cannot gate release/publication on completion of validation
- Downstream processes (paper figures, demos) reference unvalidated extractions

**Fix approach:**
1. Create validation sign-off template with per-entity/relation flags: `V` (verified), `F` (flagged), `M` (missing)
2. Track completion metrics: "32/33 entities verified" → enable automated checks
3. Establish review schedule: 1 scenario/week minimum pace
4. Document how to apply flags: update VALIDATION_RESULTS.md, re-run validation scripts, commit findings
5. Add GitHub issue template for validation blockers

**Priority:** High — blocks reproducibility and publication credibility

---

### Regex Pattern Ordering Assumptions

**Issue:** Pattern matching relies on ordering: more specific patterns must come before less specific ones to prevent overlap misclassification.

**Files:** `skills/drug-discovery-extraction/validation-scripts/scan_patterns.py` (lines 22-93)

**Current order (correct):**
1. InChIKey (very specific: `[A-Z]{14}-[A-Z]{10}-[A-Z]`)
2. InChI (specific: `InChI=1S/...`)
3. CAS numbers (specific: `\d{2,7}-\d{2}-\d`)
4. SMILES with prefix (specific: `SMILES:`)
5. NCT, Patent IDs
6. DNA/RNA (length 15+)
7. Amino acid (length 10+, loose)
8. SMILES standalone (broad, last)

**Risk:** If patterns are reordered without testing, broad patterns may consume narrow ones. E.g., if SMILES_STANDALONE moved before SMILES, the latter would never match.

**Fix approach:**
1. Add docstring comment above PATTERNS defining priority rationale
2. Create unit test for pattern ordering: verify that test cases match in expected order
3. Add test case: "SMILES:CC(=O)O should match SMILES not SMILES_STANDALONE"
4. Document in `scan_patterns.py`: "Do not reorder without running tests"

**Priority:** Low-Medium — low probability of reorder, but high consequence if it happens

---

## Known Bugs

### S4 RELATIVITY False-Positive Peptide

**Symptoms:** Entity "RELATIVITY" appears in Scenario 4 extraction with `entity_type: PEPTIDE_SEQUENCE` and a `HAS_SEQUENCE` relation linking it to a parent entity. This is incorrect — RELATIVITY is a clinical trial name.

**Files:**
- `tests/corpora/04_immunooncology/output/extraction_*.json`
- `tests/corpora/04_immunooncology/output/VALIDATION_RESULTS.md`

**Trigger:** The regex minimum length threshold (10 characters) matches the sequence. "RELATIVITY" = R-E-L-A-T-I-V-I-T-Y, all valid amino acid codes.

**Workaround:** Manual flagging documented in memory (`project_s4_manual_review.md`). Mark both RELATIVITY entity and its HAS_SEQUENCE relation as `F` (flagged) during review.

**Root cause:** See "Pattern Matching False Positives" section above.

---

### False-Positive SMILES in Parenthesized Clinical Text

**Symptoms:** 114 SMILES validation entries marked "invalid" from text like "(PD-1-blocking antibody)". These are correctly rejected by RDKit post-validation but inflate the invalid count and waste processing time.

**Files:**
- `tests/corpora/06_glp1_landscape/output/validation/results.json` — 114 false SMILES attempts
- `scripts/validate_molecules.py` — processes all matches without pre-filtering

**Trigger:** SMILES_STANDALONE regex matches the `-` and `1` in "PD-1-blocking" as `P`, `D`, `-`, `1`. RDKit then rejects it.

**Workaround:** None. The post-validation rejection is the intended defense. Consider it expected behavior for now.

**Fix approach:** Pre-filter before RDKit validation — skip matches inside parentheses or adjacent to English words (`-blocking`, `-targeting`).

**Priority:** Low — validation already catches these, but pre-filtering would improve performance

---

## Security Considerations

### No Explicit Environment Variable Validation

**Issue:** Scripts import external APIs (SerpAPI for Scholar/Patents, PubMed API) but don't validate that required environment variables are set before execution.

**Files:**
- `tests/corpora/06_glp1_landscape/scholar_rerun.py`
- `tests/corpora/06_glp1_landscape/patents_rerun.py`
- `tests/corpora/06_glp1_landscape/fetch_by_topic.py`

**Risk:** Missing API keys silently degrade to no-op or partial runs. Errors appear downstream in corpus assembly, not at the source where they're debuggable.

**Current mitigation:** Scripts exist in test directory only, not production code. User instructions document API key setup.

**Fix approach:**
1. Add `_check_env_vars()` function at module level in each script
2. Call before any API operations: `_check_env_vars(["SERPAPI_API_KEY", "PUBMED_API_EMAIL"])`
3. Raise `EnvironmentError` with clear instruction: "Set SERPAPI_API_KEY before running"
4. Document in script docstrings which env vars are required

**Priority:** Medium — affects reliability during corpus assembly, not data extraction quality

---

### Subprocess Execution Without Input Validation

**Issue:** Phase 2 name resolution plan (pending implementation) proposes calling OPSIN JAR via subprocess: `java -jar opsin.jar -osmi`. No input sanitization mentioned.

**Files:**
- `.claude/plans/goofy-wibbling-feigenbaum.md` (Phase 2 plan, not yet implemented)
- Proposed location: `skills/drug-discovery-extraction/validation-scripts/resolve_names.py` (to be created)

**Risk:** If IUPAC names are passed directly to subprocess without validation, malicious input could execute arbitrary commands.

**Current status:** Not yet implemented. This is a design-phase concern.

**Fix approach:**
1. Validate IUPAC name format before subprocess call: alphanumeric + hyphens, no shell metacharacters
2. Use `subprocess.run()` with `shell=False` (list-based args, never string)
3. Set `timeout=5` to prevent hanging on malformed input
4. Capture stderr separately: `subprocess.run(..., capture_output=True, text=True)`
5. Log all subprocess invocations with input/output for audit

**Priority:** High — should be enforced before Phase 2 implementation begins

---

## Performance Bottlenecks

### Sequential Graph Building on Single Thread

**Issue:** `scripts/run_sift.py` builds knowledge graph from extraction JSONs in sequence. No parallelization mentioned.

**Files:** `scripts/run_sift.py` (line count: 130)

**Problem:** With 6 scenarios × 15-34 documents each = 100+ documents, sequential processing is slow. Scenario 6 (GLP-1) has 34 documents — each extraction → validation → enrichment → graph build step runs serially.

**Current capacity:** Anecdotal note in docs: "ingestion takes ~10-15 min" (from `docs/demo/demo-script.md`).

**Improvement path:**
1. Parallelize extraction-level processing: `concurrent.futures.ThreadPoolExecutor` for document extraction batches
2. Use thread pool for validation: `validate_molecules.py` already processes JSON files in loop; wrap in `ThreadPoolExecutor`
3. Benchmark: measure CPU vs I/O bottleneck (reading JSONs, RDKit validation, writing enriched JSONs)
4. Consider async/await for network calls in Phase 2 (SerpAPI, PubChem lookups)

**Priority:** Low-Medium — 10-15 min is acceptable for research; only problematic if used in interactive demos

---

### InChIKey Deduplication Without Indexing

**Issue:** `validate_molecules.py` builds `inchikey_map` by scanning all results, then iterates to find duplicates. No B-tree or hash-based index for lookup.

**Files:** `scripts/validate_molecules.py` (lines 399-462)

**Current approach:**
```python
inchikey_map: dict[str, list[dict]] = defaultdict(list)  # O(1) add
# Later:
dedup_report = build_dedup_report(dict(inchikey_map), output_dir)  # O(n) scan
```

**Scalability:** For Scenario 6 with 100+ SMILES matches, this is fine. For future Phase 2 with PubChem/ChEMBL cross-reference (potentially 1000+ molecules), scanning becomes slow.

**Improvement path:**
1. Current dict approach is already O(1) for dedup detection — adequate for now
2. Add indexing only if dedup queries become frequent (e.g., real-time lookup during enrichment)
3. Consider SQLite for future scenarios: `CREATE INDEX idx_inchikey ON molecules(inchikey)`

**Priority:** Low — current approach is sufficient; defer until Scenario 6 scales

---

## Fragile Areas

### Community Labeling Heuristics

**Issue:** `scripts/label_communities.py` uses hard-coded entity type ratios (>50% genes = "Disease Risk Loci") to label graph communities. If entity composition changes, labels become nonsensical.

**Files:** `scripts/label_communities.py` (lines 59-70 heuristic definitions)

**Example fragility:**
- Threshold: >50% genes → "Disease Risk Loci (N genes)"
- If a community has 49% genes + 51% proteins → labeled as "GENE Protein Interactions" (wrong)
- Manual review reveals semantic mismatch but script doesn't detect it

**Safe modification:**
1. Never change thresholds without re-running all 6 scenarios and validating output labels are still sensible
2. Add unit test: test cases with known entity compositions → verify label outputs match expected patterns
3. Add warning to script: "Heuristics tuned to epistract domain; may not generalize to other KGs"
4. Consider adding confidence score to labels: `{label: "...", confidence: 0.75}` when heuristics are uncertain

**Test coverage:** Community labels validated manually in FINDINGS.md; automated regression tests missing.

**Priority:** Medium — labels must match scientist expectation; false labels undermine graph credibility

---

### LLM Agent Output Validation in `build_extraction.py`

**Issue:** Extraction agent prompt specifies JSON schema, but downstream script only adds defensive field normalization (`type` → `entity_type`). No validation of array lengths, entity count bounds, or relation validity.

**Files:** `scripts/build_extraction.py` (line count: 59 — very brief)

**Risk:**
- Agent could return 1000+ entities per document; no upper bound check
- Relations could reference non-existent entity IDs; no referential integrity
- Confidence scores could be out of range [0,1]; accepted as-is
- Missing type declarations in JSON arrays; type-checking happens at graph-build time (too late)

**Current defense:** Two-layer approach (prompt + normalization) works because agents are well-behaved in practice. But no explicit validation.

**Safe modification:**
1. Add `_validate_extraction()` in `build_extraction.py` before writing JSON:
   - Check entity count < 500 per document
   - Check relation source/target exist in entity list
   - Check confidence scores in [0,1]
   - Check entity_type/relation_type against schema enum
2. Log validation warnings; raise exception if critical schema violations found
3. Add unit test with intentionally malformed extraction JSON; verify validation catches it

**Priority:** Medium — prevents silent data corruption if agent prompt degrades

---

### Hard-Coded Graph Build Path in `run_sift.py`

**Issue:** Graph building assumes fixed directory structure: `<output_dir>/extractions/`, `<output_dir>/validation/`, etc. If user moves directories, build fails with cryptic errors.

**Files:** `scripts/run_sift.py`

**Risk:** No path validation or helpful error messages. Users new to the codebase might reorganize directories and break the pipeline.

**Safe modification:**
1. Add path validation at start of script:
   ```python
   def _validate_output_dir(output_dir: Path) -> None:
       required_dirs = ["extractions", "validation"]
       for d in required_dirs:
           if not (output_dir / d).is_dir():
               raise FileNotFoundError(f"{output_dir / d} not found. Run extraction first.")
   ```
2. Print helpful error message: "Expected directory structure: {output_dir}/extractions/ and {output_dir}/validation/"
3. Document expected structure in script docstring

**Priority:** Low — affects user experience; not a functional bug

---

## Test Coverage Gaps

### Epistemic Analysis Script Untested in CI

**Issue:** `scripts/label_epistemic.py` (380 lines) has complex contradiction detection and hypothesis clustering logic, but no automated tests.

**Files:**
- `scripts/label_epistemic.py` — untested
- `tests/test_unit.py` — unit tests exist but don't cover epistemic analysis

**Untested functions:**
- `detect_contradictions()` (lines 95-160) — logic for finding opposing evidence is complex
- `group_hypotheses()` (lines 167-251) — BFS clustering is easy to break with graph mutations
- `classify_epistemic_status()` (lines 66-88) — pattern matching on hedging language requires exact regex validation

**Risk:** Changes to epistemic classification rules could silently produce incorrect `claims_layer.json` output.

**Coverage path:**
1. Add unit tests for `classify_epistemic_status()` with edge cases:
   - Empty evidence string
   - Multiple hedging patterns in one evidence
   - Patent vs. paper vs. preprint source document types
2. Add fixture: mock `links` list with known contradictions; verify `detect_contradictions()` finds them
3. Add regression test: run against all 6 scenarios' `graph_data.json`; verify `claims_layer.json` output matches prior versions

**Priority:** High — epistemic analysis is novel methodology; correctness critical for paper

---

### Sequence Validation Edge Cases Not Tested

**Issue:** `validate_sequences.py` has logic for DNA→RNA disambiguation (lines 49-59) and translation (lines 122-126), but test coverage in `test_unit.py` may be incomplete.

**Files:**
- `skills/drug-discovery-extraction/validation-scripts/validate_sequences.py` — implementation
- `tests/test_unit.py` — some tests present but gaps unknown without reading

**Untested scenarios:**
- Ambiguous sequences (pure AGCN, no T or U) — should default to DNA; verify this
- Stop codon handling in protein validation
- Translation failures (non-divisible-by-3 DNA) — exception handling correctness
- Biopython import failure — graceful degradation path

**Coverage path:**
1. Add parametrized test: `@pytest.mark.parametrize("seq,expected_type", [("AGCN", "DNA"), ("AUGC", "RNA"), ...])`
2. Test exception handling: mock Biopython import failure; verify function returns `{valid: None, error: "..."}`
3. Test with real biologicial sequences from reference databases (e.g., NCBI)

**Priority:** Medium — sequence validation is less critical than SMILES, but still impacts data integrity

---

### Scenario 6 Corpus Assembly Scripts Highly Coupled

**Issue:** Corpus assembly for Scenario 6 (GLP-1) involves multiple scripts that depend on exact output formats and file ordering:
- `fetch_by_topic.py` → produces scholar/patent JSONs
- `scholar_rerun.py` / `patents_rerun.py` → re-runs specific sources
- `replace_scholar.py` / `enrich_scholar.py` → mutate existing corpus
- `assemble_corpus.py` → final assembly

**Files:**
- `tests/corpora/06_glp1_landscape/` — 6 scripts with implicit dependencies

**Risk:** Changing output format of any script breaks downstream consumers. No schema validation between scripts.

**Safe modification:**
1. Document expected JSON schema for each pipeline stage (scholar intermediate format, patents format, etc.)
2. Add optional validation flag: `--validate-schema` to check schema before consuming
3. Add unit test: run each script in isolation; verify output matches schema

**Priority:** Low-Medium — low probability of modification, but helpful for future contributors

---

## Scaling Limits

### Graph Visualization Limited to ~300 Nodes

**Issue:** Vis.js graph visualization (used in `graph.html`) becomes slow/unresponsive above ~300 nodes. Scenario 6 has 206 nodes (manageable), but Scenario 1 has 149 nodes (also fine).

**Current capacity:** All 6 scenarios fit comfortably in vis.js. Future scenarios with >400 nodes would require intervention.

**Scaling path:**
1. For >300 nodes: offer "clustered view" mode in graph.html
2. Implement node/link filtering UI: "show only GENEs", "show high-confidence links only"
3. Consider WebGL-based visualization (Babylon.js, Three.js) for 1000+ node graphs
4. Add performance warning in `graph.html`: "Graph has N nodes; interaction may be slow"

**Priority:** Low — only relevant for future scenarios; current scale is manageable

---

### Neo4j Phase 2 Not Scoped

**Issue:** Phase 2 plans mention "Neo4j + Vector RAG" (from TODO item) but no implementation details exist. No scope for:
- Which node/relationship types map to which Neo4j labels/types
- How to handle graph evolution (schema updates, re-indexing)
- Query language (Cypher) examples
- Performance targets (query latency, throughput)

**Files:** `docs/plans/2026-03-16-epistract-TODO.md` (lines 70-75)

**Risk:** When Phase 2 begins, decisions about graph normalization will be revisited. Current SMILES/Sequence enrichment may not map cleanly to Neo4j properties.

**Scoping path:**
1. Create design doc: `docs/neo4j-design.md` with:
   - Node/relationship mapping from current JSON schema
   - Indexing strategy for InChIKey lookup, entity name search
   - Query examples for common scientist workflows
   - Performance requirements (p99 latency, throughput)
2. Create Cypher template queries: entity lookup, path traversal, contradiction search
3. Add acceptance test: load one scenario's `graph_data.json` into Neo4j; run 5 query templates; verify correctness

**Priority:** Medium — Phase 2 is future work, but design decisions should be made early

---

## Missing Critical Features

### Chemical Name Resolution (Phase 2) Not Implemented

**Issue:** Epistract currently captures SMILES only if they appear literally in source text. Most papers mention drugs by name (e.g., "pembrolizumab") without SMILES. Phase 2 name resolution would fill this gap, but implementation is blocked pending user review.

**Files:**
- Plan: `.claude/plans/goofy-wibbling-feigenbaum.md` (Phase 2 cascade design)
- TODO: `docs/plans/2026-03-16-epistract-TODO.md` (lines 25-43)

**Impact:** Current extractions are chemically incomplete. Dedup and enrichment workflows can't work without canonical molecular identifiers.

**Proposed solution (from plan):**
1. Tier 0: Bundled drug cache (ChEMBL, ~2000 drugs)
2. Tier 1: OPSIN JAR (IUPAC → SMILES, offline)
3. Tier 2: PubChem PUG REST (common names, optional)
4. Tier 3: LLM agent retry on parse errors

**Blockers:** Plan written; awaiting user approval before implementation.

**Priority:** High — blocks Phase 2 progress

---

### Graph-Grounded Conversational RAG (/epistract-ask) Not Scoped

**Issue:** TODO lists `/epistract-ask` command (lines 50-53) for graph-grounded QA, but no implementation details:
- How does user query map to graph traversals?
- How are answers grounded (cite which nodes/links)?
- How is session state managed (graph stays loaded)?
- Cross-session persistence?

**Files:** `docs/plans/2026-03-16-epistract-TODO.md` (lines 50-53)

**Risk:** If implemented without clear design, could produce hallucinated answers or lose grounding.

**Design path:**
1. Create `/epistract-ask` command spec: `commands/ask.md` with examples
2. Design query → graph traversal logic: natural language parsing, entity linking, relation traversal
3. Design answer generation: template-based to ensure grounding
4. Add evaluation metric: "what % of answers cite at least one graph node/link?"

**Priority:** Medium — future feature, but should be designed before coding

---

## Dependencies at Risk

### RDKit Dependency Fragile

**Issue:** RDKit is optional but recommended. If RDKit version changes (major release), SMILES validation may produce different results (canonicalization, inchi generation).

**Files:**
- `skills/drug-discovery-extraction/validation-scripts/validate_smiles.py` — no version pin
- Fallback: returns `{valid: None, error: "RDKit not installed"}`

**Risk:** Scenario reproducibility: running the same extraction with RDKit 2023.9 vs. 2024.3 could produce different canonical SMILES, breaking dedup.

**Mitigation approach:**
1. Pin RDKit version in dependency manifest (once created): `rdkit==2023.9.1`
2. Document version requirement in DEVELOPER.md: "Validated with RDKit 2023.9.1; other versions may produce different canonicalization"
3. Add CI test: verify RDKit version matches pinned version before validation runs
4. Create migration guide: if RDKit is upgraded, re-run validation pipeline and compare InChIKey output

**Priority:** Medium — only impacts reproducibility if RDKit upgrades occur

---

### SerpAPI Rate Limits and Cost Not Managed

**Issue:** Phase 2 corpus assembly (Scenario 6) uses SerpAPI for Scholar and Patents search. No rate limiting, cost tracking, or fallback documented.

**Files:**
- `tests/corpora/06_glp1_landscape/scholar_rerun.py`
- `tests/corpora/06_glp1_landscape/patents_rerun.py`

**Risk:** If script crashes mid-run, user doesn't know how many credits were consumed. Retry logic could cause duplicate API calls and wasted budget.

**Mitigation approach:**
1. Add budget tracking: log API call count, estimated cost before/after
2. Add idempotency: skip documents that were already fetched (check output JSON timestamps)
3. Add dry-run mode: `--dry-run` to estimate API calls without executing
4. Document cost: "Scenario 6 corpus assembly costs ~$X in SerpAPI credits"

**Priority:** Low-Medium — affects research budget, not data quality

---

*Concerns audit: 2026-03-29*
