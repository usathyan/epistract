---
name: epistract-enhance
description: Run arXiv-backed quality passes over a project's knowledge graph — triple judging, entity resolution, and a bi-temporal epistemic layer
---

Improve the quality of a project's built knowledge graph with three research-backed
passes. Operates on `<project>/graph_data.json` in place and writes an
`enhancement_report.json`. Runs offline with lexical fallbacks; pass `--llm` to use a
configured LLM for calibrated judgments.

Requires a built graph — run `/epistract:build` first.

Passes (if none is named, all three run):
- `--judge` — **LLM-as-judge triple gate** (GraphJudge arXiv 2411.17388 / GraphEval
  arXiv 2407.10793): scores each relation against its evidence span, flags triples whose
  evidence does not support them.
- `--resolve` — **two-stage entity resolution** (ComEM arXiv 2405.16884): blocks by type,
  clusters by character/token/embedding similarity, merges duplicates (e.g. "GLP-1
  Receptor" and "GLP1 receptor").
- `--epistemic` — **bi-temporal contradiction layer** (Graphiti/Zep arXiv 2501.13956) with
  **graded hedge scoring** (arXiv 2405.13319): when a newer relation contradicts an older
  one, the older edge is marked `superseded` (not deleted) with provenance; every edge
  gets a graded `hedge_score` and epistemic status (asserted / hypothesized / speculative).

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop.

```
Usage: /epistract:enhance [--project <name>] [--judge] [--resolve] [--epistemic] [--llm]

Options:
  --project <name>   Target project (default: detected from cwd or $EPISTRACT_PROJECT)
  --judge            Only run the triple-judge gate
  --resolve          Only run entity resolution
  --epistemic        Only run the bi-temporal epistemic layer
  --llm              Use the configured LLM instead of the lexical fallback
  (no pass flag)     Run all three passes

Examples:
  /epistract:enhance --project glp1-research
  /epistract:enhance --project glp1-research --judge --llm
  /epistract:enhance --project acme-contracts --epistemic
```

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli enhance [--project NAME] [--judge] [--resolve] [--epistemic] [--llm]
```

Report the merge count, triple-verdict breakdown, and epistemic status counts (including
any superseded/contradicted edges). This complements `/epistract:epistemic`, which builds
the domain-specific Super Domain claims narrative.
