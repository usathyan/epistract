---
name: epistract-build
description: Build knowledge graph from existing epistract extractions
---

Build the knowledge graph from extraction JSONs already in the output directory.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:build <output-dir> [options]

Required:
  <output-dir>    Path to directory containing an extractions/ subfolder from a prior /epistract:ingest run

Options:
  --domain <name>    Domain schema to use for graph construction  (default: drug-discovery)

Examples:
  /epistract:build ./epistract-output
  /epistract:build ./my-output --domain clinicaltrials
  /epistract:build ./my-output --domain contracts
```

## Arguments

## Arguments
- `output_dir` (required): Directory containing extractions/
- `--domain` (optional): Domain name (default: drug-discovery). Use `--list-domains` to see available domains.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py build <output_dir> --domain ${CLAUDE_PLUGIN_ROOT}/domains/drug-discovery/domain.yaml
```

If `--domain` is not provided, defaults to drug-discovery for backward compatibility.

Report the entity count, relation count, and communities detected.
