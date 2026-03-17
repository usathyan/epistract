# Epistract Testing Findings & Engineering Insights

This document captures the engineering findings, bugs discovered, and architectural insights from end-to-end testing of the epistract pipeline across five drug discovery scenarios. Each finding is traced to the scenario that surfaced it, the root cause analysis, the fix applied, and the systemic lesson.

This is a living document — updated as each scenario is run.

---

## Summary of Findings

| # | Finding | Severity | Scenario | Root Cause | Fix | Systemic Lesson |
|---|---|---|---|---|---|---|
| F-001 | [entity_type field naming](#f-001-entitytype-field-naming-mismatch) | Critical | 1 | Agent prompt lacked JSON schema example | Two-layer fix: prompt + defensive normalization | LLM agents require explicit output schemas, not just field lists |
| F-002 | [Unlabeled communities](#f-002-unlabeled-communities) | Medium | 1 | sift-kg produces numbered labels only | New `label_communities.py` with heuristic labeling | Graph structure alone is insufficient for scientist consumption — semantics must be surfaced |
| F-003 | [Version number cascade](#f-003-version-number-cascade-across-plugin-system) | Critical | 2 | Version `1.0.0` hardcoded across 6 files | Synchronized all version references + wildcard permissions | Plugin version must be treated as a single source of truth with automated propagation |
| F-004 | [Output files gitignored](#f-004-output-files-unreachable-on-github) | Medium | 1 | Broad `output/` gitignore pattern | Scoped to `/output/` + explicit allow for test corpus | Test artifacts must be committed for reproducibility and review |
| F-005 | [Graph screenshot not rendering](#f-005-graph-screenshot-not-rendering-in-readme) | Low | 1 | Image referenced from gitignored directory | Moved to tracked `tests/scenarios/screenshots/` | Documentation images must be in tracked, version-controlled locations |
| F-006 | [graph.html not interactive on GitHub](#f-006-graphhtml-not-interactive-on-github) | Low | 1 | GitHub doesn't serve HTML | Added "(clone repo and open locally in browser)" | Documentation must set correct expectations for hosted vs local artifacts |
| F-007 | [Schema generalization validated](#f-007-schema-generalization-across-domains) | Positive | 1→2 | N/A | N/A | Same 17-type, 30-relation schema handles both genetics-heavy and oncology-heavy corpora |

---

## Detailed Findings

### F-001: entity_type Field Naming Mismatch

**Severity:** Critical — caused sift-kg build to silently skip documents
**Discovered in:** Scenario 1 (PICALM / Alzheimer's)
**Impact:** 3 of 15 extraction files failed to load during graph building, resulting in incomplete knowledge graphs

**Root cause:** The extractor agent prompt (`agents/extractor.md`) listed entity types and relation types but did not include a concrete JSON example showing the required field names `entity_type` and `relation_type`. LLM agents naturally used `type` as the field name — a reasonable default that happens to be incompatible with sift-kg's Pydantic model (`ExtractedEntity.entity_type`, `ExtractedRelation.relation_type`).

**Why it matters:** This is a class of bug unique to LLM-in-the-loop systems. Traditional APIs enforce schemas through type systems and serialization frameworks. When an LLM is the producer of structured output, the schema must be communicated explicitly in the prompt — field names, nesting structure, and exact types. A list of allowed values is not the same as a concrete example.

**Fix (two-layer defense):**
1. **Prompt layer:** Added explicit JSON example in `agents/extractor.md` with `entity_type` and `relation_type` field names, marked as `**CRITICAL**`
2. **Script layer:** Added `_normalize_fields()` in `scripts/build_extraction.py` that converts `type` → `entity_type`/`relation_type` at write time

**Verification:** Scenario 2 ran with 16 documents — zero field naming errors. The defensive normalization was not triggered, confirming the prompt fix is sufficient. The normalization remains as a safety net.

**Systemic lesson:** In LLM-as-producer systems, always:
- Include concrete JSON examples in agent prompts, not just field name lists
- Add defensive normalization at the consumption boundary
- Monitor for silent data loss (sift-kg logged validation errors but continued)

---

### F-002: Unlabeled Communities

**Severity:** Medium — graph was structurally correct but semantically opaque
**Discovered in:** Scenario 1 (PICALM / Alzheimer's)
**Impact:** Scientists couldn't interpret community meaning without manually inspecting member lists

**Root cause:** sift-kg's Louvain community detection produces numbered labels (`Community 1`, `Community 2`, etc.) with no semantic interpretation. The algorithm identifies structural communities but doesn't characterize them.

**Fix:** Created `scripts/label_communities.py` — a heuristic labeling engine that generates descriptive community names based on member entity composition:
- Gene-dominant clusters (>50% genes, >15 members) → "Disease Risk Loci (N genes)"
- Variant-dominant clusters (>50% variants) → "GENE Genetic Variants"
- Mechanism + cell type → "Mechanism of Action in Cell Type"
- Pathway-driven → "Pathway A / Pathway B"
- Disease + protein → "Disease — Protein1, Protein2"
- Fallback → top 3 entities by type priority

Integrated into `scripts/run_sift.py` build step — runs automatically after every graph construction.

**Validation across scenarios:**
- Scenario 1 (6 communities): "Alzheimer Disease Risk Loci (30 genes)", "Cholesterol Synthesis in Microglia" — biologically meaningful
- Scenario 2 (4 communities): "EGFR Inhibitors / Adavosertib / Panitumumab", "RAS Signaling / RAF/MEK Pathway" — therapeutically meaningful

**Systemic lesson:** Graph algorithms produce structure; human-interpretable semantics require a separate interpretation layer. For scientist-facing tools, this layer is not optional.

---

### F-003: Version Number Cascade Across Plugin System

**Severity:** Critical — silently prevented plugin updates and broke permission rules
**Discovered in:** Scenario 2 (KRAS G12C Landscape)
**Impact:**
1. `marketplace.json` still at `1.0.0` → plugin system reported "already at latest version" even after `plugin.json` was bumped to `1.1.0`
2. `.claude/settings.local.json` had hardcoded path `~/.claude/plugins/cache/epistract/epistract/1.0.0/scripts/setup.sh` → permission rule didn't match new `1.1.0` cache path, causing permission prompts that should have been pre-approved
3. `docs/epistract-plugin-design.md` showed `1.0.0` → misleading documentation

**Root cause:** The plugin version is declared in `plugin.json` but referenced — sometimes literally, sometimes as a path component — in at least 6 other files. There is no automated propagation mechanism. When `plugin.json` was bumped to `1.1.0`, the other references were not updated.

**Fix:**
1. Updated `marketplace.json` version to `1.1.0`
2. Changed `settings.local.json` permission rules to use wildcard globs (`Bash(bash */epistract/*/scripts/setup.sh)`) instead of version-specific paths
3. Updated design doc reference
4. Documented the full update workflow in `DEVELOPER.md`

**Systemic lesson:** Plugin version is a **distributed constant** — it appears in multiple files and in the filesystem cache path. Mitigations:
- Use wildcard patterns in permission rules (never hardcode version in paths)
- Document which files must be updated on version bump
- Consider a version-bump script that updates all references atomically

---

### F-004: Output Files Unreachable on GitHub

**Severity:** Medium — test results were invisible to external reviewers
**Discovered in:** Scenario 1 (PICALM / Alzheimer's)

**Root cause:** The `.gitignore` contained `output/` which matched all directories named `output` at any depth, including `tests/corpora/*/output/`. Test artifacts (graph_data.json, graph.html, extraction JSONs) were never committed.

**Fix:** Changed gitignore from `output/` to `/output/` (root-only) and added explicit allow `!tests/corpora/*/output/`.

**Systemic lesson:** For projects with test artifacts that need to be both reproducible and reviewable, gitignore rules must be scoped precisely. Broad patterns that protect development outputs can inadvertently suppress test evidence.

---

### F-005: Graph Screenshot Not Rendering in README

**Severity:** Low
**Discovered in:** Scenario 1

**Root cause:** README referenced `tests/corpora/01_picalm_alzheimers/output/screenshots/graph_overview.png` — a path inside the previously-gitignored `output/` directory.

**Fix:** Moved screenshots to `tests/scenarios/screenshots/scenario-NN-graph.png` (always tracked).

---

### F-006: graph.html Not Interactive on GitHub

**Severity:** Low
**Discovered in:** Scenario 1

**Root cause:** GitHub renders HTML files as source code, not as interactive web pages. Users clicking the graph.html link see raw HTML.

**Fix:** Added "(clone repo and open locally in browser)" to all graph.html references.

---

### F-007: Schema Generalization Across Domains

**Severity:** Positive finding — confirms design hypothesis
**Discovered in:** Scenario 1 → 2 comparison

The same 17-entity-type, 30-relation-type schema produces meaningful knowledge graphs across fundamentally different drug discovery domains:

| Dimension | Scenario 1 (Neurogenetics) | Scenario 2 (Oncology) | Scenario 3 (Rare Disease) | Scenario 4 (Immuno-Oncology) | Scenario 5 (Cardio/Inflammation) |
|---|---|---|---|---|---|
| Dominant entity types | GENE (48), PROTEIN (21), PHENOTYPE (18) | GENE (20), COMPOUND (11), SEQUENCE_VARIANT (10) | COMPOUND (5), ADVERSE_EVENT (9), BIOMARKER (8), CLINICAL_TRIAL (7) | COMPOUND (30+), PROTEIN (20+), CLINICAL_TRIAL (8), ADVERSE_EVENT (10+) | COMPOUND (5), CLINICAL_TRIAL (8), ADVERSE_EVENT (15+), BIOMARKER (10+) |
| Dominant relation types | IMPLICATED_IN (84), PARTICIPATES_IN (23) | CONFERS_RESISTANCE_TO (26), INHIBITS (10), COMBINED_WITH (9) | CAUSES (10), HAS_MECHANISM (8), EVALUATED_IN (7), DIAGNOSTIC_FOR (4) | INHIBITS (20+), INDICATED_FOR (30+), EVALUATED_IN (16+), CAUSES (10+) | EVALUATED_IN (15+), CAUSES (12+), INHIBITS (8), INDICATED_FOR (8) |
| Community themes | GWAS loci, pathways, cell biology | Drug combinations, resistance, clinical trials | PKU enzyme therapy, gene therapy safety, CNP analog, bone biology | PD-1/CTLA-4/LAG-3 checkpoint axes, HCC microenvironment, combination strategies | HCM/sarcomere biology, TYK2/JAK-STAT psoriasis, cardiac myosin inhibitors |
| Schema coverage (entity types used) | 10 of 17 (59%) | 16 of 17 (94%) | 16 of 17 (94%) | 15 of 17 (88%) | 14 of 17 (82%) |
| Schema coverage (relation types used) | 14 of 30 (47%) | 17 of 30 (57%) | 21 of 30 (70%) | 16 of 30 (53%) | 14 of 30 (47%) |

The five scenarios together exercise 17 of 17 entity types (100%) and 27 of 30 relation types (90%). Scenario 5 validated the schema's ability to cleanly separate two unrelated therapeutic areas (cardiology vs dermatology) within a single corpus — community detection correctly produced distinct clusters with no spurious cross-domain connections. The addition of CONTRAINDICATED_FOR (mavacamten/CYP2C19 inhibitors) brings the cumulative relation type coverage to 90%.

**Systemic lesson:** A domain schema designed for the breadth of drug discovery generalizes across neurogenetics, oncology, and rare disease without modification. Each domain naturally exercises different schema facets, confirming the schema is neither over-specified nor under-specified.

---

## Cumulative Test Metrics

| Metric | Scenario 1 | Scenario 2 | Scenario 3 | Scenario 4 | Scenario 5 | Combined |
|---|---|---|---|---|---|---|
| Documents processed | 15 | 16 | 15 | 16 | 15 | 77 |
| Raw entities extracted | 297 | 231 | 182 | 256 | 185 | 1151 |
| Raw relations extracted | 251 | 194 | 128 | 216 | 148 | 937 |
| Graph nodes (deduplicated) | 149 | 108 | 94 | 132 | 94 | 577 |
| Graph links | 457 | 307 | 229 | 361 | 246 | 1600 |
| Communities detected | 6 | 4 | 4 | 5 | 5 | 24 |
| Entity types exercised | 10 | 16 | 16 | 15 | 14 | 17 (100%) |
| Relation types exercised | 14 | 17 | 21 | 16 | 14 | 27 (90%) |
| UATs passed | 4/4 | 5/5 | 3/3 | 4/4 | 3/3 | 19/19 |
| Bugs found | 2 critical, 2 medium, 2 low | 1 critical | 0 new | 0 new | 0 new | 3 critical, 2 medium, 2 low |
| Code fixes applied | 6 files modified, 2 new scripts | 3 files modified | 0 (stable) | 0 (stable) | 0 (stable) | 9 files modified, 2 new scripts |

---

## Engineering Standards Applied

This testing follows production-quality engineering standards appropriate for pharmaceutical and biomedical software:

### Traceability
Every entity type and relation type in the domain schema is traced from the ontology specification → `domain.yaml` → extraction → graph → UAT validation. Findings are traced from discovery → root cause → fix → verification.

### Reproducibility
All test inputs (PubMed abstracts), outputs (extraction JSONs, graph data), and evidence (graph screenshots) are committed to the repository. Any reviewer can re-run a scenario and compare against the committed baseline.

### Defense in Depth
Critical fixes employ two-layer defenses: the primary fix addresses root cause (prompt improvement), the secondary fix catches regressions defensively (runtime normalization). This is consistent with pharmaceutical software validation practices where single points of failure are unacceptable.

### Cross-Domain Validation
The same pipeline is tested across fundamentally different drug discovery domains (neurogenetics, oncology, rare disease, immuno-oncology, and cardiovascular/inflammation). All five scenarios are complete. This validates that the system generalizes rather than overfitting to a single domain.

### Scientist-Facing Documentation
Every scenario result includes a scientific narrative that a domain expert can evaluate for accuracy. Community labels are generated algorithmically but validated against biological expectations. This bridges the gap between software validation and scientific validation.
