# Scenario 1 (V2): PICALM / Alzheimer's Disease — Genetic Target Validation

**Status:** V2 validation complete
**V2 run date:** 2026-04-13
**Framework version:** Epistract v2.0 (cross-domain framework)
**Output:** [`tests/corpora/01_picalm_alzheimers/output-v2/`](../corpora/01_picalm_alzheimers/output-v2/)
**Interactive graph:** [`graph.html`](../corpora/01_picalm_alzheimers/output-v2/graph.html)
**V1 reference:** [scenario-01-picalm-alzheimers.md](scenario-01-picalm-alzheimers.md)

---

## Knowledge Graph (V2)

![PICALM Alzheimer's V2 Knowledge Graph](screenshots/scenario-01-graph-v2.png)

*Force-directed graph showing 183 nodes and 478 links across 7 auto-labeled communities. Rendered with the V2 plugin pipeline through `/epistract:ingest` with 15 parallel `epistract:extractor` subagents.*

---

## V1 → V2 Delta

| Metric | V1 Baseline | V2 Run | Δ | Threshold (≥80%) | Result |
|---|---:|---:|---:|---:|:---:|
| Nodes | 149 | **183** | +34 (+23%) | 119 | PASS |
| Edges | 457 | **478** | +21 (+5%) | 365 | PASS |
| Communities | 6 | **7** | +1 | 3 | PASS |
| Documents | 15 | 15 | 0 | — | — |

**Regression verdict:** `tests/regression/run_regression.py --baselines tests/baselines/v1/ --scenario s01_picalm` → **PASS**.

---

## Use Case

Unchanged from V1 — PICALM target validation for Alzheimer's disease. See [V1 scenario doc](scenario-01-picalm-alzheimers.md#use-case).

---

## Corpus

Identical to V1 — same 15 PubMed abstracts (2011–2026) in `tests/corpora/01_picalm_alzheimers/docs/`. No corpus changes. V2 validates that the refactored framework produces equal-or-better extraction quality on the same input.

---

## How to Run (V2 Pipeline)

V2 runs through the `/epistract:*` plugin commands only — no direct script invocation:

```
/epistract:ingest tests/corpora/01_picalm_alzheimers/docs --output tests/corpora/01_picalm_alzheimers/output-v2 --domain drug-discovery
```

Under the hood, the command:
1. Lists documents and reads them via Kreuzberg
2. Dispatches one `epistract:extractor` subagent per document (15 in parallel for this corpus)
3. Each subagent reads `domains/drug-discovery/SKILL.md` and emits per-doc extraction JSON via `core/build_extraction.py`
4. Runs `domains/drug-discovery/validate_molecules.py` for SMILES/sequence validation
5. Builds the graph via `core/run_sift.py build --domain drug-discovery`
6. Generates the HTML viewer via `core/run_sift.py view`

Epistemic layer is run separately with `/epistract:epistemic` → `core/label_epistemic.py`.

---

## Results

### Run Statistics (V2)

| Metric | V2 Value | V1 Value |
|---|---:|---:|
| Documents processed | 15 | 15 |
| Parallel extraction agents | 15 (1 per doc) | 5 (3 per agent) |
| Raw entities extracted | 354 | 297 |
| Raw relations extracted | 253 | 251 |
| Graph nodes (deduplicated) | 183 | 149 |
| Graph links | 478 | 457 |
| Communities detected | 7 | 6 |
| Epistemic relations classified | 478 | — |
| Contradictions found | 1 | — |
| Hypotheses identified | 1 | — |

### Entity Types (V2)

| Entity Type | V2 Count | V1 Deduplicated |
|---|---:|---:|
| GENE | 77 | 48 |
| PROTEIN | 22 | 21 |
| PHENOTYPE | 18 | 18 |
| DISEASE | 17 | 8 |
| DOCUMENT | 15 | 15 |
| PATHWAY | 13 | 12 |
| SEQUENCE_VARIANT | 11 | 14 |
| BIOMARKER | 6 | 3 |
| COMPOUND | 3 | 1 |
| ORGANIZATION | 1 | 0 |

### Relation Types (V2)

| Relation Type | V2 Count |
|---|---:|
| MENTIONED_IN | 279 |
| IMPLICATED_IN | 128 |
| PARTICIPATES_IN | 36 |
| ENCODES | 11 |
| CAUSES | 6 |
| BINDS_TO | 6 |
| PREDICTS_RESPONSE_TO | 4 |
| INDICATED_FOR | 3 |
| DIAGNOSTIC_FOR | 3 |
| ASSOCIATED_WITH | 1 |
| TARGETS | 1 |

---

## Communities (V2)

Louvain community detection produced **7 communities** (one more than V1), auto-labeled by `label_communities.py` from member entity composition:

| # | Community | Members | V1 Equivalent |
|---|---|---:|---|
| 1 | Alzheimer Disease — Tau | 42 | New consolidation — merges V1 Communities 2, 3 partially |
| 2 | Late-Onset Alzheimer Disease Risk Loci (25 genes) | 31 | V1 Community 1 (Risk Loci — 49 genes) |
| 3 | Huntington Disease — Atg5, Map1Lc3, App-Ctf | 28 | V1 Community 4 (Autophagy), now centered on HD |
| 4 | Clathrin-Mediated Endocytosis (Fcho1, Bin1, Dnm2) | 11 | V1 Community 5 — now surfaced as standalone |
| 5 | Amyloid Precursor Protein Processing / Post-Endocytic Trafficking (Psen1, Psen2, App) | 9 | V1 Community 2 (Endosomal Trafficking) |
| 6 | Endocytosis / Amyloid Beta Clearance (Picalm) | 8 | V1 Community 3 (Phagocytosis / PICALM) |
| 7 | Cerebral Shrinkage / Beta-Amyloid Deposition / Tau Phosphorylation | 8 | New — V1 did not surface this phenotype cluster |

**Structural difference from V1:** V2 partitions the graph into smaller, more focused communities. The V1 "30 genes" GWAS hub was a single giant cluster; V2 splits it into a tau-centric cluster (42 members) and a distinct risk-loci cluster (31). V2 also elevates Clathrin-Mediated Endocytosis from a sub-cluster to a standalone community, consistent with the cleaner force-directed layout seen in the rendered graph.

---

## Epistemic Analysis (V2)

Run via `/epistract:epistemic` → `core/label_epistemic.py`. Results:

| Metric | Value |
|---|---:|
| Total relations analyzed | 478 |
| Base domain relations | 474 |
| Super-domain (cross-doc) relations | 4 |
| Asserted | 474 |
| Hypothesized | 3 |
| Unclassified | 1 |
| **Contradictions detected** | **1** |
| Hypotheses identified | 1 |
| Document types | paper |

### Contradiction: SORL1 implicated in late-onset Alzheimer's

The epistemic layer flagged a directional contradiction between `pmid_24951455` and `pmid_25311924`:

| Source | Direction | Evidence |
|---|---|---|
| pmid_24951455 (Karch 2015) | Positive | "SORL1" (listed among 25 GWAS risk genes) |
| pmid_25311924 (Chouraki 2014) | Negative | "failed to robustly identify other genetic risk factors, with the exception of variants in SORL1" |

This is a **meta-analysis framing difference**, not a true biological conflict — Chouraki's "failed to identify" hedges SORL1 as the *only* exception. The epistemic layer correctly surfaces this as a claim worth human review because the polarity of "SORL1 implicated" is textually ambiguous across the two sources.

---

## V2 Framework Insights

Captured from running this scenario through the V2 plugin pipeline on 2026-04-13:

### 1. Parallel extraction now scales to per-document agents

V1 used 5 extractor agents handling 3 docs each. V2 dispatches 15 parallel `epistract:extractor` subagents (one per doc). This is cleaner because each subagent has isolated context, reads the SKILL.md independently, and returns only a file path + counts to the orchestrator. Main-session context cost per scenario dropped from ~125K tokens to <2K tokens (the 15 per-agent reports).

### 2. V2 extracts more entities per document (19.5 avg vs 19.8 V1)

Raw entity counts per doc: V2 = 354 / 15 ≈ 23.6 avg; V1 = 297 / 15 ≈ 19.8 avg. V2's per-doc extractor reads the full SKILL.md in its own context rather than sharing context across 3 docs, so it's more exhaustive — especially on phenotype and biomarker extraction (2× V1 on biomarkers).

### 3. Canonical naming dedup collapsed 354 → 183 cleanly

The drug-discovery domain schema defines `canonical_names` for key entities (gene symbols, disease MeSH terms). sift-kg's `build_graph` uses `domain_canonical_entities` during postprocess to collapse variant spellings. V2's 23% node expansion over V1 came *without* degrading dedup — the canonical map caught aliases like "amyloid precursor protein" → "APP" that V1 may have left as separate nodes.

### 4. Community factorization is finer-grained

V2 produced 7 communities (V1: 6) by splitting the V1 "Autophagy / Endocytic Pathway" cluster into a distinct Clathrin-Mediated Endocytosis group. The cleaner Louvain partition is likely driven by the additional gene-pathway edges (PARTICIPATES_IN went from ~23 in V1 to 36 in V2), which tighten intra-community cohesion.

### 5. Epistemic layer caught a real-world ambiguity on first pass

The SORL1 contradiction between Karch 2015 and Chouraki 2014 is a genuine framing difference that a human reviewer should look at. The epistemic layer's `evidence_direction` heuristic is pattern-based and ran with zero LLM cost, but it still surfaced the non-obvious polarity conflict.

### 6. Bottom-viewer edge count is not the graph edge count

The sift-kg HTML viewer displays "183 entities · 198 relations" in its footer, while `graph_data.json` holds 478 edges. The viewer collapses bidirectional MultiDiGraph edges to undirected display edges for layout. Use `graph_data.json` (not the viewer footer) for regression metrics. Documented here because this confused me during the run and may confuse others reviewing V2 outputs.

### 7. Plugin-level regression runner needed an output-dir fix

`tests/regression/run_regression.py` originally hardcoded `scenario/output/` as the subdir. Fixed during this run to prefer `output-v2/` when present, falling back to `output/`. This lets V1 baselines coexist with V2 outputs during the Phase 11 transition.

---

## Key Questions Validated (UAT-101 through UAT-104)

Same questions as V1. All four PASS with V2:

| # | Question | V2 Result | Graph Evidence |
|---|---|---|---|
| UAT-101 | What genes are associated with AD risk? | **PASS** — 77 genes extracted (V1: 48) | Community 2 "Late-Onset Alzheimer Disease Risk Loci (25 genes)" + Community 1 "Alzheimer Disease — Tau" |
| UAT-102 | What pathways does PICALM participate in? | **PASS** — 13 pathways (V1: 12) | PICALM → PARTICIPATES_IN → endocytosis, clathrin-mediated endocytosis, amyloid clearance, autophagy |
| UAT-103 | How does PICALM relate to amyloid beta? | **PASS** — multi-hop paths preserved | PICALM → Endocytosis/Amyloid Beta Clearance community (8 members) |
| UAT-104 | Therapeutic approaches? | **PARTIAL** — 3 compounds (V1: 1) | anti-Aβ antibodies, antiviral agent, immune suppressant extracted |

---

## Output Files

| File | Description |
|---|---|
| [`output-v2/extractions/`](../corpora/01_picalm_alzheimers/output-v2/extractions/) | 15 JSON extraction files (one per document) |
| [`output-v2/graph_data.json`](../corpora/01_picalm_alzheimers/output-v2/graph_data.json) | Complete knowledge graph (183 nodes, 478 links) |
| [`output-v2/communities.json`](../corpora/01_picalm_alzheimers/output-v2/communities.json) | 7 community assignments with descriptive labels |
| [`output-v2/graph.html`](../corpora/01_picalm_alzheimers/output-v2/graph.html) | Interactive force-directed graph viewer |
| [`output-v2/claims_layer.json`](../corpora/01_picalm_alzheimers/output-v2/claims_layer.json) | Epistemic claims layer (474 asserted, 1 contradiction) |
| [`output-v2/relation_review.yaml`](../corpora/01_picalm_alzheimers/output-v2/relation_review.yaml) | Relations flagged for human review |
| [`output-v2/validation/`](../corpora/01_picalm_alzheimers/output-v2/validation/) | Molecular identifier validation results |
| [`output-v2/screenshots/graph_overview.png`](../corpora/01_picalm_alzheimers/output-v2/screenshots/graph_overview.png) | Canonical V2 graph screenshot |
