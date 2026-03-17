# Epistract Validation Results — Scenario 2: KRAS G12C Landscape

**Date:** 2026-03-16
**Pipeline:** 16 documents → 108 nodes, 307 links, 4 communities
**UATs:** 5/5 passed

---

## Representative Extraction: structural_sotorasib

**Source:** `tests/corpora/02_kras_g12c_landscape/docs/structural_sotorasib.txt`
**Pipeline:** Claude extraction → sift-kg build → 18 entities, 19 relations

### Entities Extracted

| # | Entity | Type | Confidence | Source Text (verify against) | Verification |
|---|--------|------|------------|------------------------------|--------------|
| 1 | sotorasib | COMPOUND | 0.98 | "Sotorasib (AMG 510, Lumakras) is a first-in-class KRAS G12C covalent inhibitor" | [ ] V / F / M |
| 2 | KRAS | PROTEIN | 0.98 | "Target: KRAS protein (UniProt: P01116)" | [ ] V / F / M |
| 3 | KRAS G12C | SEQUENCE_VARIANT | 0.98 | "Irreversibly and covalently binds to cysteine-12 of KRAS G12C" | [ ] V / F / M |
| 4 | KRAS Y96D | SEQUENCE_VARIANT | 0.93 | "Y96D (disrupts binding)" | [ ] V / F / M |
| 5 | KRAS R68S | SEQUENCE_VARIANT | 0.93 | "R68S (alters interface)" | [ ] V / F / M |
| 6 | KRAS H95Q | SEQUENCE_VARIANT | 0.93 | "H95Q/R (affects cavity geometry)" | [ ] V / F / M |
| 7 | MET | GENE | 0.90 | "Bypass: MET amplification, MAPK reactivation" | [ ] V / F / M |
| 8 | Switch II pocket | PROTEIN_DOMAIN | 0.95 | "Binding site: Switch II pocket (P2 pocket)" | [ ] V / F / M |
| 9 | MAPK pathway | PATHWAY | 0.90 | "Bypass: MET amplification, MAPK reactivation" | [ ] V / F / M |
| 10 | non-small cell lung cancer | DISEASE | 0.98 | "KRAS G12C-mutant locally advanced or metastatic NSCLC" | [ ] V / F / M |
| 11 | covalent KRAS G12C inhibition | MECHANISM_OF_ACTION | 0.95 | "locks KRAS in inactive GDP-bound conformation" | [ ] V / F / M |
| 12 | CodeBreaK 100 | CLINICAL_TRIAL | 0.98 | "CodeBreaK 100 (NCT03600883): Phase I/II, ORR 37.1%, PFS 6.8 months" | [ ] V / F / M |
| 13 | CodeBreaK 200 | CLINICAL_TRIAL | 0.98 | "CodeBreaK 200 (NCT04303780): Phase III vs docetaxel, PFS HR 0.66" | [ ] V / F / M |
| 14 | docetaxel | COMPOUND | 0.90 | "Phase III vs docetaxel" | [ ] V / F / M |
| 15 | FDA accelerated approval sotorasib | REGULATORY_ACTION | 0.98 | "FDA approved May 28, 2021 under accelerated approval" | [ ] V / F / M |
| 16 | H358 | CELL_OR_TISSUE | 0.90 | "EC50: 38 nM (H358 cells, p-ERK inhibition)" | [ ] V / F / M |
| 17 | ERK | PROTEIN | 0.88 | "EC50: 38 nM (H358 cells, p-ERK inhibition)" | [ ] V / F / M |
| 18 | p-ERK inhibition | BIOMARKER | 0.85 | "EC50: 38 nM (H358 cells, p-ERK inhibition)" | [ ] V / F / M |

### Relations Extracted

| # | Source Entity | Relation | Target Entity | Confidence | Evidence | Verification |
|---|---------------|----------|---------------|------------|----------|--------------|
| 1 | sotorasib | INHIBITS | KRAS G12C | 0.98 | "Irreversibly and covalently binds to cysteine-12 of KRAS G12C, locking protein in inactive GDP-bound conformation" | [ ] V / F / M |
| 2 | sotorasib | BINDS_TO | Switch II pocket | 0.95 | "Binding site: Switch II pocket (P2 pocket)" | [ ] V / F / M |
| 3 | sotorasib | HAS_MECHANISM | covalent KRAS G12C inhibition | 0.95 | "Irreversibly and covalently binds to cysteine-12 of KRAS G12C, locking protein in inactive GDP-bound conformation" | [ ] V / F / M |
| 4 | sotorasib | EVALUATED_IN | CodeBreaK 100 | 0.98 | "CodeBreaK 100 (NCT03600883): Phase I/II, ORR 37.1%, PFS 6.8 months" | [ ] V / F / M |
| 5 | sotorasib | EVALUATED_IN | CodeBreaK 200 | 0.98 | "CodeBreaK 200 (NCT04303780): Phase III vs docetaxel, PFS HR 0.66" | [ ] V / F / M |
| 6 | sotorasib | INDICATED_FOR | non-small cell lung cancer | 0.98 | "FDA approved May 28, 2021 under accelerated approval for KRAS G12C-mutant locally advanced or metastatic NSCLC" | [ ] V / F / M |
| 7 | sotorasib | ASSOCIATED_WITH | FDA accelerated approval sotorasib | 0.98 | "FDA approved May 28, 2021 under accelerated approval" | [ ] V / F / M |
| 8 | KRAS Y96D | CONFERS_RESISTANCE_TO | sotorasib | 0.93 | "Y96D (disrupts binding)" | [ ] V / F / M |
| 9 | KRAS R68S | CONFERS_RESISTANCE_TO | sotorasib | 0.93 | "R68S (alters interface)" | [ ] V / F / M |
| 10 | KRAS H95Q | CONFERS_RESISTANCE_TO | sotorasib | 0.93 | "H95Q/R (affects cavity geometry)" | [ ] V / F / M |
| 11 | MET | CONFERS_RESISTANCE_TO | sotorasib | 0.90 | "Bypass: MET amplification, MAPK reactivation" | [ ] V / F / M |
| 12 | KRAS | PARTICIPATES_IN | MAPK pathway | 0.88 | "Bypass: MET amplification, MAPK reactivation" | [ ] V / F / M |
| 13 | p-ERK inhibition | EXPRESSED_IN | H358 | 0.85 | "EC50: 38 nM (H358 cells, p-ERK inhibition)" | [ ] V / F / M |
| 14 | KRAS | HAS_VARIANT | KRAS G12C | 0.98 | "KRAS G12C covalent inhibitor" | [ ] V / F / M |
| 15 | KRAS | HAS_VARIANT | KRAS Y96D | 0.93 | "Resistance: Y96D (disrupts binding)" | [ ] V / F / M |
| 16 | KRAS | HAS_VARIANT | KRAS R68S | 0.93 | "R68S (alters interface)" | [ ] V / F / M |
| 17 | KRAS | HAS_VARIANT | KRAS H95Q | 0.93 | "H95Q/R (affects cavity geometry)" | [ ] V / F / M |
| 18 | KRAS G12C | IMPLICATED_IN | non-small cell lung cancer | 0.98 | "KRAS G12C-mutant locally advanced or metastatic NSCLC" | [ ] V / F / M |

### UAT Question Verification

| UAT | Question | Answer from Graph | Verified? |
|-----|----------|-------------------|-----------|
| UAT-201 | What drugs target KRAS G12C? | sotorasib (AMG 510, Lumakras) INHIBITS KRAS G12C (conf 0.98); adagrasib (MRTX849) INHIBITS KRAS G12C (conf 0.95-0.99) — confirmed across 10+ documents | [ ] |
| UAT-202 | What clinical trials? | CodeBreaK 100 (NCT03600883, Phase I/II, ORR 37.1%, PFS 6.8mo); CodeBreaK 200 (NCT04303780, Phase III vs docetaxel, PFS HR 0.66, n=345); KRYSTAL-1 (NCT03785249, Phase 1/2, adagrasib ORR 43%, intracranial ORR 33.3%) | [ ] |
| UAT-203 | Resistance mechanisms? | On-target: KRAS Y96D (disrupts binding), R68S (alters interface), H95Q/R (affects cavity geometry), G12D/R/V/W, G13D, Q61H, Y96C; Bypass: MET amplification, EGFR reactivation, NRAS/BRAF/MAP2K1/RET mutations, NF1/PTEN loss, MAPK reactivation, MRAS:SHOC2:PP1C complex activation, histologic transformation | [ ] |
| UAT-204 | Combination strategies? | KRAS G12C inhibitor + EGFR inhibitors (CRC trials underway); KRAS G12C inhibitor + immune checkpoint inhibitors (anti-PD-1/PD-L1); rationale: address EGFR-mediated adaptive resistance and immune evasion | [ ] |
| UAT-205 | Mechanism of action? | Covalent KRAS G12C inhibition: irreversibly binds cysteine-12 in Switch II pocket (P2 pocket), locks KRAS in inactive GDP-bound conformation; IC50 7.8 nM (NanoBRET), EC50 38 nM (H358 p-ERK); >1000x selectivity over KRAS WT | [ ] |

### Molecular Identifiers Detected

| Pattern | Value | Valid? | Cross-Reference |
|---------|-------|--------|-----------------|
| CAS Registry Number | 2252403-56-6 | [ ] | PubChem CID 137278711 |
| SMILES | CC1CC(C(O1)N1C=NC2=C(C=C(C=C21)F)NC(=O)C1=CC(=NN1C)C(F)(F)F)OC1=C(C=C(C=C1)F)Cl | [ ] | DrugBank DB15569 |
| Molecular Formula | C23H25ClF4N4O3 | [ ] | MW 560.92 g/mol |
| InChIKey | LFEWXACJFKQYHQ-XKBHBSJNSA-N | [ ] | PubChem lookup |
| UniProt (KRAS) | P01116 | [ ] | UniProt.org |
| NCT ID (CodeBreaK 100) | NCT03600883 | [ ] | ClinicalTrials.gov |
| NCT ID (CodeBreaK 200) | NCT04303780 | [ ] | ClinicalTrials.gov |
| NCT ID (KRYSTAL-1) | NCT03785249 | [ ] | ClinicalTrials.gov |
| PMID (Awad et al.) | 34161704 | [ ] | PubMed |
| PMID (Tang et al.) | 34607583 | [ ] | PubMed |
| PMID (Janne et al.) | 35658005 | [ ] | PubMed |
| PMID (Ji et al.) | 35837349 | [ ] | PubMed |
| PMID (de Langen et al.) | 36764316 | [ ] | PubMed |
| PMID (Zhang et al.) | 37101895 | [ ] | PubMed |

## Acceptance Sign-Off

| Metric | Count |
|--------|-------|
| Entities verified | [ ] / 18 |
| Relations verified | [ ] / 18 |
| UAT questions answered | [ ] / 5 |
| Molecular IDs verified | [ ] / 14 |

**Status:** [ ] ACCEPTED / [ ] ACCEPTED WITH CONDITIONS / [ ] REJECTED
**Reviewer:** ___________________  **Date:** ___________________
