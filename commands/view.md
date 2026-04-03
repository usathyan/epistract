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
