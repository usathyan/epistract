# Scenario 5: Cardiovascular & Inflammation — Mavacamten and Deucravacitinib

**Status:** Pending
**Output:** `tests/corpora/05_cardiovascular/output/` (not yet generated)

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

*This section will be populated after running the scenario.*
