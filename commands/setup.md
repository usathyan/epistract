---
name: epistract-setup
description: Install and verify epistract dependencies (sift-kg, optional RDKit/Biopython)
---

Run the epistract setup script to check and install dependencies:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh
```

If any dependency is missing, install it:
- sift-kg: `uv pip install sift-kg`
- RDKit (SMILES validation): `uv pip install rdkit-pypi`
- Biopython (sequence validation): `uv pip install biopython`

Report the status of each dependency to the user after running.
