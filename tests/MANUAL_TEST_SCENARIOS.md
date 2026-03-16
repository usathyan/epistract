# Epistract Manual Test Scenarios

Five real-world drug discovery research scenarios, each with a curated corpus of PubMed abstracts. Use these to test the full epistract pipeline end-to-end.

**Location:** All corpora are in `tests/corpora/` within this repository.

**How to run:** Open Claude Code in the epistract project directory, then use `/epistract-ingest` with the corpus path. Each scenario below includes the exact command.

**What to look for:** After each run, the interactive viewer opens in your browser. Use the query patterns listed under "Key Questions" to validate that the knowledge graph captured the right entities and relationships.

---

## Scenario 1: PICALM / Alzheimer's Disease — Genetic Target Validation

### Use Case

You are a neuroscience researcher investigating **PICALM** (phosphatidylinositol-binding clathrin assembly protein) as a potential therapeutic target for Alzheimer's disease. PICALM was identified as a risk locus in large-scale GWAS studies. You want to understand:

- What is the genetic evidence linking PICALM to Alzheimer's?
- What biological pathways does PICALM participate in?
- How does PICALM connect to amyloid and tau pathology?
- Are there any therapeutic approaches targeting PICALM-related biology?

This represents a **target validation** workflow — tracing from genetic evidence through biology to potential drug intervention.

### Corpus Details

| Property | Value |
|---|---|
| **Location** | `tests/corpora/01_picalm_alzheimers/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Source queries** | `PICALM Alzheimer disease genetic association` (6 results) |
| | `PICALM endocytosis amyloid beta tau pathology` (6 results) |
| | `phosphatidylinositol binding clathrin assembly protein Alzheimer` (6 results) |
| **Source database** | PubMed via NCBI E-utilities API (esearch + efetch) |
| **Date retrieved** | 2026-03-16 |
| **Format** | Plain text (.txt) — title, authors, journal, PMID, MeSH terms, abstract |

### Sample Documents

- `pmid_31385771.txt` — PICALM and Alzheimer's disease risk: meta-analysis
- `pmid_25186232.txt` — PICALM role in amyloid-beta clearance via endocytosis
- `pmid_26611835.txt` — PICALM modulates tau pathology through autophagy

### How to Run

```
/epistract-ingest tests/corpora/01_picalm_alzheimers/docs/ --output tests/corpora/01_picalm_alzheimers/output
```

### Key Questions to Validate (from UAT-101 through UAT-104)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-101 | What genes are associated with Alzheimer's risk? | GENE entities (PICALM, APOE, BIN1, CLU) → IMPLICATED_IN → DISEASE(Alzheimer's) |
| UAT-102 | What pathways does PICALM participate in? | PROTEIN(PICALM) → PARTICIPATES_IN → PATHWAY(endocytosis, clathrin-mediated) |
| UAT-103 | How does PICALM relate to amyloid beta? | Path from PICALM → PATHWAY → PROTEIN(APP/amyloid beta) |
| UAT-104 | Are there therapeutic approaches? | Any COMPOUND → TARGETS → proteins in PICALM pathways |

### What Success Looks Like

- PICALM extracted as both GENE and PROTEIN with correct disambiguation
- Alzheimer's disease extracted with MeSH-standard naming
- Endocytosis/clathrin pathways linked to PICALM
- Cross-document entity merging (PICALM mentioned across multiple papers → one node)
- ≥3 Alzheimer's risk genes identified with IMPLICATED_IN relations

---

## Scenario 2: KRAS G12C Inhibitor Landscape — Competitive Intelligence

### Use Case

You are an oncology drug discovery scientist mapping the **KRAS G12C inhibitor competitive landscape**. Two drugs are approved (sotorasib, adagrasib), and multiple next-generation inhibitors are in development. You want to understand:

- What compounds target KRAS G12C and what are their clinical results?
- What resistance mechanisms are emerging?
- What combination strategies are being explored?
- How do the approved drugs compare mechanistically?

This represents a **competitive intelligence** workflow — mapping the therapeutic landscape for a hot target.

### Corpus Details

| Property | Value |
|---|---|
| **Location** | `tests/corpora/02_kras_g12c_landscape/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Source queries** | `KRAS G12C inhibitor sotorasib adagrasib clinical trial` (5 results) |
| | `KRAS G12C covalent inhibitor resistance mechanism` (5 results) |
| | `KRAS G12C non-small cell lung cancer treatment` (5 results) |
| | `KRAS G12C combination immunotherapy` (5 results) |
| **Source database** | PubMed via NCBI E-utilities API |
| **Date retrieved** | 2026-03-16 |
| **Format** | Plain text (.txt) |

### Sample Documents

- `pmid_31658955.txt` — Hallin et al. 2020: MRTX849 (adagrasib) preclinical characterization
- `pmid_34607583.txt` — Sotorasib Phase II CodeBreaK 100 results
- `pmid_36764316.txt` — KRAS G12C resistance mechanisms and combination strategies

### How to Run

```
/epistract-ingest tests/corpora/02_kras_g12c_landscape/docs/ --output tests/corpora/02_kras_g12c_landscape/output
```

### Key Questions to Validate (from UAT-201 through UAT-205)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-201 | What drugs target KRAS G12C? | COMPOUND(sotorasib, adagrasib) → INHIBITS → GENE/PROTEIN(KRAS G12C) |
| UAT-202 | What clinical trials exist? | COMPOUND → EVALUATED_IN → CLINICAL_TRIAL(CodeBreaK, KRYSTAL) |
| UAT-203 | What resistance mechanisms? | GENE/PROTEIN → CONFERS_RESISTANCE_TO → COMPOUND |
| UAT-204 | What combinations are explored? | COMPOUND → COMBINED_WITH → COMPOUND |
| UAT-205 | What is sotorasib's mechanism? | COMPOUND(sotorasib) → HAS_MECHANISM → MOA(covalent KRAS G12C inhibition) |

### What Success Looks Like

- Both sotorasib and adagrasib extracted as COMPOUND with correct INN names
- KRAS G12C extracted as GENE (with variant) or SEQUENCE_VARIANT
- ≥2 named clinical trials (CodeBreaK 100, KRYSTAL-1) with phase and results
- ≥1 resistance mechanism (secondary KRAS mutations, MET amplification)
- NSCLC as the primary DISEASE indication
- Amgen and Mirati extracted as ORGANIZATION entities via DEVELOPED_BY

---

## Scenario 3: Rare Disease Therapeutics — PKU, Achondroplasia, Hemophilia A

### Use Case

You are a rare disease research analyst conducting **due diligence** on a rare disease therapeutics pipeline. Three key programs:

1. **Pegvaliase (Palynziq)** — enzyme substitution therapy for phenylketonuria (PKU)
2. **Vosoritide (Voxzogo)** — C-type natriuretic peptide analog for achondroplasia
3. **Valoctocogene roxaparvovec (Roctavian)** — AAV5 gene therapy for hemophilia A

You want to map the targets, mechanisms, clinical evidence, and competitive context for each program.

### Corpus Details

| Property | Value |
|---|---|
| **Location** | `tests/corpora/03_biomarin_rare_disease/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Source queries** | `pegvaliase phenylketonuria PKU enzyme substitution therapy` (5 results) |
| | `vosoritide achondroplasia FGFR3 C-type natriuretic peptide` (5 results) |
| | `valoctocogene roxaparvovec hemophilia A gene therapy` (5 results) |
| | `phenylketonuria phenylalanine hydroxylase dietary treatment` (5 results) |
| **Source database** | PubMed via NCBI E-utilities API |
| **Date retrieved** | 2026-03-16 |
| **Format** | Plain text (.txt) |

### Sample Documents

- `pmid_29653686.txt` — Pegvaliase Phase III PRISM trials
- `pmid_34694597.txt` — Vosoritide Phase III results in achondroplasia
- `pmid_38614387.txt` — Valoctocogene roxaparvovec gene therapy for hemophilia A

### How to Run

```
/epistract-ingest tests/corpora/03_biomarin_rare_disease/docs/ --output tests/corpora/03_biomarin_rare_disease/output
```

### Key Questions to Validate (from UAT-301 through UAT-303)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-301 | What is the PKU treatment? | COMPOUND(pegvaliase) → INDICATED_FOR → DISEASE(phenylketonuria) |
| UAT-302 | What is vosoritide's target? | COMPOUND(vosoritide) → TARGETS → PROTEIN(NPR-B/FGFR3 pathway) |
| UAT-303 | What gene therapy for hemophilia A? | COMPOUND(valoctocogene roxaparvovec) → INDICATED_FOR → DISEASE(hemophilia A) |

### What Success Looks Like

- Three distinct COMPOUND entities for three different drugs
- Three distinct DISEASE entities (PKU, achondroplasia, hemophilia A) — all rare diseases
- Phenylalanine ammonia lyase (PAL) extracted as the enzyme mechanism for pegvaliase
- FGFR3 pathway extracted for vosoritide
- Factor VIII / AAV5 gene therapy mechanism for valoctocogene
- Sponsor extracted as ORGANIZATION via DEVELOPED_BY
- Graph shows three distinct clusters (one per program) connected through the sponsor

---

## Scenario 4: Immuno-Oncology Combinations — Checkpoint Combinations

### Use Case

You are an immuno-oncology researcher tracking a **checkpoint inhibitor portfolio**:

1. **Nivolumab (Opdivo)** — anti-PD-1 monoclonal antibody
2. **Ipilimumab (Yervoy)** — anti-CTLA-4 monoclonal antibody
3. **Relatlimab** — anti-LAG-3 monoclonal antibody (combined with nivolumab as Opdualag)

You want to map the combination strategies, clinical trials, response biomarkers, and immune-related adverse events.

### Corpus Details

| Property | Value |
|---|---|
| **Location** | `tests/corpora/04_bms_immunooncology/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Source queries** | `nivolumab ipilimumab combination immunotherapy melanoma CheckMate` (5 results) |
| | `relatlimab LAG-3 nivolumab RELATIVITY clinical trial` (5 results) |
| | `opdivo checkpoint inhibitor PD-1` (5 results) |
| | `nivolumab resistance mechanism tumor microenvironment` (5 results) |
| **Source database** | PubMed via NCBI E-utilities API |
| **Date retrieved** | 2026-03-16 |
| **Format** | Plain text (.txt) |

### Sample Documents

- `pmid_25795410.txt` — CheckMate 037: nivolumab vs chemo in advanced melanoma
- `pmid_34359884.txt` — RELATIVITY-047: relatlimab + nivolumab Phase II/III
- `pmid_34986285.txt` — Nivolumab + ipilimumab long-term follow-up CheckMate 067

### How to Run

```
/epistract-ingest tests/corpora/04_bms_immunooncology/docs/ --output tests/corpora/04_bms_immunooncology/output
```

### Key Questions to Validate (from UAT-401 through UAT-404)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-401 | What checkpoint combinations? | COMPOUND(nivolumab) → COMBINED_WITH → COMPOUND(ipilimumab/relatlimab) |
| UAT-402 | What are key clinical trials? | COMPOUND → EVALUATED_IN → CLINICAL_TRIAL(CheckMate-067, RELATIVITY-047) |
| UAT-403 | What irAEs are reported? | COMPOUND → CAUSES → ADVERSE_EVENT(colitis, hepatitis, pneumonitis) |
| UAT-404 | What biomarkers predict response? | BIOMARKER(PD-L1, TMB) → PREDICTS_RESPONSE_TO → COMPOUND(nivolumab) |

### What Success Looks Like

- Nivolumab, ipilimumab, relatlimab as distinct COMPOUND entities with INN names
- PD-1, CTLA-4, LAG-3 as PROTEIN targets linked via TARGETS/INHIBITS
- ≥2 named CheckMate trials with phase and results data
- Immune-related adverse events (irAEs) extracted with MedDRA-like terminology
- PD-L1 and/or TMB extracted as BIOMARKER entities
- Melanoma and NSCLC as DISEASE indications
- Graph shows immunotherapy combination network centered on nivolumab

---

## Scenario 5: Cardiovascular & Inflammation — Mavacamten and Deucravacitinib

### Use Case

You are a cardiovascular/inflammation research analyst evaluating two newer programs:

1. **Mavacamten (Camzyos)** — selective cardiac myosin inhibitor for hypertrophic cardiomyopathy (HCM)
2. **Deucravacitinib (Sotyktu)** — selective TYK2 inhibitor for plaque psoriasis

These represent a diversification beyond oncology. You want to understand targets, mechanisms, clinical evidence, and safety profiles.

### Corpus Details

| Property | Value |
|---|---|
| **Location** | `tests/corpora/05_bms_cardiovascular/docs/` |
| **Documents** | 14 PubMed abstracts |
| **Source queries** | `mavacamten hypertrophic cardiomyopathy EXPLORER-HCM` (5 results) |
| | `cardiac myosin inhibitor obstructive hypertrophic cardiomyopathy` (5 results) |
| | `Camzyos mavacamten cardiac myosin inhibitor` (5 results) |
| | `deucravacitinib TYK2 psoriasis POETYK` (5 results) |
| **Source database** | PubMed via NCBI E-utilities API |
| **Date retrieved** | 2026-03-16 |
| **Format** | Plain text (.txt) |

### Sample Documents

- `pmid_32498620.txt` — EXPLORER-HCM study design and rationale
- `pmid_36115523.txt` — Mavacamten Phase III EXPLORER-HCM results
- `pmid_38176782.txt` — Deucravacitinib TYK2 selectivity and psoriasis efficacy

### How to Run

```
/epistract-ingest tests/corpora/05_bms_cardiovascular/docs/ --output tests/corpora/05_bms_cardiovascular/output
```

### Key Questions to Validate (from UAT-501 through UAT-503)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-501 | What is mavacamten's mechanism? | COMPOUND(mavacamten) → HAS_MECHANISM → MOA(cardiac myosin inhibition) |
| UAT-502 | What clinical evidence for HCM? | COMPOUND(mavacamten) → EVALUATED_IN → CLINICAL_TRIAL(EXPLORER-HCM) |
| UAT-503 | What is deucravacitinib's target? | COMPOUND(deucravacitinib) → INHIBITS → PROTEIN(TYK2) |

### What Success Looks Like

- Mavacamten and deucravacitinib as distinct COMPOUND entities
- Cardiac myosin (beta-MHC) and TYK2 as PROTEIN targets
- HCM and psoriasis as distinct DISEASE entities
- EXPLORER-HCM and POETYK trials extracted with phase and results
- Graph shows two distinct clusters (cardiology + dermatology) both linked to the developer
- LVOT gradient reduction mentioned as clinical endpoint for mavacamten
- JAK/STAT pathway context for deucravacitinib

---

## Running All Scenarios

To run all five scenarios sequentially:

```
/epistract-ingest tests/corpora/01_picalm_alzheimers/docs/ --output tests/corpora/01_picalm_alzheimers/output
/epistract-ingest tests/corpora/02_kras_g12c_landscape/docs/ --output tests/corpora/02_kras_g12c_landscape/output
/epistract-ingest tests/corpora/03_biomarin_rare_disease/docs/ --output tests/corpora/03_biomarin_rare_disease/output
/epistract-ingest tests/corpora/04_bms_immunooncology/docs/ --output tests/corpora/04_bms_immunooncology/output
/epistract-ingest tests/corpora/05_bms_cardiovascular/docs/ --output tests/corpora/05_bms_cardiovascular/output
```

After each run, use `/epistract-query` to spot-check entities:

```
/epistract-query "sotorasib" --output tests/corpora/02_kras_g12c_landscape/output
/epistract-query "nivolumab" --output tests/corpora/04_bms_immunooncology/output
/epistract-query "PICALM" --output tests/corpora/01_picalm_alzheimers/output
```

## Acceptance Criteria

A scenario **passes** when:

1. All documents in the corpus are processed without errors
2. The knowledge graph contains entities matching the key types for that scenario
3. The key relations from the "Expected Graph Evidence" column are present
4. The interactive viewer shows meaningful clusters and connections
5. Cross-document entity deduplication works (same entity from multiple papers → one node)
6. Confidence scores are calibrated (primary findings > 0.8, secondary > 0.6)

## Corpus Provenance

All documents were retrieved from **PubMed** (National Library of Medicine) via the [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/) on 2026-03-16. PubMed abstracts are publicly available for research use under NLM's terms. No full-text articles, copyrighted figures, or supplementary materials are included — only abstracts and metadata.

The PubMed queries used for each corpus are documented above. Results were sorted by relevance, deduplicated by PMID, and capped at 15 documents per topic.
