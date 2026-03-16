# Epistract — Claude Code Plugin Design Specification

**Status:** DRAFT — awaiting review
**Date:** 2026-03-16

---

## 1. What Is Epistract

Epistract is a Claude Code plugin that turns scientific documents into production-grade biomedical knowledge graphs. It wraps sift-kg as its core engine while using Claude itself as the extraction LLM — delivering expert-level entity and relation extraction from drug discovery literature, patent filings, and clinical trial reports.

**The name:** From Greek *episteme* (ἐπιστήμη) — structured scientific knowledge, the highest form of knowledge in Aristotle's taxonomy — combined with *extract*. Epistract extracts scientific knowledge.

**The pitch:** Drop PubMed papers, bioRxiv preprints, or patent PDFs into a folder. Epistract reads them with a scientist's understanding, extracts compounds, targets, diseases, mechanisms, trials, and their relationships into a structured knowledge graph, validates molecular identifiers with RDKit and Biopython, and gives you an interactive visualization you can explore in your browser — all from a single Claude Code command.

---

## 2. Phased Delivery

### Phase 1 — Extraction + KG + Visualization (this spec)
- Claude Code plugin with commands and skills
- Claude-as-extractor: Claude reads documents and produces extraction JSON
- sift-kg engine: graph building, deduplication, entity resolution, community detection
- Drug discovery domain schema (from the 2000-line domain spec)
- Molecular validation via RDKit/Biopython (inline Python execution)
- Visualization via sift-kg's interactive HTML viewer
- Export to all sift-kg native formats (JSON, GraphML, GEXF, CSV, SQLite)

### Phase 2 — Neo4j + Vector RAG (future)
- Neo4j exporter: push KG into Neo4j with Cypher MERGE
- Vector embeddings: embed entity descriptions + evidence for semantic retrieval
- Neo4j vector index: store embeddings inside Neo4j for combined graph+vector queries
- RAG query layer: Cypher + vector similarity for grounded retrieval
- Production query commands: `/epistract ask "What targets KRAS G12C?"`

### Future Phases (out of scope)
- Multi-corpus incremental ingestion
- Automated PubMed/bioRxiv fetching
- Cross-reference resolution against ChEMBL/DrugBank/UniProt APIs
- Web UI dashboard
- Multi-user collaboration

---

## 3. Architecture

### Data Flow

```
User: "/epistract ingest ./papers/"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Document Ingestion (sift-kg ingest module)    │
│  • Kreuzberg reads 75+ formats (PDF, DOCX, HTML, etc.) │
│  • OCR for scanned documents (Tesseract/EasyOCR)        │
│  • Text chunking (10K chars/chunk)                       │
│  • Pattern scanner: regex detects SMILES, sequences,     │
│    CAS numbers, NCT IDs in raw text                      │
└────────────────────┬────────────────────────────────────┘
                     │ chunks + detected patterns
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2: Entity Extraction (Claude-as-extractor)       │
│  • Claude reads each chunk with drug discovery skill    │
│  • Extracts entities using 23-type schema               │
│  • Extracts relations using 46-type schema              │
│  • Outputs DocumentExtraction JSON (sift-kg format)     │
│  • Parallel: dispatches extraction agents per document   │
└────────────────────┬────────────────────────────────────┘
                     │ extraction JSONs
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 3: Molecular Validation (inline Python)          │
│  • RDKit validates/canonicalizes SMILES, computes props  │
│  • Biopython validates sequences, computes GC/MW         │
│  • Regex-extracted identifiers matched to LLM entities   │
│  • Creates CHEMICAL_STRUCTURE, SEQUENCE entities         │
└────────────────────┬────────────────────────────────────┘
                     │ validated extraction JSONs
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 4: Graph Building (sift-kg graph module)         │
│  • Pre-dedup: SemHash, Unicode normalization, titles     │
│  • Build NetworkX MultiDiGraph                           │
│  • Canonical relation merging (product-complement conf.) │
│  • Post-processing: passive voice fix, redundant edges   │
│  • Community detection (Louvain)                         │
│  • Flag low-confidence relations for review              │
└────────────────────┬────────────────────────────────────┘
                     │ graph_data.json
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 5: Output                                         │
│  • Interactive HTML viewer (sift-kg visualize)           │
│  • Export: JSON, GraphML, GEXF, CSV, SQLite              │
│  • Entity descriptions + narrative (optional)            │
│  • Search: entity lookup from terminal                   │
│  • Topology: structural overview for agents              │
└─────────────────────────────────────────────────────────┘
```

### Claude-as-Extractor Adapter

The key architectural innovation. Instead of calling LiteLLM, Claude itself reads each text chunk and produces the extraction JSON.

**How it works:**

1. sift-kg's `ingest/reader.py` reads and chunks documents (unchanged)
2. The epistract skill instructs Claude on the drug discovery schema
3. Claude reads each chunk and writes a JSON extraction to `output/extractions/{doc_id}.json`
4. The JSON matches sift-kg's `DocumentExtraction` Pydantic model exactly
5. sift-kg's `graph/builder.py` consumes these JSONs (unchanged)

**The extraction JSON format** (sift-kg native — we match it exactly):

```json
{
  "document_id": "paper_001",
  "document_path": "./papers/paper_001.pdf",
  "chunks_processed": 3,
  "entities": [
    {
      "name": "sotorasib",
      "entity_type": "COMPOUND",
      "attributes": {"modality": "small molecule", "development_stage": "approved"},
      "confidence": 0.95,
      "context": "Sotorasib (AMG 510) is a first-in-class KRAS G12C inhibitor..."
    }
  ],
  "relations": [
    {
      "relation_type": "INHIBITS",
      "source_entity": "sotorasib",
      "target_entity": "KRAS G12C",
      "confidence": 0.98,
      "evidence": "Sotorasib irreversibly inhibits KRAS G12C by..."
    }
  ],
  "model_used": "claude-opus-4-6",
  "domain_name": "Drug Discovery",
  "chunk_size": 10000,
  "cost_usd": 0.0
}
```

**Why this works:** sift-kg's `DocumentExtraction` model is a simple Pydantic class with `entities: list[ExtractedEntity]` and `relations: list[ExtractedRelation]`. Everything downstream — graph builder, resolver, exporter, viewer — consumes this format. We produce it directly.

---

## 4. Plugin Structure

```
epistract/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest
│
├── commands/
│   ├── ingest.md                      # /epistract-ingest — full pipeline
│   ├── validate.md                    # /epistract-validate — molecular validation
│   ├── build.md                       # /epistract-build — graph from extractions
│   ├── view.md                        # /epistract-view — open interactive viewer
│   ├── query.md                       # /epistract-query — search entities
│   ├── export.md                      # /epistract-export — export to formats
│   └── setup.md                       # /epistract-setup — install dependencies
│
├── skills/
│   └── drug-discovery-extraction/
│       ├── SKILL.md                   # Core extraction skill
│       ├── domain.yaml                # Drug discovery domain schema
│       ├── extraction-template.md     # Extraction prompt template
│       ├── validation-scripts/
│       │   ├── validate_smiles.py     # RDKit SMILES validator
│       │   ├── validate_sequences.py  # Biopython sequence validator
│       │   └── scan_patterns.py       # Regex pattern scanner
│       └── references/
│           ├── entity-types.md        # Entity type reference card
│           ├── relation-types.md      # Relation type reference card
│           └── ontology-map.md        # Ontology cross-reference
│
├── agents/
│   ├── extractor.md                   # Parallel document extraction agent
│   └── validator.md                   # Molecular validation agent
│
├── scripts/
│   ├── setup.sh                       # Install sift-kg + optional deps
│   ├── ingest.py                      # Orchestration: read docs → chunks
│   ├── build_extractions.py           # Write Claude extraction to sift-kg format
│   ├── validate_molecules.py          # Run RDKit/Biopython validation
│   └── run_sift.py                    # Call sift-kg Python API
│
├── README.md                          # For scientists and researchers
├── DEVELOPER.md                       # Technical reference for developers
└── LICENSE
```

### plugin.json

```json
{
  "name": "epistract",
  "version": "1.1.0",
  "description": "Expert drug discovery knowledge graph extraction from scientific literature",
  "author": {
    "name": "Umesh Bhatt"
  },
  "keywords": [
    "drug-discovery",
    "knowledge-graph",
    "biomedical",
    "pharma",
    "entity-extraction",
    "sift-kg"
  ]
}
```

---

## 5. Commands

### /epistract-setup

Installs sift-kg and optional molecular validation dependencies.

```
Checks: Python 3.11+, uv/pip available
Installs: sift-kg, rdkit-pypi (optional), biopython (optional)
Creates: .env with API key placeholders, sift.yaml with drug-discovery domain
Validates: imports work, domain loads
```

### /epistract-ingest

The main command. Full pipeline: ingest → extract → validate → build → visualize.

```
Arguments:
  path       — directory or file to ingest (required)
  --domain   — domain override (default: drug-discovery)
  --validate — enable molecular validation (default: true if rdkit installed)
  --view     — open viewer after build (default: true)
  --output   — output directory (default: ./epistract-output)
```

**Workflow when invoked:**
1. Claude runs `sift-kg ingest` to read and chunk documents
2. Claude reads each chunk using the drug-discovery-extraction skill
3. Claude writes extraction JSON per document
4. If --validate: runs molecular validation scripts
5. Runs `sift build` via Python API
6. Runs `sift view` to open interactive graph

### /epistract-validate

Run molecular validation on existing extractions.

```
Scans extraction JSONs for SMILES, sequences, CAS numbers
Validates using RDKit/Biopython
Reports: valid, invalid, enriched count
Updates extraction JSONs with validated attributes
```

### /epistract-build

Build graph from existing extractions (skip extraction step).

```
Runs sift-kg build → resolve → apply-merges pipeline
Detects communities
Outputs graph_data.json
```

### /epistract-view

Open interactive graph visualization.

```
Arguments: same filter flags as sift view
  --neighborhood, --top, --community, --source-doc, --min-confidence
```

### /epistract-query

Search the knowledge graph from the terminal.

```
Arguments:
  query      — search term
  --type     — filter by entity type (COMPOUND, GENE, PROTEIN, etc.)
  --relations — show relations
  --json     — output as JSON (for agent consumption)
```

### /epistract-export

Export to external formats.

```
Arguments:
  format     — json | graphml | gexf | csv | sqlite
  --output   — output path
```

---

## 6. Skills

### drug-discovery-extraction (Core Skill)

**SKILL.md** — loaded into Claude's context when the plugin activates. This is the brain of the system. It teaches Claude:

1. **The 23 entity types** with naming conventions, disambiguation rules, and extraction hints
2. **The 46 relation types** with source/target constraints and confidence calibration
3. **The extraction output format** — exact JSON schema matching sift-kg's `DocumentExtraction`
4. **Document type awareness** — different strategies for research articles, reviews, patents, regulatory docs
5. **Molecular identifier detection** — when Claude sees SMILES/sequences, it flags them for validation
6. **Confidence scoring** — calibrated for scientific literature

**Key design decision:** The skill file will be large (~800-1000 lines) because it contains the full domain schema. This is acceptable because:
- It only loads when the plugin is active
- The domain knowledge is essential for extraction quality
- It replaces what would otherwise be dozens of LLM API calls for schema discovery

**The skill will include the extraction prompt template:**

```markdown
Extract entities and relations from the following text chunk.
Use the drug discovery domain schema defined in this skill.

Output ONLY valid JSON matching this exact format:
{
  "entities": [...],
  "relations": [...]
}

TEXT CHUNK (from document: {doc_id}, chunk {chunk_index} of {total_chunks}):
{chunk_text}

DOCUMENT CONTEXT:
{doc_summary}
```

---

## 7. Agents

### extractor (Parallel Document Extraction)

When ingesting multiple documents, Claude dispatches extraction agents that each process one document independently. This uses Claude Code's `Agent` tool with `subagent_type: "general-purpose"`.

```markdown
---
description: Extract biomedical entities and relations from a single document
---

You are processing a single document for the epistract drug discovery
knowledge graph. Read the document text, apply the drug discovery schema,
and write the extraction JSON to the output directory.

Your output must match sift-kg's DocumentExtraction format exactly.
```

**Parallelism:** For a folder of 10 papers, Claude dispatches 10 extraction agents that run concurrently. Each writes its own `{doc_id}.json`. Then the main flow calls `sift build`.

### validator (Molecular Validation)

Runs molecular validation as a background agent.

```markdown
---
description: Validate molecular identifiers (SMILES, sequences) in extraction results
---

Scan extraction JSONs for molecular identifiers.
Run validation scripts (RDKit for chemistry, Biopython for sequences).
Update extraction files with validated attributes.
```

---

## 8. Scripts

### setup.sh

```bash
#!/bin/bash
# Install epistract dependencies
cd "$CLAUDE_PLUGIN_ROOT"

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 11)" || {
  echo "Python 3.11+ required"; exit 1
}

# Install sift-kg
uv pip install sift-kg 2>/dev/null || pip install sift-kg

# Optional: molecular validation
echo "Install molecular validation? (RDKit ~50MB, Biopython ~20MB)"
read -p "[y/N] " answer
if [[ "$answer" =~ ^[Yy] ]]; then
  uv pip install rdkit-pypi biopython 2>/dev/null || pip install rdkit-pypi biopython
fi
```

### build_extractions.py

Converts Claude's extraction output into sift-kg's `DocumentExtraction` format and writes to disk.

```python
"""Write Claude's extraction output to sift-kg format."""
import json
import sys
from pathlib import Path

def write_extraction(doc_id: str, entities: list, relations: list,
                     output_dir: Path, **metadata):
    """Write a single document's extraction in sift-kg format."""
    extraction = {
        "document_id": doc_id,
        "document_path": metadata.get("document_path", ""),
        "chunks_processed": metadata.get("chunks_processed", 1),
        "entities": entities,
        "relations": relations,
        "cost_usd": 0.0,  # Claude extraction = free
        "model_used": "claude-opus-4-6",
        "domain_name": "Drug Discovery",
        "chunk_size": metadata.get("chunk_size", 10000),
        "extracted_at": metadata.get("extracted_at", ""),
    }

    out_path = output_dir / "extractions" / f"{doc_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(extraction, indent=2))
    return out_path
```

### validate_molecules.py

```python
"""Molecular identifier validation using RDKit and Biopython."""
import json
import re
import sys
from pathlib import Path

# Regex patterns for molecular identifiers
SMILES_PATTERN = r'(?<!\w)(?:[A-IK-Z][a-z]?(?:[\(\)\[\]=#@+\-\\\/\.:0-9]|[A-IK-Z][a-z]?){3,})(?!\w)'
INCHIKEY_PATTERN = r'[A-Z]{14}-[A-Z]{10}-[A-Z]'
DNA_PATTERN = r'(?<![A-Z])[ATGC]{10,}(?![A-Z])'
AA_PATTERN = r'(?<![A-Z])[ARNDCEQGHILKMFPSTWYV]{8,}(?![A-Z])'

def validate_smiles(smiles: str) -> dict:
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, inchi
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"valid": False, "error": "Invalid SMILES"}
        return {
            "valid": True,
            "canonical_smiles": Chem.MolToSmiles(mol),
            "inchi": inchi.MolToInchi(mol),
            "inchikey": inchi.MolToInchiKey(mol),
            "molecular_formula": Chem.rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": round(Descriptors.ExactMolWt(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "hbd": Descriptors.NumHDonors(mol),
            "hba": Descriptors.NumHAcceptors(mol),
            "tpsa": round(Descriptors.TPSA(mol), 1),
            "num_rings": Chem.rdMolDescriptors.CalcNumRings(mol),
        }
    except ImportError:
        return {"valid": None, "error": "RDKit not installed"}

def validate_sequence(seq: str) -> dict:
    try:
        from Bio.Seq import Seq
        from Bio.SeqUtils import gc_fraction
        seq_upper = seq.upper().strip()
        if set(seq_upper) <= set("ATGCN"):
            bio_seq = Seq(seq_upper)
            return {
                "valid": True, "type": "DNA", "length": len(seq_upper),
                "gc_content": round(gc_fraction(bio_seq), 3),
            }
        elif set(seq_upper) <= set("AUGCN"):
            return {"valid": True, "type": "RNA", "length": len(seq_upper)}
        elif set(seq_upper) <= set("ACDEFGHIKLMNPQRSTVWYX*"):
            from Bio.SeqUtils.ProtParam import ProteinAnalysis
            analysis = ProteinAnalysis(seq_upper.replace("*", "").replace("X", "A"))
            return {
                "valid": True, "type": "protein", "length": len(seq_upper),
                "molecular_weight": round(analysis.molecular_weight(), 1),
                "isoelectric_point": round(analysis.isoelectric_point(), 2),
            }
        return {"valid": False, "error": "Unknown sequence type"}
    except ImportError:
        return {"valid": None, "error": "Biopython not installed"}

# CLI: python validate_molecules.py <extraction_dir>
if __name__ == "__main__":
    # Scan extraction JSONs, validate, enrich, report
    ...
```

### run_sift.py

Thin wrapper calling sift-kg's Python API.

```python
"""Call sift-kg Python API from epistract plugin."""
from pathlib import Path
from sift_kg import run_build, run_export, run_view, load_domain

def build_graph(output_dir: str, domain_path: str = None):
    output = Path(output_dir)
    domain = load_domain(domain_path=Path(domain_path)) if domain_path else load_domain(bundled_name="drug-discovery")
    kg = run_build(output, domain)
    print(f"Graph built: {kg.entity_count} entities, {kg.relation_count} relations")
    return kg

def view_graph(output_dir: str, **filters):
    run_view(Path(output_dir), **filters)

def export_graph(output_dir: str, fmt: str):
    run_export(Path(output_dir), fmt)
```

---

## 9. Workflow Example

A scientist has 15 papers on KRAS G12C inhibitors in `./kras_papers/`.

```
User: /epistract-ingest ./kras_papers/

Claude: Setting up epistract for drug discovery extraction.

  Scanning documents...
  Found 15 PDF files in ./kras_papers/

  Reading documents via sift-kg (Kreuzberg)...
  ✓ 15 documents read, 47 text chunks prepared

  Extracting entities and relations...
  [Claude dispatches 15 extraction agents in parallel]
  ✓ sotorasib: 23 entities, 18 relations
  ✓ adagrasib: 19 entities, 15 relations
  ✓ kras_biology_review: 45 entities, 38 relations
  ...
  ✓ 312 entities, 241 relations extracted across 15 documents

  Validating molecular identifiers...
  ✓ 8 SMILES strings found → 7 valid (1 invalid, skipped)
  ✓ 3 peptide sequences found → 3 valid
  ✓ 12 CAS numbers matched to compounds

  Building knowledge graph...
  ✓ Pre-dedup: 312 → 267 unique entities (45 merged)
  ✓ Graph: 267 entities, 489 relations, 6 communities
  ✓ 4 relations flagged for review (low confidence)

  Opening interactive viewer...
  ✓ Graph visualization at epistract-output/graph.html

  Summary:
  Entities: 267 (COMPOUND: 34, PROTEIN: 45, GENE: 28, DISEASE: 19, ...)
  Relations: 489 (INHIBITS: 67, TARGETS: 45, INDICATED_FOR: 23, ...)
  Output: ./epistract-output/
```

---

## 10. What Stays in sift-kg vs. What's in the Plugin

| Component | Location | Why |
|---|---|---|
| Document ingestion (Kreuzberg) | sift-kg | Battle-tested, 75+ formats |
| Text chunking | sift-kg | Works well as-is |
| LLM extraction (LiteLLM) | sift-kg (unused by plugin) | Plugin uses Claude instead |
| Drug discovery domain YAML | epistract plugin | Domain-specific, not general |
| Extraction prompt/skill | epistract plugin | Plugin-specific knowledge |
| Molecular validation | epistract plugin scripts | New capability |
| Graph builder | sift-kg | Core engine, no changes needed |
| Pre-dedup (SemHash) | sift-kg | Works well as-is |
| Entity resolution | sift-kg | Works well as-is |
| Community detection | sift-kg | Works well as-is |
| Post-processing | sift-kg | Works well as-is |
| Export (all formats) | sift-kg | Works well as-is |
| Interactive viewer | sift-kg | Works well as-is |
| Narrative generation | sift-kg (called by plugin) | Works well, used via API |
| Neo4j exporter | Phase 2 — sift-kg addition | New sift-kg export format |
| Vector embeddings | Phase 2 — sift-kg addition | New sift-kg capability |

**Principle:** sift-kg is the engine. Epistract is the expert driver.

---

## 11. Dependencies

### Required
- Python 3.11+
- sift-kg (pip install sift-kg)
- Claude Code (the runtime environment)

### Optional (for molecular validation)
- rdkit-pypi (~50MB) — SMILES validation, canonicalization, property computation
- biopython (~20MB) — sequence validation, analysis

### Bundled (no install needed)
- Drug discovery domain YAML
- Extraction prompt templates
- Validation scripts (Python)
- Pattern scanner (regex)

---

## 12. Success Criteria for Phase 1

1. **End-to-end pipeline works:** `/epistract-ingest ./papers/` produces a viewable knowledge graph
2. **Extraction quality:** ≥85% precision on entity extraction from PubMed abstracts
3. **Domain coverage:** All 23 entity types extractable from representative drug discovery literature
4. **Molecular validation:** SMILES validated by RDKit, sequences by Biopython, when those libraries are installed
5. **sift-kg compatibility:** Extraction JSONs consumed by sift-kg graph builder without modification
6. **Visualization works:** Interactive graph opens in browser with community regions, search, filtering
7. **Export works:** All sift-kg export formats (JSON, GraphML, GEXF, CSV, SQLite) produce valid output
