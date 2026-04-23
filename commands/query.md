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

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:query <search-term> [options]

Required:
  <search-term>    Entity name or keyword to search for in the knowledge graph

Options:
  --type <entity-type>    Filter results by entity type
                          (Trial, Compound, Condition, Sponsor, Endpoint, Arm, Biomarker,
                           Gene, Protein, Drug, Disease, Party, Obligation, etc.)
  <output-dir>            Path to extraction output directory  (default: ./epistract-output)

Examples:
  /epistract:query "remdesivir"
  /epistract:query "COVID-19" --type Condition
  /epistract:query "NCT04280705" --type Trial
```

Arguments:
- `query` -- search term
- `--type` -- filter by entity type (COMPOUND, GENE, PROTEIN, etc.)
- `output_dir` -- directory with graph_data.json (default: ./epistract-output)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py search <output_dir> <query> [--type TYPE]
```

Present results as a formatted table with entity name, type, and confidence.

