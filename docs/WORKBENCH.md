# Interactive Workbench

In addition to the static `graph.html` viewer, epistract ships an interactive FastAPI-backed workbench with three panels: a force-directed graph canvas, a chat assistant powered by Claude, and an auto-generated dashboard summary.

Launch it with:

```
/epistract:dashboard <output_dir> --domain <name>
```

The workbench opens at `http://127.0.0.1:8000`.

## Install

Epistract runs as a [Claude Code](https://claude.ai/claude-code) plugin. Two-step install:

### Prerequisites

- **[Claude Code](https://claude.ai/claude-code)** — the CLI/IDE host for the plugin
- **Python 3.11, 3.12, or 3.13** — `scripts/setup.sh` enforces `>= 3.11` and warns on 3.14+. Tested primarily on 3.13.
- **[uv](https://docs.astral.sh/uv/)** — required. Handles the project `.venv`, dependency resolution, and lockfile. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`.

Optional (enabled automatically when detected):
- **RDKit** — molecular validation for drug-discovery SMILES / InChIKeys
- **Biopython** — sequence validation for DNA / RNA / protein sequences
- **Azure AI Foundry, Anthropic, or OpenRouter API key** — only needed for the chat panel and the epistemic narrator. Graph, extraction, and rule-based epistemic analysis all work without an LLM key.

### Step 1 — Install the plugin in Claude Code

```
/plugin marketplace add usathyan/epistract
/plugin install epistract
```

You should see `epistract` (version 3.0.0) in the installed list, and the `/epistract:*` commands should autocomplete in your Claude Code prompt (`setup`, `ingest`, `build`, `view`, `validate`, `epistemic`, `query`, `export`, `domain`, `dashboard`, `ask`, `acquire`).

### Step 2 — Install Python dependencies

```
/epistract:setup
```

This runs `scripts/setup.sh` which creates `.venv/`, installs `sift-kg`, `chonkie`, `pydantic`, `fastapi`, and the other runtime dependencies, and checks for RDKit / Biopython. Re-run this whenever you upgrade the plugin.

## Panels

### Dashboard — auto-generated summary

![Workbench Dashboard — drug-discovery summary](screenshots/workbench-01-dashboard.png)

Auto-generated entity summary for the loaded graph — entity types with deduplicated counts, totals at the bottom, top communities. Domains can ship a custom `dashboard.html` under `domains/<name>/workbench/` for richer layouts; otherwise `/api/dashboard` builds the summary from `graph_data.json`.

### Chat — domain-aware analyst

![Workbench Chat — welcome](screenshots/workbench-02-chat-welcome.png)

The chat panel reads its title, body text, placeholder, starter questions, and system-prompt **persona** from `domains/<name>/workbench/template.yaml`. Switch domains and the entire chat persona changes — the same workbench code works for any domain.

### Graph — visual exploration

![Workbench Graph Panel — S6 GLP-1](screenshots/workbench-03-graph-glp1.png)

Full knowledge graph rendered in the workbench: nodes color-coded by entity type, community clusters, entity-type filter pills at the top, search bar for direct entity lookup. Pan, zoom, click any node to see neighborhood context; toggle entity types on and off to isolate sub-graphs.

### Chat — epistemic layer in action

![Workbench Chat — prophetic patent claims](screenshots/workbench-04-chat-epistemic.png)

Ask *"Which patents make prophetic claims about new indications?"* and the chat panel surfaces the prophetic claims the epistemic layer identified. With the drug-discovery persona active, Claude produces a structured analysis: per-patent prophetic claims, status flags, grouped summaries, and a meta-analysis highlighting the biggest gaps between prophetic claims and commercial reality. This is the cross-document synthesis the workbench is designed for.

## What You Can Do

- **Ask natural-language questions** — *"What are the resistance mechanisms for sotorasib?"*, *"Compare semaglutide vs tirzepatide adverse events"*. Answers stream back via SSE with citations to source documents.
- **Explore the graph visually** — pan, zoom, filter by entity type, search by name, click any node for neighborhood context.
- **Drill to source** — every answer links to the documents, entities, and relations that support it (sources panel).
- **Review the epistemic layer** — contradictions, hypotheses, prophetic claims, and the full analyst narrative surface in chat answers when `/epistract:epistemic` has been run.

## Configuration

Workbench appearance and persona are domain-configurable via `domains/<name>/workbench/template.yaml` — title, subtitle, entity colors, persona prompt, starter questions, placeholder, loading message, and `analysis_patterns`. The same workbench code works for any domain.

The `persona` field serves **both** surfaces: the workbench chat uses it as its system prompt (reactive — fires on user questions), and `/epistract:epistemic` feeds the same persona to the LLM narrator that writes `epistemic_narrative.md` (proactive — fires after the graph is built). Upgrade the persona once; both surfaces improve together. A strong persona names a profession, describes depth of expertise, and commits to the epistemic-status vocabulary (`asserted` / `prophetic` / `hypothesized` / `contested` / `contradictions` / `negative`) — see `domains/drug-discovery/workbench/template.yaml` for a reference implementation.

## LLM Provider

The chat panel and the epistemic narrator share credential-resolution logic. Priority:

1. **Azure AI Foundry** — `AZURE_FOUNDRY_API_KEY` (or alias `ANTHROPIC_FOUNDRY_API_KEY`) plus **one** endpoint selector:
   - `AZURE_FOUNDRY_BASE_URL` (or alias `ANTHROPIC_FOUNDRY_BASE_URL`) — full custom gateway URL for enterprise deployments behind API management, private endpoints, or reverse proxies. `/v1/messages` is auto-appended if missing.
   - `AZURE_FOUNDRY_RESOURCE` — standard Azure resource name. The workbench builds `https://<resource>.services.ai.azure.com/anthropic/v1/messages`.
   - Optional: `AZURE_FOUNDRY_DEPLOYMENT` (or alias `ANTHROPIC_FOUNDRY_DEPLOYMENT`) — deployment/model name, defaults to `claude-sonnet-4-6`.
   - **Fails loud** if the API key is set but neither `AZURE_FOUNDRY_BASE_URL` nor `AZURE_FOUNDRY_RESOURCE` is configured.
2. **`ANTHROPIC_API_KEY`** → calls Anthropic directly with `claude-sonnet-4-20250514`.
3. **`OPENROUTER_API_KEY`** → calls OpenRouter with `anthropic/claude-sonnet-4.6`.

Set one of these in your shell before launching. The graph, sources, and rule-based epistemic analysis all work without any LLM credentials — only the chat panel and the narrator need them.

### Azure AI Foundry — standard endpoint

```bash
export AZURE_FOUNDRY_API_KEY="your-foundry-api-key"
export AZURE_FOUNDRY_RESOURCE="my-company-ai"                # your Azure resource name
export AZURE_FOUNDRY_DEPLOYMENT="claude-sonnet-4-6"          # optional; this is the default
/epistract:dashboard ./my-graph-output --domain drug-discovery
```

### Azure AI Foundry — custom gateway (enterprise)

When your Foundry endpoint sits behind an API management gateway, VNet-integrated private endpoint, or corporate reverse proxy on a non-standard hostname, set the full URL directly:

```bash
export AZURE_FOUNDRY_API_KEY="your-foundry-api-key"
export AZURE_FOUNDRY_BASE_URL="https://ai-gateway.acme.internal/anthropic"
/epistract:dashboard ./my-graph-output --domain drug-discovery
```

Or using the provider-first naming some enterprise environments prefer:

```bash
export ANTHROPIC_FOUNDRY_API_KEY="your-foundry-api-key"
export ANTHROPIC_FOUNDRY_BASE_URL="https://ai-gateway.acme.internal/anthropic/v1/messages"
```

`AZURE_FOUNDRY_*` and `ANTHROPIC_FOUNDRY_*` are accepted as aliases. `AZURE_FOUNDRY_*` wins if both are set.

### Anthropic / OpenRouter

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export OPENROUTER_API_KEY="sk-or-..."
/epistract:dashboard ./my-graph-output --domain drug-discovery
```

## Troubleshooting

- **"No API key found"** in chat or narrator → set one of the env vars above, restart the workbench.
- **Workbench shows generic persona / default title** → `graph_data.json` has no `metadata.domain`. Rebuild with `/epistract:ingest --domain <name>` to populate the field, or pass `--domain` explicitly to the dashboard command.
- **`/epistract:setup` fails on Python 3.14** → prebuilt wheels may not exist yet. Use 3.13 or 3.12.
- **Port 8000 already in use** → pass `--port 8042` (or any free port) to `/epistract:dashboard`.
