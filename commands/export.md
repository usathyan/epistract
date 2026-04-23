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

## Usage Guard

**If invoked with no format argument or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:export <format> [output-dir]

Required:
  <format>       Export format: json, graphml, gexf, csv, or sqlite

Options:
  <output-dir>   Path to extraction output containing graph_data.json  (default: ./epistract-output)

Examples:
  /epistract:export graphml
  /epistract:export csv ./my-output
  /epistract:export sqlite
  /epistract:export json ./clinical-output
```

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

