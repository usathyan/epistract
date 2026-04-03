---
name: epistract-export
description: Export knowledge graph to GraphML, GEXF, CSV, SQLite, or JSON
---

Export the knowledge graph to an external format.

Arguments:
- `format` -- one of: json, graphml, gexf, csv, sqlite
- `output_dir` -- directory with graph_data.json (default: ./epistract-output)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py export <output_dir> <format>
```

Report the export path and format-specific usage tips:
- graphml: Open in Gephi, yEd, or Cytoscape
- sqlite: Query with SQL, DuckDB, or Datasette
- csv: Import to Excel, pandas, or R
