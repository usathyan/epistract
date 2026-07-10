---
name: epistract-projects
description: List, inspect, or delete epistract projects in the registry
---

Manage the project registry — the map of named datasets to their directories, domains,
and creation dates (`$EPISTRACT_HOME/registry.json`, default `~/.epistract/`).

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop.

```
Usage: /epistract:projects <action> [options]

Actions:
  list                       List all registered projects
  info <name>                Show a project's domain, root, and source count
  delete <name> [--purge]    Remove a project from the registry.
                             Without --purge, corpus files and pipeline outputs
                             are left untouched; with --purge the .epistract
                             state dir (manifest + index) is also removed.

Examples:
  /epistract:projects list
  /epistract:projects info glp1-research
  /epistract:projects delete old-project --purge
```

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli projects list
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli projects info <name>
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli projects delete <name> [--purge]
```

For `list`, present a table of name, domain, and root. Deletion is registry-only by
default; confirm before using `--purge`, which removes indexed state.
