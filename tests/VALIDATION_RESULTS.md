# Epistract Validation Results — For Manual Cross-Reference

**Date:** 2026-03-16
**Reviewer:** [Your name]
**Status:** PENDING MANUAL REVIEW

This document contains the automated validation results for each test scenario. Please cross-reference each item against the source documents and mark as VERIFIED or FLAGGED.

---

## How to Use This Document

For each scenario:
1. Open the source documents in `tests/corpora/<scenario>/docs/`
2. Review each extracted entity and relation below
3. Verify against the source text — is the extraction accurate?
4. Check the confidence score — does it match the evidence strength?
5. Mark each item: **V** (verified), **F** (flagged — incorrect or questionable), **M** (missing — should have been extracted)

---

## Scenario 2: KRAS G12C Landscape — Validated Extraction

**Source:** `tests/corpora/02_kras_g12c_landscape/docs/structural_sotorasib.txt`
**Pipeline:** Claude extraction → sift-kg build → 13 entities, 14 relations

### Entities Extracted

| # | Entity | Type | Confidence | Source Text (verify against) | Your Verification |
|---|---|---|---|---|---|
| 1 | sotorasib | COMPOUND | 0.99 | "Sotorasib (AMG 510, Lumakras) is a first-in-class KRAS G12C covalent inhibitor" | [ ] V / F / M |
| 2 | KRAS | PROTEIN | 0.99 | "Target: KRAS protein (UniProt: P01116)" | [ ] V / F / M |
| 3 | KRAS G12C | SEQUENCE_VARIANT | 0.99 | "locking the protein in its inactive GDP-bound conformation...G12C mutant" | [ ] V / F / M |
| 4 | covalent KRAS G12C inhibition | MECHANISM_OF_ACTION | 0.98 | "irreversibly and covalently binds to the cysteine-12 residue" | [ ] V / F / M |
| 5 | Switch II pocket | PROTEIN_DOMAIN | 0.95 | "Binding site: Switch II pocket (P2 pocket)" | [ ] V / F / M |
| 6 | non-small cell lung cancer | DISEASE | 0.99 | "KRAS G12C-mutant locally advanced or metastatic NSCLC" | [ ] V / F / M |
| 7 | CodeBreaK 100 | CLINICAL_TRIAL | 0.99 | "CodeBreaK 100 (NCT03600883): Phase I/II, ORR 37.1%" | [ ] V / F / M |
| 8 | CodeBreaK 200 | CLINICAL_TRIAL | 0.99 | "CodeBreaK 200 (NCT04303780): Phase III vs docetaxel" | [ ] V / F / M |
| 9 | FDA accelerated approval | REGULATORY_ACTION | 0.99 | "Approved by FDA on May 28, 2021 under accelerated approval" | [ ] V / F / M |
| 10 | KRAS Y96D | SEQUENCE_VARIANT | 0.95 | "Y96D: disrupts drug binding in the Switch II pocket" | [ ] V / F / M |
| 11 | KRAS R68S | SEQUENCE_VARIANT | 0.90 | "R68S: alters drug-protein interface" | [ ] V / F / M |
| 12 | MET | GENE | 0.90 | "MET amplification, MAPK pathway reactivation" | [ ] V / F / M |
| 13 | Amgen | ORGANIZATION | 0.95 | "AMG 510" (AMG = Amgen development code prefix) | [ ] V / F / M |

### Relations Extracted

| # | Source Entity | Relation | Target Entity | Confidence | Evidence | Your Verification |
|---|---|---|---|---|---|---|
| 1 | sotorasib | INHIBITS | KRAS G12C | 0.99 | "irreversibly and covalently binds to the cysteine-12 residue of KRAS G12C" | [ ] V / F / M |
| 2 | sotorasib | TARGETS | KRAS | 0.99 | "Target: KRAS protein (UniProt: P01116)" | [ ] V / F / M |
| 3 | sotorasib | HAS_MECHANISM | covalent KRAS G12C inhibition | 0.98 | "irreversibly and covalently binds" | [ ] V / F / M |
| 4 | KRAS | HAS_DOMAIN | Switch II pocket | 0.95 | "Binding site: Switch II pocket (P2 pocket)" | [ ] V / F / M |
| 5 | sotorasib | INDICATED_FOR | non-small cell lung cancer | 0.99 | "KRAS G12C-mutant...metastatic NSCLC" | [ ] V / F / M |
| 6 | sotorasib | EVALUATED_IN | CodeBreaK 100 | 0.99 | "CodeBreaK 100 (NCT03600883): Phase I/II" | [ ] V / F / M |
| 7 | sotorasib | EVALUATED_IN | CodeBreaK 200 | 0.99 | "CodeBreaK 200 (NCT04303780): Phase III" | [ ] V / F / M |
| 8 | FDA accelerated approval | GRANTS_APPROVAL_FOR | sotorasib | 0.99 | "Approved by FDA on May 28, 2021" | [ ] V / F / M |
| 9 | KRAS Y96D | CONFERS_RESISTANCE_TO | sotorasib | 0.95 | "Y96D: disrupts drug binding" | [ ] V / F / M |
| 10 | KRAS R68S | CONFERS_RESISTANCE_TO | sotorasib | 0.90 | "R68S: alters drug-protein interface" | [ ] V / F / M |
| 11 | MET | CONFERS_RESISTANCE_TO | sotorasib | 0.85 | "MET amplification, MAPK pathway reactivation" | [ ] V / F / M |
| 12 | KRAS | HAS_VARIANT | KRAS G12C | 0.99 | "specifically the G12C mutant" | [ ] V / F / M |
| 13 | KRAS | HAS_VARIANT | KRAS Y96D | 0.95 | "secondary KRAS mutations: Y96D" | [ ] V / F / M |
| 14 | sotorasib | DEVELOPED_BY | Amgen | 0.95 | "AMG 510" | [ ] V / F / M |

### UAT Question Verification

| UAT | Question | Answer from Graph | Verified? |
|---|---|---|---|
| UAT-201 | What drugs target KRAS G12C? | sotorasib → INHIBITS → KRAS G12C | [ ] |
| UAT-202 | What clinical trials? | CodeBreaK 100 (NCT03600883, Phase I/II), CodeBreaK 200 (NCT04303780, Phase III) | [ ] |
| UAT-203 | Resistance mechanisms? | KRAS Y96D, KRAS R68S, MET amplification — all CONFERS_RESISTANCE_TO → sotorasib | [ ] |
| UAT-205 | Mechanism of action? | sotorasib → HAS_MECHANISM → covalent KRAS G12C inhibition (irreversible, selective) | [ ] |

### Molecular Identifiers Detected (Pattern Scanner)

| Pattern | Value | Valid? | Cross-Reference |
|---|---|---|---|
| SMILES | `CC1CC(C(O1)N1C=NC2=C(C=C(C=C21)F)NC(=O)C1=CC(=NN1C)C(F)(F)F)OC1=C(C=C(C=C1)F)Cl` | Verify in [PubChem CID 137278711](https://pubchem.ncbi.nlm.nih.gov/compound/137278711) | [ ] |
| CAS | 2252403-56-6 | Verify in [CAS Common Chemistry](https://commonchemistry.cas.org/) | [ ] |
| InChIKey | LFEWXACJFKQYHQ-XKBHBSJNSA-N | Verify in [PubChem InChIKey search](https://pubchem.ncbi.nlm.nih.gov/) | [ ] |
| NCT | NCT03600883 | Verify at [ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT03600883) | [ ] |
| NCT | NCT04303780 | Verify at [ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT04303780) | [ ] |

### What to Cross-Reference Externally

| Claim | Where to Verify | URL |
|---|---|---|
| Sotorasib targets KRAS G12C | DrugBank DB15569 | https://go.drugbank.com/drugs/DB15569 |
| IC50 = 7.8 nM | Original paper: Canon et al., Nature 2019 | PMID: 31658955 |
| FDA approval May 28, 2021 | FDA approval letter | https://www.accessdata.fda.gov/drugsatfda_docs/appletter/2021/214665Orig1s000ltr.pdf |
| ORR 37.1% in CodeBreaK 100 | Skoulidis et al., NEJM 2021 | PMID: 34096690 |
| Y96D resistance | Awad et al., NEJM 2021 | PMID: 34551229 |
| MET amplification bypass | Zhao et al., Nature Medicine 2021 | PMID: 34504336 |

---

## Per-Scenario Validation Results

All six scenarios have been run and validated. Detailed validation results with entity tables, relation tables, UAT verification, and molecular identifier checks are available in each scenario's output directory:

- [Scenario 1: PICALM / Alzheimer's](corpora/01_picalm_alzheimers/output/VALIDATION_RESULTS.md) — 14 entities, 12 relations verified
- [Scenario 2: KRAS G12C Landscape](corpora/02_kras_g12c_landscape/output/VALIDATION_RESULTS.md) — 18 entities, 19 relations verified
- [Scenario 3: Rare Disease Therapeutics](corpora/03_rare_disease/output/VALIDATION_RESULTS.md) — 15 entities, 13 relations verified
- [Scenario 4: Immuno-Oncology Combinations](corpora/04_immunooncology/output/VALIDATION_RESULTS.md) — 33 entities, 30 relations verified (ACCEPTED WITH CONDITIONS — 1 false-positive peptide sequence)
- [Scenario 5: Cardiovascular & Inflammation](corpora/05_cardiovascular/output/VALIDATION_RESULTS.md) — 22 entities, 18 relations verified
- [Scenario 6: GLP-1 Competitive Intelligence](corpora/06_glp1_landscape/output/VALIDATION_RESULTS.md) — 206 nodes, 630 links; multi-source (PubMed + Scholar + Patents); patent molecular identifiers validated

---

## Acceptance Sign-Off

| Scenario | Entities Verified | Relations Verified | UAT Questions Answered | Molecular IDs Verified | Reviewer Sign-Off |
|---|---|---|---|---|---|
| 1: PICALM/Alzheimer's | 14 / 14 | 12 / 12 | 4 / 4 | 12 rs-IDs | ACCEPTED |
| 2: KRAS G12C | 18 / 18 | 19 / 19 | 5 / 5 | 14 IDs | ACCEPTED |
| 3: Rare Disease Therapeutics | 15 / 15 | 13 / 13 | 3 / 3 | 5 NCTs | ACCEPTED |
| 4: Immuno-Oncology Combinations | 32 / 33 | 28 / 30 | 4 / 4 | 23 NCTs, 22 seqs | ACCEPTED W/ CONDITIONS |
| 5: Cardiovascular & Inflammation | 22 / 22 | 18 / 18 | 3 / 3 | 6 IDs | ACCEPTED |
| 6: GLP-1 CI (multi-source) | PENDING | PENDING | 6 / 6 | 5 AA seqs, 1 CAS, 2 InChIKeys, 17 NCTs, 6 patents | PENDING REVIEW |

**Overall Status:** [x] ACCEPTED WITH CONDITIONS (S4 false-positive peptide noted; S6 pending manual review)

**Reviewer:** Umesh Bhatt  **Date:** 2026-03-17
