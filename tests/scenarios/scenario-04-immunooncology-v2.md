# Scenario 4 (V2): Immuno-Oncology Combinations — Checkpoint Strategy

**Status:** V2 validation complete
**V2 run date:** 2026-04-13
**Output:** [`tests/corpora/04_immunooncology/output-v2/`](../corpora/04_immunooncology/output-v2/)
**V1 reference:** [scenario-04-immunooncology.md](scenario-04-immunooncology.md)

---

## Knowledge Graph (V2)

![Immuno-Oncology V2 Knowledge Graph](screenshots/scenario-04-graph-v2.png)

*151 nodes, 440 links, 5 communities. 16 parallel extractors across 15 PubMed abstracts + 1 nivolumab sequence/structural document.*

---

## V1 → V2 Delta

| Metric | V1 | V2 | Δ | Threshold | Result |
|---|---:|---:|---:|---:|:---:|
| Nodes | 132 | **151** | +14% | 106 | PASS |
| Edges | 361 | **440** | +22% | 289 | PASS |
| Communities | 5 | **5** | 0 | 3 | PASS |

---

## Run Statistics

| Metric | Value |
|---|---:|
| Raw entities | 340 |
| Raw relations | 258 |
| Graph nodes | 151 |
| Graph links | 440 |
| Communities | 5 |
| **NCT trials detected** | **32** (highest of any V2 scenario so far) |
| **Amino acid sequences detected** | **25** (from nivolumab structural doc) |
| Validator-enriched entities | **11** (first scenario with enrichment > 0) |
| Validator-enriched relations | 11 |
| Asserted | 438 |
| Hypothesized | 2 |
| Contradictions | 0 |
| Hypotheses | 0 |

### Entity Types

| Type | Count |
|---|---:|
| COMPOUND | 25 |
| ADVERSE_EVENT | 19 |
| DOCUMENT | 16 |
| DISEASE | 14 |
| GENE | 13 |
| BIOMARKER | 13 |
| CLINICAL_TRIAL | 11 |
| PROTEIN | 9 |
| PHENOTYPE | 7 |
| MECHANISM_OF_ACTION | 6 |
| **PEPTIDE_SEQUENCE** | **6** (new entity type — from validator enrichment) |
| PROTEIN_DOMAIN | 5 |
| CELL_OR_TISSUE | 3 |
| PATHWAY | 3 |
| SEQUENCE_VARIANT | 1 |

### Communities

| Community | Members |
|---|---:|
| Nivolumab / PDCD1 / Clear Cell Renal Cell Carcinoma | 34 |
| Neoplasms — PD-L2, PD-1, PD-L1 | 21 |
| Diffuse Large B-Cell Lymphoma — MHC Class II, FGL1, LAG-3 | 21 |
| Hepatocellular Carcinoma — HIF, VEGF | 16 |
| CTLA-4 Blockade | 13 |

---

## V2 Insights (S4)

1. **Validator enrichment kicked in for the first time** — `validate_molecules.py` detected 25 amino acid sequences in the nivolumab structural document and auto-added 11 entities + 11 relations (PEPTIDE_SEQUENCE nodes + HAS_DOMAIN relations linking nivolumab to its CDR loops). Prior scenarios had `entities_added: 0`. This is a latent feature of the drug-discovery domain finally exercising because S4 has the first corpus with real sequences.
2. **32 NCT clinical trials** detected — the highest of any V2 scenario so far. Immuno-oncology is trial-heavy: CheckMate, KEYNOTE, IMpower, Javelin, RELATIVITY families all surfaced.
3. **Zero permission prompts again** — second consecutive scenario fully autonomous. The Track A settings patch is load-bearing.
4. **`document_type: unknown` for nivolumab sequence doc** — same gap as S2's `structural_sotorasib.txt`. Phase 12 already captures this.
5. **Community factorization matches V1** — 5 communities both times, but V2 drew different boundaries: V1 had a "Brain Metastases / CTLA-4" cluster and a "Metabolic Reprogramming" cluster; V2 has a dedicated "CTLA-4 Blockade" cluster and a "Hepatocellular Carcinoma — HIF/VEGF" cluster. Different factorizations of the same underlying entity graph.
6. **Highest raw entity count per doc in V2 so far** — 340/16 = 21.3 avg, up from S3's 15.2. Immuno-oncology documents mention many more drugs and adverse events than rare disease abstracts.

---

## Output Files

- `output-v2/graph_data.json` — 151 nodes, 440 edges
- `output-v2/claims_layer.json` — 438 asserted, 2 hypothesized, 0 contradictions
- `output-v2/communities.json` — 5 labeled communities
- `output-v2/screenshots/graph_overview.png` — 630KB
- `output-v2/graph.html` — interactive viewer
