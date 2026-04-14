# Scenario 2 (V2): KRAS G12C Inhibitor Landscape — Competitive Intelligence

**Status:** V2 validation complete
**V2 run date:** 2026-04-13
**Framework version:** Epistract v2.0
**Output:** [`tests/corpora/02_kras_g12c_landscape/output-v2/`](../corpora/02_kras_g12c_landscape/output-v2/)
**Interactive graph:** [`graph.html`](../corpora/02_kras_g12c_landscape/output-v2/graph.html)
**V1 reference:** [scenario-02-kras-g12c-landscape.md](scenario-02-kras-g12c-landscape.md)

---

## Knowledge Graph (V2)

![KRAS G12C V2 Knowledge Graph](screenshots/scenario-02-graph-v2.png)

*Force-directed graph showing 140 nodes and 432 links across 5 auto-labeled communities. 16 parallel `epistract:extractor` subagents processed 15 PubMed abstracts + 1 structural biology document (sotorasib X-ray crystal structure).*

---

## V1 → V2 Delta

| Metric | V1 Baseline | V2 Run | Δ | Threshold (≥80%) | Result |
|---|---:|---:|---:|---:|:---:|
| Nodes | 108 | **140** | +32 (+30%) | 87 | PASS |
| Edges | 307 | **432** | +125 (+41%) | 246 | PASS |
| Communities | 4 | **5** | +1 | 2 | PASS |
| Documents | 16 | 16 | 0 | — | — |

**Regression verdict:** `python3 tests/regression/run_regression.py --baselines tests/baselines/v1/ --scenario s02_kras` → **PASS**.

S2 shows the largest V2 edge-count expansion of any scenario so far (+41% vs V1). Likely driven by the richer `HAS_MECHANISM`, `CONFERS_RESISTANCE_TO`, `PREDICTS_RESPONSE_TO`, and `BINDS_TO` relations produced by per-document subagents reading the full drug-discovery SKILL.md.

---

## Corpus

Unchanged from V1 — 16 documents in `tests/corpora/02_kras_g12c_landscape/docs/`:

- **15 PubMed abstracts** (pmid_31658955 through pmid_40116975) covering the KRAS G12C inhibitor competitive landscape: sotorasib, adagrasib, divarasib, glecirasib, fulzerasib, MRTX1133 (G12D), emerging RAS-ON inhibitors, combination trials, and resistance mechanisms
- **1 structural biology document** (`structural_sotorasib.txt`) describing the sotorasib/KRAS G12C covalent binding mechanism — this is *not* a PubMed abstract and is a novel document type for the V2 validation

See [V1 scenario doc](scenario-02-kras-g12c-landscape.md#corpus) for full PMID list and query provenance.

---

## How to Run (V2 Pipeline)

```
/epistract:ingest tests/corpora/02_kras_g12c_landscape/docs --output tests/corpora/02_kras_g12c_landscape/output-v2 --domain drug-discovery
/epistract:epistemic tests/corpora/02_kras_g12c_landscape/output-v2
```

Then outside the plugin (regression + screenshot + docs) — see the runbook section in `docs/showcases/drug-discovery-v2.md`.

---

## Results

### Run Statistics (V2)

| Metric | V2 Value |
|---|---:|
| Documents processed | 16 |
| Parallel extraction agents | 16 (1 per doc) |
| Raw entities extracted | 311 |
| Raw relations extracted | 259 |
| Graph nodes (deduplicated) | 140 |
| Graph links | 432 |
| Communities detected | 5 |
| Epistemic relations classified | 432 |
| Contradictions found | 0 |
| Hypotheses identified | 0 |

### Entity Types (V2)

| Entity Type | V2 Count |
|---|---:|
| GENE | 22 |
| PROTEIN | 18 |
| DOCUMENT | 16 |
| SEQUENCE_VARIANT | 16 |
| DISEASE | 12 |
| COMPOUND | 10 |
| ADVERSE_EVENT | 9 |
| PATHWAY | 7 |
| PHENOTYPE | 7 |
| MECHANISM_OF_ACTION | 6 |
| CLINICAL_TRIAL | 6 |
| REGULATORY_ACTION | 5 |
| BIOMARKER | 4 |
| PROTEIN_DOMAIN | 2 |

Notable additions over S1:
- **CLINICAL_TRIAL** (6 extracted) — CodeBreaK 100, CodeBreaK 200, KRYSTAL-1, KRYSTAL-12, KRYSTAL-7
- **REGULATORY_ACTION** (5) — FDA approvals for sotorasib (2021), adagrasib (2022), and accelerated approval pathways
- **ADVERSE_EVENT** (9) — immune-mediated colitis, hepatotoxicity, QT prolongation, etc.
- **PROTEIN_DOMAIN** (2) — the switch-II pocket and P-loop, extracted from the structural biology document
- **SEQUENCE_VARIANT** (16) — 12 different KRAS mutations (G12C, G12D, G12V, G13D, Q61H, etc.) plus resistance variants (Y96D, H95D, R68S)

### Relation Types (V2)

| Relation Type | V2 Count |
|---|---:|
| MENTIONED_IN | 241 |
| IMPLICATED_IN | 49 |
| ASSOCIATED_WITH | 16 |
| INDICATED_FOR | 15 |
| CAUSES | 15 |
| INHIBITS | 13 |
| HAS_MECHANISM | 11 |
| PARTICIPATES_IN | 10 |
| CONFERS_RESISTANCE_TO | 10 |
| EVALUATED_IN | 8 |
| TARGETS | 7 |
| BINDS_TO | 7 |
| HAS_VARIANT | 7 |
| PREDICTS_RESPONSE_TO | 7 |
| ENCODES | 6 |
| ACTIVATES | 3 |
| COMBINED_WITH | 2 |
| GRANTS_APPROVAL_FOR | 2 |
| APPROVES | 2 |
| DIAGNOSTIC_FOR | 1 |

The distribution is characteristic of competitive-intelligence corpora: `CONFERS_RESISTANCE_TO` (10) and `HAS_MECHANISM` (11) are prominent because resistance biology dominates the KRAS G12C literature (post-sotorasib escape mutations, adaptive MAPK reactivation, KEAP1/STK11 co-mutations).

---

## Communities (V2)

Louvain community detection produced **5 communities** (V1: 4), auto-labeled by `label_communities.py`:

| # | Community | Members | V1 Equivalent |
|---|---|---:|---|
| 1 | Cancer — KRAS Protein | 29 | V1 "Adagrasib / ICI / BRAF" hub, now generalized to core KRAS biology |
| 2 | RAS-Mutant Cancer — VCP, MRAS:SHOC2:PP1C Complex, EGFR | 29 | V1 "EGFR Inhibitors / Combination Strategies" + RAS signaling merged |
| 3 | Lung Adenocarcinoma — KRAS G12C Protein, KRAS | 28 | V1 "RAS Signaling / RAF/MEK" — V2 centers this cluster on LUAD directly |
| 4 | PD-1 Checkpoint Blockade | 12 | **New standalone** — V1 merged this into adagrasib/ICI community |
| 5 | Scribble Pathway / Hippo Signaling Pathway | 8 | **New** — adaptive resistance biology not surfaced in V1 |

**Structural difference from V1:** V2 splits the V1 "adagrasib / immune checkpoint" community into a dedicated PD-1 checkpoint cluster (12 members) and a distinct Hippo/Scribble signaling cluster (8 members). The Hippo cluster captures a specific resistance-biology finding — that YAP/TAZ activation via Hippo pathway suppression is one of the escape routes from KRAS G12C inhibition. V1's coarser partition didn't surface this.

The **structural biology document contributed disproportionately** to the community factorization: PROTEIN_DOMAIN entities (switch-II pocket, P-loop) and structural binding relations (`BINDS_TO` with atomic-residue evidence) created tight sub-clusters that Louvain picked up as a distinct boundary.

---

## Epistemic Analysis (V2)

| Metric | Value |
|---|---:|
| Total relations analyzed | 432 |
| Base domain relations | 431 |
| Super-domain relations | 1 |
| Asserted | 431 |
| Unclassified | 1 |
| Contradictions detected | 0 |
| Hypotheses identified | 0 |
| Document types | paper, **unknown** |

**Note:** The structural biology document registered as `unknown` document type — the domain's epistemic classifier only knows `paper` and `patent` signatures. This is a minor gap worth capturing as a future-improvement todo: the classifier should recognize structural biology papers (PDB entries, X-ray crystallography methods) as a third signature class with their own hedging conventions ("the crystal structure reveals..." is high-confidence, "the observed interaction is likely..." is hedged).

No contradictions detected — the KRAS G12C corpus is predominantly declarative clinical/mechanistic reporting with consistent findings across sources. This contrasts with S1's Alzheimer's genetics corpus (1 contradiction) where meta-analyses disagreed on SORL1 as an independent risk factor.

---

## V2 Framework Insights

Captured from the S2 run on 2026-04-13:

### 1. Mixed-document-type corpora test the framework more rigorously

S2 is the first V2 scenario with a non-PubMed document (`structural_sotorasib.txt`). The `epistract:extractor` subagent correctly extracted structural features (P-loop, switch-II pocket, C12 covalent bond) as `PROTEIN_DOMAIN` entities and captured the sotorasib→KRAS G12C binding as a high-confidence `BINDS_TO` relation with residue-level evidence. No schema errors or format confusion.

### 2. Competitive-intelligence corpora produce more relations per document than genetics corpora

S2: 259 raw relations / 16 docs = 16.2 relations/doc average.
S1: 253 raw relations / 15 docs = 16.9 relations/doc average.

Close in per-document yield, but S2's relations hit **more distinct relation types** (20 types used vs S1's 11). The drug-discovery schema's diversity is getting more exercise in a CI corpus because every doc mentions trials (`EVALUATED_IN`), drugs (`INHIBITS`/`TARGETS`), resistance (`CONFERS_RESISTANCE_TO`), and approvals (`GRANTS_APPROVAL_FOR`).

### 3. Settings pre-approval plan is already paying off

S2 ran with substantially fewer permission prompts than S1 because `.claude/settings.local.json` was patched before the run to cover:
- `Bash(PYTHONPATH=. python3:*)` — covers run_sift, label_epistemic, validate_molecules
- `Bash(cp tests/corpora/:*)` — covers screenshot copying
- `Write(//Users/umeshbhatt/code/epistract/**)` — covers V2 doc/screenshot writes
- `Edit(//Users/umeshbhatt/code/epistract/**)` — covers any in-flight fixes

This is Track A of the auto-approve todo. Three more scenarios + contracts to confirm the allow-list is complete.

### 4. The `unknown` document type in epistemic is a minor gap

The structural biology doc was classified as `unknown` in the epistemic summary. For now this only affects the per-doctype breakdown (which aggregates across classes); no contradictions or hypotheses were mis-classified. Worth folding into the auto-approve todo as a second-order improvement: extend `domains/drug-discovery/epistemic.py` with a `structural` signature class.

### 5. Edge-count gain outpaces node-count gain

S2 V2/V1 delta: +30% nodes, **+41% edges**. This inverts the usual pattern where dedup collapses more entities than edges. S2's extra edges come from the per-document subagents being more aggressive about capturing adverse-event and resistance relations that V1's shared-context agents may have skipped. Cross-validation: S1 also showed V2 edges > V1 edges (+5%), so this is a consistent V2 direction not a one-scenario fluke.

### 6. The S1/S2 pattern predicts S3-S6 will also pass

Both S1 and S2 exceeded V1 baselines by wide margins. The remaining four drug-discovery scenarios (S3 rare disease, S4 immuno-oncology, S5 cardiovascular, S6 GLP-1) use the same drug-discovery domain schema, same extractor agent, and same sift-kg build/postprocess pipeline. Barring corpus-specific edge cases, confidence is high that all six will PASS the regression threshold.

---

## Key Questions Validated

Same questions as V1:

| # | Question | V2 Result | Graph Evidence |
|---|---|---|---|
| UAT-201 | What KRAS G12C inhibitors are in clinical development? | **PASS** — sotorasib, adagrasib, divarasib, glecirasib, fulzerasib, MRTX1133 extracted | 10 COMPOUND entities + 6 CLINICAL_TRIAL + 5 REGULATORY_ACTION |
| UAT-202 | What resistance mechanisms have been described? | **PASS** — CONFERS_RESISTANCE_TO relations capture secondary KRAS mutations, MAPK reactivation, KEAP1/STK11 co-mutations | 10 `CONFERS_RESISTANCE_TO` edges |
| UAT-203 | What are the combination strategies under investigation? | **PASS** — SHP2, SOS1, MEK, EGFR, PD-1/PD-L1 combinations extracted | 2 `COMBINED_WITH` + EGFR/PD-1 communities |
| UAT-204 | What is the structural basis for sotorasib covalent binding? | **PASS** — P-loop, switch-II pocket, C12 cysteine captured | `structural_sotorasib` extraction: 26 entities, 25 relations |

---

## Output Files

| File | Description |
|---|---|
| [`output-v2/extractions/`](../corpora/02_kras_g12c_landscape/output-v2/extractions/) | 16 JSON extraction files |
| [`output-v2/graph_data.json`](../corpora/02_kras_g12c_landscape/output-v2/graph_data.json) | 140 nodes, 432 edges |
| [`output-v2/communities.json`](../corpora/02_kras_g12c_landscape/output-v2/communities.json) | 5 community assignments |
| [`output-v2/graph.html`](../corpora/02_kras_g12c_landscape/output-v2/graph.html) | Interactive viewer |
| [`output-v2/claims_layer.json`](../corpora/02_kras_g12c_landscape/output-v2/claims_layer.json) | Epistemic layer (431 asserted, 0 contradictions) |
| [`output-v2/relation_review.yaml`](../corpora/02_kras_g12c_landscape/output-v2/relation_review.yaml) | Low-confidence relations flagged for review |
| [`output-v2/validation/`](../corpora/02_kras_g12c_landscape/output-v2/validation/) | Molecular + NCT validation results (9 NCT numbers detected) |
| [`output-v2/screenshots/graph_overview.png`](../corpora/02_kras_g12c_landscape/output-v2/screenshots/graph_overview.png) | V2 graph screenshot |
