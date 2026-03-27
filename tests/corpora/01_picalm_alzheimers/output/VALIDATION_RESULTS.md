# Epistract Validation Results — Scenario 1: PICALM / Alzheimer's

**Date:** 2026-03-16
**Pipeline:** 15 documents -> 149 nodes, 457 links, 6 communities
**UATs:** 4/4 passed

## Legend
- **V** = Verified — extraction matches source text accurately
- **F** = Flagged — incorrect, hallucinated, or questionable extraction
- **M** = Missing — should have been extracted from source but wasn't

---

## Representative Extraction: pmid_36552756 (Ando et al., 2022)

**Source:** `tests/corpora/01_picalm_alzheimers/docs/pmid_36552756.txt`
**Pipeline:** Claude extraction -> sift-kg build -> 14 entities, 12 relations

### Entities Extracted

| # | Source File | Entity | Type | Confidence | Source Text (verify against) | Verification |
|---|---|---|---|---|---|---|
| 1 | pmid_36552756.txt:8 | PICALM | GENE | 0.95 | "PICALM (Phosphatidylinositol binding clathrin-assembly protein) gene as the most significant genetic susceptibility locus after APOE and BIN1" | [V] V / F / M |
| 2 | pmid_36552756.txt:8 | PICALM | PROTEIN | 0.95 | "PICALM is a clathrin-adaptor protein that plays a critical role in clathrin-mediated endocytosis and autophagy" | [V] V / F / M |
| 3 | pmid_36552756.txt:8 | APOE | GENE | 0.95 | "the most significant genetic susceptibility locus after APOE and BIN1" | [V] V / F / M |
| 4 | pmid_36552756.txt:8 | BIN1 | GENE | 0.95 | "the most significant genetic susceptibility locus after APOE and BIN1" | [V] V / F / M |
| 5 | pmid_36552756.txt:8 | APP | GENE | 0.95 | "differential modulation of APP processing...by PICALM" | [V] V / F / M |
| 6 | pmid_36552756.txt:8 | amyloid precursor protein | PROTEIN | 0.95 | "differential modulation of APP processing" | [V] V / F / M |
| 7 | pmid_36552756.txt:8 | amyloid beta | PROTEIN | 0.95 | "A-beta transcytosis by PICALM" | [V] V / F / M |
| 8 | pmid_36552756.txt:8 | tau | PROTEIN | 0.90 | "significant effects of PICALM modulation of tau pathology progression" | [V] V / F / M |
| 9 | pmid_36552756.txt:1 | Alzheimer disease | DISEASE | 0.95 | "PICALM and Alzheimer's Disease" | [V] V / F / M |
| 10 | pmid_36552756.txt:8 | clathrin-mediated endocytosis | PATHWAY | 0.95 | "PICALM is a clathrin-adaptor protein that plays a critical role in clathrin-mediated endocytosis" | [V] V / F / M |
| 11 | pmid_36552756.txt:8 | autophagy | PATHWAY | 0.90 | "plays a critical role in clathrin-mediated endocytosis and autophagy" | [V] V / F / M |
| 12 | pmid_36552756.txt:8 | PICALM | BIOMARKER | 0.85 | "effects of genetic variants of PICALM as AD-susceptibility loci have been confirmed by independent genetic studies in several distinct cohorts" | [V] V / F / M |
| 13 | pmid_36552756.txt:8 | amyloid beta transcytosis | MECHANISM_OF_ACTION | 0.90 | "A-beta transcytosis by PICALM" | [V] V / F / M |
| 14 | pmid_36552756.txt:8 | tau pathology | PHENOTYPE | 0.90 | "significant effects of PICALM modulation of tau pathology progression have also been evidenced in Alzheimer's disease models" | [V] V / F / M |

### Relations Extracted

| # | Source File | Source Entity | Relation | Target Entity | Confidence | Evidence | Verification |
|---|---|---|---|---|---|---|---|
| 1 | pmid_36552756.txt:8 | PICALM | IMPLICATED_IN | Alzheimer disease | 0.95 | "PICALM gene as the most significant genetic susceptibility locus after APOE and BIN1" | [V] V / F / M |
| 2 | pmid_36552756.txt:8 | APOE | IMPLICATED_IN | Alzheimer disease | 0.95 | "the most significant genetic susceptibility locus after APOE" | [V] V / F / M |
| 3 | pmid_36552756.txt:8 | BIN1 | IMPLICATED_IN | Alzheimer disease | 0.95 | "the most significant genetic susceptibility locus after APOE and BIN1" | [V] V / F / M |
| 4 | pmid_36552756.txt:8 | PICALM | PARTICIPATES_IN | clathrin-mediated endocytosis | 0.95 | "PICALM is a clathrin-adaptor protein that plays a critical role in clathrin-mediated endocytosis" | [V] V / F / M |
| 5 | pmid_36552756.txt:8 | PICALM | PARTICIPATES_IN | autophagy | 0.90 | "plays a critical role in clathrin-mediated endocytosis and autophagy" | [V] V / F / M |
| 6 | pmid_36552756.txt:8 | PICALM | REGULATES_EXPRESSION | amyloid precursor protein | 0.85 | "differential modulation of APP processing...by PICALM" | [V] V / F / M |
| 7 | pmid_36552756.txt:8 | PICALM | ASSOCIATED_WITH | amyloid beta | 0.90 | "A-beta transcytosis by PICALM has been reported" | [V] V / F / M |
| 8 | pmid_36552756.txt:8 | PICALM | ASSOCIATED_WITH | tau | 0.90 | "significant effects of PICALM modulation of tau pathology progression have also been evidenced in Alzheimer's disease models" | [V] V / F / M |
| 9 | pmid_36552756.txt:8 | APP | ENCODES | amyloid precursor protein | 0.95 | "amyloid precursor protein (APP)" | [V] V / F / M |
| 10 | pmid_36552756.txt:8 | amyloid beta | IMPLICATED_IN | Alzheimer disease | 0.90 | "A-beta transcytosis...AD risk" | [V] V / F / M |
| 11 | pmid_36552756.txt:8 | tau | IMPLICATED_IN | Alzheimer disease | 0.90 | "tau pathology progression...in Alzheimer's disease models" | [V] V / F / M |
| 12 | pmid_36552756.txt:8 | tau pathology | ASSOCIATED_WITH | Alzheimer disease | 0.90 | "PICALM modulation of tau pathology progression have also been evidenced in Alzheimer's disease models" | [V] V / F / M |

### UAT Question Verification

| UAT | Question | Answer from Graph | Verified? |
|---|---|---|---|
| UAT-101 | What genes are associated with AD risk? | 30 genes in Community 1: PICALM, APOE, BIN1, CLU, CR1, CD33, ABCA7, TREM2, PTK2B, INPP5D, MEF2C, SORL1, FERMT2, CASS4, + 16 others all linked via IMPLICATED_IN -> Alzheimer disease | [ ] |
| UAT-102 | What pathways does PICALM participate in? | 4 pathways: clathrin-mediated endocytosis, autophagy, phagocytosis, amyloid-beta processing (via PARTICIPATES_IN and ASSOCIATED_WITH edges) | [ ] |
| UAT-103 | What variants are linked to PICALM? | rs3851179 (A allele protective, OR=0.88), rs541458 (C allele protective, OR=0.86, Caucasian-specific), rs592297 (no association), rs10792832 (causal SNP, reduces PU.1 binding in microglia) | [ ] |
| UAT-104 | What therapeutic approaches exist? | anti-A-beta antibodies (only disease-modifying treatment); no small molecules targeting PICALM directly (consistent with literature). Microglial phagocytosis identified as convergent mechanism for 27 AD risk genes. | [ ] |

### Molecular Identifiers Detected

| Pattern | Value | Valid? | Cross-Reference |
|---|---|---|---|
| dbSNP | rs3851179 | Verify at dbSNP | [ ] |
| dbSNP | rs541458 | Verify at dbSNP | [ ] |
| dbSNP | rs592297 | Verify at dbSNP | [ ] |
| dbSNP | rs10792832 | Verify at dbSNP | [ ] |
| dbSNP | rs2373115 | Verify at dbSNP (GAB2) | [ ] |
| dbSNP | rs1010159 | Verify at dbSNP (SORL1) | [ ] |
| dbSNP | rs641120 | Verify at dbSNP (SORL1) | [ ] |
| dbSNP | rs668387 | Verify at dbSNP (SORL1) | [ ] |
| dbSNP | rs689021 | Verify at dbSNP (SORL1) | [ ] |
| dbSNP | rs12285364 | Verify at dbSNP (SORL1) | [ ] |
| dbSNP | rs2070045 | Verify at dbSNP (SORL1) | [ ] |
| dbSNP | rs2282649 | Verify at dbSNP (SORL1) | [ ] |
| SMILES | 21 false positives | All invalid | Parenthesized gene names (e.g., "(PICALM)") mismatched as SMILES |

---

## Acceptance Sign-Off

| Metric | Count |
|---|---|
| Entities verified | [ ] / 14 |
| Relations verified | [ ] / 12 |
| UAT questions answered | [ ] / 4 |
| Molecular IDs verified | [ ] / 12 |

**Status:** [ ] ACCEPTED / [ ] ACCEPTED WITH CONDITIONS / [ ] REJECTED
**Reviewer:** ___________________  **Date:** ___________________
