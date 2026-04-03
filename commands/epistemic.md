---
name: epistract-epistemic
description: Analyze epistemic patterns (hypotheses, contradictions, conditional claims) in a built knowledge graph and produce a Super Domain claims layer
---

# Epistract Epistemic Analysis

Analyze a built knowledge graph for epistemic patterns — hypotheses, contradictions, conditional claims, negative results, and patent vs. paper epistemic signatures. Produces a `claims_layer.json` overlay complementing the existing community structure.

## Arguments
- `path` (required): Output directory containing `graph_data.json` (from a prior `/epistract-ingest` or `/epistract-build`)

## What This Does

This command runs **after** the graph is built (after `/epistract-ingest` or `/epistract-build`). It reads the assembled `graph_data.json` — where cross-document evidence is merged — and identifies five categories of epistemic facts:

1. **Hypothesized mechanisms** — clusters of hedged relations forming a conjecture
2. **Conflicting evidence** — same relation with opposing evidence from different sources
3. **Patent vs. paper signatures** — prophetic/claimed vs. empirically demonstrated
4. **Temporal state transitions** — evolving truth (pre-clinical → approved)
5. **Negative results** — high-confidence statements about absence

## Pipeline

### Step 1: Run the epistemic analysis script

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/label_epistemic.py <output_dir>
```

This reads `graph_data.json` and produces:
- `claims_layer.json` — the Super Domain overlay (epistemic claims, contradictions, grouped hypotheses)
- Updates `graph_data.json` nodes/links with `epistemic_status` field

### Step 2: Report Summary

Tell the user:
- Total relations analyzed
- Breakdown by epistemic status (asserted, hypothesized, speculative, prophetic, negative, conflicting)
- Named claims identified (grouped hypotheses)
- Contradictions detected (with evidence quotes from both sides)
- Patent vs. paper distribution
- How this complements the community structure

### Step 3: Suggest Next Steps

- Review contradictions manually (highest-value findings)
- Use `/epistract-query` to search within the claims layer
- Export with `/epistract-export` — claims_layer.json is included in exports
