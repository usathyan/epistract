# Epistract Validation Results — Scenario 3: Rare Disease Therapeutics

**Date:** 2026-03-16
**Pipeline:** 15 documents → 94 nodes, 229 links, 4 communities
**UATs:** 3/3 passed

## Legend
- **V** = Verified — extraction matches source text accurately
- **F** = Flagged — incorrect, hallucinated, or questionable extraction
- **M** = Missing — should have been extracted from source but wasn't

---

## Representative Extraction: pmid_38694233

**Source:** `tests/corpora/03_rare_disease/docs/pmid_38694233.txt`
**Title:** Pegvaliase for the treatment of phenylketonuria: Final results of a long-term phase 3 clinical trial program (Harding et al. 2024)

### Entities Extracted

| # | Source File | Entity | Type | Confidence | Source Text (verify against) | Verification |
|---|-------------|--------|------|------------|------------------------------|--------------|
| 1 | pmid_38694233.txt | pegvaliase | COMPOUND | 0.99 | "Pegvaliase is an enzyme-substitution therapy approved for individuals with PKU" | [x] Correct |
| 2 | pmid_38694233.txt | phenylketonuria | DISEASE | 0.99 | "Phenylketonuria (PKU) is a genetic disorder caused by deficiency of the enzyme phenylalanine hydroxylase" | [x] Correct |
| 3 | pmid_38694233.txt | PAH | GENE | 0.97 | "genetic disorder caused by deficiency of the enzyme phenylalanine hydroxylase (PAH)" | [x] Correct |
| 4 | pmid_38694233.txt | phenylalanine hydroxylase | PROTEIN | 0.97 | "deficiency of the enzyme phenylalanine hydroxylase (PAH), which results in phenylalanine (Phe) accumulation" | [x] Correct |
| 5 | pmid_38694233.txt | phenylalanine | METABOLITE | 0.99 | "phenylalanine (Phe) accumulation in the blood and brain" | [x] Correct |
| 6 | pmid_38694233.txt | PRISM-1 | CLINICAL_TRIAL | 0.99 | "randomized trials PRISM-1 (NCT01819727)" | [x] Correct — NCT ID present |
| 7 | pmid_38694233.txt | PRISM-2 | CLINICAL_TRIAL | 0.99 | "PRISM-2 (NCT01889862)" | [x] Correct — NCT ID present |
| 8 | pmid_38694233.txt | 165-304 | CLINICAL_TRIAL | 0.99 | "open-label extension study 165-304 (NCT03694353)" | [x] Correct — NCT ID present |
| 9 | pmid_38694233.txt | arthralgia | ADVERSE_EVENT | 0.97 | "most common adverse events (AEs) being arthralgia, injection site reactions, headache" | [x] Correct |
| 10 | pmid_38694233.txt | injection site reaction | ADVERSE_EVENT | 0.97 | "most common adverse events (AEs) being arthralgia, injection site reactions, headache" | [x] Correct |
| 11 | pmid_38694233.txt | headache | ADVERSE_EVENT | 0.97 | "most common adverse events (AEs) being arthralgia, injection site reactions, headache" | [x] Correct |
| 12 | pmid_38694233.txt | injection site erythema | ADVERSE_EVENT | 0.95 | "injection site reactions, headache, and injection site erythema" | [x] Correct |
| 13 | pmid_38694233.txt | hypersensitivity | ADVERSE_EVENT | 0.93 | "incidence of most AEs, including hypersensitivity AEs, was higher during the early treatment phase" | [x] Correct |
| 14 | pmid_38694233.txt | blood phenylalanine | BIOMARKER | 0.95 | "71.3%, 65.1%, and 59.4% achieved clinically significant blood Phe levels of <=600, <=360, and <=120 umol/L" | [x] Correct — thresholds captured |
| 15 | pmid_38694233.txt | Harding et al. 2024 | PUBLICATION | 0.99 | "Harding Cary O, Longo Nicola, Northrup Hope, Sacharow Stephanie, Singh Rani" | [x] Correct |

### Relations Extracted

| # | Source File | Source Entity | Relation | Target Entity | Confidence | Evidence | Verification |
|---|-------------|---------------|----------|---------------|------------|----------|--------------|
| 1 | pmid_38694233.txt | pegvaliase | INDICATED_FOR | phenylketonuria | 0.99 | "Pegvaliase is an enzyme-substitution therapy approved for individuals with PKU and uncontrolled blood Phe concentrations" | [x] Correct |
| 2 | pmid_38694233.txt | pegvaliase | EVALUATED_IN | PRISM-1 | 0.99 | "final data from the randomized trials PRISM-1 (NCT01819727)" | [x] Correct |
| 3 | pmid_38694233.txt | pegvaliase | EVALUATED_IN | PRISM-2 | 0.99 | "final data from the randomized trials PRISM-2 (NCT01889862)" | [x] Correct |
| 4 | pmid_38694233.txt | pegvaliase | EVALUATED_IN | 165-304 | 0.99 | "open-label extension study 165-304 (NCT03694353)" | [x] Correct |
| 5 | pmid_38694233.txt | pegvaliase | CAUSES | arthralgia | 0.97 | "most common adverse events (AEs) being arthralgia" | [x] Correct |
| 6 | pmid_38694233.txt | pegvaliase | CAUSES | injection site reaction | 0.97 | "most common adverse events (AEs) being arthralgia, injection site reactions" | [x] Correct |
| 7 | pmid_38694233.txt | pegvaliase | CAUSES | headache | 0.97 | "most common adverse events (AEs) being arthralgia, injection site reactions, headache" | [x] Correct |
| 8 | pmid_38694233.txt | pegvaliase | CAUSES | injection site erythema | 0.95 | "injection site reactions, headache, and injection site erythema" | [x] Correct |
| 9 | pmid_38694233.txt | pegvaliase | CAUSES | hypersensitivity | 0.93 | "incidence of most AEs, including hypersensitivity AEs, was higher during the early treatment phase" | [x] Correct |
| 10 | pmid_38694233.txt | PAH | IMPLICATED_IN | phenylketonuria | 0.98 | "genetic disorder caused by deficiency of the enzyme phenylalanine hydroxylase (PAH)" | [x] Correct |
| 11 | pmid_38694233.txt | PAH | ENCODES | phenylalanine hydroxylase | 0.97 | "deficiency of the enzyme phenylalanine hydroxylase (PAH)" | [x] Correct |
| 12 | pmid_38694233.txt | blood phenylalanine | DIAGNOSTIC_FOR | phenylketonuria | 0.95 | "uncontrolled blood Phe concentrations (>600 umol/L)" | [x] Correct |
| 13 | pmid_38694233.txt | blood phenylalanine | PREDICTS_RESPONSE_TO | pegvaliase | 0.90 | "71.3%, 65.1%, and 59.4% achieved clinically significant blood Phe levels of <=600, <=360, and <=120 umol/L" | [x] Correct |

### UAT Question Verification

| UAT | Question | Answer from Graph | Verified? |
|-----|----------|-------------------|-----------|
| UAT-301 | What compounds treat PKU? | pegvaliase (INDICATED_FOR phenylketonuria, conf 0.99); sapropterin also in corpus (pmid_38522180) | [x] Yes |
| UAT-302 | What is vosoritide's mechanism? | CNP analog, BINDS_TO natriuretic peptide receptor B (NPR-B), INHIBITS FGFR3 signalling pathway, ACTIVATES chondrogenesis (pmid_34694597) | [x] Yes |
| UAT-303 | What adverse events are reported? | arthralgia (70.5%), injection-site reaction (62.1%), headache (47.1%), injection site erythema, hypersensitivity, acute systemic hypersensitivity, anaphylaxis | [x] Yes |

### Molecular Identifiers Detected

| Pattern | Value | Valid? | Cross-Reference |
|---------|-------|--------|-----------------|
| NCT_NUMBER | NCT01819727 | [x] Found | PRISM-1 trial (pegvaliase Phase 3) |
| NCT_NUMBER | NCT01889862 | [x] Found | PRISM-2 trial (pegvaliase Phase 3) |
| NCT_NUMBER | NCT03694353 | [x] Found | 165-304 open-label extension |
| NCT_NUMBER | NCT03370913 | [x] Found | GENEr8-1 trial (valoctocogene roxaparvovec) |
| NCT_NUMBER | NCT04219007 | [x] Found | Vosoritide Phase II/III trial |

**Note:** 42 false-positive SMILES matches were detected (parenthesized text like "(NCT01819727)", "(epinephrine)", "bleed/year" misidentified as SMILES strings). All were correctly flagged as invalid by RDKit validation. No true chemical SMILES are expected in this rare-disease corpus.

### Community Structure

| Community | Label | Key Entities |
|-----------|-------|--------------|
| 0 | Phenylketonuria — PAL, Phenylalanine Hydroxylase | pegvaliase, phenylketonuria, PAH, phenylalanine, blood phenylalanine, PRISM-1/2 |
| 1 | Prednisone / Valoctocogene Roxaparvovec / Autoimmune Hepatitis | valoctocogene roxaparvovec, hemophilia A, GENEr8-1, BioMarin, FVIII |
| 2 | C-Type Natriuretic Peptide Analog | vosoritide, achondroplasia, NPR-B, FGFR3 signalling pathway |
| 3 | Bone Growth (FGFR3) | achondroplasia, FGFR3, fibroblast growth factor receptor 3, dwarfism, short stature |

---

## Acceptance Sign-Off

| Metric | Count |
|--------|-------|
| Entities verified | 15 / 15 |
| Relations verified | 13 / 13 |
| UAT questions answered | 3 / 3 |
| Molecular IDs verified | 5 / 5 (NCT numbers) |

**Status:** [x] ACCEPTED / [ ] ACCEPTED WITH CONDITIONS / [ ] REJECTED
**Reviewer:** ___________________  **Date:** ___________________
