# Scenario 3: Rare Disease Therapeutics — PKU, Achondroplasia, Hemophilia A

**Status:** Pending
**Output:** `tests/corpora/03_rare_disease/output/` (not yet generated)

---

## Use Case

You are a rare disease research analyst conducting **due diligence** on a rare disease therapeutics pipeline. Three key programs:

1. **Pegvaliase (Palynziq)** — enzyme substitution therapy for phenylketonuria (PKU)
2. **Vosoritide (Voxzogo)** — C-type natriuretic peptide analog for achondroplasia
3. **Valoctocogene roxaparvovec (Roctavian)** — AAV5 gene therapy for hemophilia A

You want to map the targets, mechanisms, clinical evidence, and competitive context for each program.

---

## Corpus

| Property | Value |
|---|---|
| **Location** | `tests/corpora/03_rare_disease/docs/` |
| **Documents** | 15 PubMed abstracts |
| **Format** | Plain text (.txt) |
| **Source** | PubMed via NCBI E-utilities API, retrieved 2026-03-16 |

**PubMed queries used:**
- `pegvaliase phenylketonuria PKU enzyme substitution therapy`
- `vosoritide achondroplasia FGFR3 C-type natriuretic peptide`
- `valoctocogene roxaparvovec hemophilia A gene therapy`
- `phenylketonuria phenylalanine hydroxylase dietary treatment`

### Sample Documents

- `pmid_29653686.txt` — Pegvaliase Phase III PRISM trials
- `pmid_34694597.txt` — Vosoritide Phase III results in achondroplasia
- `pmid_38614387.txt` — Valoctocogene roxaparvovec gene therapy for hemophilia A

---

## How to Run

```
/epistract-ingest tests/corpora/03_rare_disease/docs/ --output tests/corpora/03_rare_disease/output
```

---

## Key Questions to Validate (UAT-301 through UAT-303)

| # | Question | Expected Graph Evidence |
|---|---|---|
| UAT-301 | What is the PKU treatment? | COMPOUND(pegvaliase) → INDICATED_FOR → DISEASE(phenylketonuria) |
| UAT-302 | What is vosoritide's target? | COMPOUND(vosoritide) → TARGETS → PROTEIN(NPR-B/FGFR3 pathway) |
| UAT-303 | What gene therapy for hemophilia A? | COMPOUND(valoctocogene roxaparvovec) → INDICATED_FOR → DISEASE(hemophilia A) |

## What Success Looks Like

- Three distinct COMPOUND entities for three different drugs
- Three distinct DISEASE entities (PKU, achondroplasia, hemophilia A)
- Phenylalanine ammonia lyase (PAL) extracted as the enzyme mechanism for pegvaliase
- FGFR3 pathway extracted for vosoritide
- Factor VIII / AAV5 gene therapy mechanism for valoctocogene
- Graph shows three distinct clusters (one per program)

## Expected Communities

- **PKU / Pegvaliase** — enzyme substitution, phenylalanine metabolism, PRISM trials
- **Achondroplasia / Vosoritide** — FGFR3 signaling, bone growth, CNP pathway
- **Hemophilia A / Gene Therapy** — Factor VIII, AAV5, gene therapy mechanism

---

## Results

*This section will be populated after running the scenario.*
