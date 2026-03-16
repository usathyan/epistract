# Scenario 4: Immuno-Oncology Combinations — Checkpoint Inhibitors

**Status:** Pending
**Output:** `tests/corpora/04_immunooncology/output/` (not yet generated)

---

## Use Case

You are an immuno-oncology researcher tracking a **checkpoint inhibitor portfolio**:

1. **Nivolumab (Opdivo)** — anti-PD-1 monoclonal antibody
2. **Ipilimumab (Yervoy)** — anti-CTLA-4 monoclonal antibody
3. **Relatlimab** — anti-LAG-3 monoclonal antibody (combined with nivolumab as Opdualag)

You want to map the combination strategies, clinical trials, response biomarkers, and immune-related adverse events.

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/04_immunooncology/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Format** | Plain text (.txt) |
| **Source** | PubMed via NCBI E-utilities API, retrieved 2026-03-16 |

**PubMed queries used:**
- `nivolumab ipilimumab combination immunotherapy melanoma CheckMate`
- `relatlimab LAG-3 nivolumab RELATIVITY clinical trial`
- `opdivo checkpoint inhibitor PD-1`
- `nivolumab resistance mechanism tumor microenvironment`

### Sample Documents

- `pmid_25795410.txt` — CheckMate 037: nivolumab vs chemo in advanced melanoma
- `pmid_34359884.txt` — RELATIVITY-047: relatlimab + nivolumab Phase II/III
- `pmid_34986285.txt` — Nivolumab + ipilimumab long-term follow-up CheckMate 067

---

## How to Run

```
/epistract-ingest tests/corpora/04_immunooncology/docs/ --output tests/corpora/04_immunooncology/output
```

---

## Key Questions to Validate (UAT-401 through UAT-404)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-401 | What checkpoint combinations? | COMPOUND(nivolumab) → COMBINED_WITH → COMPOUND(ipilimumab/relatlimab) |
| UAT-402 | What are key clinical trials? | COMPOUND → EVALUATED_IN → CLINICAL_TRIAL(CheckMate-067, RELATIVITY-047) |
| UAT-403 | What irAEs are reported? | COMPOUND → CAUSES → ADVERSE_EVENT(colitis, hepatitis, pneumonitis) |
| UAT-404 | What biomarkers predict response? | BIOMARKER(PD-L1, TMB) → PREDICTS_RESPONSE_TO → COMPOUND(nivolumab) |

## What Success Looks Like

- Nivolumab, ipilimumab, relatlimab as distinct COMPOUND entities with INN names
- PD-1, CTLA-4, LAG-3 as PROTEIN targets linked via TARGETS/INHIBITS
- ≥2 named CheckMate trials with phase and results data
- Immune-related adverse events (irAEs) extracted with MedDRA-like terminology
- PD-L1 and/or TMB extracted as BIOMARKER entities
- Melanoma and NSCLC as DISEASE indications
- Graph shows immunotherapy combination network centered on nivolumab

## Expected Communities

- **PD-1 / Nivolumab Core** — nivolumab, PD-1, PD-L1 biomarker, melanoma, NSCLC
- **Combination Regimens** — ipilimumab + nivolumab, relatlimab + nivolumab, CTLA-4, LAG-3
- **Clinical Trials** — CheckMate-067, CheckMate-227, RELATIVITY-047
- **Safety / irAEs** — colitis, hepatitis, pneumonitis, thyroiditis

---

## Results

*This section will be populated after running the scenario.*
