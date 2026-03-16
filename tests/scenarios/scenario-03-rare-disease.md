# Scenario 3: Rare Disease Therapeutics — PKU, Achondroplasia, Hemophilia A

**Status:** Completed
**Last run:** 2026-03-16
**Output:** [`tests/corpora/03_rare_disease/output/`](../corpora/03_rare_disease/output/)
**Interactive graph:** [`graph.html`](../corpora/03_rare_disease/output/graph.html) (clone repo and open locally in browser)

---

## Knowledge Graph

![Rare Disease Therapeutics Knowledge Graph](screenshots/scenario-03-graph.png)

*Force-directed graph showing 94 nodes and 229 links across 4 auto-labeled communities. Each community corresponds to a distinct therapeutic program. Node color = community membership. Node size = connection count.*

---

## Use Case

You are a rare disease research analyst conducting **due diligence** on a rare disease therapeutics pipeline. Three key programs:

1. **Pegvaliase (Palynziq)** — enzyme substitution therapy for phenylketonuria (PKU)
2. **Vosoritide (Voxzogo)** — C-type natriuretic peptide analog for achondroplasia
3. **Valoctocogene roxaparvovec (Roctavian)** — AAV5 gene therapy for hemophilia A

You want to map the targets, mechanisms, clinical evidence, safety profiles, and regulatory milestones for each program.

This represents a **due diligence** workflow — evaluating a diversified rare disease pipeline across three distinct modalities (enzyme substitution, peptide analog, gene therapy).

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/03_rare_disease/docs/` |
| **Documents** | 15 PubMed abstracts (2016–2025) |
| **Format** | Plain text (.txt) |
| **Source** | PubMed via NCBI E-utilities API, retrieved 2026-03-16 |

**PubMed queries used:**
- `pegvaliase phenylketonuria PKU enzyme substitution therapy`
- `vosoritide achondroplasia FGFR3 C-type natriuretic peptide`
- `valoctocogene roxaparvovec hemophilia A gene therapy`

### Documents

| PMID | Year | First Author | Program | Focus |
|---|---|---|---|---|
| 26684019 | 2016 | Legeai-Mallet | Achondroplasia | CNP analog (BMN111) preclinical rationale |
| 29653686 | 2018 | Thomas | PKU | Pegvaliase PRISM Phase 3 — 261 patients, Phe reduction 68.7% |
| 31258325 | 2019 | Hydery | PKU | Comprehensive pegvaliase review — first FDA-approved enzyme substitution |
| 31375398 | 2019 | Hausmann | PKU | Pegvaliase immunological profile — Type III hypersensitivity management |
| 34070375 | 2021 | Wrobel | Achondroplasia | Treatment methods review — rhGH vs vosoritide comparison |
| 34694597 | 2021 | Duggan | Achondroplasia | Vosoritide first approval — EU August 2021, BioMarin |
| 35294811 | 2022 | Ozelo | Hemophilia A | **NEJM**: GENEr8-1 Phase 3, 1-year — FVIII +41.9 IU/dL, bleeding -83.8% |
| 36812433 | 2023 | Mahlangu | Hemophilia A | **NEJM**: GENEr8-1 2-year — FVIII half-life 123 weeks, bleeding -84.5% |
| 38522180 | 2024 | Scala | PKU | Pegvaliase real-world Italy — 18 cases, 61% reached Phe <600 |
| 38614387 | 2024 | Madan | Hemophilia A | GENEr8-1 3-year — FVIII 18.4 IU/dL, bleeding -96.8%, QoL improved |
| 38694233 | 2024 | Harding | PKU | PRISM final results — 261 patients, sustained Phe response 85.5% |
| 38813446 | 2024 | Dauber | Achondroplasia | Vosoritide in hypochondroplasia — Phase 2, AGV +2.26 SD |
| 38991118 | 2024 | Samelson-Jones | Hemophilia A | Roctavian review — EMA/FDA approvals, FVIII decline concern |
| 39226466 | 2024 | La Mura | Hemophilia A | Liver monitoring expert guidance — contraindications, ALT management |
| 40821249 | 2025 | Jones | Achondroplasia | Vosoritide review — 7-year data, real-world evidence France/Germany/Japan |

---

## How to Run

```
/epistract-ingest tests/corpora/03_rare_disease/docs/ --output tests/corpora/03_rare_disease/output
```

---

## Results

### Run Statistics

| Metric | Value |
|---|---|
| Documents processed | 15 |
| Parallel extraction agents | 5 (3 docs each) |
| Graph nodes (deduplicated) | 94 |
| Graph links | 229 |
| Communities detected | 4 |
| Raw entities extracted | 182 |
| Raw relations extracted | 128 |
| NCT numbers detected | 12 |

### Entity Types

| Entity Type | Raw | Deduplicated |
|---|---|---|
| COMPOUND | 20 | 5 |
| PROTEIN | 20 | 7 |
| DISEASE | 19 | 7 |
| ADVERSE_EVENT | 19 | 9 |
| PHENOTYPE | 16 | 6 |
| BIOMARKER | 15 | 8 |
| CLINICAL_TRIAL | 12 | 7 |
| MECHANISM_OF_ACTION | 10 | 8 |
| GENE | 9 | 3 |
| METABOLITE | 9 | 1 |
| PATHWAY | 5 | 5 |
| SEQUENCE_VARIANT | 5 | 5 |
| ORGANIZATION | 5 | 2 |
| REGULATORY_ACTION | 4 | 4 |
| CELL_OR_TISSUE | 3 | 2 |
| DOCUMENT | — | 15 |

### Relation Types

| Relation Type | Count | What It Captures |
|---|---|---|
| MENTIONED_IN | 142 | Entity-to-document provenance |
| CAUSES | 10 | Drug → adverse events (arthralgia, ALT elevation, injection site reactions) |
| ASSOCIATED_WITH | 10 | General associations |
| HAS_MECHANISM | 8 | Drug → mechanism (enzyme substitution, CNP analog, gene addition) |
| EVALUATED_IN | 7 | Drug → clinical trial |
| IMPLICATED_IN | 7 | Gene → disease |
| HAS_VARIANT | 5 | FGFR3 → activating mutations |
| PREDICTS_RESPONSE_TO | 5 | Biomarker → drug response |
| INDICATED_FOR | 4 | Drug → disease indication |
| INHIBITS | 4 | Vosoritide → FGFR3 signaling |
| ENCODES | 4 | Gene → protein (F8 → FVIII, PAH → PAH enzyme) |
| DIAGNOSTIC_FOR | 4 | Biomarker → disease (blood Phe, FVIII activity) |
| GRANTS_APPROVAL_FOR | 4 | Regulatory action → drug (FDA/EMA approvals) |
| CONTRAINDICATED_FOR | 3 | Drug → contraindicated conditions (liver disease) |
| ACTIVATES | 2 | Pathway activation |
| EXPRESSED_IN | 2 | Tissue expression |
| PARTICIPATES_IN | 2 | Pathway membership |
| BINDS_TO | 1 | Vosoritide → NPR-B receptor binding |
| COMBINED_WITH | 1 | Prednisone co-administration with gene therapy |
| LOCALIZED_TO | 1 | Tissue localization |
| REGULATES_EXPRESSION | 1 | Gene regulation |

---

## Communities

The graph self-organized into **4 communities** — one for each therapeutic program, with achondroplasia splitting into a molecular biology cluster and a therapeutic cluster:

### 1. Phenylketonuria — PAL, Phenylalanine Hydroxylase — 19 members

The **PKU/pegvaliase program**. Contains pegvaliase (the compound), phenylalanine hydroxylase (the deficient enzyme), phenylalanine ammonia lyase (the therapeutic enzyme), PKU (the disease), the PRISM-1 and PRISM-2 clinical trials, blood phenylalanine (the primary biomarker), adverse events (arthralgia, injection-site reactions, hypersensitivity), FDA approval, and metabolites (phenylalanine, trans-cinnamic acid, ammonia). This cluster captures the complete **enzyme substitution therapy story**.

**Key entities:** pegvaliase, PKU, PAH, PAL, phenylalanine, PRISM-1, PRISM-2, blood Phe biomarker, FDA approval

### 2. Prednisone / Valoctocogene Roxaparvovec / Autoimmune Hepatitis — 16 members

The **hemophilia A/gene therapy program**. Contains valoctocogene roxaparvovec (Roctavian), hemophilia A, the GENEr8-1 trial, FVIII expression and activity (biomarkers), ALT elevation (key safety signal), prednisone (immunosuppressant co-medication), FDA/EMA approvals, BioMarin, and contraindications (autoimmune hepatitis, cirrhosis, liver infection). The community label highlights the **safety management** dimension — liver monitoring and immunosuppression are central to this program's clinical story.

**Key entities:** valoctocogene roxaparvovec, hemophilia A, GENEr8-1, FVIII activity, ALT elevation, prednisone, BioMarin, FDA/EMA approvals

### 3. C-Type Natriuretic Peptide Analog — 14 members

The **vosoritide therapeutic program**. Contains vosoritide (the compound), NPR-B receptor (the target), BioMarin (the developer), MAPK pathway downregulation (the mechanism), EU approval, the Phase II/III trial, chondrogenesis pathway, and NCT04219007 (hypochondroplasia extension). This cluster captures **how vosoritide works and its regulatory path**.

**Key entities:** vosoritide, NPR-B, BioMarin, MAPK pathway, EU approval, chondrogenesis

### 4. Bone Growth (FGFR3) — 12 members

The **achondroplasia disease biology** cluster. Contains FGFR3 (the causative gene/protein), achondroplasia and hypochondroplasia (the diseases), activating and missense mutations (the variants), growth-related phenotypes (dwarfism, short stature, spinal canal stenosis), and recombinant human growth hormone (the prior standard of care). This cluster captures the **biological understanding** underlying the therapeutic need.

**Key entities:** FGFR3, achondroplasia, hypochondroplasia, FGFR3 activating mutation, dwarfism, bone growth, rhGH

---

## Scientific Narrative

This corpus maps three distinct rare disease therapeutic programs, each representing a different treatment modality:

1. **Enzyme Substitution (PKU/Pegvaliase)** — PKU is caused by PAH deficiency → phenylalanine accumulation → neurological damage. Pegvaliase provides an alternative catabolic pathway: PAL enzyme converts phenylalanine to trans-cinnamic acid + ammonia. PRISM trials (261 patients) showed 68.7% blood Phe reduction at 24 months, with 59.4% reaching normal levels (≤120 µmol/L). Key challenge: Type III hypersensitivity reactions require careful induction/titration and H1-receptor antagonist premedication. Real-world data from Italy confirms efficacy but highlights adherence challenges.

2. **Peptide Analog (Achondroplasia/Vosoritide)** — Achondroplasia is caused by gain-of-function FGFR3 mutations → impaired endochondral ossification → disproportionate short stature. Vosoritide (CNP analog) binds NPR-B → inhibits FGFR3-activated MAPK pathway → restores chondrogenesis. Phase II/III: AGV increase of 1.5-2.0 cm/year sustained over 7 years. EU approved August 2021. Now extending to hypochondroplasia (Phase 2: AGV +2.26 SD). First targeted therapy for a skeletal dysplasia.

3. **Gene Therapy (Hemophilia A/Valoctocogene Roxaparvovec)** — Hemophilia A is caused by F8 mutations → FVIII deficiency → bleeding. Roctavian delivers B-domain-deleted FVIII via AAV5 to hepatocytes. GENEr8-1 (134 men): FVIII +41.9 IU/dL at year 1, bleeding -83.8%, FVIII use -98.6%. Year 3: efficacy maintained (0.97 bleeds/year), but FVIII decline raises durability questions (half-life ~123 weeks). ALT elevation in 85.8% managed with prednisone. First licensed HA gene therapy (EMA 2022, FDA 2023). Expert guidance: contraindicated with liver stiffness ≥8 kPa.

---

## Key Questions Validated (UAT-301 through UAT-303)

| # | Question | Result | Graph Evidence |
|---|---|---|---|
| UAT-301 | What is the PKU treatment? | **PASS** | pegvaliase → INDICATED_FOR → PKU; HAS_MECHANISM → enzyme substitution therapy; PAH IMPLICATED_IN PKU; blood Phe DIAGNOSTIC_FOR PKU |
| UAT-302 | What is vosoritide's target? | **PASS** | vosoritide → BINDS_TO → NPR-B; INHIBITS → FGFR3 signalling; HAS_MECHANISM → CNP analog; FGFR3 IMPLICATED_IN achondroplasia |
| UAT-303 | What gene therapy for hemophilia A? | **PASS** | valoctocogene roxaparvovec → INDICATED_FOR → hemophilia A; HAS_MECHANISM → AAV gene addition; DEVELOPED_BY → BioMarin; FVIII activity DIAGNOSTIC_FOR hemophilia A |

---

## Comparison with Prior Scenarios

| Metric | S1 (PICALM/AD) | S2 (KRAS G12C) | S3 (Rare Disease) |
|---|---|---|---|
| Documents | 15 | 16 | 15 |
| Graph nodes | 149 | 108 | 94 |
| Graph links | 457 | 307 | 229 |
| Communities | 6 | 4 | 4 |
| Dominant entity types | GENE, PROTEIN | COMPOUND, SEQUENCE_VARIANT | COMPOUND, ADVERSE_EVENT, BIOMARKER |
| Key relation types | IMPLICATED_IN | CONFERS_RESISTANCE_TO | CAUSES, INDICATED_FOR, DIAGNOSTIC_FOR |
| New relation types exercised | — | — | CONTRAINDICATED_FOR, GRANTS_APPROVAL_FOR, DIAGNOSTIC_FOR, PREDICTS_RESPONSE_TO |

Scenario 3 exercises 4 new relation types not used in prior scenarios — **CONTRAINDICATED_FOR** (liver disease contraindications for gene therapy), **GRANTS_APPROVAL_FOR** (FDA/EMA regulatory milestones), **DIAGNOSTIC_FOR** (biomarker-disease links), and **PREDICTS_RESPONSE_TO** (biomarker-drug response prediction). It also heavily uses CAUSES (drug-AE) and BIOMARKER entities, reflecting the clinical/safety focus of rare disease due diligence.

---

## Output Files

| File | Description |
|---|---|
| [`output/extractions/`](../corpora/03_rare_disease/output/extractions/) | 15 JSON extraction files |
| [`output/graph_data.json`](../corpora/03_rare_disease/output/graph_data.json) | Knowledge graph (94 nodes, 229 links) |
| [`output/communities.json`](../corpora/03_rare_disease/output/communities.json) | Community assignments with descriptive labels |
| [`output/graph.html`](../corpora/03_rare_disease/output/graph.html) | Interactive graph viewer |
| [`output/relation_review.yaml`](../corpora/03_rare_disease/output/relation_review.yaml) | Relations flagged for review |
| [`output/validation/`](../corpora/03_rare_disease/output/validation/) | Validation results (12 NCT numbers detected) |
| [`screenshots/scenario-03-graph.png`](screenshots/scenario-03-graph.png) | Graph screenshot |
