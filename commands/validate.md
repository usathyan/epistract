---
name: epistract-validate
description: Validate molecular identifiers (SMILES, sequences) in extraction results
---

Run molecular validation on existing extractions.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/domains/drug-discovery/validate_molecules.py <output_dir>
```

Report: SMILES found/valid, sequences found/valid, other identifiers found.
If RDKit or Biopython not installed, suggest installation commands.
