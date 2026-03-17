# Scenario 6: GLP-1 Receptor Agonists — Competitive Intelligence

**Status:** Completed (2026-03-17)
**Output:** `tests/corpora/06_glp1_landscape/output/`

![GLP-1 Competitive Intelligence Knowledge Graph](screenshots/scenario-06-graph.png)

---

## Use Case

You are a competitive intelligence analyst at a pharmaceutical company evaluating the GLP-1 receptor agonist landscape. Your goal is to build a comprehensive knowledge graph covering:

1. **Key compounds** — semaglutide, tirzepatide, orforglipron, retatrutide, survodutide, CagriSema, danuglipron
2. **Companies** — Novo Nordisk, Eli Lilly, Pfizer, Hanmi Pharmaceutical, Zealand Pharma, Boehringer Ingelheim
3. **Indications** — T2D, obesity, MASH/NASH, cardiovascular, Alzheimer's, addiction, CKD, sleep apnea, PCOS, pain
4. **Patent landscape** — peptide sequences, CAS numbers, chemical formulas, patent assignees
5. **Pipeline evolution** — single → dual → triple agonists, peptide → oral small molecule

**What makes this scenario unique:**
- **Multi-source corpus** — first scenario to use PubMed + Google Scholar + Google Patents via SerpAPI (not just PubMed)
- **Patent extraction** — molecular identifiers (peptide sequences, CAS numbers, InChIKeys) extracted from patent documents
- **Largest corpus** — 34 documents (vs 15-16 for S1-S5)
- **CI workflow** — mimics how a human researcher does competitive intelligence: searching multiple sources, cross-referencing findings, building a knowledge graph

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/06_glp1_landscape/docs/` |
| **Documents** | 34 (24 PubMed abstracts + 10 patents) |
| **Format** | Plain text (.txt) |
| **Sources** | PubMed via NCBI E-utilities, Google Scholar via SerpAPI, Google Patents via SerpAPI |
| **Date retrieved** | 2026-03-17 |

### Corpus Assembly Methodology

This scenario used a multi-source assembly pipeline that mirrors a real researcher's competitive intelligence workflow:

**Step 1: PubMed (NCBI E-utilities)**
- 9 targeted queries covering core compounds and emerging indications
- Queries: `"semaglutide" AND "cardiovascular"`, `"tirzepatide" AND "obesity"`, `"orforglipron" AND "oral"`, `"survodutide" AND "NASH"`, `"retatrutide" AND "triple agonist"`, `"CagriSema" AND "obesity"`, `"GLP-1 receptor agonist" AND "Alzheimer"`, `"semaglutide" AND "MASH"`, `"GLP-1" AND "addiction"`
- Retrieved 18 unique abstracts with full structured data (authors, MeSH terms, journal)

**Step 2: Google Scholar (SerpAPI)**
- 8 queries with `as_sdt=7` (include patents), `num=10`
- Queries covering: competitive landscape, head-to-head comparisons, oral small molecules, neurodegeneration, addiction, triple agonists, CagriSema, oral nonpeptide
- 79 unique results discovered; used to identify 6 additional PubMed papers for topics not covered by direct PubMed search
- Note: Scholar snippets were too short (~500 bytes) for extraction — full abstracts retrieved from PubMed for the same papers

**Step 3: Google Patents (SerpAPI)**
- 5 targeted queries with `assignee`, `country`, `status`, `after` filters
- Queries: Novo Nordisk GLP-1 peptides, Eli Lilly tirzepatide, oral small molecule GLP-1, triple agonists, oral semaglutide SNAC
- 42 unique patents discovered; 10 selected based on molecular data richness and assignee diversity
- Full abstracts and molecular data fetched from patents.google.com

**Step 4: Enrichment**
- Patent documents manually enriched with peptide sequences, CAS numbers, chemical formulas, and InChIKeys from patent full text
- PubMed papers cross-referenced to avoid duplicates

### Bring Your Own Papers

Several high-impact papers (Lancet, JAMA, BMJ, NEJM) were behind publisher paywalls and could not be ingested automatically. Scientists with institutional access can supplement this corpus by adding full-text PDFs to the `docs/` directory. Key papers to consider:

- Rosenstock et al., Lancet 2023 — Retatrutide Phase 2 (405 citations)
- Yao et al., BMJ 2024 — Comparative effectiveness meta-analysis (503 citations)
- Rodriguez et al., JAMA Intern Med 2024 — Semaglutide vs tirzepatide real-world (257 citations)
- Frias et al., Lancet 2023 — CagriSema Phase 2 (311 citations)

Re-running `/epistract-ingest` after adding papers will enrich the knowledge graph with additional entities and relations.

### Patent Documents

| # | Patent ID | Assignee | Subject |
|---|-----------|----------|---------|
| 1 | US10888605B2 | Novo Nordisk | Semaglutide formulation (phenol-free) |
| 2 | US11357820B2 | Eli Lilly | Tirzepatide composition (dual GIP/GLP-1) |
| 3 | US10335462B2 | Novo Nordisk | Long-acting GLP-1 peptides (dosing regimen) |
| 4 | WO2020159949A1 | Eli Lilly | Tirzepatide manufacturing process |
| 5 | WO2018109607A1 | Pfizer | Oral small-molecule GLP-1 agonists (benzimidazole class) |
| 6 | US10370426B2 | Hanmi Pharmaceutical | Triple GLP-1/GIP/glucagon agonist (102 peptide variants) |
| 7 | WO2019239319A1 | Pfizer | Danuglipron benzimidazole series (2nd generation) |
| 8 | US12054528B2 | Novo Nordisk | GLP-1/amylin co-agonist (single molecule, 256 SEQ IDs) |
| 9 | US11111285B2 | Zealand Pharma | Glucagon-GLP-1-GIP triple agonist compounds |
| 10 | US11622996B2 | Novo Nordisk | Oral semaglutide + SNAC (Rybelsus formulation) |

---

## How to Run

```
/epistract-ingest tests/corpora/06_glp1_landscape/docs/ --output tests/corpora/06_glp1_landscape/output
```

---

## Key Questions to Validate (UAT-601 through UAT-606)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-601 | What compounds target GLP-1R? | COMPOUND(semaglutide/tirzepatide/orforglipron/...) → ACTIVATES → PROTEIN(GLP1R) |
| UAT-602 | Which companies develop which drugs? | COMPOUND(semaglutide) → DEVELOPED_BY → ORGANIZATION(Novo Nordisk) |
| UAT-603 | What is tirzepatide's dual mechanism? | COMPOUND(tirzepatide) → ACTIVATES → PROTEIN(GLP1R) + PROTEIN(GIPR) |
| UAT-604 | What emerging indications for GLP-1 RAs? | COMPOUND(semaglutide) → INDICATED_FOR → DISEASE(Alzheimer's/MASH/CKD/addiction/...) |
| UAT-605 | What molecular data from patents? | PEPTIDE_SEQUENCE entities with sequence attributes; CAS numbers in COMPOUND attributes |
| UAT-606 | What clinical trials are mapped? | COMPOUND → EVALUATED_IN → CLINICAL_TRIAL (with NCT numbers) |

## What Success Looks Like

- All 7+ GLP-1 compounds as distinct COMPOUND entities with rich attributes
- GLP1R, GIPR, GCGR as PROTEIN targets with correct agonist relationships
- 10+ DISEASE entities spanning T2D, obesity, MASH, cardiovascular, neurodegeneration, addiction, CKD
- 15+ CLINICAL_TRIAL entities with NCT numbers (SUSTAIN, STEP, SURPASS, SURMOUNT, FLOW, REDEFINE, ACHIEVE)
- 5+ ORGANIZATION entities (Novo Nordisk, Eli Lilly, Pfizer, Hanmi, Zealand)
- PEPTIDE_SEQUENCE entities from patent extraction
- Graph shows meaningful community structure reflecting the competitive landscape
- Patent-derived molecular identifiers (CAS, sequences, InChIKeys) validated

## Expected Communities

- **Semaglutide / oral delivery** — SNAC, GLP-1(7-37) peptide, Rybelsus, oral formulation
- **Tirzepatide / next-gen competitors** — dual/triple agonists, orforglipron, MASLD
- **CagriSema / amylin** — cagrilintide, combination therapy, REDEFINE trials
- **Emerging indications** — neurodegeneration, addiction, cardiovascular protection
- **MASH therapeutics** — survodutide, retatrutide, competitor drugs (resmetirom, etc.)

---

## Results

**Status:** Completed (2026-03-17)

### Graph Statistics

| Metric | Value |
|---|---|
| Documents processed | 34 (24 PubMed + 10 patents) |
| Graph nodes (deduplicated) | 206 |
| Graph links | 630 |
| Communities detected | 9 |

### Entity Type Distribution

| Entity Type | Count |
|---|---|
| DOCUMENT | 34 |
| COMPOUND | 34 |
| DISEASE | 31 |
| CLINICAL_TRIAL | 19 |
| MECHANISM_OF_ACTION | 14 |
| PROTEIN | 11 |
| PUBLICATION | 9 |
| PATHWAY | 9 |
| BIOMARKER | 9 |
| ADVERSE_EVENT | 9 |
| ORGANIZATION | 8 |
| PHENOTYPE | 8 |
| PEPTIDE_SEQUENCE | 3 |
| CELL_OR_TISSUE | 3 |
| PROTEIN_DOMAIN | 2 |
| METABOLITE | 2 |
| REGULATORY_ACTION | 1 |

**Entity types exercised: 17 of 17 (100%)**

### Relation Type Distribution

| Relation Type | Count |
|---|---|
| MENTIONED_IN | 384 |
| INDICATED_FOR | 64 |
| ASSOCIATED_WITH | 30 |
| ACTIVATES | 26 |
| EVALUATED_IN | 21 |
| HAS_MECHANISM | 20 |
| CAUSES | 15 |
| PARTICIPATES_IN | 12 |
| DEVELOPS | 11 |
| PUBLISHED_IN | 9 |
| DIAGNOSTIC_FOR | 7 |
| COMBINED_WITH | 6 |
| IMPLICATED_IN | 6 |
| BINDS_TO | 4 |
| TARGETS | 3 |
| DERIVED_FROM | 3 |
| EXPRESSED_IN | 3 |
| HAS_DOMAIN | 2 |
| GRANTS_APPROVAL_FOR | 2 |
| REGULATES_EXPRESSION | 1 |
| PREDICTS_RESPONSE_TO | 1 |

**Relation types exercised: 21 of 30 (70%)**

### Top Connected Entities (Hub Nodes)

| Connections | Entity Type | Name |
|---|---|---|
| 59 | COMPOUND | semaglutide |
| 59 | PROTEIN | GLP1R |
| 52 | DISEASE | obesity |
| 33 | DISEASE | type 2 diabetes mellitus |
| 26 | COMPOUND | tirzepatide |
| 17 | COMPOUND | orforglipron |
| 17 | COMPOUND | retatrutide |
| 15 | COMPOUND | CagriSema |
| 15 | COMPOUND | Zealand triple agonist peptide |
| 14 | MECHANISM_OF_ACTION | GLP-1 receptor agonism |

### Communities

| # | Community Label | Members | Key Entities |
|---|---|---|---|
| 1 | Metabolic Dysfunction-Associated Steatohepatitis — GCGR, Albumin, GIPR | 26 | survodutide, retatrutide, GCGR, liver fibrosis |
| 2 | GLP-1 Receptor Agonism / Chronic Low-Grade Inflammation | 14 | GLP-1 RAs (class), inflammation pathway, cardiovascular protection |
| 3 | Danuglipron / Alzheimer Disease / Parkinson Disease | 19 | danuglipron, oral GLP-1, neurodegeneration, cognitive function |
| 4 | GLP-1(7-37) / SNAC / Semaglutide | 24 | semaglutide, GLP-1(7-37) peptide, SNAC, oral delivery, Rybelsus |
| 5 | Appetite Regulation in Infralimbic Cortex | 21 | GABA, central amygdala, alcohol use disorder, addiction |
| 6 | Orforglipron / Tirzepatide / MASLD | 18 | orforglipron, tirzepatide, MASLD, ACHIEVE, SURMOUNT trials |
| 7 | CagriSema / GLP-1/Amylin Co-Agonist / Cagrilintide | 17 | CagriSema, cagrilintide, amylin receptor, REDEFINE trials |
| 8 | Anti-Inflammatory Activity | 9 | anti-inflammatory pathway, cardiovascular risk reduction |
| 9 | Denifanstat / Efruxifermin / Lanifibranor | 9 | MASH competitor therapies, non-GLP-1 approaches |

### Community Analysis — Competitive Landscape Interpretation

**Community 1 (MASH therapeutics)** correctly groups survodutide (GLP-1/glucagon dual agonist) and retatrutide (triple agonist) with GCGR and liver-related entities. This reflects the emerging MASH indication where glucagon receptor agonism drives hepatic lipid oxidation — a distinct mechanism from weight loss alone.

**Community 4 (Oral semaglutide)** captures the SNAC absorption enhancer technology cluster, including GLP-1(7-37) peptide sequence and oral formulation innovation. This is the first scenario to extract molecular delivery technology as a distinct community.

**Community 5 (Addiction/appetite)** is a novel finding — the graph correctly identifies brain regions (infralimbic cortex, central amygdala), neurotransmitters (GABA), and substance use disorders as a coherent cluster linked to GLP-1 receptor expression in the CNS. This emerging indication was not an obvious cluster a priori.

**Community 7 (CagriSema)** captures the combination therapy strategy: amylin receptor agonism + GLP-1 receptor agonism in a single administration. The graph correctly separates this from pure GLP-1 agonism (Communities 2/4) and from the single-molecule co-agonist approach (patent 08).

**Community 9 (Non-GLP-1 MASH drugs)** is a "competitive landscape" cluster — it groups MASH therapies that compete with GLP-1 agonists (denifanstat, efruxifermin, lanifibranor) but act through different mechanisms. This emerges from the MASH network meta-analysis paper (PMID 39903735).

### Molecular Identifiers Validated

| Type | Count | Examples |
|---|---|---|
| Amino acid sequences | 5 | GLP-1(7-37): HAEGTFTSDVSSYLEGQAAKEFIAWLVKGRG, tirzepatide SEQ ID NO: 1 |
| CAS numbers | 1 | Tirzepatide: 2023788-19-2 |
| InChIKeys | 2 | SNAC: UOENJXXSKABLJL-UHFFFAOYSA-M |
| SEQ IDs | 5 | Patents 06, 08, 09 (102, 256, 58 variants respectively) |
| NCT numbers | 17 | NCT03548935, NCT04184622, NCT03819153, NCT05394519, NCT05567796, NCT05971940, etc. |
| US Patents | 6 | US10888605B2, US11357820B2, US10335462B2, etc. |

### UAT Results

| # | Question | Result | Evidence |
|---|---|---|---|
| UAT-601 | Compounds targeting GLP-1R? | PASS | 59 connections to GLP1R node; semaglutide, tirzepatide, orforglipron, danuglipron, liraglutide all linked via ACTIVATES |
| UAT-602 | Company → drug mapping? | PASS | 8 ORGANIZATION entities; Novo Nordisk, Eli Lilly, Pfizer, Hanmi, Zealand linked via DEVELOPS to their compounds |
| UAT-603 | Tirzepatide dual mechanism? | PASS | tirzepatide → ACTIVATES → GLP1R + GIPR; CAS 2023788-19-2 in attributes |
| UAT-604 | Emerging indications? | PASS | INDICATED_FOR links to 31 diseases: obesity, T2D, MASH, CKD, Alzheimer's, Parkinson's, PCOS, AUD, chronic pain, sleep apnea |
| UAT-605 | Patent molecular data? | PASS | 3 PEPTIDE_SEQUENCE entities; CAS numbers, InChIKeys, chemical formulas in COMPOUND attributes |
| UAT-606 | Clinical trial mapping? | PASS | 19 CLINICAL_TRIAL entities; 17 NCT numbers; SUSTAIN, STEP, SURPASS, SURMOUNT, FLOW, REDEFINE, ACHIEVE mapped |

**UATs passed: 6/6**
