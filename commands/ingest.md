---
name: epistract-ingest
description: Ingest scientific documents and build a drug discovery knowledge graph
---

# Epistract Document Ingestion Pipeline

You are running the epistract drug discovery knowledge graph pipeline.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:ingest <corpus-dir> [options]

Required:
  <corpus-dir>    Directory or file path containing documents to ingest (PDF, DOCX, HTML, TXT, and 75+ formats)

Options:
  --domain <name>           Domain schema to use  (default: drug-discovery; choices: drug-discovery, contracts, clinicaltrials)
  --output <dir>            Output directory       (default: ./epistract-output)
  --validate                Enable molecular validation (auto-enabled if RDKit is installed)
  --view                    Open graph viewer after build (default: true)
  --fail-threshold <float>  Minimum extraction pass rate before graph build (default: 0.95, range: 0.0–1.0)
  --enrich                  Enrich graph via external APIs after build — clinicaltrials domain only
                            (Trial nodes → ClinicalTrials.gov v2; Compound nodes → PubChem PUG REST)

Examples:
  /epistract:ingest ./my-papers
  /epistract:ingest ./papers --domain clinicaltrials --enrich
  /epistract:ingest ./papers --domain contracts --output ./out --fail-threshold 0.9
```

## Arguments
- `path` (required): Directory or file path containing documents
- `--output` (optional): Output directory (default: ./epistract-output)
- `--domain` (optional): Domain name for extraction (default: drug-discovery). Use 'contract' for event contract analysis.
- `--validate` (optional): Enable molecular validation (default: true if rdkit installed)
- `--view` (optional): Open viewer after build (default: true)
- `--fail-threshold <float>` (optional): Minimum post-normalization pass rate required before graph build (default: 0.95, range: [0.0, 1.0]). Pipeline aborts with a clear error if the pass rate falls below this threshold.
- `--enrich` (optional flag): When present AND `--domain` is `clinicaltrials` (or aliases `clinicaltrial` / `clinical_trials`), triggers post-build enrichment against ClinicalTrials.gov v2 and PubChem PUG REST APIs. Trial nodes with NCT IDs get trial metadata; Compound nodes get molecular data. Non-blocking: API failures log counts but do not abort the pipeline.

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
python3 ${CLAUDE_PLUGIN_ROOT}/core/build_extraction.py <doc_id> <output_dir> --json '<combined_json>'
```

**Provenance threading (BOTH env var AND `--model` flag):** Before dispatching extraction agents, do BOTH of the following unconditionally:

1. Set `EPISTRACT_MODEL=<model_id>` in the invocation env for the agent dispatch.
2. Pass `--model <model_id>` literally in the Bash invocation shown in the dispatch prompt to the extractor agent.

Example dispatch-prompt Bash line shown to each agent:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/build_extraction.py <doc_id> <output_dir> --domain <domain_name> --model <model_id> --json '<combined_json>'
```

This is belt + suspenders per D-07 cascade (`--model` flag > `EPISTRACT_MODEL` env > null): if Claude Code's Agent tool inherits env vars, both paths succeed and the `--model` flag wins the cascade; if env inheritance does not work in this runtime, the `--model` flag alone still threads provenance end-to-end. No runtime ambiguity — both paths are always set.

**For 4+ documents:** Use the Agent tool to dispatch parallel extraction agents (one per document) for speed.

### Step 3.5: Normalize Extractions

**MUST run AFTER all Agent-dispatched extractions complete.** Parallel Agent dispatches block until all return — but this step boundary is stated explicitly so future changes to the dispatcher do not accidentally break the sequencing.

Normalize the `extractions/*.json` files in place: rename variant filenames to canonical `<doc_id>.json`, infer missing `document_id` from filename stems, dedupe same-doc_id files (richer version wins; losers moved to `extractions/_dedupe_archive/`), and validate every payload against sift-kg's `DocumentExtraction` Pydantic schema.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/normalize_extractions.py <output_dir> --fail-threshold 0.95
```

Pass the user's `--fail-threshold` value through if they supplied one; otherwise the default 0.95 applies.

A one-line summary prints to stdout. A detailed audit report is written to `<output_dir>/extractions/_normalization_report.json`. If the post-normalization pass-rate is below `--fail-threshold`, the script exits non-zero — the pipeline MUST abort before Step 4 and surface the error and the report path to the user.

### Step 4: Validate Molecular Identifiers

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/domains/drug-discovery/validate_molecules.py <output_dir>
```

### Step 5: Build Knowledge Graph

If `--domain` was provided to this command, pass it through. Otherwise omit (defaults to drug-discovery).

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py build <output_dir> --domain ${CLAUDE_PLUGIN_ROOT}/domains/drug-discovery/domain.yaml
```

### Step 5.5: Enrich Knowledge Graph (if --enrich flag provided)

Skip this step entirely unless BOTH of these are true:
1. The user passed `--enrich` to the command.
2. The resolved `--domain` is `clinicaltrials` (or one of its aliases: `clinicaltrial`, `clinical_trials`).

When both conditions hold, invoke the domain's enrichment module:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/domains/clinicaltrials/enrich.py <output_dir>
```

What this step does:
- Loads `<output_dir>/graph_data.json` via `sift_kg.KnowledgeGraph.load()`.
- For every Trial node whose name matches `NCT\d{8}`, calls the ClinicalTrials.gov v2 API (`/api/v2/studies/{nctId}`) and attaches `ct_overall_status`, `ct_phase`, `ct_enrollment`, `ct_start_date`, `ct_completion_date`, `ct_brief_title` as node attributes.
- For every Compound node, calls PubChem PUG REST (`/rest/pug/compound/name/{name}/property/.../JSON`) and attaches `pubchem_cid`, `molecular_formula`, `molecular_weight`, `canonical_smiles`, `inchi` as node attributes.
- Saves the mutated graph back to `graph_data.json`.
- Writes a summary to `<output_dir>/extractions/_enrichment_report.json` containing per-entity-type counts (total / enriched / not_found / failed) and hit rates.

Enrichment is **non-blocking**. If the Python process exits non-zero, report the failure to the user and continue to Step 6. Do NOT abort the pipeline — the unenriched graph is still valid output.

Rate-limit considerations:
- ClinicalTrials.gov: undocumented limit; enrich.py sleeps 0.1s between requests as a courtesy.
- PubChem: 5 req/sec official limit; enrich.py sleeps 0.2s between requests and retries up to 3x with exponential backoff on 429.

### Step 6: Open Visualization

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py view <output_dir>
```

### Step 7: Report Summary

Tell the user:
- Documents processed and format breakdown
- Normalization pass-rate (read from `<output_dir>/extractions/_normalization_report.json`, e.g., "23/23 = 100.0% (0 recovered, 0 unrecoverable)")
- Total entities by type (table)
- Total relations by type (table)
- Molecular identifiers found and validated
- Communities detected
- Output directory location
- How to explore further (/epistract-query, /epistract-export)
- If `--enrich` was used: enrichment hit rates (read from `<output_dir>/extractions/_enrichment_report.json`, e.g., "Trials: 12/15 enriched (80%), Compounds: 20/23 enriched (87%)")
