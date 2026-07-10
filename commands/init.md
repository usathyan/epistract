---
name: epistract-init
description: Create a new named epistract project (persistent dataset) with its own corpus, graph, and search index
---

Create a new persistent project: a named dataset directory with its own corpus,
knowledge graph, epistemic layer, and hybrid search index. Projects are tracked in
a global registry (`$EPISTRACT_HOME/registry.json`, default `~/.epistract/`) so
`/epistract:search`, `/epistract:index`, and related commands can address them by name.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:init <name> [options]

Required:
  <name>    Project name (letters, digits, '.', '_', '-')

Options:
  --domain <name>    Domain schema for extraction (default: drug-discovery).
                     Use `python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py --list-domains` to see options.
  --dir <path>       Project directory (default: ./<name>)

Examples:
  /epistract:init glp1-research --domain drug-discovery
  /epistract:init acme-contracts --domain contracts --dir ~/datasets/acme
```

## Arguments
- `name` (required): Project name.
- `--domain` (optional): Domain package name (default: drug-discovery).
- `--dir` (optional): Project root directory (default: `./<name>`).

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli init <name> [--domain DOMAIN] [--dir PATH]
```

After creation, tell the user the project root and suggest the next step:
`/epistract:add-files <name> <paths...>` to add documents, then `/epistract:index <name>`.
