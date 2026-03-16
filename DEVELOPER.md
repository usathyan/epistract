# Epistract — Developer & Technical Reference

This document is for developers extending, debugging, or integrating with Epistract. For usage, see [README.md](README.md).

---

## Table of Contents

1. [Architecture](#architecture)
2. [Core Dependencies](#core-dependencies)
3. [Domain Schema Reference](#domain-schema-reference)
4. [Biomedical Ontologies & Standards](#biomedical-ontologies--standards)
5. [sift-kg Integration](#sift-kg-integration)
6. [Claude-as-Extractor Adapter](#claude-as-extractor-adapter)
7. [Molecular Validation Pipeline](#molecular-validation-pipeline)
8. [Plugin Component Reference](#plugin-component-reference)
9. [Data Formats](#data-formats)
10. [Testing & Validation](#testing--validation)
11. [Phase 2: Neo4j & Vector RAG](#phase-2-neo4j--vector-rag)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Runtime                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 Epistract Plugin                       │  │
│  │                                                       │  │
│  │  Commands ──→ Skills ──→ Agents                       │  │
│  │     │            │          │                         │  │
│  │     └────────────┼──────────┘                         │  │
│  │                  │                                    │  │
│  │         Claude reads documents                        │  │
│  │         Claude extracts entities/relations             │  │
│  │         Claude writes DocumentExtraction JSON          │  │
│  │                  │                                    │  │
│  │     ┌────────────▼────────────┐                       │  │
│  │     │  Validation Scripts     │                       │  │
│  │     │  (Python via Bash tool) │                       │  │
│  │     │  • RDKit (chemistry)    │                       │  │
│  │     │  • Biopython (seqs)     │                       │  │
│  │     │  • Regex (patterns)     │                       │  │
│  │     └────────────┬────────────┘                       │  │
│  └──────────────────┼────────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼────────────────────────────────────┐  │
│  │              sift-kg Python Library                    │  │
│  │                                                       │  │
│  │  ingest/     → Kreuzberg document reading + OCR       │  │
│  │  graph/      → NetworkX graph builder + pre-dedup     │  │
│  │  resolve/    → Entity resolution (LLM-proposed)       │  │
│  │  narrate/    → Narrative generation                   │  │
│  │  export.py   → GraphML, GEXF, CSV, SQLite, JSON      │  │
│  │  visualize.py → Interactive HTML viewer               │  │
│  │  domains/    → Schema definitions (YAML)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** sift-kg's interchange format is `DocumentExtraction` — a Pydantic model containing `entities: list[ExtractedEntity]` and `relations: list[ExtractedRelation]`. Epistract produces this JSON directly from Claude's extraction. Everything downstream in sift-kg (graph builder, resolver, exporter, viewer) consumes it unchanged.

---

## Core Dependencies

### Runtime

| Dependency | Version | Purpose | Source |
|---|---|---|---|
| **Python** | ≥3.11 | Runtime | [python.org](https://www.python.org/) |
| **Claude Code** | latest | LLM runtime, plugin host | [claude.ai/claude-code](https://claude.ai/claude-code) |
| **sift-kg** | ≥0.9.0 | Document ingestion, graph building, export, visualization | [github.com/juanceresa/sift-kg](https://github.com/juanceresa/sift-kg) |

### sift-kg Transitive Dependencies

| Dependency | Purpose | Project |
|---|---|---|
| **NetworkX** ≥3.2 | Graph data structure (MultiDiGraph) | [networkx.org](https://networkx.org/) |
| **Pydantic** ≥2.5 | Data models, validation | [docs.pydantic.dev](https://docs.pydantic.dev/) |
| **LiteLLM** ≥1.0 | Multi-provider LLM client (used for entity resolution, narration) | [github.com/BerriAI/litellm](https://github.com/BerriAI/litellm) |
| **Kreuzberg** ≥4.0 | Document text extraction (75+ formats) | [kreuzberg-dev.github.io/kreuzberg](https://kreuzberg-dev.github.io/kreuzberg/) |
| **SemHash** ≥0.4 | Fuzzy string deduplication | [github.com/MinishLab/semhash](https://github.com/MinishLab/semhash) |
| **pyvis** ≥0.3 | Graph visualization (HTML) | [pyvis.readthedocs.io](https://pyvis.readthedocs.io/) |
| **pdfplumber** ≥0.10 | Legacy PDF extraction backend | [github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber) |
| **python-docx** ≥1.0 | DOCX reading | [python-docx.readthedocs.io](https://python-docx.readthedocs.io/) |
| **BeautifulSoup4** ≥4.12 | HTML parsing | [crummy.com/software/BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) |
| **Unidecode** ≥1.3 | Unicode normalization | [pypi.org/project/Unidecode](https://pypi.org/project/Unidecode/) |
| **inflect** ≥7.0 | Singularization for dedup | [pypi.org/project/inflect](https://pypi.org/project/inflect/) |
| **Rich** ≥13.0 | Terminal formatting | [rich.readthedocs.io](https://rich.readthedocs.io/) |
| **Typer** ≥0.9 | CLI framework | [typer.tiangolo.com](https://typer.tiangolo.com/) |
| **PyYAML** ≥6.0 | YAML parsing | [pyyaml.org](https://pyyaml.org/) |

### Optional: Molecular Validation

| Dependency | Size | Purpose | Project |
|---|---|---|---|
| **RDKit** (rdkit-pypi) | ~50MB | SMILES validation, canonicalization, molecular properties, Lipinski analysis | [rdkit.org](https://www.rdkit.org/) |
| **Biopython** | ~20MB | Sequence validation (DNA/RNA/protein), GC content, isoelectric point, BLAST | [biopython.org](https://biopython.org/) |

### Optional: sift-kg Extras

| Dependency | Size | Purpose |
|---|---|---|
| **sentence-transformers** | ~2GB (PyTorch) | Semantic clustering for entity resolution (`sift-kg[embeddings]`) |
| **google-cloud-vision** | ~20MB | Google Cloud Vision OCR backend (`sift-kg[ocr]`) |

---

## Domain Schema Reference

The drug discovery domain schema defines 23 entity types and 46 relation types. The full specification is in `docs/drug-discovery-domain-spec.md`.

### Entity Type Hierarchy

```
Named Thing (Biolink root)
├── Chemical/Drug
│   ├── COMPOUND              — Therapeutic agents (drugs, candidates, biologics)
│   ├── CHEMICAL_STRUCTURE    — SMILES, InChI, IUPAC notation
│   └── METABOLITE            — Endogenous small molecules, cofactors, neurotransmitters
│
├── Molecular Biology
│   ├── GENE                  — Genes, genetic loci (HGNC symbols)
│   ├── PROTEIN               — Proteins, receptors, enzymes (UniProt)
│   ├── PROTEIN_DOMAIN        — Functional domains, binding sites (InterPro)
│   ├── PROTEIN_COMPLEX       — Multi-subunit assemblies (Complex Portal)
│   ├── SEQUENCE_VARIANT      — Mutations, SNPs, fusions (ClinVar, COSMIC)
│   ├── NUCLEOTIDE_SEQUENCE   — DNA/RNA sequences
│   └── PEPTIDE_SEQUENCE      — Amino acid sequences, CDRs
│
├── Disease & Phenotype
│   ├── DISEASE               — Diseases, conditions, indications (MeSH)
│   ├── PHENOTYPE             — Observable characteristics (HPO)
│   └── ADVERSE_EVENT         — Drug side effects, toxicities (MedDRA)
│
├── Clinical
│   ├── CLINICAL_TRIAL        — Registered clinical studies (NCT)
│   ├── BIOMARKER             — Diagnostic/predictive indicators (BEST)
│   └── REGULATORY_ACTION     — FDA/EMA approvals, designations
│
├── Pathways & Mechanisms
│   ├── PATHWAY               — Signaling/metabolic pathways (KEGG, Reactome)
│   └── MECHANISM_OF_ACTION   — Pharmacological mechanisms
│
├── Genomics
│   ├── GENETIC_ASSOCIATION   — GWAS hits, eQTL, Mendelian randomization
│   └── GENE_SIGNATURE        — Multi-gene expression panels
│
└── Context
    ├── ORGANIZATION          — Companies, agencies, institutions
    ├── PUBLICATION           — Papers, patents, regulatory documents
    └── CELL_OR_TISSUE        — Cell types, tissues, organs (Cell Ontology, Uberon)
```

### Relation Categories

| Category | Relations | Count |
|---|---|---|
| Drug-Target Pharmacology | TARGETS, INHIBITS, ACTIVATES, BINDS_TO, HAS_MECHANISM | 5 |
| Drug-Disease | INDICATED_FOR, CONTRAINDICATED_FOR | 2 |
| Drug-Clinical | EVALUATED_IN, CAUSES | 2 |
| Drug-Drug | DERIVED_FROM, COMBINED_WITH, INTERACTS_WITH | 3 |
| Molecular Biology | ENCODES, PARTICIPATES_IN, IMPLICATED_IN, CONFERS_RESISTANCE_TO | 4 |
| Biomarker | PREDICTS_RESPONSE_TO, DIAGNOSTIC_FOR | 2 |
| Molecular Biology (extended) | EXPRESSED_IN, LOCALIZED_TO, HAS_VARIANT, HAS_DOMAIN, METABOLIZED_BY, PRODUCES_METABOLITE, SUBSTRATE_OF, PHOSPHORYLATES, FORMS_COMPLEX_WITH, REGULATES_EXPRESSION | 10 |
| Statistical Genetics | GENETICALLY_ASSOCIATED_WITH, MODULATES_EXPRESSION_OF, MODULATES_PROTEIN_LEVEL_OF, CAUSAL_FOR | 4 |
| Proteomics | SUBUNIT_OF, CLEAVES, UBIQUITINATES, DEGRADES | 4 |
| Genomics | MEMBER_OF, CLASSIFIES, ENRICHED_IN | 3 |
| Molecular Identifiers | HAS_STRUCTURE, HAS_SEQUENCE, SEQUENCE_SIMILARITY_TO, TARGETS_SEQUENCE | 4 |
| Organizational | DEVELOPED_BY, PUBLISHED_IN, GRANTS_APPROVAL_FOR | 3 |
| Fallback | ASSOCIATED_WITH | 1 |

---

## Biomedical Ontologies & Standards

### Chemical & Drug

| Resource | URL | Use in Epistract |
|---|---|---|
| ChEBI | https://www.ebi.ac.uk/chebi/ | Chemical entity classification, roles |
| DrugBank | https://go.drugbank.com/ | Drug-target interactions, drug properties |
| ChEMBL | https://www.ebi.ac.uk/chembl/ | Bioactivity data, compound lookup |
| PubChem | https://pubchem.ncbi.nlm.nih.gov/ | Structure search, compound properties |
| UNII (FDA) | https://precision.fda.gov/unii | Regulatory substance identification |
| ATC (WHO) | https://www.whocc.no/atc/ | Therapeutic classification |
| RxNorm | https://www.nlm.nih.gov/research/umls/rxnorm/ | Normalized drug names |
| CAS Registry | https://www.cas.org/ | Chemical abstracts identifiers |

### Gene & Protein

| Resource | URL | Use in Epistract |
|---|---|---|
| HGNC | https://www.genenames.org/ | **Canonical gene symbols** |
| NCBI Gene | https://www.ncbi.nlm.nih.gov/gene/ | Gene identifiers, annotations |
| Ensembl | https://www.ensembl.org/ | Genome browser, gene models |
| UniProtKB | https://www.uniprot.org/ | **Canonical protein reference** |
| PDB | https://www.rcsb.org/ | Protein 3D structures |
| InterPro | https://www.ebi.ac.uk/interpro/ | Protein domains, families |
| Pfam | https://www.ebi.ac.uk/interpro/entry/pfam/ | Protein family HMMs |
| SMART | https://smart.embl.de/ | Domain architecture |
| PROSITE | https://prosite.expasy.org/ | Protein motifs, patterns |
| Protein Ontology (PRO) | https://proconsortium.org/ | Protein forms, modifications |
| Complex Portal | https://www.ebi.ac.uk/complexportal/ | Curated protein complexes |

### Gene Ontology Ecosystem

| Resource | URL | Ontology ID | Use in Epistract |
|---|---|---|---|
| Gene Ontology (GO) | http://geneontology.org/ | — | Three sub-ontologies below |
| GO Molecular Function | — | GO:MF | Protein function annotations |
| GO Biological Process | — | GO:BP | PATHWAY entities, cellular processes |
| GO Cellular Component | — | GO:CC | CELL_OR_TISSUE subcellular locations |
| Relation Ontology (RO) | https://oborel.github.io/ | RO: | Standard relation predicates |
| Sequence Ontology (SO) | http://www.sequenceontology.org/ | SO: | Variant type classification |

### Disease & Phenotype

| Resource | URL | Use in Epistract |
|---|---|---|
| MeSH | https://meshb.nlm.nih.gov/ | **Primary disease naming standard** |
| Disease Ontology | https://disease-ontology.org/ | Disease classification hierarchy |
| ICD-11 (WHO) | https://icd.who.int/ | International disease classification |
| OMIM | https://www.omim.org/ | Genetic disorders |
| Orphanet | https://www.orpha.net/ | Rare diseases |
| HPO | https://hpo.jax.org/ | Clinical phenotype terms |
| EFO | https://www.ebi.ac.uk/efo/ | Experimental Factor Ontology (GWAS traits) |

### Clinical & Safety

| Resource | URL | Use in Epistract |
|---|---|---|
| MedDRA | https://www.meddra.org/ | **Adverse event terminology** |
| CTCAE (NCI) | https://ctep.cancer.gov/protocoldevelopment/electronic_applications/ctc.htm | AE severity grading |
| BEST Framework | https://www.ncbi.nlm.nih.gov/books/NBK326791/ | Biomarker classification |
| ClinicalTrials.gov | https://clinicaltrials.gov/ | Trial registration, schema |
| CDISC | https://www.cdisc.org/ | Clinical data interchange standards |
| FDA Orange Book | https://www.fda.gov/drugs/drug-approvals-and-databases/approved-drug-products-therapeutic-equivalence-evaluations-orange-book | Drug approval data |

### Variant Databases

| Resource | URL | Use in Epistract |
|---|---|---|
| ClinVar | https://www.ncbi.nlm.nih.gov/clinvar/ | Clinical variant significance |
| dbSNP | https://www.ncbi.nlm.nih.gov/snp/ | SNP identifiers (rs numbers) |
| COSMIC | https://cancer.sanger.ac.uk/cosmic | Somatic mutations in cancer |
| gnomAD | https://gnomad.broadinstitute.org/ | Population allele frequencies |
| HGVS Nomenclature | https://varnomen.hgvs.org/ | **Variant naming standard** |

### Pathway & Process

| Resource | URL | Use in Epistract |
|---|---|---|
| KEGG | https://www.genome.jp/kegg/ | Metabolic/signaling pathways |
| Reactome | https://reactome.org/ | Curated pathway models |
| WikiPathways | https://www.wikipathways.org/ | Community pathways |
| MSigDB | https://www.gsea-msigdb.org/gsea/msigdb/ | Gene set collections |

### Anatomical & Cell

| Resource | URL | Use in Epistract |
|---|---|---|
| Cell Ontology (CL) | http://obofoundry.org/ontology/cl.html | Cell type terms |
| Uberon | http://obofoundry.org/ontology/uberon.html | Anatomy terms |
| BRENDA Tissue Ontology | https://www.brenda-enzymes.org/ontology.php | Enzyme tissue sources |

### Knowledge Graph Standards

| Resource | URL | Use in Epistract |
|---|---|---|
| Biolink Model | https://biolink.github.io/biolink-model/ | **Entity/relation alignment standard** |
| OBO Foundry | http://obofoundry.org/ | Ontology governance, standards |
| Relation Ontology (RO) | https://oborel.github.io/ | Relation type grounding |
| NCATS Translator | https://ncats.nih.gov/translator | Biomedical KG consortium |

### Reference Knowledge Graphs

| Resource | URL | Relevance |
|---|---|---|
| Hetionet | https://het.io/ | Integrative biomedical KG (47K nodes, 2.25M edges) |
| OpenTargets | https://www.opentargets.org/ | Target-disease evidence scoring |
| SPOKE | https://spoke.ucsf.edu/ | Precision medicine KG |
| Monarch Initiative | https://monarchinitiative.org/ | Disease-gene association KG |
| Drug Repurposing Hub | https://clue.io/repurposing | Drug-target-indication mappings |

---

## sift-kg Integration

### Python API (what Epistract uses)

```python
from sift_kg import (
    load_domain,        # Load domain YAML
    run_build,          # Build graph from extraction JSONs
    run_resolve,        # Find duplicate entities
    run_apply_merges,   # Apply merge decisions
    run_narrate,        # Generate narrative
    run_export,         # Export to formats
    run_view,           # Open interactive viewer
    KnowledgeGraph,     # Graph class for direct manipulation
)
from sift_kg.domains.models import DomainConfig
from sift_kg.extract.models import DocumentExtraction, ExtractedEntity, ExtractedRelation
from sift_kg.graph.knowledge_graph import KnowledgeGraph
from sift_kg.ingest.reader import discover_documents, read_document
from sift_kg.ingest.chunker import chunk_text
```

### DocumentExtraction Format

This is the interchange format between Epistract (extraction) and sift-kg (graph building).

```python
class ExtractedEntity(BaseModel):
    name: str                    # Entity name (INN, HGNC symbol, etc.)
    entity_type: str             # One of 23 types
    attributes: dict = {}        # Type-specific attributes
    confidence: float = 0.5      # 0.0-1.0
    context: str = ""            # Quote from source text

class ExtractedRelation(BaseModel):
    relation_type: str           # One of 46 types
    source_entity: str           # Entity name (not ID)
    target_entity: str           # Entity name (not ID)
    confidence: float = 0.5      # 0.0-1.0
    evidence: str = ""           # Quote from source text

class DocumentExtraction(BaseModel):
    document_id: str
    document_path: str = ""
    chunks_processed: int = 0
    entities: list[ExtractedEntity] = []
    relations: list[ExtractedRelation] = []
    error: str | None = None
    cost_usd: float = 0.0
    model_used: str = ""
    domain_name: str = ""
    chunk_size: int = 0
    extracted_at: str = ""
```

### Key sift-kg Modules

| Module | Purpose | Epistract Uses |
|---|---|---|
| `ingest/reader.py` | Document reading (Kreuzberg/pdfplumber) | `discover_documents()`, `read_document()` |
| `ingest/chunker.py` | Text chunking with overlap | `chunk_text()` |
| `graph/builder.py` | Graph construction from extractions | `build_graph()` via `run_build()` |
| `graph/prededup.py` | Deterministic pre-deduplication (SemHash) | Called by builder automatically |
| `graph/postprocessor.py` | Edge cleanup, passive voice, direction fix | Called by builder automatically |
| `graph/communities.py` | Louvain community detection | Called by builder automatically |
| `graph/knowledge_graph.py` | NetworkX MultiDiGraph wrapper | `KnowledgeGraph` class |
| `resolve/resolver.py` | LLM-based entity resolution | `run_resolve()` |
| `export.py` | Multi-format export | `run_export()` |
| `visualize.py` | Interactive HTML viewer | `run_view()` |
| `domains/loader.py` | Domain YAML loading | `load_domain()` |

---

## Claude-as-Extractor Adapter

### How Claude Replaces LiteLLM for Extraction

In standard sift-kg, extraction works like this:

```
chunk text → build_combined_prompt() → LiteLLM.acall_json() → parse JSON → ExtractedEntity/Relation
```

In Epistract, Claude IS the LLM:

```
chunk text → Claude reads chunk (guided by drug-discovery-extraction skill) → Claude writes JSON → ExtractedEntity/Relation
```

The skill file contains the full domain schema and extraction prompt template. When Claude processes a chunk, it outputs JSON matching `DocumentExtraction` format. The `scripts/build_extractions.py` helper writes this to disk in the location sift-kg expects.

### Why This Works Better

1. **Claude understands biochemistry deeply** — it knows HGVS notation, signaling cascades, patent claim structure
2. **No JSON parse failures** — Claude produces well-formed JSON natively (no markdown fence wrapping, no truncation)
3. **No API cost for extraction** — the LLM calls are part of the Claude Code session
4. **Context-aware** — Claude can reference earlier chunks in the same document
5. **Interactive** — Claude can ask the user for clarification on ambiguous entities

---

## Molecular Validation Pipeline

### Components

| Script | Location | Dependencies | Purpose |
|---|---|---|---|
| `scan_patterns.py` | `skills/drug-discovery-extraction/validation-scripts/` | None (stdlib re) | Regex pattern scanning for SMILES, sequences, identifiers |
| `validate_smiles.py` | Same | rdkit-pypi (optional) | SMILES validation, canonicalization, property computation |
| `validate_sequences.py` | Same | biopython (optional) | DNA/RNA/protein sequence validation and analysis |
| `validate_molecules.py` | `scripts/` | Both optional | Orchestrator: scan → validate → enrich extraction JSONs |

### Regex Patterns

```python
SMILES_STRICT   = r'(?<!\w)(?:[A-IK-Z][a-z]?(?:[\(\)\[\]=#@+\-\\\/\.:0-9]|[A-IK-Z][a-z]?){3,})(?!\w)'
INCHI_PATTERN   = r'InChI=1S?/[A-Za-z0-9\.\+\-\(\)/,;?]+'
INCHIKEY_PATTERN = r'[A-Z]{14}-[A-Z]{10}-[A-Z]'
CAS_PATTERN     = r'\b\d{2,7}-\d{2}-\d\b'
DNA_PATTERN     = r'(?<![A-Z])[ATGC]{10,}(?![A-Z])'
RNA_PATTERN     = r'(?<![A-Z])[AUGC]{10,}(?![A-Z])'
AA_1LETTER      = r'(?<![A-Z])[ARNDCEQGHILKMFPSTWYV]{8,}(?![A-Z])'
SEQ_ID_PATTERN  = r'SEQ\s*ID\s*NO:?\s*\d+'
NCT_PATTERN     = r'NCT\d{8}'
US_PATENT       = r'US\s*\d{1,3},?\d{3},?\d{3}\s*[AB]\d?'
PCT_PATENT      = r'WO\s*\d{4}/\d{5,6}'
```

### RDKit Validation Output

For each valid SMILES, RDKit computes:

| Property | Description | Drug-Likeness Relevance |
|---|---|---|
| canonical_smiles | Unique canonical form | Deduplication |
| inchi | InChI identifier | Cross-database lookup |
| inchikey | 27-char hash | PubChem/ChEBI key |
| molecular_formula | e.g., C9H8O4 | Verification |
| molecular_weight | Daltons | Lipinski Ro5: MW < 500 |
| logp | Octanol-water partition | Lipinski Ro5: LogP < 5 |
| hbd | H-bond donors | Lipinski Ro5: HBD ≤ 5 |
| hba | H-bond acceptors | Lipinski Ro5: HBA ≤ 10 |
| tpsa | Topological polar surface area | Oral absorption: TPSA < 140 |
| num_rings | Ring count | Drug-likeness indicator |

### Biopython Validation Output

For nucleotide sequences: length, GC content, complement, reverse complement, translation (if divisible by 3).

For protein sequences: length, molecular weight, isoelectric point, aromaticity, instability index, GRAVY (hydrophobicity).

---

## Plugin Component Reference

### Commands

| Command | Script/Logic | sift-kg API Used |
|---|---|---|
| `/epistract-setup` | `scripts/setup.sh` | Installs sift-kg |
| `/epistract-ingest` | Orchestrates full pipeline | `read_document()`, `chunk_text()`, `run_build()`, `run_view()` |
| `/epistract-validate` | `scripts/validate_molecules.py` | — |
| `/epistract-build` | `scripts/run_sift.py` | `run_build()` |
| `/epistract-view` | `scripts/run_sift.py` | `run_view()` |
| `/epistract-query` | `scripts/run_sift.py` | `KnowledgeGraph.load()`, search |
| `/epistract-export` | `scripts/run_sift.py` | `run_export()` |

### Agents

| Agent | Triggered By | Purpose |
|---|---|---|
| `extractor` | `/epistract-ingest` with multiple documents | Parallel per-document extraction |
| `validator` | `/epistract-ingest --validate` | Background molecular validation |

### Skills

| Skill | Triggers On | Content |
|---|---|---|
| `drug-discovery-extraction` | Any drug discovery extraction task | Full 23-type entity schema, 46-type relation schema, extraction prompts, disambiguation rules, confidence calibration |

---

## Data Formats

### Output Directory Structure

```
epistract-output/
├── extractions/                # Per-document extraction JSON
│   ├── paper_001.json
│   └── paper_002.json
├── discovered_domain.yaml      # Domain used (or auto-discovered)
├── graph_data.json             # Knowledge graph (sift-kg native)
├── communities.json            # Louvain community assignments
├── entity_descriptions.json    # Per-entity descriptions
├── merge_proposals.yaml        # Entity resolution proposals
├── relation_review.yaml        # Flagged relations
├── narrative.md                # Prose summary (optional)
├── graph.html                  # Interactive visualization
├── validation/                 # Molecular validation results
│   ├── smiles_validated.json
│   └── sequences_validated.json
└── exports/                    # Export outputs
    ├── graph.graphml
    ├── graph.gexf
    ├── graph.sqlite
    └── csv/
        ├── entities.csv
        └── relations.csv
```

### graph_data.json Schema

```json
{
  "metadata": {
    "created_at": "ISO-8601",
    "entity_count": 267,
    "relation_count": 489,
    "entity_type_summary": {"COMPOUND": 34, "PROTEIN": 45, ...},
    "sift_kg_version": "0.9.0"
  },
  "nodes": [
    {
      "id": "compound:sotorasib",
      "entity_type": "COMPOUND",
      "name": "sotorasib",
      "confidence": 0.95,
      "source_documents": ["paper_001", "paper_003"],
      "attributes": {"modality": "small molecule", "development_stage": "approved"}
    }
  ],
  "links": [
    {
      "source": "compound:sotorasib",
      "target": "gene:kras_g12c",
      "relation_type": "INHIBITS",
      "confidence": 0.98,
      "evidence": "Sotorasib irreversibly inhibits KRAS G12C...",
      "source_document": "paper_001",
      "support_count": 3,
      "support_documents": ["paper_001", "paper_003", "paper_007"]
    }
  ]
}
```

---

## Testing & Validation

### Schema Coverage Test

Extract from 5-10 representative PubMed abstracts. Verify ≥90% of scientifically meaningful entities map to defined types.

### Extraction Precision Test

Review extracted relations. Target ≥85% precision for confidence > 0.8.

### Molecular Validation Test

- 10 known SMILES → RDKit: all must validate and canonicalize
- 10 known sequences → Biopython: all must validate with correct type detection
- 5 invalid SMILES → must be flagged as invalid

### sift-kg Compatibility Test

Epistract-generated extraction JSONs must load via `DocumentExtraction(**json.loads(text))` and build via `run_build()` without errors.

### Round-Trip Test

Ingest → Extract → Build → Export (SQLite) → verify entity/relation counts match.

---

## Phase 2: Neo4j & Vector RAG

### Neo4j Exporter (planned)

New export format for sift-kg that pushes the knowledge graph into Neo4j:

```python
# sift_kg/export.py addition
def _export_neo4j(kg: KnowledgeGraph, neo4j_uri: str, auth: tuple):
    """Export knowledge graph to Neo4j using MERGE for idempotency."""
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(neo4j_uri, auth=auth)

    # Create constraints for entity IDs
    # MERGE nodes with properties
    # MERGE relationships with properties
    # Create vector index for entity embeddings
```

### Vector Embeddings (planned)

Embed entity descriptions and evidence text for semantic retrieval:

```python
# Using Neo4j's built-in vector index
# or sentence-transformers for local embedding generation
# Store embeddings as node properties in Neo4j
```

### Combined Graph+Vector RAG Query (planned)

```
User: "What compounds target KRAS G12C and what are their clinical results?"

1. Vector search: find entities semantically similar to query
2. Graph traversal: expand neighborhood of matched entities
3. Combine: ranked subgraph with evidence passages
4. Generate: Claude synthesizes answer from subgraph context
```

---

## Plugin Development Workflow

### Local Plugin Install & Update Cycle

Epistract is a Claude Code plugin. When you modify plugin files (agents, commands, skills, scripts), the cached copy must be refreshed. The plugin system caches by **name + version** — changing files without bumping the version won't trigger a refresh.

**Update workflow:**

1. Make your changes to the repo
2. Bump version in `.claude-plugin/plugin.json` (e.g., `1.1.0` → `1.2.0`)
3. Commit and push
4. In Claude Code:
   ```
   /plugin          → select epistract → Uninstall
   /reload-plugins
   /plugin marketplace add /path/to/epistract
   /plugin install epistract@epistract
   /reload-plugins
   ```
5. Verify: `/plugin` should show the new version

**Key gotchas:**
- You must run `/reload-plugins` **both** after uninstall and after install
- Local plugins show "Local plugins cannot be updated remotely" — this is expected; uninstall/reinstall is the update path
- The cache lives at `~/.claude/plugins/cache/epistract/epistract/<version>/`
- If the cache is stale, you can nuke it: `rm -rf ~/.claude/plugins/cache/epistract/` then reinstall
- After reinstall, restart Claude Code (or `/reload-plugins`) for agents and skills to load

### Field Naming: entity_type vs type

sift-kg's Pydantic models require `entity_type` on entities and `relation_type` on relations. LLM agents naturally gravitate toward `type` as a field name. Two defenses:

1. **Agent prompts must include explicit JSON examples** with the exact field names (see `agents/extractor.md`)
2. **`build_extraction.py` normalizes defensively** — `_normalize_fields()` converts `type` → `entity_type`/`relation_type` at write time

If you create new agent prompts that produce extraction JSON, always include a concrete JSON example showing `entity_type` and `relation_type`.

### Community Labeling

sift-kg's Louvain community detection produces numbered labels (`Community 1`, `Community 2`). The `label_communities.py` script auto-generates descriptive labels based on member entity composition. It runs automatically after `run_sift.py build`.

The labeling heuristic priority:
1. Gene-dominant clusters (>50% genes, >15 members) → "Disease Risk Loci (N genes)"
2. Variant-dominant clusters (>50% variants) → "GENE Genetic Variants"
3. Mechanism + cell type → "Mechanism in Cell Type"
4. Pathway-driven → "Pathway A / Pathway B"
5. Disease + protein → "Disease — Protein1, Protein2"
6. Fallback → top 3 entities by priority

### Running Test Scenarios

Each scenario in `tests/scenarios/` is self-contained. After running:

1. Capture a screenshot: use Playwright (`python3 -c "from playwright.sync_api import ..."`) to screenshot `output/graph.html`
2. Save screenshot to `tests/scenarios/screenshots/scenario-NN-graph.png`
3. Update the scenario markdown with results, community analysis, UAT pass/fail
4. Commit output files (`tests/corpora/*/output/` is allowed by `.gitignore`)

**Fully automated runs** (no permission prompts):
```bash
claude --dangerously-skip-permissions
```

Or pre-approve in `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": ["Bash(python3 *)", "Bash(echo *)", "Read(*)", "Write(*/output/*)"]
  }
}
```

### Scripts Reference

| Script | Purpose | Called By |
|---|---|---|
| `scripts/setup.sh` | Install sift-kg, check RDKit/Biopython | `/epistract-setup` command |
| `scripts/build_extraction.py` | Write Claude's extraction JSON in sift-kg format (with field normalization) | Extractor agents via stdin pipe |
| `scripts/run_sift.py` | sift-kg Python API wrapper (build, view, export, search, info) | All commands |
| `scripts/label_communities.py` | Auto-label communities with descriptive names | Called by `run_sift.py build` |
| `scripts/validate_molecules.py` | Scan extractions for SMILES/sequences, validate with RDKit/Biopython | `/epistract-validate` and ingest pipeline |

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code patterns (sift-kg conventions)
4. Bump the plugin version in `.claude-plugin/plugin.json` for any user-facing changes
5. Run the test suite
6. Submit a pull request with a clear description

## License

MIT
