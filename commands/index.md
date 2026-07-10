---
name: epistract-index
description: Incrementally index an epistract project's corpus and graph for hybrid search
---

Build or refresh a project's hybrid search index (SQLite FTS5 over document chunks
plus entities from the knowledge graph). Indexing is incremental: documents whose
content hash is unchanged since the last run are skipped, so re-indexing after
`/epistract:add-files` only processes the new material.

This indexes raw corpus text for search. To build the knowledge graph itself from
extractions, use `/epistract:build`; the index picks up graph entities automatically
once `graph_data.json` exists.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop.

```
Usage: /epistract:index [--project <name>] [--rebuild]

Options:
  --project <name>   Target project (default: detected from cwd or $EPISTRACT_PROJECT)
  --rebuild          Drop and rebuild the index from scratch

Examples:
  /epistract:index --project glp1-research
  /epistract:index --project glp1-research --rebuild
```

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli index [--project NAME] [--rebuild]
```

Report how many documents were indexed vs. skipped, total chunks, and entity count.
Then suggest `/epistract:search <query> --project <name>`.
