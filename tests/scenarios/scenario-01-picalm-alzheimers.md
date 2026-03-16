# Scenario 1: PICALM / Alzheimer's Disease — Genetic Target Validation

**Status:** Completed
**Last run:** 2026-03-16
**Output:** [`tests/corpora/01_picalm_alzheimers/output/`](../corpora/01_picalm_alzheimers/output/)
**Interactive graph:** [`graph.html`](../corpora/01_picalm_alzheimers/output/graph.html) (open in browser)

---

## Knowledge Graph

![PICALM Alzheimer's Knowledge Graph](../corpora/01_picalm_alzheimers/output/screenshots/graph_overview.png)

*Force-directed graph showing 149 nodes and 457 links across 6 auto-labeled communities. Node color = community membership. Node size = connection count. Edge color = relation type.*

---

## Use Case

You are a neuroscience researcher investigating **PICALM** (phosphatidylinositol-binding clathrin assembly protein) as a potential therapeutic target for Alzheimer's disease. PICALM was identified as a risk locus in large-scale GWAS studies. You want to understand:

- What is the genetic evidence linking PICALM to Alzheimer's?
- What biological pathways does PICALM participate in?
- How does PICALM connect to amyloid and tau pathology?
- Are there any therapeutic approaches targeting PICALM-related biology?

This represents a **target validation** workflow — tracing from genetic evidence through biology to potential drug intervention.

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/01_picalm_alzheimers/docs/` |
| **Documents** | 15 PubMed abstracts (2011–2026) |
| **Format** | Plain text (.txt) — title, authors, journal, PMID, MeSH terms, abstract |
| **Source** | PubMed via NCBI E-utilities API, retrieved 2026-03-16 |

**PubMed queries used:**
- `PICALM Alzheimer disease genetic association`
- `PICALM endocytosis amyloid beta tau pathology`
- `phosphatidylinositol binding clathrin assembly protein Alzheimer`

### Documents

| PMID | Year | First Author | Focus |
|---|---|---|---|
| 21167244 | 2011 | Carter | HSV-1 / AD immune hypothesis — PICALM as HSV-1 binding partner |
| 21300948 | 2011 | Schjeide | GWAS replication of CLU, CR1, PICALM as AD risk loci |
| 24067654 | 2013 | Tian | AP2/PICALM targets APP-CTF for autophagy via LC3 |
| 24729694 | 2014 | Bagyinszky | AD genetics overview — early-onset and late-onset genes |
| 24951455 | 2015 | Karch | 25 GWAS risk genes and their pathogenic mechanisms |
| 25186232 | 2015 | Xu | Review of PICALM functions in AD (Aβ, tau, lipid, iron) |
| 25311924 | 2014 | Chouraki | Comprehensive AD genetics — 20+ GWAS loci catalog |
| 26611835 | 2016 | Wang | Meta-analysis: GAB2, PICALM, SORL1 variants and AD |
| 31385771 | 2019 | Zeng | Meta-analysis: rs3851179 and rs541458 protect against AD |
| 33453937 | 2021 | Goldstein | Post-endocytic APP trafficking as therapeutic target |
| 34130600 | 2022 | Deneubourg | Autophagy disorders spectrum (AD, PD, FTD, rare diseases) |
| 36552756 | 2022 | Ando | PICALM update: clathrin endocytosis, autophagy, tau modulation |
| 38915309 | 2024 | Jaye | ITSN1 isoform changes in AD — sex/brain-region specific |
| 40903578 | 2025 | Kozlova | **Nature**: PICALM risk allele → lipid droplets in microglia |
| 41315858 | 2026 | Brown | Microglial phagocytosis as convergent AD mechanism |

---

## How to Run

```
/epistract-ingest tests/corpora/01_picalm_alzheimers/docs/ --output tests/corpora/01_picalm_alzheimers/output
```

For fully automated (no permission prompts):
```bash
claude --dangerously-skip-permissions
```
Then run the ingest command above.

---

## Results

### Run Statistics

| Metric | Value |
|---|---|
| Documents processed | 15 |
| Parallel extraction agents | 5 (3 docs each) |
| Total extraction time | ~3 min |
| Total tokens | ~125,000 across 5 agents |
| Graph nodes (deduplicated) | 149 |
| Graph links | 457 |
| Communities detected | 6 |
| Raw entities extracted | 297 |
| Raw relations extracted | 251 |

### Entity Types

| Entity Type | Raw | Deduplicated |
|---|---|---|
| GENE | 135 | 48 |
| PROTEIN | 42 | 21 |
| PHENOTYPE | 30 | 18 |
| DISEASE | 28 | 8 |
| PATHWAY | 21 | 12 |
| SEQUENCE_VARIANT | 16 | 14 |
| CELL_OR_TISSUE | 11 | 3 |
| MECHANISM_OF_ACTION | 9 | 6 |
| BIOMARKER | 3 | 3 |
| COMPOUND | 1 | 1 |
| DOCUMENT | — | 15 |

### Relation Types

| Relation Type | Count | What It Captures |
|---|---|---|
| MENTIONED_IN | 253 | Entity-to-document provenance links |
| IMPLICATED_IN | 84 | Gene/protein → disease associations (GWAS, functional) |
| ASSOCIATED_WITH | 44 | General associations not fitting specific types |
| PARTICIPATES_IN | 23 | Protein/gene → pathway membership |
| HAS_VARIANT | 14 | Gene → specific SNP/mutation |
| ENCODES | 9 | Gene → protein product |
| TARGETS | 6 | Compound/protein → molecular target |
| EXPRESSED_IN | 5 | Gene/protein → tissue/cell type |
| REGULATES_EXPRESSION | 5 | Transcription factor → gene regulation |
| BINDS_TO | 4 | Physical protein-protein interactions |
| CAUSES | 4 | Compound/pathogen → phenotype/disease |
| HAS_MECHANISM | 3 | Entity → mechanism of action |
| FORMS_COMPLEX_WITH | 1 | Protein-protein complex formation |
| LOCALIZED_TO | 1 | Protein → subcellular compartment |
| INDICATED_FOR | 1 | Compound → disease indication |

---

## Communities

The graph self-organized into **6 communities** via Louvain community detection, auto-labeled by `label_communities.py` based on member entity composition:

### 1. Alzheimer Disease Risk Loci (30 genes) — 49 members

The GWAS hub cluster. Contains APOE, CLU, CR1, BIN1, CD33, ABCA7, TREM2, and 23 other genes identified through genome-wide association studies, all converging on late-onset Alzheimer's disease. Also includes tau phosphorylation, complement activation, and the APOE E4 variant. This community captures the **genetic landscape** — the starting point for any target validation effort.

**Key entities:** APOE, CLU, CR1, BIN1, CD33, TREM2, ABCA7, PTK2B, INPP5D, MEF2C, SORL1, FERMT2, CASS4

### 2. Endosomal Trafficking (APP, PSEN1, PSEN2) — 18 members

The core AD pathology cascade. APP processing through presenilins, amyloid-beta production, tau protein, and endosomal trafficking form the canonical amyloid hypothesis. Anti-Aβ antibodies (the only disease-modifying treatment) and amyloidogenic processing mechanism are here. This is the **disease mechanism** cluster.

**Key entities:** APP, PSEN1, PSEN2, amyloid-beta, tau, amyloid precursor protein, anti-Aβ antibodies, endosomal trafficking

### 3. Phagocytosis / Amyloid Beta Processing — 15 members

PICALM's functional biology at the intersection of endocytosis and phagocytosis. Contains the PICALM gene itself, specific SNP variants (rs3851179, rs541458, rs592297), and links to TREM2, CD33, and phagocytosis pathways. CSF Aβ42 appears as a biomarker. This cluster captures **what PICALM does**.

**Key entities:** PICALM, rs3851179, rs541458, TREM2, CD33, SPI1, CSF Aβ42 biomarker

### 4. Autophagy / Endocytic Pathway — 17 members

Cross-disease cluster linking autophagy to multiple neurodegenerative disorders. LC3 (MAP1LC3) and APP-CTF degradation connect to Parkinson's disease, frontotemporal dementia, and neurodevelopmental disorders through shared autophagy machinery (CHMP2B, GBA, EPG5, VCP). This reveals **pathway-level connections** beyond AD.

**Key entities:** autophagy pathway, LC3, APP-CTF, PICALM protein, GBA, CHMP2B, Parkinson disease

### 5. Clathrin-Mediated Endocytosis in Hippocampus — 10 members

Tissue-specific cell biology. ITSN1, DNM2, AP2A1, FCHO1 — the scaffolding proteins of clathrin-mediated endocytosis — show isoform-specific, sex-dependent, and brain-region-dependent changes in AD. Enlarged early endosomes emerge as an early cellular phenotype. This is the **cellular mechanism** cluster.

**Key entities:** ITSN1, DNM2, AP2A1, FCHO1, hippocampus, frontal cortex, enlarged early endosomes

### 6. Cholesterol Synthesis in Microglia — 8 members

The 2025 Nature discovery (Kozlova et al.). The causal chain: rs10792832 risk allele → reduced PU.1 transcription factor binding → reduced PICALM expression → impaired Aβ and myelin debris uptake → lipid droplet accumulation → phagocytosis deficit. This is **microglial-specific** and represents the most recent mechanistic insight.

**Key entities:** rs10792832, PU.1, microglia, lipid droplet accumulation, cholesterol synthesis, phagocytosis deficit

---

## Scientific Narrative

This corpus tells the complete story of PICALM as an Alzheimer's target, spanning 15 years of research:

1. **Discovery (2011)** — Genome-wide association studies identify PICALM alongside CLU and CR1 as AD risk loci. The rs541458 variant in PICALM affects CSF Aβ42 levels, providing the first clue to mechanism.

2. **Mechanism (2013–2015)** — The AP2/PICALM complex is shown to function as an autophagic cargo receptor, binding LC3 and targeting APP-CTF for degradation. PICALM affects AD risk through Aβ production, transport, and clearance — but also through Aβ-independent pathways (tauopathy, synaptic dysfunction, lipid metabolism, iron homeostasis).

3. **Genetic Refinement (2016–2019)** — Large meta-analyses confirm rs3851179 (protective, OR=0.88) and rs541458 (protective, OR=0.86) as the key PICALM variants. The protective effect of rs541458 is Caucasian-specific. Seven SORL1 variants are also mapped with opposing risk/protective effects.

4. **Cell Biology (2024)** — Comprehensive evaluation of clathrin-mediated endocytosis hub proteins in human AD brain tissue reveals that ITSN1-long decreases in male frontal cortex and female hippocampus, while ITSN1-short increases in hippocampus of both sexes — changes that are transient and stage-dependent.

5. **Causal Variant (2025)** — A Nature paper identifies rs10792832 as the causal SNP through allele-specific open chromatin mapping in iPSC-derived microglia. The risk allele reduces PU.1 binding → reduced PICALM expression → impaired Aβ and myelin debris uptake → aberrant lipid droplet accumulation. This is **microglial-specific**.

6. **Therapeutic Direction (2026)** — A review in Nature Reviews Neurology shows that most known AD genetic risk (27 genes including PICALM) converges on microglial phagocytosis. Anti-Aβ antibodies — the only disease-modifying treatments — work by increasing microglial phagocytosis of Aβ aggregates. This positions PICALM-related biology at the center of current therapeutic thinking.

---

## Key Questions Validated (UAT-101 through UAT-104)

| # | Question | Result | Graph Evidence |
|---|---|---|---|
| UAT-101 | What genes are associated with AD risk? | **PASS** — 30 genes in Community 1 | PICALM, APOE, BIN1, CLU, CR1, CD33, ABCA7, TREM2 + 22 others → IMPLICATED_IN → Alzheimer disease |
| UAT-102 | What pathways does PICALM participate in? | **PASS** — 4 pathways linked | endocytosis, phagocytosis, amyloid-beta processing, autophagy |
| UAT-103 | How does PICALM relate to amyloid beta? | **PASS** — multiple paths | PICALM → PARTICIPATES_IN → endocytosis; AP2/PICALM → BINDS_TO → LC3 → autophagy of APP-CTF |
| UAT-104 | Therapeutic approaches? | **PARTIAL** — 1 compound class | anti-Aβ antibodies extracted; no small molecules targeting PICALM directly (consistent with literature) |

---

## Bugs Found During This Run

1. **`entity_type`/`relation_type` field naming** — Extractor agents used `type` instead of sift-kg-required `entity_type`/`relation_type`. Fix: explicit JSON example in `agents/extractor.md` + defensive normalization in `build_extraction.py`.

2. **Unlabeled communities** — sift-kg produces numbered communities with no semantic labels. Fix: new `label_communities.py` auto-generates descriptive labels, integrated into `run_sift.py build`.

---

## Output Files

| File | Description |
|---|---|
| [`output/extractions/`](../corpora/01_picalm_alzheimers/output/extractions/) | 15 JSON extraction files (one per document) |
| [`output/graph_data.json`](../corpora/01_picalm_alzheimers/output/graph_data.json) | Complete knowledge graph (149 nodes, 457 links) |
| [`output/communities.json`](../corpora/01_picalm_alzheimers/output/communities.json) | Community assignments with descriptive labels |
| [`output/graph.html`](../corpora/01_picalm_alzheimers/output/graph.html) | Interactive force-directed graph viewer |
| [`output/relation_review.yaml`](../corpora/01_picalm_alzheimers/output/relation_review.yaml) | Relations flagged for human review |
| [`output/validation/`](../corpora/01_picalm_alzheimers/output/validation/) | Molecular identifier validation results |
| [`output/screenshots/`](../corpora/01_picalm_alzheimers/output/screenshots/) | Graph screenshots for documentation |
