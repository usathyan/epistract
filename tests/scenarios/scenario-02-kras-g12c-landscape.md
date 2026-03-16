# Scenario 2: KRAS G12C Inhibitor Landscape — Competitive Intelligence

**Status:** Completed
**Last run:** 2026-03-16
**Output:** [`tests/corpora/02_kras_g12c_landscape/output/`](../corpora/02_kras_g12c_landscape/output/)
**Interactive graph:** [`graph.html`](../corpora/02_kras_g12c_landscape/output/graph.html) (clone repo and open locally in browser)

---

## Knowledge Graph

![KRAS G12C Inhibitor Landscape Knowledge Graph](screenshots/scenario-02-graph.png)

*Force-directed graph showing 108 nodes and 307 links across 4 auto-labeled communities. Node color = community membership. Node size = connection count. Edge color = relation type.*

---

## Use Case

You are an oncology drug discovery scientist mapping the **KRAS G12C inhibitor competitive landscape**. Two drugs are approved (sotorasib, adagrasib), and multiple next-generation inhibitors are in development. You want to understand:

- What compounds target KRAS G12C and what are their clinical results?
- What resistance mechanisms are emerging?
- What combination strategies are being explored?
- How do the approved drugs compare mechanistically?

This represents a **competitive intelligence** workflow — mapping the therapeutic landscape for a hot target.

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/02_kras_g12c_landscape/docs/` |
| **Documents** | 16 (15 PubMed abstracts + 1 structural pharmacological profile) |
| **Format** | Plain text (.txt) |
| **Source** | PubMed via NCBI E-utilities API + compiled structural data, retrieved 2026-03-16 |

**PubMed queries used:**
- `KRAS G12C inhibitor sotorasib adagrasib clinical trial`
- `KRAS G12C covalent inhibitor resistance mechanism`
- `KRAS G12C non-small cell lung cancer treatment`
- `KRAS G12C combination immunotherapy`

### Documents

| PMID | Year | First Author | Focus |
|---|---|---|---|
| 31658955 | 2020 | Hallin | MRTX849 (adagrasib) preclinical characterization, resistance mechanisms, combinations |
| 34161704 | 2021 | Awad | **NEJM**: Acquired resistance to KRAS G12C inhibitors — comprehensive landscape |
| 34607583 | 2021 | Tang | Review: oncogenic KRAS blockade therapy, direct vs indirect approaches |
| 34953682 | 2021 | Nussinov | Drug resistance perspective — AI-informed combination strategies |
| 35658005 | 2022 | Janne | **NEJM**: Adagrasib Phase 2 KRYSTAL-1 — ORR 42.9%, PFS 6.5 months |
| 35837349 | 2022 | Ji | KRAS G12C in CRC — EGFR-mediated resistance, combination rationale |
| 36764316 | 2023 | de Langen | **Lancet**: Sotorasib vs docetaxel Phase 3 CodeBreaK 200 — PFS HR 0.66 |
| 37101895 | 2023 | Zhang | CodeBreaK 200 commentary — sotorasib vs adagrasib competitive analysis |
| 38072173 | 2024 | Rosell | MRAS:SHOC2:PP1C complex activation, STK11 comutations, adaptive resistance |
| 38625662 | 2024 | Torres-Jimenez | Review: KRAS G12C-mutated NSCLC — current treatments, future directions |
| 39215000 | 2024 | Nokin | **Nat Commun**: RAS-ON inhibitors (RMC-6291) overcome OFF-state resistance |
| 39337530 | 2024 | Liu | Emerging NSCLC targets: KRAS non-G12C, HER3, Nectin-4, PRMT5 |
| 39725152 | 2024 | Yamamoto | WEE1 confers sotorasib resistance via MCL-1 upregulation |
| 39732595 | 2025 | Isermann | Review: KRAS inhibitor resistance drivers and combinatorial strategies |
| 40116975 | 2025 | Sayed | Systematic review: KRAS G12C inhibitors in CRC — 9 trials, 668 patients |
| structural | — | Compiled | Sotorasib structural/pharmacological profile (SMILES, IC50, clinical data) |

---

## How to Run

```
/epistract-ingest tests/corpora/02_kras_g12c_landscape/docs/ --output tests/corpora/02_kras_g12c_landscape/output
```

---

## Results

### Run Statistics

| Metric | Value |
|---|---|
| Documents processed | 16 (15 abstracts + 1 structural profile) |
| Parallel extraction agents | 4 (4 docs each) |
| Total extraction time | ~3 min |
| Graph nodes (deduplicated) | 108 |
| Graph links | 307 |
| Communities detected | 4 |
| Raw entities extracted | 231 |
| Raw relations extracted | 194 |
| Molecular identifiers found | 6 NCT numbers |

### Entity Types

| Entity Type | Raw | Deduplicated |
|---|---|---|
| GENE | 56 | 20 |
| COMPOUND | 37 | 11 |
| SEQUENCE_VARIANT | 29 | 10 |
| DISEASE | 23 | 3 |
| PROTEIN | 16 | 10 |
| PATHWAY | 11 | 8 |
| PHENOTYPE | 9 | 1 |
| MECHANISM_OF_ACTION | 7 | 5 |
| CLINICAL_TRIAL | 7 | 4 |
| ADVERSE_EVENT | 7 | 6 |
| REGULATORY_ACTION | 7 | 5 |
| ORGANIZATION | 5 | 2 |
| PROTEIN_DOMAIN | 3 | 2 |
| BIOMARKER | 2 | 2 |
| METABOLITE | 2 | 2 |
| CELL_OR_TISSUE | 1 | 1 |
| DOCUMENT | — | 16 |

### Relation Types

| Relation Type | Count | What It Captures |
|---|---|---|
| MENTIONED_IN | 189 | Entity-to-document provenance links |
| CONFERS_RESISTANCE_TO | 26 | Gene/variant → drug resistance (the core competitive intelligence signal) |
| IMPLICATED_IN | 11 | Gene/pathway → disease associations |
| INHIBITS | 10 | Compound → target inhibition |
| PARTICIPATES_IN | 10 | Gene/protein → pathway membership |
| COMBINED_WITH | 9 | Drug combination strategies |
| HAS_VARIANT | 9 | KRAS → specific resistance mutations |
| BINDS_TO | 7 | Physical drug-target binding |
| CAUSES | 7 | Drug → adverse events |
| ASSOCIATED_WITH | 7 | General associations |
| INDICATED_FOR | 5 | Drug → disease indication |
| EVALUATED_IN | 5 | Drug → clinical trial |
| HAS_MECHANISM | 4 | Drug → mechanism of action |
| ACTIVATES | 2 | Feedback activation of bypass pathways |
| FORMS_COMPLEX_WITH | 2 | MRAS:SHOC2:PP1C complex |
| REGULATES_EXPRESSION | 1 | WEE1 → MCL-1 |
| EXPRESSED_IN | 1 | Tissue-specific expression |

---

## Communities

The graph self-organized into **4 communities** via Louvain detection, auto-labeled by `label_communities.py`:

### 1. EGFR Inhibitors / Adavosertib / Panitumumab — 25 members

The **combination strategy and CRC** cluster. Contains EGFR inhibitors (cetuximab, panitumumab), the WEE1 inhibitor adavosertib, MCL-1 (resistance mediator), sotorasib, docetaxel, Amgen (developer), and clinical adverse events (diarrhoea, ALT/AST increase). Also contains the MRAS:SHOC2:PP1C complex (adaptive resistance mechanism) and CodeBreaK trial data. This is where the competitive intelligence on **how to improve sotorasib responses** lives.

**Key entities:** sotorasib, adavosertib, panitumumab, cetuximab, WEE1, MCL-1, EGFR, Amgen, diarrhoea, ALT increase

### 2. Adagrasib / Immune Checkpoint Inhibitors / BRAF — 20 members

The **adagrasib competitive cluster**. Contains adagrasib (MRTX849), immune checkpoint inhibitors, Mirati Therapeutics, FDA accelerated approval, KRYSTAL-1 trial, and the bypass resistance genes (BRAF, NF1, PTEN, NRAS). Also contains the covalent irreversible inhibition mechanism and multiple KRAS resistance variants (G13D, H95D/Q/R). This cluster captures **adagrasib's clinical profile and the genomic resistance landscape**.

**Key entities:** adagrasib, immune checkpoint inhibitors, Mirati Therapeutics, BRAF, NF1, PTEN, NRAS, KRAS G13D, KRAS H95D

### 3. RAS Signaling / RAF/MEK Pathway — 17 members

The **biology and emerging targets** cluster. Contains the RAS signaling pathway, RAF/MEK pathway, KRAS gene itself, and key resistance variants (Y96C, G12D, Q61H). Also includes emerging NSCLC targets (PRMT5, ITGB6, HER3, Nectin-4, folate receptor alpha) and the Switch II pocket (drug binding site). This is the **mechanistic biology** cluster — understanding what KRAS does and where else to intervene.

**Key entities:** KRAS, RAS signaling, RAF/MEK pathway, Switch II pocket, Y96C, G12D, Q61H, HER3, PRMT5

### 4. Pancreatic Ductal Adenocarcinoma / PD-1 — 10 members

The **disease indication and next-generation** cluster. Contains CRC, pancreatic ductal adenocarcinoma, NSCLC, the KRAS G12C variant, divarasib (next-gen inhibitor), RMC-6291/RMC-4998 (RAS-ON inhibitors), cetuximab, and STK11 comutation. This cluster captures **where the field is going** — beyond NSCLC to CRC/pancreatic, and beyond OFF-state to ON-state inhibitors.

**Key entities:** KRAS G12C, divarasib, RMC-6291, RMC-4998, NSCLC, CRC, pancreatic ductal adenocarcinoma, STK11

---

## Scientific Narrative

This corpus maps the KRAS G12C therapeutic landscape from first-in-class discovery through competitive dynamics to next-generation strategies:

1. **Discovery & Preclinical (2020)** — MRTX849 (adagrasib) identified as potent, selective, covalent KRAS G12C inhibitor. Preclinical models show 65% response rate, but also reveal resistance through RTK activation, KRAS nucleotide cycling, and cell cycle bypass. Combinations with mTOR and RTK inhibitors show enhanced responses.

2. **Resistance Landscape (2021)** — Awad et al. (NEJM) provide the definitive resistance map: 45% of patients develop identifiable resistance. Mechanisms include secondary KRAS mutations (G12D/R/V/W, Y96C, H95D/Q/R), bypass through MET/NRAS/BRAF/RET/ALK, and histologic transformation. Multiple coincident mechanisms in 18% of patients.

3. **Clinical Proof (2022-2023)** — Adagrasib KRYSTAL-1 Phase 2: ORR 42.9%, PFS 6.5 months, with CNS activity (33% intracranial ORR). Sotorasib CodeBreaK 200 Phase 3: PFS 5.6 vs 4.5 months (docetaxel), HR 0.66. Both FDA-approved. In CRC, responses are lower (ORR 7-10% monotherapy) — EGFR feedback reactivation drives resistance.

4. **Combination Strategies (2024-2025)** — CRC responds much better to KRAS G12C inhibitors + EGFR inhibitors: adagrasib+cetuximab ORR 42%, divarasib+cetuximab ORR 62.5%. WEE1 inhibitor adavosertib shows synergy with sotorasib via MCL-1 downregulation. STK11/LKB1 comutations jeopardize checkpoint inhibitor responses.

5. **Next Generation (2024-2025)** — RAS-ON inhibitors (RMC-6291) target the active GTP-bound state, overcoming resistance from increased KRAS-GTP loading. Divarasib emerges as a third KRAS G12C inhibitor with higher CRC responses than sotorasib/adagrasib monotherapy.

---

## Key Questions Validated (UAT-201 through UAT-205)

| # | Question | Result | Graph Evidence |
|---|---|---|---|
| UAT-201 | What drugs target KRAS G12C? | **PASS** — 5 compounds | sotorasib, adagrasib, divarasib, RMC-6291, RMC-4998 → INHIBITS → KRAS G12C |
| UAT-202 | What clinical trials exist? | **PASS** — 4 trials | CodeBreaK 100 (NCT03600883), CodeBreaK 200 (NCT04303780), KRYSTAL-1 (NCT03785249), plus unnamed early-phase |
| UAT-203 | What resistance mechanisms? | **PASS** — 10+ variants + bypass genes | KRAS G12D/R/V/W, Y96C, G13D, Q61H, H95D/Q/R + MET, NRAS, BRAF, NF1, PTEN, WEE1 → CONFERS_RESISTANCE_TO → sotorasib/adagrasib |
| UAT-204 | What combinations are explored? | **PASS** — 6 combination partners | cetuximab, panitumumab, adavosertib, immune checkpoint inhibitors, RMC-6291, docetaxel → COMBINED_WITH → KRAS G12C inhibitors |
| UAT-205 | What is sotorasib's mechanism? | **PASS** — full mechanism captured | Covalent irreversible KRAS G12C inhibition → BINDS_TO → Switch II pocket, IC50 7.8 nM |

---

## Comparison with Scenario 1

| Metric | Scenario 1 (PICALM/AD) | Scenario 2 (KRAS G12C) |
|---|---|---|
| Documents | 15 | 16 |
| Graph nodes | 149 | 108 |
| Graph links | 457 | 307 |
| Communities | 6 | 4 |
| Dominant entity types | GENE (48), PROTEIN (21) | GENE (20), COMPOUND (11), SEQUENCE_VARIANT (10) |
| Key relation types | IMPLICATED_IN (84) | CONFERS_RESISTANCE_TO (26), INHIBITS (10), COMBINED_WITH (9) |
| Domain focus | Genetic target validation | Competitive intelligence |
| Molecular identifiers | 0 | 6 NCT numbers |

Scenario 2 exercises a completely different part of the schema — heavy on COMPOUND, CLINICAL_TRIAL, SEQUENCE_VARIANT, ADVERSE_EVENT, REGULATORY_ACTION, and ORGANIZATION entities; and on CONFERS_RESISTANCE_TO, COMBINED_WITH, INDICATED_FOR, and EVALUATED_IN relations. This validates that the epistract pipeline generalizes across drug discovery use cases.

---

## Output Files

| File | Description |
|---|---|
| [`output/extractions/`](../corpora/02_kras_g12c_landscape/output/extractions/) | 16 JSON extraction files (one per document) |
| [`output/graph_data.json`](../corpora/02_kras_g12c_landscape/output/graph_data.json) | Complete knowledge graph (108 nodes, 307 links) |
| [`output/communities.json`](../corpora/02_kras_g12c_landscape/output/communities.json) | Community assignments with descriptive labels |
| [`output/graph.html`](../corpora/02_kras_g12c_landscape/output/graph.html) | Interactive force-directed graph viewer |
| [`output/relation_review.yaml`](../corpora/02_kras_g12c_landscape/output/relation_review.yaml) | Relations flagged for human review |
| [`output/validation/`](../corpora/02_kras_g12c_landscape/output/validation/) | Molecular identifier validation results (6 NCT numbers detected) |
| [`screenshots/scenario-02-graph.png`](screenshots/scenario-02-graph.png) | Graph screenshot for documentation |
