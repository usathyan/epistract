---
name: epistract-validate
description: Validate molecular identifiers (SMILES, sequences) in extraction results
---

Run molecular validation on existing extractions.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:validate <output-dir>

Required:
  <output-dir>    Path to directory containing extraction JSON files (from /epistract:ingest or /epistract:build)

Examples:
  /epistract:validate ./epistract-output
  /epistract:validate ./my-output
```

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/domains/drug-discovery/validate_molecules.py <output_dir>
```

Report: SMILES found/valid, sequences found/valid, other identifiers found.
If RDKit or Biopython not installed, suggest installation commands.
