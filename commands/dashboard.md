---
name: epistract-dashboard
description: Launch the interactive web workbench for exploring a knowledge graph — chat + force-directed graph + source inspector
---

# Epistract Dashboard — Interactive Workbench

Launch the FastAPI-backed workbench for an existing knowledge graph. The workbench serves three synchronized panels:

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:dashboard <output-dir> [options]

Required:
  <output-dir>    Path to directory containing graph_data.json

Options:
  --domain <name>    Domain for branding and entity colors  (default: auto-detected from graph_data.json)
  --port <n>         Port to serve on  (default: 8000)
  --host <addr>      Host address      (default: 127.0.0.1)

Examples:
  /epistract:dashboard ./epistract-output
  /epistract:dashboard ./out --domain clinicaltrials --port 8080
  /epistract:dashboard ./out --host 0.0.0.0 --port 3000
```

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
- Python 3.11–3.13 with FastAPI and sift-kg installed (`/epistract:setup`)
- **One** of the following LLM credentials set in the shell (only needed for the chat panel — graph + sources work without any):
  - **Azure AI Foundry** — `AZURE_FOUNDRY_API_KEY` (or alias `ANTHROPIC_FOUNDRY_API_KEY`) plus **one** endpoint selector:
    - `AZURE_FOUNDRY_BASE_URL` (or alias `ANTHROPIC_FOUNDRY_BASE_URL`) — full custom gateway URL. Use this when you route through an API management gateway, private endpoint, or reverse proxy with a non-standard hostname. `/v1/messages` is appended automatically if missing.
    - `AZURE_FOUNDRY_RESOURCE` — standard Azure resource name. The workbench builds `https://<resource>.services.ai.azure.com/anthropic/v1/messages`.
    - Optional: `AZURE_FOUNDRY_DEPLOYMENT` (or alias `ANTHROPIC_FOUNDRY_DEPLOYMENT`) — deployment/model name, defaults to `claude-sonnet-4-6`.
  - **Anthropic direct** — `ANTHROPIC_API_KEY` (uses `claude-sonnet-4-20250514`)
  - **OpenRouter** — `OPENROUTER_API_KEY` (uses `anthropic/claude-sonnet-4`)

Provider detection runs in that order — whichever key is set first wins. If a Foundry API key is set without **either** `AZURE_FOUNDRY_BASE_URL` or `AZURE_FOUNDRY_RESOURCE`, the chat panel returns a clear error listing both options instead of falling through to a different provider (fails loud on misconfiguration).

## Notes

- The workbench binds to `127.0.0.1` by default (localhost only). Use `--host 0.0.0.0` only on trusted networks.
- Starting the server takes ~2 seconds. The browser tab will show "Loading..." until `graph_data.json` is parsed (larger graphs take longer).
- To stop the workbench, press `Ctrl+C` in the terminal where it was launched.
