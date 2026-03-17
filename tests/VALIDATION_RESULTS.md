# Epistract Validation Results — Master Sign-Off

**Status:** PENDING MANUAL REVIEW
**Reviewer:** Umesh Bhatt
**Date:** ____

This is the master sign-off document. Detailed validation tables with source file references are in each scenario's output directory (linked below).

---

## How to Validate

For each scenario:
1. Open the per-scenario validation doc (linked below)
2. Each entity/relation table includes: the **source file** where the text was found, a **quoted passage** to verify against, and a **confidence score**
3. Open the source file in `tests/corpora/<scenario>/docs/<filename>` and verify the quoted passage exists and the extraction is accurate
4. Mark each item:
   - **V** = Verified — extraction is accurate and matches source text
   - **F** = Flagged — extraction is incorrect, hallucinated, or questionable
   - **M** = Missing — an entity/relation that should have been extracted but wasn't

---

## Per-Scenario Validation Documents

| # | Scenario | Docs | Nodes | Links | Communities | Representative Extraction | Validation Document |
|---|---|---|---|---|---|---|---|
| 1 | PICALM / Alzheimer's | 15 | 149 | 457 | 6 | `pmid_36552756.txt` | [VALIDATION_RESULTS.md](corpora/01_picalm_alzheimers/output/VALIDATION_RESULTS.md) |
| 2 | KRAS G12C Landscape | 16 | 108 | 307 | 4 | `structural_sotorasib.txt` | [VALIDATION_RESULTS.md](corpora/02_kras_g12c_landscape/output/VALIDATION_RESULTS.md) |
| 3 | Rare Disease Therapeutics | 15 | 94 | 229 | 4 | `pmid_38694233.txt` | [VALIDATION_RESULTS.md](corpora/03_rare_disease/output/VALIDATION_RESULTS.md) |
| 4 | Immuno-Oncology | 16 | 132 | 361 | 5 | `structural_nivolumab_sequence.txt` | [VALIDATION_RESULTS.md](corpora/04_immunooncology/output/VALIDATION_RESULTS.md) |
| 5 | Cardiovascular & Inflammation | 15 | 94 | 246 | 5 | `structural_mavacamten.txt` | [VALIDATION_RESULTS.md](corpora/05_cardiovascular/output/VALIDATION_RESULTS.md) |
| 6 | GLP-1 Competitive Intelligence | 34 | 206 | 630 | 9 | `patent_02_US11357820B2_tirzepatide.txt` | [VALIDATION_RESULTS.md](corpora/06_glp1_landscape/output/VALIDATION_RESULTS.md) |

---

## Acceptance Sign-Off

| Scenario | Entities Verified | Relations Verified | UATs Passed | Molecular IDs | Reviewer Sign-Off |
|---|---|---|---|---|---|
| 1: PICALM/Alzheimer's | _ / 14 | _ / 12 | 4 / 4 | 12 rs-IDs | PENDING REVIEW |
| 2: KRAS G12C | _ / 18 | _ / 19 | 5 / 5 | 14 IDs (SMILES, CAS, InChIKey, NCTs) | PENDING REVIEW |
| 3: Rare Disease | _ / 15 | _ / 13 | 3 / 3 | 5 NCTs | PENDING REVIEW |
| 4: Immuno-Oncology | _ / 33 | _ / 30 | 4 / 4 | 23 NCTs, 22 seqs | PENDING REVIEW |
| 5: Cardiovascular | _ / 22 | _ / 18 | 3 / 3 | 6 IDs | PENDING REVIEW |
| 6: GLP-1 CI | _ / _ | _ / _ | 6 / 6 | 5 AA seqs, 1 CAS, 2 InChIKeys, 17 NCTs | PENDING REVIEW |

**Overall Status:** [ ] PENDING MANUAL REVIEW — all 6 scenarios awaiting human validation

**Reviewer:** _______________  **Date:** ____

---

## Legend

- **V** = Verified — extraction matches source text accurately
- **F** = Flagged — incorrect, hallucinated, or questionable extraction
- **M** = Missing — should have been extracted from source but wasn't
