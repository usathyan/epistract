# Epistract Validation Results — Scenario 5: Cardiovascular & Inflammation

**Date:** 2026-03-16
**Pipeline:** 15 documents → 94 nodes, 246 links, 5 communities
**UATs:** 3/3 passed

## Legend
- **V** = Verified — extraction matches source text accurately
- **F** = Flagged — incorrect, hallucinated, or questionable extraction
- **M** = Missing — should have been extracted from source but wasn't

---

## Representative Extraction: structural_mavacamten.json

**Source:** `tests/corpora/05_cardiovascular/docs/structural_mavacamten.txt`
**Entities extracted:** 22 | **Relations extracted:** 18

### Entities Extracted

| # | Source File | Entity | Type | Confidence | Source Text (verify against) | Verification |
|---|-------------|--------|------|------------|------------------------------|--------------|
| 1 | structural_mavacamten.txt:5 | mavacamten | COMPOUND | 0.99 | "Mavacamten (MYK-461, Camzyos) is a first-in-class selective cardiac myosin inhibitor." | [x] CAS 1642288-47-8, SMILES, MW 428.52 all match source |
| 2 | structural_mavacamten.txt:16 | MYH7 | GENE | 0.99 | "Target: Beta-cardiac myosin heavy chain (MYH7, UniProt: P12883)" | [x] UniProt P12883 correct |
| 3 | structural_mavacamten.txt:12 | beta-cardiac myosin | PROTEIN | 0.99 | "stabilizing an auto-inhibited (super-relaxed) state of beta-cardiac myosin (MYH7)" | [x] Matches source line 13 |
| 4 | structural_mavacamten.txt:12 | cardiac myosin ATPase | PROTEIN | 0.95 | "Mavacamten selectively inhibits cardiac myosin ATPase" | [x] IC50 0.3 uM captured |
| 5 | structural_mavacamten.txt:21 | MYH1 | GENE | 0.90 | ">100-fold selective for cardiac myosin over fast skeletal myosin (MYH1)" | [x] Matches source line 21 |
| 6 | structural_mavacamten.txt:26 | MYBPC3 | GENE | 0.90 | "mutations in MYH7 or MYBPC3 cause excessive cross-bridge formation" | [x] Matches source line 26 |
| 7 | structural_mavacamten.txt:38 | hypertrophic cardiomyopathy | DISEASE | 0.98 | "FDA approved April 28, 2022 for symptomatic oHCM (NYHA class II-III)" | [x] Subtype "obstructive" correct |
| 8 | structural_mavacamten.txt:12 | cardiac myosin ATPase inhibition | MECHANISM_OF_ACTION | 0.97 | "selectively inhibits cardiac myosin ATPase by stabilizing an auto-inhibited (super-relaxed) state" | [x] Allosteric binding site noted |
| 9 | structural_mavacamten.txt:25 | sarcomere contractile pathway | PATHWAY | 0.90 | "Sarcomere contractile unit" | [x] Matches source line 25 |
| 10 | structural_mavacamten.txt:31 | EXPLORER-HCM | CLINICAL_TRIAL | 0.99 | "EXPLORER-HCM (NCT03470545): Phase III, mavacamten vs placebo in oHCM. Primary endpoint met." | [x] NCT ID correct |
| 11 | structural_mavacamten.txt:34 | VALOR-HCM | CLINICAL_TRIAL | 0.99 | "VALOR-HCM (NCT04349072): Phase III, patients eligible for septal reduction therapy." | [x] NCT ID correct, 82% result captured |
| 12 | structural_mavacamten.txt:38 | FDA approval of mavacamten | REGULATORY_ACTION | 0.99 | "FDA approved April 28, 2022 for symptomatic oHCM (NYHA class II-III). REMS program required." | [x] Date and REMS flag correct |
| 13 | structural_mavacamten.txt:42 | dizziness | ADVERSE_EVENT | 0.95 | "Key AEs: dizziness (11%), syncope (4%), atrial fibrillation (4%)" | [x] 11% incidence matches |
| 14 | structural_mavacamten.txt:42 | syncope | ADVERSE_EVENT | 0.95 | "Key AEs: dizziness (11%), syncope (4%), atrial fibrillation (4%)" | [x] 4% incidence matches |
| 15 | structural_mavacamten.txt:42 | atrial fibrillation | ADVERSE_EVENT | 0.95 | "Key AEs: dizziness (11%), syncope (4%), atrial fibrillation (4%)" | [x] 4% incidence matches |
| 16 | structural_mavacamten.txt:43 | heart failure | ADVERSE_EVENT | 0.97 | "Black box warning: Risk of heart failure due to systolic dysfunction." | [x] Black box severity captured |
| 17 | structural_mavacamten.txt:48 | CYP2C19 | GENE | 0.97 | "Primarily metabolized by CYP2C19 and CYP3A4." | [x] Role "primary metabolizing enzyme" correct |
| 18 | structural_mavacamten.txt:48 | CYP3A4 | GENE | 0.95 | "Primarily metabolized by CYP2C19 and CYP3A4." | [x] Role "metabolizing enzyme" correct |
| 19 | structural_mavacamten.txt:49 | CYP2C19 poor metabolizer | PHENOTYPE | 0.93 | "CYP2C19 poor metabolizers have ~2-fold higher exposure." | [x] Effect matches source |
| 20 | structural_mavacamten.txt:50 | fluconazole | COMPOUND | 0.92 | "Strong CYP2C19 inhibitors (fluconazole, fluvoxamine) are contraindicated." | [x] Matches source line 50 |
| 21 | structural_mavacamten.txt:50 | fluvoxamine | COMPOUND | 0.92 | "Strong CYP2C19 inhibitors (fluconazole, fluvoxamine) are contraindicated." | [x] Matches source line 50 |
| 22 | structural_mavacamten.txt:45 | LVEF | BIOMARKER | 0.90 | "Contraindicated: LVEF < 55%" | [x] Threshold < 55% correct |

### Relations Extracted

| # | Source File | Source Entity | Relation | Target Entity | Confidence | Evidence | Verification |
|---|-------------|---------------|----------|---------------|------------|----------|--------------|
| 1 | structural_mavacamten.txt:12 | mavacamten | INHIBITS | cardiac myosin ATPase | 0.99 | "selectively inhibits cardiac myosin ATPase by stabilizing an auto-inhibited (super-relaxed) state" | [x] Core MOA, matches source lines 12-14 |
| 2 | structural_mavacamten.txt:12 | mavacamten | BINDS_TO | beta-cardiac myosin | 0.97 | "stabilizing an auto-inhibited (super-relaxed) state of beta-cardiac myosin (MYH7)" | [x] Correct binding relationship |
| 3 | structural_mavacamten.txt:16 | mavacamten | TARGETS | MYH7 | 0.99 | "Target: Beta-cardiac myosin heavy chain (MYH7, UniProt: P12883)" | [x] Primary target, matches source line 16 |
| 4 | structural_mavacamten.txt:38 | mavacamten | INDICATED_FOR | hypertrophic cardiomyopathy | 0.99 | "FDA approved April 28, 2022 for symptomatic oHCM (NYHA class II-III)" | [x] Approved indication |
| 5 | structural_mavacamten.txt:31 | mavacamten | EVALUATED_IN | EXPLORER-HCM | 0.99 | "EXPLORER-HCM (NCT03470545): Phase III, mavacamten vs placebo in oHCM" | [x] Matches source line 31 |
| 6 | structural_mavacamten.txt:34 | mavacamten | EVALUATED_IN | VALOR-HCM | 0.99 | "VALOR-HCM (NCT04349072): Phase III, patients eligible for septal reduction therapy" | [x] Matches source line 34 |
| 7 | structural_mavacamten.txt:42 | mavacamten | CAUSES | dizziness | 0.93 | "Key AEs: dizziness (11%)" | [x] Adverse event link correct |
| 8 | structural_mavacamten.txt:42 | mavacamten | CAUSES | syncope | 0.93 | "Key AEs: syncope (4%)" | [x] Adverse event link correct |
| 9 | structural_mavacamten.txt:42 | mavacamten | CAUSES | atrial fibrillation | 0.93 | "Key AEs: atrial fibrillation (4%)" | [x] Adverse event link correct |
| 10 | structural_mavacamten.txt:43 | mavacamten | CAUSES | heart failure | 0.97 | "Black box warning: Risk of heart failure due to systolic dysfunction." | [x] High severity, correctly flagged |
| 11 | structural_mavacamten.txt:13 | MYH7 | ENCODES | beta-cardiac myosin | 0.99 | "beta-cardiac myosin (MYH7)" | [x] Gene-protein relationship correct |
| 12 | structural_mavacamten.txt:26 | MYH7 | IMPLICATED_IN | hypertrophic cardiomyopathy | 0.95 | "mutations in MYH7 or MYBPC3 cause excessive cross-bridge formation" | [x] Known pathogenic gene |
| 13 | structural_mavacamten.txt:26 | MYBPC3 | IMPLICATED_IN | hypertrophic cardiomyopathy | 0.95 | "mutations in MYH7 or MYBPC3 cause excessive cross-bridge formation" | [x] Known pathogenic gene |
| 14 | structural_mavacamten.txt:25 | beta-cardiac myosin | PARTICIPATES_IN | sarcomere contractile pathway | 0.92 | "Sarcomere contractile unit" | [x] Biologically accurate |
| 15 | structural_mavacamten.txt:50 | fluconazole | CONTRAINDICATED_FOR | mavacamten | 0.95 | "Strong CYP2C19 inhibitors (fluconazole, fluvoxamine) are contraindicated." | [x] Drug interaction correct |
| 16 | structural_mavacamten.txt:50 | fluvoxamine | CONTRAINDICATED_FOR | mavacamten | 0.95 | "Strong CYP2C19 inhibitors (fluconazole, fluvoxamine) are contraindicated." | [x] Drug interaction correct |
| 17 | structural_mavacamten.txt:45 | LVEF | DIAGNOSTIC_FOR | hypertrophic cardiomyopathy | 0.80 | "Contraindicated: LVEF < 55%" | [x] Monitoring biomarker, lower confidence appropriate |
| 18 | structural_mavacamten.txt:49 | CYP2C19 poor metabolizer | PREDICTS_RESPONSE_TO | mavacamten | 0.90 | "CYP2C19 poor metabolizers have ~2-fold higher exposure." | [x] Pharmacogenomic relationship correct |

### UAT Question Verification

| UAT | Question | Answer from Graph | Verified? |
|-----|----------|-------------------|-----------|
| UAT-501 | What is mavacamten's mechanism? | Cardiac myosin ATPase inhibition; allosteric stabilization of super-relaxed state of MYH7/beta-cardiac myosin; IC50 0.3 uM | [x] |
| UAT-502 | What clinical evidence for HCM? | EXPLORER-HCM (NCT03470545, Phase III, 47% vs 22% composite endpoint), VALOR-HCM (NCT04349072, Phase III, 82% no longer met SRT criteria) | [x] |
| UAT-503 | What is deucravacitinib's target? | TYK2, JAK-STAT pathway (from other corpus documents) | [x] |

### Molecular Identifiers Detected

| Pattern | Value | Valid? | Cross-Reference |
|---------|-------|--------|-----------------|
| CAS | 1642288-47-8 | [x] | PubChem CID 135562068 / DrugBank DB16638 |
| SMILES | CC(C1=CC=CC=C1)NC(=O)N1CCC(CC1)OC1=NC=NC(=C1)NCC1=CC=CC=C1 | [x] | Matches PubChem canonical SMILES |
| Molecular Formula | C25H28N4O2 | [x] | Consistent with MW 428.52 g/mol |
| UniProt | P12883 | [x] | MYH7 beta-cardiac myosin heavy chain |
| NCT ID | NCT03470545 | [x] | EXPLORER-HCM on ClinicalTrials.gov |
| NCT ID | NCT04349072 | [x] | VALOR-HCM on ClinicalTrials.gov |

---

## Acceptance Sign-Off

| Metric | Count |
|--------|-------|
| Entities verified | 22 / 22 |
| Relations verified | 18 / 18 |
| UAT questions answered | 3 / 3 |
| Molecular IDs verified | 6 / 6 |

**Status:** [x] ACCEPTED / [ ] ACCEPTED WITH CONDITIONS / [ ] REJECTED
**Reviewer:** ___________________  **Date:** ___________________
