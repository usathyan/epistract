---
name: epistract-ingest
description: Ingest scientific documents and build a drug discovery knowledge graph
---

# Epistract Document Ingestion Pipeline

You are running the epistract drug discovery knowledge graph pipeline.

## Arguments
- `path` (required): Directory or file path containing documents
- `--output` (optional): Output directory (default: ./epistract-output)
- `--domain` (optional): Domain name for extraction (default: drug-discovery). Use 'contract' for event contract analysis.
- `--validate` (optional): Enable molecular validation (default: true if rdkit installed)
- `--view` (optional): Open viewer after build (default: true)

## Pipeline Steps

### Step 1: Discover and Read Documents

List all files in the provided path. Supported formats: PDF, DOCX, XLSX, PPTX, HTML, TXT, EPUB, and 75+ more via sift-kg's Kreuzberg engine.

For each document, read its text content using sift-kg:
```python
from sift_kg.ingest.reader import read_document
text = read_document(Path(doc_path))
```

Or via the command line: read each file and note its content.

### Step 2: Chunk Text

Split each document's text into ~10,000 character chunks with overlap. Use your judgment on natural break points (paragraph boundaries, section headers).

### Step 3: Extract Entities and Relations

For EACH text chunk, extract entities and relations using the domain's SKILL.md for guidance. When spawning extraction agents, provide the domain name so they load the correct SKILL.md. Output valid JSON:

```json
{
  "entities": [
    {"name": "sotorasib", "entity_type": "COMPOUND", "attributes": {"modality": "small molecule"}, "confidence": 0.95, "context": "exact quote from text"}
  ],
  "relations": [
    {"relation_type": "INHIBITS", "source_entity": "sotorasib", "target_entity": "KRAS G12C", "confidence": 0.98, "evidence": "exact quote"}
  ]
}
```

Write each document's combined extraction to disk:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build_extraction.py <doc_id> <output_dir> --json '<combined_json>'
```

**For 4+ documents:** Use the Agent tool to dispatch parallel extraction agents (one per document) for speed.

### Step 4: Validate Molecular Identifiers

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_molecules.py <output_dir>
```

### Step 5: Build Knowledge Graph

If `--domain` was provided to this command, pass it through. Otherwise omit (defaults to drug-discovery).

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_sift.py build <output_dir> --domain <domain_name>
```

### Step 6: Open Visualization

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_sift.py view <output_dir>
```

### Step 7: Report Summary

Tell the user:
- Documents processed and format breakdown
- Total entities by type (table)
- Total relations by type (table)
- Molecular identifiers found and validated
- Communities detected
- Output directory location
- How to explore further (/epistract-query, /epistract-export)
