# Epistract

**Turn scientific literature into structured biomedical knowledge.**

[![Demo Video](https://img.youtube.com/vi/7mHbdb0nn3Y/maxresdefault.jpg)](https://youtu.be/7mHbdb0nn3Y)

> **Paper:** [Beyond RAG: Domain-Specific Agentic Architecture for Biomedical Knowledge Graph Construction](paper/main.pdf) — technical report describing the architecture, evaluation across 6 drug discovery domains, and the evolution from GraphRAG to comprehension-based extraction.

Epistract reads drug discovery documents — PubMed papers, bioRxiv preprints, patent filings, clinical trial reports, FDA labels — and builds a knowledge graph that captures the entities and relationships a scientist cares about: compounds, targets, mechanisms, trials, biomarkers, pathways, and how they connect.

It runs as a [Claude Code](https://claude.ai/claude-code) plugin. You point it at a folder of documents. It reads them with a scientist's understanding, extracts structured knowledge using a schema grounded in 40+ established biomedical ontologies, validates molecular identifiers with [RDKit](https://www.rdkit.org/) and [Biopython](https://biopython.org/), and produces an interactive graph you can explore in your browser.

## The Name

From Greek **episteme** (ἐπιστήμη) — structured scientific knowledge, the highest form of knowledge in Aristotle's epistemological hierarchy — combined with **extract**. Episteme is not opinion or belief; it is knowledge grounded in evidence, demonstration, and systematic understanding. That is what this tool produces: not a bag of keywords, but a structured representation of how scientific concepts relate to each other, traceable back to the source text.

---

## Quick Start

### 1. Install

Requires [Claude Code](https://claude.ai/claude-code) and Python 3.11+.

**Install from GitHub** — run these inside any Claude Code session:

```
/plugin marketplace add usathyan/epistract
/plugin install epistract@epistract
```

Then restart Claude Code. The plugin is now available in all sessions.

**For developers** — clone locally and install as a dev marketplace:

```bash
git clone https://github.com/usathyan/epistract.git
```

```
/plugin marketplace add /path/to/epistract
/plugin install epistract@epistract
```

Restart Claude Code after installing.

**Verify installation:**

```
/epistract-setup
```

This installs [sift-kg](https://github.com/juanceresa/sift-kg) (the knowledge graph engine) and checks for optional molecular validation libraries ([RDKit](https://www.rdkit.org/), [Biopython](https://biopython.org/)).

**Set up API keys** — sift-kg uses [LiteLLM](https://docs.litellm.ai/) for entity resolution during graph building. Set one of the following in your environment before running the pipeline:

```bash
# Option A: OpenRouter (recommended — one key, many models; used in development)
export OPENROUTER_API_KEY="your-key-here"

# Option B: OpenAI (SIFT_ prefix required — sift-kg forwards to LiteLLM)
export SIFT_OPENAI_API_KEY="your-key-here"

# Option C: Anthropic (SIFT_ prefix required)
export SIFT_ANTHROPIC_API_KEY="your-key-here"

# Option D: Google Gemini (SIFT_ prefix required)
export SIFT_GEMINI_API_KEY="your-key-here"

# Option E: AWS Bedrock (standard AWS credentials — LiteLLM reads directly)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION_NAME="us-east-1"

# Option F: Local models via Ollama (no API key needed)
# Just ensure ollama is running: ollama serve
```

> **Note:** OpenRouter and AWS Bedrock keys are read directly by LiteLLM (no prefix). OpenAI, Anthropic, and Gemini keys use the `SIFT_` prefix because sift-kg manages them through its config layer. You can also set `SIFT_DEFAULT_MODEL` to choose the model (e.g., `openai/gpt-4o-mini`, `anthropic/claude-haiku`, `ollama/llama3.3`).

This is separate from Claude Code's own API access, which is handled by your Claude Code subscription.

**PubMed API key (optional)** — if you plan to use `/epistract-acquire` to search and download articles from PubMed, an NCBI API key increases rate limits from 3 to 10 requests/second. The key is free.

To obtain one:
1. Create a free NCBI account at https://www.ncbi.nlm.nih.gov/account/
2. Sign in, go to **Settings** > **API Key Management** > **Create an API Key**
3. Set it in your environment:

```bash
export NCBI_API_KEY="your-key-here"
```

> **Note:** The PubMed connector works without this key — it just runs at lower rate limits. For small corpora (<20 articles) you likely won't notice the difference. For larger acquisitions, the key prevents rate-limit pauses.

### 2. Ingest Documents

```
/epistract-ingest ./my-papers/
```

Epistract will:
1. Read and chunk all documents (PDFs, DOCX, HTML, TXT, 75+ formats, OCR for scans)
2. Extract entities and relations using the drug discovery schema
3. Validate SMILES, sequences, CAS numbers, NCT IDs found in the text
4. Create structural graph nodes from validated molecular identifiers
5. Build a deduplicated knowledge graph with community detection and auto-labeling
6. Open an interactive visualization in your browser

### 3. Explore

The interactive viewer shows your knowledge graph with labeled community regions, focus mode, trail breadcrumbs, search, and filtering.

### 4. Export

```
/epistract-export graphml    # For Gephi, yEd, Cytoscape
/epistract-export sqlite     # For SQL queries, DuckDB, Datasette
/epistract-export csv        # For spreadsheets, pandas
```

### 5. Query

```
/epistract-query "sotorasib"              # Find entities by name
/epistract-query "KRAS" --type PROTEIN    # Filter by type
```

---

## Commands

| Command | Description |
|---|---|
| `/epistract-setup` | Install dependencies (sift-kg, optional RDKit/Biopython) |
| `/epistract-acquire <query>` | Search PubMed and download articles into a local corpus |
| `/epistract-ingest <path>` | Full pipeline: ingest → extract → validate → build → view |
| `/epistract-build` | Build graph from existing extractions |
| `/epistract-validate` | Validate molecular identifiers in extractions |
| `/epistract-view` | Open interactive graph viewer |
| `/epistract-epistemic` | Analyze epistemic patterns (hypotheses, contradictions, claims) |
| `/epistract-query <term>` | Search entities in the knowledge graph |
| `/epistract-export <format>` | Export to graphml, gexf, csv, sqlite, json |

---

## Use Cases

- **Literature review** — Map how compounds, targets, and mechanisms connect across a body of research
- **Target validation** — Trace genetic evidence (GWAS, MR) through to protein targets and existing compounds
- **Competitive intelligence** — Ingest patent filings and clinical trial publications to map a therapeutic landscape
- **Safety signal detection** — Extract and connect adverse events across clinical trial reports
- **Biomarker discovery** — Identify which biomarkers predict response to which therapies
- **Due diligence** — Build a structured knowledge base from a target company's publication and patent portfolio

---

## Test Scenarios

Epistract ships with six drug discovery research scenarios, each backed by a curated corpus. Scenarios 1-5 use PubMed abstracts; Scenario 6 demonstrates multi-source corpus assembly from PubMed + Google Scholar + Google Patents via SerpAPI. Each scenario page includes the use case, corpus details, how to run, expected graph structure, and actual results with graph screenshots and community analysis.

> **Note:** These are hypothetical test scenarios designed to validate the pipeline across diverse drug discovery domains. They are not attributable to any ongoing research. This project explores how AI-assisted tooling can accelerate scientific literature analysis.

| # | Scenario | Focus | Documents | Sources |
|---|---|---|---|---|
| 1 | [PICALM / Alzheimer's](tests/scenarios/scenario-01-picalm-alzheimers.md) | Genetic target validation | 15 papers | PubMed |
| 2 | [KRAS G12C Landscape](tests/scenarios/scenario-02-kras-g12c-landscape.md) | Competitive intelligence | 16 papers | PubMed |
| 3 | [Rare Disease Therapeutics](tests/scenarios/scenario-03-rare-disease.md) | Due diligence | 15 papers | PubMed |
| 4 | [Immuno-Oncology Combinations](tests/scenarios/scenario-04-immunooncology.md) | Checkpoint combinations | 16 papers | PubMed |
| 5 | [Cardiovascular & Inflammation](tests/scenarios/scenario-05-cardiovascular.md) | Cardiology + inflammation | 15 papers | PubMed |
| 6 | [GLP-1 Competitive Intelligence](tests/scenarios/scenario-06-glp1-landscape.md) | Multi-source CI landscape | 34 docs | PubMed + Scholar + Patents |

See [tests/MANUAL_TEST_SCENARIOS.md](tests/MANUAL_TEST_SCENARIOS.md) for the full index, acceptance criteria, and corpus provenance.

### Scenario 1 Result: PICALM / Alzheimer's Disease

![PICALM Alzheimer's Knowledge Graph](tests/scenarios/screenshots/scenario-01-graph.png)

*149 nodes, 457 links, 6 auto-labeled communities. Full results: [scenario-01-picalm-alzheimers.md](tests/scenarios/scenario-01-picalm-alzheimers.md)*

| Community | Members | Theme |
|---|---|---|
| **Alzheimer Disease Risk Loci (30 genes)** | 49 | GWAS genes converging on LOAD |
| **Endosomal Trafficking (APP, PSEN1, PSEN2)** | 18 | Core amyloid/tau pathology cascade |
| **Phagocytosis / Amyloid Beta Processing** | 15 | PICALM variants, TREM2, CD33 |
| **Autophagy / Endocytic Pathway** | 17 | Cross-disease autophagy links (AD, PD) |
| **Clathrin-Mediated Endocytosis in Hippocampus** | 10 | Tissue-specific CME biology |
| **Cholesterol Synthesis in Microglia** | 8 | 2025 Nature: rs10792832 causal mechanism |

### Scenario 2 Result: KRAS G12C Inhibitor Landscape

![KRAS G12C Knowledge Graph](tests/scenarios/screenshots/scenario-02-graph.png)

*108 nodes, 307 links, 4 auto-labeled communities. Full results: [scenario-02-kras-g12c-landscape.md](tests/scenarios/scenario-02-kras-g12c-landscape.md)*

| Community | Members | Theme |
|---|---|---|
| **EGFR Inhibitors / Adavosertib / Panitumumab** | 25 | Combination strategies and CRC responses |
| **Adagrasib / Immune Checkpoint Inhibitors / BRAF** | 20 | Adagrasib clinical profile and bypass resistance |
| **RAS Signaling / RAF/MEK Pathway** | 17 | Mechanistic biology and emerging targets |
| **Pancreatic Ductal Adenocarcinoma / PD-1** | 10 | Disease indications and next-gen RAS-ON inhibitors |

### Scenario 3 Result: Rare Disease Therapeutics

![Rare Disease Knowledge Graph](tests/scenarios/screenshots/scenario-03-graph.png)

*94 nodes, 229 links, 4 auto-labeled communities. Full results: [scenario-03-rare-disease.md](tests/scenarios/scenario-03-rare-disease.md)*

| Community | Members | Theme |
|---|---|---|
| **PKU Enzyme Replacement / Gene Therapy Safety** | 28 | Pegvaliase, sapropterin, PAH gene therapy |
| **CNP Analog / Bone Biology** | 24 | Vosoritide, achondroplasia, FGFR3/NPR-B pathway |
| **Arimoclomol / HSP Co-induction** | 22 | Niemann-Pick C, HSF1/HSP70, miglustat |
| **ERT Immunogenicity / Clinical Trials** | 20 | Enzyme replacement therapy, anti-drug antibodies |

### Scenario 4 Result: Immuno-Oncology Combinations

![Immuno-Oncology Knowledge Graph](tests/scenarios/screenshots/scenario-04-graph.png)

*132 nodes, 361 links, 5 auto-labeled communities. Full results: [scenario-04-immunooncology.md](tests/scenarios/scenario-04-immunooncology.md)*

| Community | Members | Theme |
|---|---|---|
| **PD-1 Immune Checkpoint Blockade in CD8+ T Cells** | 31 | Core nivolumab biology, biomarkers (PD-L1, TMB, MSI-H) |
| **Brain Metastases — CTLA-4** | 16 | Ipilimumab combinations, CheckMate trials, melanoma |
| **LAG-3 Signaling Pathway (LAG3)** | 18 | Relatlimab, RELATIVITY trials, dual checkpoint blockade |
| **PD-1/PD-L1 Signaling Pathway (PDCD1, CD274)** | 15 | 13 approved anti-PD-(L)1 agents, combination strategies |
| **Metabolic Reprogramming in Tumor Immune Microenvironment** | 15 | HCC immunotherapy, cabozantinib/VEGF, spatial transcriptomics |

### Scenario 5 Result: Cardiovascular & Inflammation

![Cardiovascular Knowledge Graph](tests/scenarios/screenshots/scenario-05-graph.png)

*94 nodes, 246 links, 5 auto-labeled communities. Full results: [scenario-05-cardiovascular.md](tests/scenarios/scenario-05-cardiovascular.md)*

| Community | Members | Theme |
|---|---|---|
| **Obstructive HCM — Cardiac Myosin ATPase** | 24 | Mavacamten trials, LVOT gradient, NT-proBNP |
| **Sarcomere Contractile Pathway (MYBPC3, MYH7)** | 15 | Aficamten, R403Q mutation, sarcomere biology |
| **TYK2 Allosteric Inhibition** | 14 | Deucravacitinib, POETYK trials, psoriasis |
| **JAK-STAT Signaling Pathway** | 11 | IL-12/IL-23, type I interferons, cytokine signaling |
| **Cardiac Myosin Inhibition** | 8 | Shared mechanism hub, FDA approval, REMS |

### Scenario 6 Result: GLP-1 Competitive Intelligence

![GLP-1 Knowledge Graph](tests/scenarios/screenshots/scenario-06-graph.png)

*206 nodes, 630 links, 9 auto-labeled communities. 34 documents (24 PubMed + 10 patents from 5 companies). Full results: [scenario-06-glp1-landscape.md](tests/scenarios/scenario-06-glp1-landscape.md)*

| Community | Members | Theme |
|---|---|---|
| **MASH — GCGR, Albumin, GIPR** | 26 | Survodutide, retatrutide, hepatic lipid oxidation |
| **GLP-1(7-37) / SNAC / Semaglutide** | 24 | Oral delivery technology, SNAC absorption enhancer |
| **Appetite Regulation in Infralimbic Cortex** | 21 | GLP-1 in addiction, GABA modulation, CNS expression |
| **Danuglipron / Alzheimer / Parkinson** | 19 | Oral small molecules, neurodegeneration |
| **Orforglipron / Tirzepatide / MASLD** | 18 | Next-gen compounds, ACHIEVE/SURMOUNT trials |
| **CagriSema / Amylin Co-Agonist / Cagrilintide** | 17 | Combination therapy, REDEFINE trials |
| **GLP-1 Receptor Agonism / Inflammation** | 14 | Core mechanism, cardiovascular protection |
| **Anti-Inflammatory Activity** | 9 | CV risk reduction mechanisms |
| **Denifanstat / Efruxifermin / Lanifibranor** | 9 | Non-GLP-1 MASH competitor drugs |

**What's new in Scenario 6:**
- **Multi-source corpus** — first scenario using PubMed + Google Scholar + Google Patents (via SerpAPI)
- **Patent extraction** — peptide sequences, CAS numbers (tirzepatide: 2023788-19-2), InChIKeys, chemical formulas from 10 patents across 5 companies
- **Largest graph** — 206 nodes, 630 links (vs 94-149 nodes for S1-S5)
- **"Bring Your Own Papers"** — scientists with institutional access can supplement the corpus with paywalled Lancet/JAMA/BMJ papers

### Automating Test Runs

To run fully automated without permission prompts:

```bash
# Option 1: Skip all permissions (trusted local use only)
claude --dangerously-skip-permissions

# Option 2: Pre-approve specific patterns
claude --allowedTools "Bash(python3 *)" --allowedTools "Read(*)" --allowedTools "Write(*)"
```

Or add to `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(python3 *)",
      "Bash(echo *)",
      "Bash(ls *)",
      "Bash(mkdir *)",
      "Read(*)",
      "Write(*/output/*)",
      "Edit(*)"
    ]
  }
}
```

### Testing Rigor & Findings

Each test run exercises the full pipeline and feeds engineering findings back into the codebase. Three critical bugs were discovered and fixed during testing — including an LLM-output schema mismatch (F-001), a semantic community labeling gap (F-002), and a plugin version propagation failure (F-003). All findings include root cause analysis, two-layer fixes, and cross-scenario verification.

See [tests/FINDINGS.md](tests/FINDINGS.md) for the complete engineering findings log.

---

## Architecture

```mermaid
flowchart TB
    subgraph CC["Claude Code Runtime"]
        subgraph EP["Epistract Plugin"]
            ACQ["Acquire<br/>/acquire"]
            CMD["Commands<br/>/ingest /build /view<br/>/query /export /validate"]
            SKL["Drug Discovery<br/>Extraction Skill"]
            AGT["Agents<br/>extractor · validator<br/>acquirer"]
            ACQ --> CMD
            CMD --> SKL
            SKL --> AGT
        end
        subgraph SK["sift-kg Engine"]
            ING["Document Ingest<br/>Kreuzberg · OCR"]
            GRB["Graph Builder<br/>NetworkX · SemHash"]
            RES["Entity Resolution<br/>LLM-proposed merges"]
            EXP["Export<br/>JSON · GraphML · GEXF<br/>CSV · SQLite"]
            VIZ["Interactive Viewer<br/>HTML · Force-directed"]
            ING --> GRB --> RES --> EXP
            RES --> VIZ
        end
        EP --> SK
    end
    PUB["PubMed<br/>NCBI E-utilities"] --> ACQ
    USR["Scientist / Researcher"] --> CMD
    USR --> ACQ
    VIZ --> BRW["Browser"]
    EXP --> EXT["Gephi · Cytoscape<br/>DuckDB · pandas"]
```

## Pipeline

```mermaid
flowchart LR
    PUB["PubMed Search<br/>/acquire<br/>(optional)"] -.-> DOCS
    DOCS["Documents<br/>PDF · DOCX · HTML<br/>TXT · Patents"] --> ING["Text Extraction<br/>+ Chunking"]
    ING --> EXT["Claude Extraction<br/>Entities + Relations"]
    EXT --> VAL["Molecular Validation<br/>RDKit · Biopython"]
    VAL --> BLD["Graph Building<br/>Dedup · Communities"]
    BLD --> LBL["Community Labeling<br/>Auto-generated names"]
    LBL --> OUT["Output"]
    OUT --> VIZ["Interactive Viewer"]
    OUT --> EXPF["Export<br/>GraphML · SQLite · CSV"]
    OUT --> QRY["Search & Query"]
```

---

## What It Extracts

Epistract uses a domain schema designed for drug discovery, grounded in the [Biolink Model](https://biolink.github.io/biolink-model/), [Gene Ontology](http://geneontology.org/), [ChEBI](https://www.ebi.ac.uk/chebi/), [MeSH](https://meshb.nlm.nih.gov/), and 40+ other biomedical ontologies.

### Domain Schema — 17 Entity Types, 30 Relation Types

**Implemented in `domain.yaml`, enforced during extraction:**

| Category | Entity Types | Count |
|---|---|---|
| **Drug & Chemistry** | COMPOUND, METABOLITE | 2 |
| **Molecular Biology** | GENE, PROTEIN, PROTEIN_DOMAIN, SEQUENCE_VARIANT, CELL_OR_TISSUE | 5 |
| **Disease & Phenotype** | DISEASE, PHENOTYPE, ADVERSE_EVENT | 3 |
| **Clinical** | CLINICAL_TRIAL, BIOMARKER, REGULATORY_ACTION | 3 |
| **Pathways & Mechanisms** | PATHWAY, MECHANISM_OF_ACTION | 2 |
| **Context** | ORGANIZATION, PUBLICATION | 2 |

**30 relation types** covering:
- **Drug-Target** — TARGETS, INHIBITS, ACTIVATES, BINDS_TO, HAS_MECHANISM
- **Drug-Disease** — INDICATED_FOR, CONTRAINDICATED_FOR
- **Drug-Clinical** — EVALUATED_IN, CAUSES
- **Drug-Drug** — DERIVED_FROM, COMBINED_WITH, INTERACTS_WITH
- **Molecular Biology** — ENCODES, PARTICIPATES_IN, IMPLICATED_IN, CONFERS_RESISTANCE_TO, EXPRESSED_IN, LOCALIZED_TO, HAS_VARIANT, HAS_DOMAIN, METABOLIZED_BY, PHOSPHORYLATES, FORMS_COMPLEX_WITH, REGULATES_EXPRESSION
- **Biomarker** — PREDICTS_RESPONSE_TO, DIAGNOSTIC_FOR
- **Organizational** — DEVELOPED_BY, PUBLISHED_IN, GRANTS_APPROVAL_FOR
- **Fallback** — ASSOCIATED_WITH

Every extraction links back to the source document and passage. Every relation carries a confidence score calibrated for scientific literature.

### Molecular Biology Linkage

```mermaid
flowchart TB
    GENE["GENE<br/>HGNC symbol"] -->|ENCODES| PROT["PROTEIN<br/>UniProt"]
    GENE -->|HAS_VARIANT| VAR["SEQUENCE_VARIANT<br/>ClinVar · COSMIC"]
    PROT -->|PARTICIPATES_IN| PATH["PATHWAY<br/>KEGG · Reactome"]
    PROT -->|EXPRESSED_IN| CELL["CELL_OR_TISSUE<br/>Cell Ontology"]
    PATH -->|IMPLICATED_IN| DIS["DISEASE<br/>MeSH"]
    VAR -->|CONFERS_RESISTANCE_TO| DRUG["COMPOUND<br/>ChEBI · DrugBank"]
    VAR -->|PREDICTS_RESPONSE_TO| DRUG
    DRUG -->|TARGETS| PROT
    DRUG -->|INHIBITS| PROT
    DRUG -->|INDICATED_FOR| DIS
    DRUG -->|EVALUATED_IN| TRIAL["CLINICAL_TRIAL<br/>NCT"]
    DRUG -->|CAUSES| AE["ADVERSE_EVENT<br/>MedDRA"]
    DRUG -->|HAS_MECHANISM| MOA["MECHANISM_OF_ACTION"]
    BIO["BIOMARKER<br/>BEST framework"] -->|PREDICTS_RESPONSE_TO| DRUG
    BIO -->|DIAGNOSTIC_FOR| DIS
```

The schema captures the full chain from gene → protein → pathway → disease, with drug intervention points, resistance mechanisms, and biomarker links at every level.

---

## Structural Enrichment

Epistract doesn't just extract text — it **validates and enriches molecular structures and sequences**, creating first-class graph nodes from validated identifiers.

### Three Levels of Structural Knowledge

**Level 1 — Structure as Identity:**
Validated SMILES strings become `CHEMICAL_STRUCTURE` nodes with canonical SMILES, InChI, InChIKey, molecular weight, LogP, TPSA, and Lipinski Ro5 analysis. Validated sequences become `NUCLEOTIDE_SEQUENCE` or `PEPTIDE_SEQUENCE` nodes with computed properties. All linked to parent entities via `HAS_STRUCTURE` / `HAS_SEQUENCE` relations.

**Level 2 — InChIKey Deduplication:**
Same molecule, different names across documents? Epistract detects this via InChIKey matching. If two papers call the same compound different names but contain the same SMILES → same InChIKey → merge candidate reported. This is structural deduplication — far more reliable than name matching.

**Level 3 — Computed Properties as Knowledge:**
RDKit computes drug-likeness properties (Lipinski Ro5 violations, TPSA, LogP) that become queryable attributes. Biopython computes sequence properties (GC content, isoelectric point, molecular weight) that enable filtering.

### Why This Matters

LLMs cannot reliably reproduce character-exact molecular notation (SMILES, sequences). A single transposition produces a different molecule. Epistract uses a **hybrid approach**:
1. **Claude** identifies molecular identifiers in text and understands what they represent
2. **Regex patterns** extract the exact strings from the source text
3. **RDKit/Biopython** validates and enriches with computed properties

This means your knowledge graph contains **verified** molecular structures, not LLM approximations.

---

## Molecular Validation

When [RDKit](https://www.rdkit.org/) and/or [Biopython](https://biopython.org/) are installed, Epistract automatically validates molecular identifiers:

**Chemistry (RDKit):**
- SMILES → canonical form, InChI, InChIKey, molecular formula, MW, LogP, HBD/HBA, TPSA, Lipinski Ro5
- Invalid SMILES → flagged and excluded from graph

**Sequences (Biopython):**
- DNA/RNA → GC content, complement, reverse complement, translation
- Amino acid → molecular weight, isoelectric point, instability index, GRAVY
- Antibody CDR sequences → identified by region (H1/H2/H3, L1/L2/L3)

**Pattern Detection (no dependencies):**
- NCT numbers → ClinicalTrials.gov identifiers
- CAS numbers → chemical registry identifiers
- Patent numbers (US, PCT) → intellectual property references
- InChIKey → 27-character molecular fingerprints

---

## How It Works

Epistract combines two systems:

1. **Claude** reads scientific text with deep domain understanding. It identifies entities, classifies them into the schema, extracts relationships with confidence scores, and captures evidence passages. Claude understands that "BRAF V600E" is a sequence variant in the BRAF gene, that "pembrolizumab" is a PD-1-targeting monoclonal antibody, and that "KEYNOTE-024" is a Phase III trial.

2. **[sift-kg](https://github.com/juanceresa/sift-kg)** handles everything downstream: text ingestion from 75+ formats, graph construction with automatic deduplication (SemHash, Unicode normalization), entity resolution with human-in-the-loop review, Louvain community detection, interactive visualization, and export to GraphML/GEXF/CSV/SQLite.

3. **Community labeling** (`label_communities.py`) automatically generates descriptive names for each community based on member entity composition — gene-dominant clusters become "Disease Risk Loci (N genes)", pathway-driven clusters name the pathway, mechanism+cell clusters produce labels like "Cholesterol Synthesis in Microglia".

---

## Ontology Grounding

Every entity type maps to established biomedical ontologies:

| Entity Type | Primary Ontology | Cross-References |
|---|---|---|
| COMPOUND | [ChEBI](https://www.ebi.ac.uk/chebi/) | DrugBank, ChEMBL, PubChem |
| GENE | [HGNC](https://www.genenames.org/) | NCBI Gene, Ensembl |
| PROTEIN | [UniProtKB](https://www.uniprot.org/) | PDB, InterPro |
| DISEASE | [MeSH](https://meshb.nlm.nih.gov/) | Disease Ontology, ICD-11, OMIM |
| PATHWAY | [KEGG](https://www.genome.jp/kegg/) | Reactome, GO Biological Process |
| ADVERSE_EVENT | [MedDRA](https://www.meddra.org/) | CTCAE |
| SEQUENCE_VARIANT | [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) | dbSNP, COSMIC |
| BIOMARKER | [BEST Framework](https://www.ncbi.nlm.nih.gov/books/NBK326791/) | Per-analyte ontology |
| CELL_OR_TISSUE | [Cell Ontology](http://obofoundry.org/ontology/cl.html) | Uberon |
| PROTEIN_DOMAIN | [InterPro](https://www.ebi.ac.uk/interpro/) | Pfam, SMART |
| METABOLITE | [ChEBI](https://www.ebi.ac.uk/chebi/) | HMDB, KEGG Compound |

---

## Naming Conventions

Epistract enforces standard biomedical nomenclature:

| Entity | Standard | Example |
|---|---|---|
| Drugs | INN (International Nonproprietary Name) | pembrolizumab, not Keytruda |
| Genes | HGNC symbols | EGFR, TP53, BRCA1 |
| Variants | HGVS protein notation | BRAF V600E, KRAS G12C |
| Diseases | MeSH preferred terms | non-small cell lung cancer |
| Adverse events | MedDRA preferred terms | immune-mediated colitis |
| Proteins | UniProt standard names | PD-1, HER2, VEGFR-2 |

---

## Roadmap

- **Neo4j graph database export** — MERGE nodes/edges with constraints and indexes
- **Vector embeddings** — entity description embeddings and Morgan fingerprints in Neo4j vector index
- **Combined RAG query** — `/epistract-ask` for vector + graph + structure similarity in one query
- **External enrichment** — PubChem/ChEMBL/UniProt API lookups adding nodes from external knowledge bases

---

## Technical Documentation

- **[DEVELOPER.md](DEVELOPER.md)** — Technical reference with 40+ ontology links, sift-kg integration details, data formats, and the full dependency tree
- **[Domain Specification](docs/drug-discovery-domain-spec.md)** — Complete 2000-line schema specification with ontology alignment, extraction guidance, and validation criteria
- **[Plugin Design](docs/epistract-plugin-design.md)** — Architecture and component design
- **[Test Scenarios](tests/MANUAL_TEST_SCENARIOS.md)** — 6 real-world drug discovery scenarios with curated corpora (PubMed + Google Scholar + Google Patents)
- **[Test Requirements](tests/TEST_REQUIREMENTS.md)** — 16 unit tests, 8 functional tests, 18 user acceptance tests with traceability matrix
- **[Engineering Findings](tests/FINDINGS.md)** — Bugs discovered, root cause analysis, systemic lessons from production-quality testing

---

## Requirements

- [Claude Code](https://claude.ai/claude-code) (the runtime environment — handles all extraction via its own API access)
- Python 3.11+
- sift-kg (installed by `/epistract-setup`) — requires an LLM API key for entity resolution (see Quick Start above)
- Optional: [RDKit](https://www.rdkit.org/) (~50MB) for SMILES validation and structural enrichment
- Optional: [Biopython](https://biopython.org/) (~20MB) for sequence validation

## License

MIT
