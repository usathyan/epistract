# Epistract

**Turn scientific literature into structured biomedical knowledge.**

Epistract reads drug discovery documents — PubMed papers, bioRxiv preprints, patent filings, clinical trial reports, FDA labels — and builds a knowledge graph that captures the entities and relationships a scientist cares about: compounds, targets, mechanisms, trials, biomarkers, pathways, and how they connect.

It runs as a Claude Code plugin. You point it at a folder of documents. It reads them with a scientist's understanding, extracts structured knowledge using a 23-type entity schema grounded in established biomedical ontologies, validates molecular identifiers with RDKit and Biopython, and produces an interactive graph you can explore in your browser.

## The Name

From Greek **episteme** (ἐπιστήμη) — structured scientific knowledge, the highest form of knowledge in Aristotle's epistemological hierarchy — combined with **extract**. Episteme is not opinion or belief; it is knowledge grounded in evidence, demonstration, and systematic understanding. That is what this tool produces: not a bag of keywords, but a structured representation of how scientific concepts relate to each other, traceable back to the source text.

## What It Extracts

Epistract uses a domain schema designed for drug discovery, grounded in the [Biolink Model](https://biolink.github.io/biolink-model/), [Gene Ontology](http://geneontology.org/), [ChEBI](https://www.ebi.ac.uk/chebi/), [MeSH](https://meshb.nlm.nih.gov/), and 40+ other biomedical ontologies.

### Entities (23 types)

| Category | Entity Types |
|---|---|
| **Drug & Chemistry** | COMPOUND, CHEMICAL_STRUCTURE, METABOLITE |
| **Molecular Biology** | GENE, PROTEIN, PROTEIN_DOMAIN, SEQUENCE_VARIANT, PROTEIN_COMPLEX |
| **Sequences** | NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE |
| **Disease & Phenotype** | DISEASE, PHENOTYPE, ADVERSE_EVENT |
| **Clinical** | CLINICAL_TRIAL, BIOMARKER, REGULATORY_ACTION |
| **Pathways & Processes** | PATHWAY, MECHANISM_OF_ACTION |
| **Genomics** | GENETIC_ASSOCIATION, GENE_SIGNATURE |
| **Context** | ORGANIZATION, PUBLICATION, CELL_OR_TISSUE |

### Relations (46 types)

Covering drug-target pharmacology (TARGETS, INHIBITS, ACTIVATES, BINDS_TO), drug-disease (INDICATED_FOR, CONTRAINDICATED_FOR), clinical development (EVALUATED_IN, CAUSES), molecular biology (ENCODES, PARTICIPATES_IN, EXPRESSED_IN, PHOSPHORYLATES), statistical genetics (GENETICALLY_ASSOCIATED_WITH, CAUSAL_FOR), and more.

Every extraction links back to the source document and passage. Every relation carries a confidence score calibrated for scientific literature.

## Quick Start

### 1. Install

Epistract requires [Claude Code](https://claude.ai/claude-code) and Python 3.11+.

```bash
# Clone the repository
git clone https://github.com/yourusername/epistract.git
cd epistract

# Install as a Claude Code plugin
claude plugin add ./epistract

# Or symlink for development
ln -s $(pwd) ~/.claude/plugins/epistract
```

Then, inside a Claude Code session:

```
/epistract-setup
```

This installs sift-kg and optionally RDKit (for SMILES validation) and Biopython (for sequence validation).

### 2. Ingest Documents

Place your documents in a folder — PDFs, DOCX, HTML, plain text, and 75+ other formats are supported.

```
/epistract-ingest ./my-papers/
```

Epistract will:
1. Read and chunk all documents (handling scanned PDFs with OCR if needed)
2. Extract entities and relations using the drug discovery schema
3. Validate any SMILES strings and sequences found in the text
4. Build a deduplicated knowledge graph with community detection
5. Open an interactive visualization in your browser

### 3. Explore

The interactive viewer shows your knowledge graph with:
- **Community regions** — colored zones grouping related entities
- **Focus mode** — double-click any entity to isolate its neighborhood
- **Trail breadcrumb** — tracks your exploration path through the graph
- **Search** — find entities by name, type, or source document
- **Filtering** — by entity type, community, confidence, source document

### 4. Export

```
/epistract-export graphml    # For Gephi, yEd, Cytoscape
/epistract-export sqlite     # For SQL queries, DuckDB, Datasette
/epistract-export csv        # For spreadsheets, pandas
```

## Example: KRAS G12C Inhibitor Landscape

```
/epistract-ingest ./kras_papers/

Result:
  15 papers processed
  267 entities extracted:
    34 compounds, 45 proteins, 28 genes, 19 diseases,
    23 clinical trials, 15 mechanisms, 12 biomarkers, ...
  489 relations:
    67 INHIBITS, 45 TARGETS, 23 INDICATED_FOR,
    18 EVALUATED_IN, 15 CONFERS_RESISTANCE_TO, ...
  7 SMILES validated, 3 sequences validated
  6 communities detected
```

The resulting graph connects sotorasib and adagrasib to their shared target (KRAS G12C), links to clinical trials (CodeBreaK 100, KRYSTAL-1), captures resistance mechanisms (acquired mutations in KRAS, MET amplification), and maps the upstream signaling cascade (RAS-MAPK pathway) — all traceable to specific passages in the source papers.

## Molecular Validation

When RDKit and/or Biopython are installed, Epistract automatically validates molecular identifiers found in your documents:

**Chemistry (RDKit):**
- SMILES strings → validated, canonicalized, enriched with molecular weight, LogP, H-bond donors/acceptors, TPSA, ring count
- InChI/InChIKey → cross-referenced
- Invalid SMILES → flagged and excluded

**Sequences (Biopython):**
- DNA/RNA sequences → validated, GC content computed, reverse complement generated
- Amino acid sequences → validated, molecular weight and isoelectric point computed
- Antibody CDR sequences → identified and annotated

This matters because LLMs cannot reliably reproduce character-exact molecular notation. Epistract uses a hybrid approach: Claude identifies and contextualizes molecular identifiers, then deterministic tools extract and validate the exact strings from the source text.

## How It Works

Epistract combines two systems:

1. **Claude** (the LLM running in Claude Code) reads scientific text with deep domain understanding. It identifies entities, classifies them into the 23-type schema, extracts relationships with confidence scores, and captures evidence passages. Claude understands that "BRAF V600E" is a sequence variant in the BRAF gene, that "pembrolizumab" is a PD-1-targeting monoclonal antibody, and that "KEYNOTE-024" is a Phase III trial — this domain expertise produces higher-quality extractions than general-purpose NER.

2. **sift-kg** (the knowledge graph engine) handles everything downstream: text ingestion from 75+ document formats, graph construction with automatic deduplication, entity resolution with human-in-the-loop review, community detection, interactive visualization, and export to GraphML/GEXF/CSV/SQLite. It is a mature, tested pipeline that Epistract uses as its core engine.

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

This grounding means extracted entities can be cross-referenced against public databases — linking your knowledge graph to the broader biomedical knowledge ecosystem.

## Use Cases

- **Literature review** — Map how compounds, targets, and mechanisms connect across a body of research. See which findings support or contradict each other.
- **Target validation** — Trace genetic evidence (GWAS, Mendelian randomization) through to protein targets and existing compounds.
- **Competitive intelligence** — Ingest patent filings and clinical trial publications to map the landscape for a therapeutic area.
- **Safety signal detection** — Extract and connect adverse events across clinical trial reports and post-marketing surveillance documents.
- **Biomarker discovery** — Identify which biomarkers predict response to which therapies, across published evidence.
- **Due diligence** — Build a structured knowledge base from a target company's publication and patent portfolio.

## Naming Conventions

Epistract enforces standard biomedical nomenclature in its extractions:

| Entity | Standard | Example |
|---|---|---|
| Drugs | INN (International Nonproprietary Name) | pembrolizumab, not Keytruda |
| Genes | HGNC symbols | EGFR, TP53, BRCA1 |
| Variants | HGVS protein notation | BRAF V600E, KRAS G12C |
| Diseases | MeSH preferred terms | non-small cell lung cancer |
| Adverse events | MedDRA preferred terms | immune-mediated colitis |
| Proteins | UniProt standard names | PD-1, HER2, VEGFR-2 |

## Test Scenarios

Epistract ships with five real-world drug discovery research scenarios, each backed by a curated corpus of PubMed abstracts:

| # | Scenario | Focus | Documents |
|---|---|---|---|
| 1 | [PICALM / Alzheimer's](tests/MANUAL_TEST_SCENARIOS.md#scenario-1-picalm--alzheimers-disease--genetic-target-validation) | Genetic target validation | 15 papers |
| 2 | [KRAS G12C Landscape](tests/MANUAL_TEST_SCENARIOS.md#scenario-2-kras-g12c-inhibitor-landscape--competitive-intelligence) | Competitive intelligence | 15 papers |
| 3 | [BioMarin Rare Disease](tests/MANUAL_TEST_SCENARIOS.md#scenario-3-biomarin-rare-disease-pipeline--pku-achondroplasia-hemophilia-a) | Due diligence | 15 papers |
| 4 | [BMS Immuno-Oncology](tests/MANUAL_TEST_SCENARIOS.md#scenario-4-bristol-myers-squibb-immuno-oncology--checkpoint-combinations) | Checkpoint combinations | 15 papers |
| 5 | [BMS Cardiovascular](tests/MANUAL_TEST_SCENARIOS.md#scenario-5-bms-cardiovascular--inflammation--mavacamten-and-deucravacitinib) | Cardiology + inflammation | 14 papers |

See [MANUAL_TEST_SCENARIOS.md](tests/MANUAL_TEST_SCENARIOS.md) for full details on each scenario, including the PubMed queries used, expected knowledge graph structure, and acceptance criteria.

## Phases

**Phase 1 (current):** Document extraction, knowledge graph building, interactive visualization, static export formats.

**Phase 1.5 (in progress):** Structural enrichment — validated SMILES, sequences, and molecular identifiers become first-class graph nodes with computed properties. InChIKey-based compound deduplication. Structural similarity edges.

**Phase 2 (planned):**
1. **Neo4j Cypher exporter** — MERGE nodes/edges into Neo4j with constraints and indexes
2. **Entity description embeddings** — embed entity descriptions with sentence-transformers, store in Neo4j vector index
3. **Morgan fingerprint embeddings** — RDKit molecular fingerprints stored as vectors for structural similarity search
4. **Combined RAG query** — `/epistract-ask "What compounds similar to sotorasib target KRAS?"` → vector search + graph traversal + structure similarity in one query
5. **External enrichment** — PubChem/ChEMBL/UniProt API lookups that add nodes and edges from external knowledge bases

## Requirements

- [Claude Code](https://claude.ai/claude-code) (the runtime environment)
- Python 3.11+
- sift-kg (installed by `/epistract-setup`)
- Optional: RDKit (~50MB), Biopython (~20MB) for molecular validation

## License

MIT
