# Scenario 2: KRAS G12C Inhibitor Landscape — Competitive Intelligence

**Status:** Pending
**Output:** `tests/corpora/02_kras_g12c_landscape/output/` (not yet generated)

---

## Use Case

You are an oncology drug discovery scientist mapping the **KRAS G12C inhibitor competitive landscape**. Two drugs are approved (sotorasib, adagrasib), and multiple next-generation inhibitors are in development. You want to understand:

- What compounds target KRAS G12C and what are their clinical results?
- What resistance mechanisms are emerging?
- What combination strategies are being explored?
- How do the approved drugs compare mechanistically?

This represents a **competitive intelligence** workflow — mapping the therapeutic landscape for a hot target.

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/02_kras_g12c_landscape/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Format** | Plain text (.txt) |
| **Source** | PubMed via NCBI E-utilities API, retrieved 2026-03-16 |

**PubMed queries used:**
- `KRAS G12C inhibitor sotorasib adagrasib clinical trial`
- `KRAS G12C covalent inhibitor resistance mechanism`
- `KRAS G12C non-small cell lung cancer treatment`
- `KRAS G12C combination immunotherapy`

### Sample Documents

- `pmid_31658955.txt` — Hallin et al. 2020: MRTX849 (adagrasib) preclinical characterization
- `pmid_34607583.txt` — Sotorasib Phase II CodeBreaK 100 results
- `pmid_36764316.txt` — KRAS G12C resistance mechanisms and combination strategies

---

## How to Run

```
/epistract-ingest tests/corpora/02_kras_g12c_landscape/docs/ --output tests/corpora/02_kras_g12c_landscape/output
```

---

## Key Questions to Validate (UAT-201 through UAT-205)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-201 | What drugs target KRAS G12C? | COMPOUND(sotorasib, adagrasib) → INHIBITS → GENE/PROTEIN(KRAS G12C) |
| UAT-202 | What clinical trials exist? | COMPOUND → EVALUATED_IN → CLINICAL_TRIAL(CodeBreaK, KRYSTAL) |
| UAT-203 | What resistance mechanisms? | GENE/PROTEIN → CONFERS_RESISTANCE_TO → COMPOUND |
| UAT-204 | What combinations are explored? | COMPOUND → COMBINED_WITH → COMPOUND |
| UAT-205 | What is sotorasib's mechanism? | COMPOUND(sotorasib) → HAS_MECHANISM → MOA(covalent KRAS G12C inhibition) |

## What Success Looks Like

- Both sotorasib and adagrasib extracted as COMPOUND with correct INN names
- KRAS G12C extracted as SEQUENCE_VARIANT with parent GENE(KRAS)
- ≥2 named clinical trials (CodeBreaK 100, KRYSTAL-1) with phase and results
- ≥1 resistance mechanism (secondary KRAS mutations, MET amplification)
- NSCLC as the primary DISEASE indication
- Amgen and Mirati extracted as ORGANIZATION entities via DEVELOPED_BY

## Expected Communities

Based on the corpus content, the graph should show clusters for:
- **KRAS G12C Inhibitors** — sotorasib, adagrasib, mechanism of action, Switch II pocket
- **Clinical Trials** — CodeBreaK, KRYSTAL trials, NSCLC indication
- **Resistance Mechanisms** — secondary mutations, MET amplification, MAPK reactivation
- **Combination Strategies** — checkpoint inhibitors, SHP2/SOS1 inhibitors

---

## Results

*This section will be populated after running the scenario.*
