---
name: epistract-build
description: Build knowledge graph from existing epistract extractions
---

Build the knowledge graph from extraction JSONs already in the output directory.

## Arguments
- `output_dir` (required): Directory containing extractions/
- `--domain` (optional): Domain name (default: drug-discovery). Use `--list-domains` to see available domains.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_sift.py build <output_dir> --domain <domain_name>
```

If `--domain` is not provided, defaults to drug-discovery for backward compatibility.

Report the entity count, relation count, and communities detected.
