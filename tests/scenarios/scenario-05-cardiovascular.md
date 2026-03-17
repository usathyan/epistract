# Scenario 5: Cardiovascular & Inflammation — Mavacamten and Deucravacitinib

**Status:** Completed (2026-03-16)
**Output:** `tests/corpora/05_cardiovascular/output/`

![Cardiovascular & Inflammation Knowledge Graph](screenshots/scenario-05-graph.png)

---

## Use Case

You are a cardiovascular/inflammation research analyst evaluating two newer programs:

1. **Mavacamten (Camzyos)** — selective cardiac myosin inhibitor for hypertrophic cardiomyopathy (HCM)
2. **Deucravacitinib (Sotyktu)** — selective TYK2 inhibitor for plaque psoriasis

These represent a diversification beyond oncology. You want to understand targets, mechanisms, clinical evidence, and safety profiles.

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/05_cardiovascular/docs/` |
| **Documents** | 14 PubMed abstracts |
| **Format** | Plain text (.txt) |
| **Source** | PubMed via NCBI E-utilities API, retrieved 2026-03-16 |

**PubMed queries used:**
- `mavacamten hypertrophic cardiomyopathy EXPLORER-HCM`
- `cardiac myosin inhibitor obstructive hypertrophic cardiomyopathy`
- `Camzyos mavacamten cardiac myosin inhibitor`
- `deucravacitinib TYK2 psoriasis POETYK`

### Sample Documents

- `pmid_32498620.txt` — EXPLORER-HCM study design and rationale
- `pmid_36115523.txt` — Mavacamten Phase III EXPLORER-HCM results
- `pmid_38176782.txt` — Deucravacitinib TYK2 selectivity and psoriasis efficacy

---

## How to Run

```
/epistract-ingest tests/corpora/05_cardiovascular/docs/ --output tests/corpora/05_cardiovascular/output
```

---

## Key Questions to Validate (UAT-501 through UAT-503)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-501 | What is mavacamten's mechanism? | COMPOUND(mavacamten) → HAS_MECHANISM → MOA(cardiac myosin inhibition) |
| UAT-502 | What clinical evidence for HCM? | COMPOUND(mavacamten) → EVALUATED_IN → CLINICAL_TRIAL(EXPLORER-HCM) |
| UAT-503 | What is deucravacitinib's target? | COMPOUND(deucravacitinib) → INHIBITS → PROTEIN(TYK2) |

## What Success Looks Like

- Mavacamten and deucravacitinib as distinct COMPOUND entities
- Cardiac myosin (beta-MHC) and TYK2 as PROTEIN targets
- HCM and psoriasis as distinct DISEASE entities
- EXPLORER-HCM and POETYK trials extracted with phase and results
- Graph shows two distinct clusters (cardiology + dermatology)
- LVOT gradient reduction mentioned as clinical endpoint for mavacamten
- JAK/STAT pathway context for deucravacitinib

## Expected Communities

- **HCM / Mavacamten** — cardiac myosin, EXPLORER-HCM, VALOR-HCM, LVOT gradient
- **Psoriasis / Deucravacitinib** — TYK2, JAK/STAT pathway, POETYK trials, IL-23/IL-12
- **Shared mechanisms** (if any) — kinase biology, selectivity profiles

---

## Results

**Status:** Completed (2026-03-16)

### Metrics

| Metric | Value |
|---|---|
| Documents processed | 15 (14 PubMed abstracts + 1 structural profile) |
| Raw entities extracted | 185 |
| Raw relations extracted | 148 |
| Graph nodes (deduplicated) | 94 |
| Graph links | 246 |
| Communities detected | 5 |

### Communities

| # | Label | Members | Theme |
|---|---|---|---|
| 1 | **Obstructive Hypertrophic Cardiomyopathy — Cardiac Myosin ATPase** | 24 | Mavacamten clinical trials (EXPLORER-HCM, MAVA-LTE), LVOT gradient, NT-proBNP, adverse events |
| 2 | **Sarcomere Contractile Pathway (MYBPC3, MYH7)** | 15 | Sarcomere biology, aficamten, R403Q mutation, cardiac myocyte selectivity |
| 3 | **TYK2 Allosteric Inhibition** | 14 | Deucravacitinib, POETYK trials, psoriasis, apremilast comparator |
| 4 | **JAK-STAT Signaling Pathway** | 11 | IL-12, IL-23, type I interferons, cytokine signaling in psoriasis |
| 5 | **Cardiac Myosin Inhibition** | 8 | Shared mechanism node linking mavacamten and aficamten, FDA approval, REMS |

### UAT Validation

| # | Question | Expected | Result |
|---|---|---|---|
| UAT-501 | What is mavacamten's mechanism? | COMPOUND(mavacamten) → HAS_MECHANISM → MOA(cardiac myosin inhibition) | **PASS** — mavacamten INHIBITS cardiac myosin/MYH7, HAS_MECHANISM cardiac myosin inhibition |
| UAT-502 | What clinical evidence for HCM? | COMPOUND(mavacamten) → EVALUATED_IN → CLINICAL_TRIAL(EXPLORER-HCM) | **PASS** — EXPLORER-HCM, PIONEER-HCM, MAVA-LTE, VALOR-HCM, SEQUOIA-HCM (aficamten) |
| UAT-503 | What is deucravacitinib's target? | COMPOUND(deucravacitinib) → INHIBITS → PROTEIN(TYK2) | **PASS** — deucravacitinib INHIBITS TYK2, with JAK-STAT pathway context |

### Scientific Narrative

The graph validates the scenario's core hypothesis: two completely unrelated therapeutic areas produce two clearly separated cluster groups. The cardiology side (Communities 1, 2, 5) centers on cardiac myosin inhibition in HCM, with mavacamten and aficamten as distinct compounds sharing the same mechanism but binding different allosteric sites. The dermatology side (Communities 3, 4) captures TYK2-selective inhibition in psoriasis, with the JAK-STAT signaling pathway correctly linked to IL-12/IL-23/type I interferons.

Community 5 (Cardiac Myosin Inhibition) serves as a shared mechanism hub linking mavacamten and aficamten — the graph correctly identifies them as competitors in the same mechanism class. The R403Q variant in MYH7 is captured in the sarcomere community, reflecting the genetic basis of HCM.

Notably, SEQUOIA-HCM (aficamten's Phase III trial) was not in the original scenario description but was correctly extracted from the corpus, demonstrating the pipeline's ability to capture competitive intelligence beyond the pre-specified UATs.

### Output Files

- `tests/corpora/05_cardiovascular/output/graph_data.json` — Full graph data
- `tests/corpora/05_cardiovascular/output/graph.html` — Interactive viewer (clone repo and open locally in browser)
- `tests/corpora/05_cardiovascular/output/extractions/` — 15 extraction JSON files
- `tests/corpora/05_cardiovascular/output/communities.json` — Community assignments and labels
