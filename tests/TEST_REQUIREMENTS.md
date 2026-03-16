# Epistract Test Requirements Specification

**Traceability:** Each requirement has a unique ID (REQ-XXX) traceable from:
- Domain spec → Entity/Relation types → Unit tests → Functional tests → User acceptance tests

---

## 1. Unit Tests (UT)

Unit tests validate individual components in isolation.

### UT-001: Domain YAML Loads Successfully
- **Traces to:** Domain spec Section 3 (Entity Types)
- **Test:** Load `domain.yaml` via sift-kg DomainLoader, verify 13 entity types and 22 relation types
- **Pass criteria:** No errors, correct counts

### UT-002: Pattern Scanner Detects SMILES
- **Traces to:** Domain spec Section 16.6 (Regex Patterns)
- **Test:** Feed text containing known SMILES `CC(=O)Oc1ccccc1C(=O)O` to scan_patterns.scan_text()
- **Pass criteria:** Returns match with pattern_type="smiles"

### UT-003: Pattern Scanner Detects NCT Numbers
- **Traces to:** Domain spec Section 16.6
- **Test:** Feed text containing `NCT04303780` to scan_patterns.scan_text()
- **Pass criteria:** Returns match with pattern_type="nct_number"

### UT-004: Pattern Scanner Detects DNA Sequences
- **Traces to:** Domain spec Section 16.6
- **Test:** Feed text containing `ATCGATCGATCGATCG` (≥15 chars)
- **Pass criteria:** Returns match with pattern_type="dna_sequence"

### UT-005: Pattern Scanner Detects CAS Numbers
- **Traces to:** Domain spec Section 16.6
- **Test:** Feed text containing `2252403-56-6` (sotorasib CAS)
- **Pass criteria:** Returns match with pattern_type="cas_number"

### UT-006: SMILES Validator Returns Properties
- **Traces to:** Domain spec Section 16.7 (Validation Pipeline)
- **Test:** validate_smiles("CC(=O)Oc1ccccc1C(=O)O") → valid, MW ~180, canonical form
- **Pass criteria:** valid=True, molecular_weight present, canonical_smiles present
- **Dependency:** RDKit installed

### UT-007: SMILES Validator Rejects Invalid SMILES
- **Traces to:** Domain spec Section 16.7
- **Test:** validate_smiles("not_a_smiles") → valid=False
- **Pass criteria:** valid=False, error message present
- **Dependency:** RDKit installed

### UT-008: SMILES Validator Graceful Without RDKit
- **Traces to:** Design spec Section 16.7
- **Test:** With RDKit not importable, validate_smiles returns valid=None
- **Pass criteria:** valid=None, error mentions "not installed"

### UT-009: Sequence Validator Validates DNA
- **Traces to:** Domain spec Section 16.7
- **Test:** validate_sequence("ATCGATCGATCGATCG") → valid=True, type=DNA, gc_content present
- **Pass criteria:** valid=True, type="DNA"
- **Dependency:** Biopython installed

### UT-010: Sequence Validator Validates Protein
- **Traces to:** Domain spec Section 16.7
- **Test:** validate_sequence("MTEYKLVVVGAGGVGKSALT") → valid=True, type=protein
- **Pass criteria:** valid=True, type="protein", molecular_weight present
- **Dependency:** Biopython installed

### UT-011: Sequence Validator Auto-Detects Type
- **Traces to:** Domain spec Section 16.7
- **Test:** detect_type("ATCGATCG") → "DNA", detect_type("AUGCUAGC") → "RNA", detect_type("MTEYKLVVV") → "protein"
- **Pass criteria:** Correct type for each

### UT-012: Extraction Adapter Writes Valid JSON
- **Traces to:** Design spec Section 3 (Claude-as-Extractor)
- **Test:** Call build_extraction.write_extraction() with sample data, load resulting JSON, verify it matches sift-kg DocumentExtraction schema
- **Pass criteria:** JSON loads, all required fields present, entities/relations are lists

### UT-013: run_sift.py Build Command Works
- **Traces to:** Design spec Section 8 (Scripts)
- **Test:** Create test extraction JSONs, run `python run_sift.py build <dir>`, verify graph_data.json created
- **Pass criteria:** graph_data.json exists with entities > 0

### UT-014: Validation Orchestrator Scans Extractions
- **Traces to:** Design spec Section 16.9
- **Test:** Create extraction JSON with SMILES in context, run validate_molecules.py, verify results.json created
- **Pass criteria:** results.json exists, identifiers_found > 0

---

## 2. Functional Tests (FT)

Functional tests validate end-to-end pipeline behavior.

### FT-001: Full Pipeline — Single Document
- **Traces to:** Design spec Section 9 (Workflow)
- **Test:** Ingest single PubMed abstract → extract → build → verify graph has entities and relations
- **Pass criteria:** graph_data.json has ≥5 entities and ≥3 relations

### FT-002: Full Pipeline — Multiple Documents
- **Traces to:** Design spec Section 9
- **Test:** Ingest 5 KRAS G12C abstracts → extract → build → verify graph merges cross-document entities
- **Pass criteria:** Entity count < sum of per-document entities (dedup working), relations span documents

### FT-003: Entity Type Coverage
- **Traces to:** Domain spec Section 3
- **Test:** Extract from mixed corpus (oncology + clinical trial report), verify ≥8 of 13 entity types present
- **Pass criteria:** ≥8 distinct entity_type values in graph nodes

### FT-004: Relation Type Coverage
- **Traces to:** Domain spec Section 4
- **Test:** Extract from KRAS corpus, verify TARGETS, INHIBITS, INDICATED_FOR, EVALUATED_IN all present
- **Pass criteria:** All 4 relation types found in graph edges

### FT-005: Export Formats
- **Traces to:** Design spec Section 5 (/epistract-export)
- **Test:** Build graph, export to JSON, GraphML, SQLite, CSV — verify all produce valid output
- **Pass criteria:** All files created, SQLite queryable, CSV has headers

### FT-006: Molecular Validation Integration
- **Traces to:** Domain spec Section 16.9
- **Test:** Ingest document containing known SMILES, run validation, verify SMILES detected and (if RDKit available) validated
- **Pass criteria:** validation/results.json has smiles_found ≥ 1

### FT-007: Community Detection
- **Traces to:** sift-kg graph/communities.py
- **Test:** Build graph from 15 KRAS documents, verify communities detected
- **Pass criteria:** communities.json has ≥2 communities

### FT-008: Interactive Viewer Generates HTML
- **Traces to:** sift-kg visualize.py
- **Test:** Build graph, run view command, verify graph.html created
- **Pass criteria:** graph.html exists, contains <script> tags, file size > 10KB

---

## 3. User Acceptance Tests (UAT) — PhD Scientist Questions

These are real research questions a PhD scientist would ask. Each tests whether the knowledge graph can provide a meaningful, scientifically accurate answer through graph traversal.

### Topic 1: PICALM / Alzheimer's Disease

#### UAT-101: What genes are associated with Alzheimer's disease risk?
- **Expected:** PICALM, APOE, BIN1, CLU, CR1, CD33, ABCA7, and others extracted as GENE entities with IMPLICATED_IN → DISEASE(Alzheimer's disease)
- **Graph traversal:** DISEASE(Alzheimer) ← IMPLICATED_IN ← GENE
- **Acceptance:** ≥3 risk genes identified with GWAS evidence

#### UAT-102: What biological pathways does PICALM participate in?
- **Expected:** Endocytosis, clathrin-mediated vesicle trafficking, amyloid precursor protein processing
- **Graph traversal:** GENE/PROTEIN(PICALM) → PARTICIPATES_IN → PATHWAY
- **Acceptance:** ≥1 pathway linked to PICALM

#### UAT-103: What is the relationship between PICALM and amyloid beta?
- **Expected:** PICALM modulates endocytosis affecting APP processing and Aβ clearance
- **Graph traversal:** PROTEIN(PICALM) → relations → PROTEIN(APP) or PATHWAY(endocytosis) → IMPLICATED_IN → DISEASE
- **Acceptance:** A traceable path from PICALM to amyloid biology

#### UAT-104: What therapeutic approaches target PICALM-related pathways?
- **Expected:** Compounds targeting endocytosis or APP processing
- **Graph traversal:** PATHWAY ← PARTICIPATES_IN ← PROTEIN(PICALM); PATHWAY ← INHIBITS/ACTIVATES ← COMPOUND
- **Acceptance:** If any compounds are mentioned in the literature, they should be extracted

### Topic 2: KRAS G12C Inhibitor Landscape

#### UAT-201: What drugs target KRAS G12C?
- **Expected:** sotorasib (AMG 510), adagrasib (MRTX849), and emerging compounds
- **Graph traversal:** GENE(KRAS G12C) ← TARGETS/INHIBITS ← COMPOUND
- **Acceptance:** Both sotorasib and adagrasib extracted and linked

#### UAT-202: What clinical trials evaluate KRAS G12C inhibitors?
- **Expected:** CodeBreaK 100, CodeBreaK 200, KRYSTAL-1, KRYSTAL-7
- **Graph traversal:** COMPOUND(sotorasib/adagrasib) → EVALUATED_IN → CLINICAL_TRIAL
- **Acceptance:** ≥2 named trials with phase and results attributes

#### UAT-203: What resistance mechanisms exist for KRAS G12C inhibitors?
- **Expected:** Secondary KRAS mutations (G12D/V/R, Y96C), MET amplification, MAPK reactivation
- **Graph traversal:** COMPOUND(sotorasib) ← CONFERS_RESISTANCE_TO ← GENE/PROTEIN
- **Acceptance:** ≥1 resistance mechanism extracted

#### UAT-204: What combination strategies are being explored?
- **Expected:** KRAS G12C inhibitors + anti-PD-1, + SHP2 inhibitors, + SOS1 inhibitors, + MEK inhibitors
- **Graph traversal:** COMPOUND(sotorasib) → COMBINED_WITH → COMPOUND
- **Acceptance:** ≥1 combination partner identified

#### UAT-205: What is the mechanism of action of sotorasib?
- **Expected:** Covalent, irreversible KRAS G12C inhibitor that locks KRAS in inactive GDP-bound state
- **Graph traversal:** COMPOUND(sotorasib) → HAS_MECHANISM → MECHANISM_OF_ACTION; COMPOUND → INHIBITS → PROTEIN(KRAS)
- **Acceptance:** Mechanism described with covalent/irreversible attributes

### Topic 3: Rare Disease Therapeutics

#### UAT-301: What is the approach to treating PKU?
- **Expected:** Pegvaliase (enzyme substitution with PEGylated phenylalanine ammonia lyase)
- **Graph traversal:** COMPOUND(pegvaliase) → INDICATED_FOR → DISEASE(phenylketonuria); COMPOUND → HAS_MECHANISM → MOA
- **Acceptance:** Pegvaliase linked to PKU with mechanism

#### UAT-302: What is vosoritide's target and mechanism?
- **Expected:** C-type natriuretic peptide analog targeting FGFR3 pathway to promote bone growth
- **Graph traversal:** COMPOUND(vosoritide) → TARGETS → PROTEIN; COMPOUND → HAS_MECHANISM → MOA
- **Acceptance:** Target pathway identified, achondroplasia indication linked

#### UAT-303: What gene therapy approaches exist for hemophilia A?
- **Expected:** Valoctocogene roxaparvovec (AAV5-FVIII gene therapy)
- **Graph traversal:** COMPOUND(valoctocogene roxaparvovec) → INDICATED_FOR → DISEASE(hemophilia A)
- **Acceptance:** Gene therapy compound extracted with correct indication

### Topic 4: Immuno-Oncology Combinations

#### UAT-401: What checkpoint combinations have been developed?
- **Expected:** nivolumab + ipilimumab (PD-1 + CTLA-4), nivolumab + relatlimab (PD-1 + LAG-3)
- **Graph traversal:** COMPOUND(nivolumab) → COMBINED_WITH → COMPOUND; each → TARGETS → PROTEIN(checkpoint)
- **Acceptance:** Both combinations identified with correct targets

#### UAT-402: What are the key clinical trials for nivolumab combinations?
- **Expected:** CheckMate-067 (melanoma), CheckMate-227 (NSCLC), RELATIVITY-047 (melanoma with relatlimab)
- **Graph traversal:** COMPOUND(nivolumab) → EVALUATED_IN → CLINICAL_TRIAL
- **Acceptance:** ≥2 named trials extracted

#### UAT-403: What immune-related adverse events are associated with checkpoint inhibitors?
- **Expected:** Colitis, hepatitis, pneumonitis, thyroiditis, dermatitis, myocarditis
- **Graph traversal:** COMPOUND(nivolumab/ipilimumab) → CAUSES → ADVERSE_EVENT
- **Acceptance:** ≥2 irAEs extracted

#### UAT-404: What biomarkers predict response to nivolumab?
- **Expected:** PD-L1 expression (TPS), TMB, MSI-H
- **Graph traversal:** BIOMARKER → PREDICTS_RESPONSE_TO → COMPOUND(nivolumab)
- **Acceptance:** ≥1 predictive biomarker linked

### Topic 5: Cardiovascular & Inflammation

#### UAT-501: What is mavacamten's mechanism of action?
- **Expected:** Selective cardiac myosin inhibitor that reduces cardiac hypercontractility
- **Graph traversal:** COMPOUND(mavacamten) → HAS_MECHANISM → MOA; COMPOUND → TARGETS → PROTEIN(cardiac myosin)
- **Acceptance:** Mechanism and target identified

#### UAT-502: What clinical evidence supports mavacamten for HCM?
- **Expected:** EXPLORER-HCM (Phase 3), VALOR-HCM trials, LVOT gradient reduction
- **Graph traversal:** COMPOUND(mavacamten) → EVALUATED_IN → CLINICAL_TRIAL; COMPOUND → INDICATED_FOR → DISEASE(HCM)
- **Acceptance:** ≥1 trial with results

#### UAT-503: What is deucravacitinib's target and indication?
- **Expected:** Selective TYK2 inhibitor for moderate-to-severe plaque psoriasis
- **Graph traversal:** COMPOUND(deucravacitinib) → INHIBITS → PROTEIN(TYK2); COMPOUND → INDICATED_FOR → DISEASE(psoriasis)
- **Acceptance:** TYK2 target and psoriasis indication linked

---

## 4. Traceability Matrix

| Requirement | Domain Spec Section | Entity Types Tested | Relation Types Tested | Test Corpus |
|---|---|---|---|---|
| UT-001 | 3 | All 13 | All 22 | N/A (schema test) |
| UT-002–005 | 16.6 | CHEMICAL_STRUCTURE, CLINICAL_TRIAL | N/A | Synthetic text |
| UT-006–008 | 16.7 | CHEMICAL_STRUCTURE | HAS_STRUCTURE | Synthetic SMILES |
| UT-009–011 | 16.7 | NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE | HAS_SEQUENCE | Synthetic sequences |
| UT-012–014 | Design spec 3, 8, 16.9 | All | All | Synthetic extraction |
| FT-001–008 | Design spec 9 | All | All | PubMed abstracts |
| UAT-101–104 | 3, 4 | GENE, PROTEIN, DISEASE, PATHWAY | IMPLICATED_IN, PARTICIPATES_IN | 01_picalm_alzheimers |
| UAT-201–205 | 3, 4 | COMPOUND, GENE, CLINICAL_TRIAL, MOA | TARGETS, INHIBITS, EVALUATED_IN, CONFERS_RESISTANCE_TO, COMBINED_WITH, HAS_MECHANISM | 02_kras_g12c_landscape |
| UAT-301–303 | 3, 4 | COMPOUND, DISEASE, PROTEIN, MOA | INDICATED_FOR, HAS_MECHANISM, TARGETS | 03_rare_disease |
| UAT-401–404 | 3, 4 | COMPOUND, CLINICAL_TRIAL, ADVERSE_EVENT, BIOMARKER | COMBINED_WITH, EVALUATED_IN, CAUSES, PREDICTS_RESPONSE_TO | 04_immunooncology |
| UAT-501–503 | 3, 4 | COMPOUND, PROTEIN, DISEASE, CLINICAL_TRIAL | HAS_MECHANISM, TARGETS, INHIBITS, EVALUATED_IN, INDICATED_FOR | 05_cardiovascular |
