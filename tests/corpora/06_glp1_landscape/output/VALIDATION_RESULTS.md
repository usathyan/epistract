# Epistract Validation Results — Scenario 6: GLP-1 Competitive Intelligence

**Date:** 2026-03-17
**Pipeline:** 34 documents → 206 nodes, 630 links, 9 communities
**UATs:** 6/6 passed

---

## What's New in Scenario 6

This scenario introduces three capabilities not tested in S1-S5:

1. **Multi-source corpus assembly** — PubMed E-utilities + Google Scholar (SerpAPI) + Google Patents (SerpAPI)
2. **Patent document extraction** — molecular identifiers (peptide sequences, CAS numbers, InChIKeys, chemical formulas) from patent abstracts
3. **Competitive intelligence framing** — graph structured for company→compound→indication analysis

### Corpus Assembly via SerpAPI

| API | Endpoint | Key Parameters | Results |
|-----|----------|---------------|---------|
| PubMed | NCBI E-utilities | `esearch` + `efetch`, XML format | 18 unique abstracts |
| Google Scholar | `serpapi.com/search?engine=google_scholar` | `as_sdt=7` (include patents), `num=10` | 79 unique results → 6 papers added |
| Google Patents | `serpapi.com/search?engine=google_patents` | `assignee`, `country`, `status`, `after` filters, `num=10` | 42 unique patents → 10 selected |

**Learning:** Google Scholar snippets are too short for extraction (~500 bytes). The value of Scholar is **discovery** — finding papers and patents not surfaced by PubMed. Full text must then be retrieved from the source (PubMed Entrez for papers, patents.google.com for patents).

**Learning:** Using `as_sdt=7` in Google Scholar returns patent results inline with paper results, eliminating the need for a separate Google Patents API call for discovery. The Patents API is still valuable for targeted assignee/date/status filtering.

---

## Representative Extraction: patent_02 (Tirzepatide)

**Source:** `tests/corpora/06_glp1_landscape/docs/patent_02_US11357820B2_tirzepatide.txt`

### Entities Extracted

| # | Entity | Type | Confidence | Source Text | Verification |
|---|--------|------|------------|-------------|--------------|
| 1 | tirzepatide | COMPOUND | 0.99 | "tirzepatide is a dual GIP/GLP-1 receptor agonist peptide with CAS Registry Number 2023788-19-2" | [x] CAS 2023788-19-2 verified |
| 2 | GLP1R | PROTEIN | 0.99 | "dual GIP/GLP-1 receptor agonist" | [x] Target receptor correct |
| 3 | GIPR | PROTEIN | 0.99 | "dual GIP/GLP-1 receptor agonist" | [x] Second target correct |
| 4 | Eli Lilly | ORGANIZATION | 0.98 | "Assignee: Eli Lilly and Company" | [x] Patent assignee correct |
| 5 | type 2 diabetes mellitus | DISEASE | 0.98 | "treatment of type 2 diabetes mellitus and obesity" | [x] Primary indication |
| 6 | obesity | DISEASE | 0.98 | "treatment of type 2 diabetes mellitus and obesity" | [x] Approved indication |
| 7 | dual GIP/GLP-1 receptor agonism | MECHANISM_OF_ACTION | 0.97 | "imbalanced potency favoring GIP receptor activation" | [x] MOA with selectivity detail |
| 8 | SURPASS | CLINICAL_TRIAL | 0.95 | "SURPASS clinical trial program" | [x] Phase 3 program name |
| 9 | tirzepatide peptide sequence | PEPTIDE_SEQUENCE | 0.95 | "YX1EGTFTSDYSIX2LDKIAQKAFVQWLMGGPSSGAPPPS, where X1 = Aib and X2 = Aib" | [x] 39-AA sequence with Aib substitutions |

### Relations Extracted

| # | Source → Relation → Target | Confidence | Evidence | Verification |
|---|---------------------------|------------|----------|--------------|
| 1 | tirzepatide → ACTIVATES → GLP1R | 0.99 | "dual GIP/GLP-1 receptor agonist" | [x] Core MOA |
| 2 | tirzepatide → ACTIVATES → GIPR | 0.99 | "imbalanced potency favoring GIP receptor activation" | [x] GIP-biased agonism |
| 3 | tirzepatide → INDICATED_FOR → T2DM | 0.99 | "treatment of type 2 diabetes mellitus" | [x] Approved indication |
| 4 | tirzepatide → INDICATED_FOR → obesity | 0.99 | "treatment of... obesity" | [x] Approved indication |
| 5 | tirzepatide → DEVELOPED_BY → Eli Lilly | 0.98 | "Assignee: Eli Lilly and Company" | [x] Patent assignee |
| 6 | tirzepatide → EVALUATED_IN → SURPASS | 0.95 | "SURPASS clinical trial program" | [x] Phase 3 program |
| 7 | tirzepatide → HAS_MECHANISM → dual GIP/GLP-1 agonism | 0.97 | "dual agonist mechanism activates both the GIP receptor (primary) and the GLP-1 receptor" | [x] Correct dual mechanism |

---

## Representative Extraction: pmid_37192005 (Semaglutide in Addiction)

**Source:** `tests/corpora/06_glp1_landscape/docs/pmid_37192005.txt`

### Entities Extracted

| # | Entity | Type | Confidence | Source Text | Verification |
|---|--------|------|------------|-------------|--------------|
| 1 | semaglutide | COMPOUND | 0.99 | "glucagon-like peptide-1 (GLP-1) analogue semaglutide reduces alcohol drinking" | [x] Correct compound |
| 2 | GLP1R | PROTEIN | 0.99 | "GLP-1 receptor" | [x] Target receptor |
| 3 | GABA | METABOLITE | 0.95 | "semaglutide modulates GABAergic transmission" | [x] Neurotransmitter |
| 4 | alcohol use disorder | DISEASE | 0.90 | "reduces alcohol drinking" | [x] Emerging indication |
| 5 | central amygdala | CELL_OR_TISSUE | 0.92 | "central amygdala" | [x] Brain region |
| 6 | infralimbic cortex | CELL_OR_TISSUE | 0.92 | "infralimbic cortex" | [x] Brain region |

### Relations Extracted

| # | Source → Relation → Target | Confidence | Evidence | Verification |
|---|---------------------------|------------|----------|--------------|
| 1 | semaglutide → ACTIVATES → GLP1R | 0.99 | "GLP-1 analogue" | [x] Core MOA |
| 2 | semaglutide → INDICATED_FOR → alcohol use disorder | 0.75 | "reduces alcohol drinking" | [x] Emerging/preclinical, lower confidence appropriate |
| 3 | GLP1R → EXPRESSED_IN → central amygdala | 0.90 | "GLP-1 receptor in central amygdala" | [x] Brain expression |
| 4 | semaglutide → REGULATES_EXPRESSION → GABA | 0.85 | "modulates GABAergic transmission" | [x] Mechanism of anti-addictive effect |

---

## Graph Quality Metrics

### Hub Node Analysis

The graph's hub structure correctly reflects the competitive landscape:

- **Semaglutide (59 connections)** — most connected compound, consistent with its market-leading position and broadest indication coverage
- **GLP1R (59 connections)** — shared target across all GLP-1 agonists, correctly serves as the central hub
- **Obesity (52 connections)** — primary indication driving the market, correctly most-connected disease
- **Tirzepatide (26 connections)** — second-most connected compound, reflecting its position as the main competitor to semaglutide

### Cross-Source Validation

The graph successfully merges information from different source types:
- **Semaglutide** appears in 17 source documents (4 patents + 13 PubMed papers) → single deduplicated node with merged attributes
- **Tirzepatide** appears in 12 source documents (2 patents + 10 PubMed papers) → correctly merged
- **GLP1R** appears across all document types as the shared target

### Community Quality

All 9 communities are biologically and commercially meaningful:
- No spurious cross-domain connections
- Competition patterns correctly emerge (Community 9 groups non-GLP-1 MASH competitors)
- Emerging indications form coherent clusters (Community 5 for addiction/appetite)
- Drug delivery innovation captured as distinct community (Community 4 for SNAC/oral)

---

## Findings

### F-008: Multi-Source Corpus Assembly Validates Human CI Workflow

**Severity:** Positive finding
**Discovered in:** Scenario 6

The multi-source assembly pipeline (PubMed → Scholar → Patents) mimics how a human competitive intelligence analyst actually works: searching multiple databases, cross-referencing findings, and building a mental knowledge graph. This workflow produces a richer graph (206 nodes vs 94-149 for single-source S1-S5) with novel entity types not available from PubMed alone (patent assignees, peptide sequences, CAS numbers, chemical formulas).

**Key insight:** Scholar is best used for **discovery** (finding what to search for), not for **extraction** (snippets too short). Patents are the richest source of molecular identifiers. PubMed remains the backbone for clinical data.

### F-009: Patent Extraction Yields Novel Entity Types

**Severity:** Positive finding
**Discovered in:** Scenario 6

Patent documents produced entity types and attributes not seen in any PubMed-only scenario:
- PEPTIDE_SEQUENCE entities with full amino acid sequences
- CAS numbers (2023788-19-2 for tirzepatide, 2212020-52-3 for orforglipron)
- InChIKeys (SNAC: UOENJXXSKABLJL-UHFFFAOYSA-M)
- Chemical formulas (orforglipron: C48H48F2N10O5)
- Patent assignee → compound DEVELOPED_BY relations
- Process chemistry details (Fmoc SPPS, desulfurization, depsi peptide conversion)

This validates that the epistract schema is rich enough to capture patent-specific molecular data without modification.

### F-010: SMILES Validation False Positives on IUPAC Names

**Severity:** Low — expected behavior, no impact on graph quality
**Discovered in:** Scenario 6

The molecular validation script attempts to parse various string patterns as SMILES. IUPAC chemical names (e.g., "N-(8-(2-hydroxybenzoyl)amino)caprylate"), compound abbreviations with parentheses (e.g., "GLP-1(7-37)"), and patent references (e.g., "WO2006/097537") triggered SMILES parse errors. These are correctly rejected and do not affect the graph.

**Recommendation:** Future improvement could add a pre-filter to skip strings that match IUPAC name patterns or patent number formats before attempting SMILES parsing.
