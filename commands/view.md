---
name: epistract-view
description: Open interactive knowledge graph visualization in browser
---

Open the interactive graph viewer. Supports optional filters.

Arguments:
- `output_dir` -- directory with graph_data.json (default: ./epistract-output)
- `--neighborhood <entity>` -- focus on entity neighborhood
- `--top <n>` -- show top N entities by connections

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py view <output_dir> [--neighborhood <entity>] [--top <n>]
```

## Usage Guard

**If invoked with `--help`:** Display the following usage block verbatim and stop. Otherwise proceed with existing logic.

```
Usage: /epistract:view [output-dir] [options]

  All arguments are optional — running with no arguments opens the default output directory.

Options:
  <output-dir>              Path to extraction output containing graph_data.json  (default: ./epistract-output)
  --neighborhood <entity>   Show neighborhood subgraph centered on a named entity
  --top <n>                 Limit to top N nodes by degree  (default: all)

Examples:
  /epistract:view
  /epistract:view ./my-output
  /epistract:view --neighborhood "remdesivir"
  /epistract:view --top 20
```

Arguments:
- `output_dir` -- directory with graph_data.json (default: ./epistract-output)
- `--neighborhood <entity>` -- focus on entity neighborhood
- `--top <n>` -- show top N entities by connections

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/run_sift.py view <output_dir> [--neighborhood <entity>] [--top <n>]
```

