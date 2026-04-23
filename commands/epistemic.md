---
name: epistract-epistemic
description: Analyze epistemic patterns (hypotheses, contradictions, conditional claims) in a built knowledge graph and produce a Super Domain claims layer
---

# Epistract Epistemic Analysis

Analyze a built knowledge graph for epistemic patterns — hypotheses, contradictions, conditional claims, negative results, and patent vs. paper epistemic signatures. Produces a `claims_layer.json` overlay complementing the existing community structure.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:epistemic <output-dir>

Required:
  <output-dir>    Path to directory containing graph_data.json from a prior /epistract:ingest or /epistract:build run

Examples:
  /epistract:epistemic ./epistract-output
  /epistract:epistemic ./clinical-output
```

## Arguments

## Arguments
- `path` (required): Output directory containing `graph_data.json` (from a prior `/epistract-ingest` or `/epistract-build`)
- `--no-narrate` (optional): Skip the LLM analyst narrator and produce only the deterministic rule output. Use for offline runs, when no API key is available, or when you want byte-identical repeat runs.

## What This Does

This command runs **after** the graph is built (after `/epistract-ingest` or `/epistract-build`). It reads the assembled `graph_data.json` — where cross-document evidence is merged — and identifies five categories of epistemic facts:

1. **Hypothesized mechanisms** — clusters of hedged relations forming a conjecture
2. **Conflicting evidence** — same relation with opposing evidence from different sources
3. **Patent vs. paper signatures** — prophetic/claimed vs. empirically demonstrated
4. **Temporal state transitions** — evolving truth (pre-clinical → approved)
5. **Negative results** — high-confidence statements about absence

After the rule-based analysis, an automatic **analyst narrator** reads the domain persona (from `domains/<name>/workbench/template.yaml:persona`) plus the fresh `claims_layer.json` and produces `epistemic_narrative.md` — a structured briefing an analyst would write: prophetic claim landscape grouped by topic, contested claims with source IDs, coverage gaps, recommended follow-ups. The narrator is ADDITIVE — any failure (no API key, API error, domain has no persona) leaves `claims_layer.json` on disk as the authoritative rule output and prints a clear note to stderr.

## Pipeline

### Step 1: Run the epistemic analysis script

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/label_epistemic.py <output_dir>          # with narrator
python3 ${CLAUDE_PLUGIN_ROOT}/core/label_epistemic.py <output_dir> --no-narrate   # rule-only
```

This reads `graph_data.json` and produces:
- `claims_layer.json` — the Super Domain overlay (epistemic claims, contradictions, grouped hypotheses) — rule-based, deterministic.
- `epistemic_narrative.md` — the analyst briefing — LLM-generated. Skipped when `--no-narrate` is passed, when no API credentials are set, or when the domain's `workbench/template.yaml` has no `persona` field.
- Updates `graph_data.json` nodes/links with `epistemic_status` field.

### Narrator credentials (same priority as workbench chat)

1. `AZURE_FOUNDRY_API_KEY` (with `AZURE_FOUNDRY_BASE_URL` or `AZURE_FOUNDRY_RESOURCE`) — Azure AI Foundry or custom Anthropic gateway.
2. `ANTHROPIC_API_KEY` — direct Anthropic API.
3. `OPENROUTER_API_KEY` — OpenRouter (OpenAI-compatible).

### Narrator persona — single source of truth

The narrator reads the `persona` field from `domains/<name>/workbench/template.yaml` — the SAME persona the workbench chat uses at runtime. Upgrade the persona once; both surfaces improve together. The epistemic-status vocabulary (`asserted` / `prophetic` / `hypothesized` / `contested` / `contradictions` / `negative`) should be called out explicitly in the persona so the narrator knows to use it.

### Step 2: Report Summary

Tell the user:
- Total relations analyzed
- Breakdown by epistemic status (asserted, hypothesized, speculative, prophetic, negative, conflicting)
- Named claims identified (grouped hypotheses)
- Contradictions detected (with evidence quotes from both sides)
- Patent vs. paper distribution
- How this complements the community structure
- Whether `epistemic_narrative.md` was produced (print the `narrative_status` value from the JSON output — `ok` / `no-persona` / `disabled` / `error: …`)

### Step 3: Suggest Next Steps

- Review contradictions manually (highest-value findings)
- Read `epistemic_narrative.md` for the analyst synthesis; open the same graph in `/epistract:dashboard` to chat with the SAME persona reactively
- Use `/epistract-query` to search within the claims layer
- Export with `/epistract-export` — `claims_layer.json` and `epistemic_narrative.md` are included in exports
