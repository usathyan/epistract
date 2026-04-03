---
name: epistract-query
description: Search entities in the drug discovery knowledge graph
---

Search the knowledge graph for entities by name.

Arguments:
- `query` -- search term
- `--type` -- filter by entity type (COMPOUND, GENE, PROTEIN, etc.)
- `output_dir` -- directory with graph_data.json (default: ./epistract-output)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py search <output_dir> <query> [--type TYPE]
```

Present results as a formatted table with entity name, type, and confidence.
