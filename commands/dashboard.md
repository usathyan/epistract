---
name: epistract-dashboard
description: Launch the interactive web workbench for exploring a knowledge graph — chat + force-directed graph + source inspector
---

# Epistract Dashboard — Interactive Workbench

Launch the FastAPI-backed workbench for an existing knowledge graph. The workbench serves three synchronized panels:

1. **Chat panel** — ask natural-language questions of the graph, answers streamed with citations back to source documents
2. **Graph panel** — force-directed interactive visualization with community coloring, entity-type filters, and relation-type toggles
3. **Sources panel** — drill into the underlying documents, entities, and relations that ground each answer

## Arguments

- `<output_dir>` (required) — directory containing `graph_data.json`, `communities.json`, and (optionally) `claims_layer.json` from a prior `/epistract:ingest` + `/epistract:epistemic` run
- `--domain <name>` (optional) — domain package name (e.g., `drug-discovery`, `contracts`). Loads domain-specific workbench template (title, entity colors, persona prompt). Defaults to reading the domain from the output_dir's graph_data.json metadata.
- `--port <port>` (optional) — HTTP port (default: 8000)
- `--host <host>` (optional) — bind host (default: 127.0.0.1 for localhost-only)

## How to Run

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/launch_workbench.py <output_dir> [--domain <name>] [--port 8000]
```

Then open `http://127.0.0.1:8000` in your browser.

### Example: Drug Discovery

```
/epistract:dashboard tests/corpora/01_picalm_alzheimers/output-v2 --domain drug-discovery
```

### Example: Contracts

```
/epistract:dashboard ./my-contracts-output --domain contracts
```

## What You Can Do in the Workbench

- **Explore the graph visually** — pan, zoom, and click nodes to see neighborhood context. Filter by entity type or community to isolate sub-graphs.
- **Ask questions** — the chat panel uses the domain-specific persona prompt (defined in `domains/<name>/workbench/template.yaml`) and streams Claude's responses with inline citations.
- **Drill to source** — every answer in the chat panel links to the specific documents, entities, and relations that support it. Click through to see the exact source text.
- **Review epistemic layer** — if `/epistract:epistemic` has been run, contradictions, hypotheses, and prophetic claims are highlighted in the graph view.

## Configuration

Workbench appearance and behavior is domain-configurable via `domains/<name>/workbench/template.yaml`:

- `title` — browser tab and header title
- `entity_colors` — color map for node types
- `persona_prompt` — system prompt for the chat assistant (domain expertise)
- `dashboard_html` — optional static HTML for a landing page
- `starter_questions` — suggested queries for new users

## Pre-requisites

- A completed ingest run (`/epistract:ingest` has written `graph_data.json` to `<output_dir>`)
- Python 3.11+ with FastAPI and sift-kg installed (`/epistract:setup`)
- The `ANTHROPIC_API_KEY` environment variable if you want the chat panel to stream Claude responses

## Notes

- The workbench binds to `127.0.0.1` by default (localhost only). Use `--host 0.0.0.0` only on trusted networks.
- Starting the server takes ~2 seconds. The browser tab will show "Loading..." until `graph_data.json` is parsed (larger graphs take longer).
- To stop the workbench, press `Ctrl+C` in the terminal where it was launched.
