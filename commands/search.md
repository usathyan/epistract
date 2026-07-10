---
name: epistract-search
description: Hybrid search over an epistract project — entities and document chunks, with optional graph expansion
---

Search a project's knowledge graph and corpus. Unlike `/epistract:query` (which does a
substring scan of graph nodes only), this runs a BM25 full-text search over both entities
and indexed document chunks, fuses the ranked lists with reciprocal rank fusion, and can
optionally expand the results through the graph via personalized PageRank (HippoRAG 2
pattern) to surface multi-hop-related entities.

Requires a built index — run `/epistract:index <project>` first.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop.

```
Usage: /epistract:search <query> [options]

Required:
  <query>            Search terms

Options:
  --project <name>   Target project (default: detected from cwd or $EPISTRACT_PROJECT)
  --type <type>      Filter entity results by entity type
  -k <n>             Max results (default: 10)
  --expand           Graph expansion via personalized PageRank from entity hits

Examples:
  /epistract:search "GLP-1 receptor agonist" --project glp1-research
  /epistract:search "semaglutide" --project glp1-research --expand -k 15
  /epistract:search "indemnification" --project acme-contracts --type Obligation
```

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli search <query> [--project NAME] [--type TYPE] [-k N] [--expand]
```

Present entity hits, chunk hits (with source doc), and — if `--expand` was used — the
graph-expanded related entities, as formatted sections. Add `--json` for machine-readable output.
