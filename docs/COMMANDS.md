# Commands Reference

Slash commands split into two groups — **full-pipeline commands** that do everything needed for a scenario, and **single-stage re-run commands** that operate on existing output. For a fresh scenario you only need three commands: `/epistract:ingest`, `/epistract:epistemic`, `/epistract:dashboard`.

Each command has a fuller spec under `commands/<name>.md` — this doc is the quick reference.

## Full pipeline

| Command | Runs | When to use |
|---|---|---|
| `/epistract:setup` | Dependency installer | First-time setup, re-run after upgrades |
| `/epistract:ingest <docs> --output <dir> --domain <name>` | read → chunk → extract → validate → build → viewer | **Fresh scenario run** — start here |
| `/epistract:epistemic <dir>` | Epistemic rule engine → `claims_layer.json` + LLM narrator → `epistemic_narrative.md` | After every fresh `ingest` — separate because it reads the built graph |
| `/epistract:dashboard <dir> --domain <name>` | Launch interactive workbench (graph + chat + dashboard) | Exploration, briefings, stakeholder demos |

## Acquire and create

| Command | Runs | When to use |
|---|---|---|
| `/epistract:acquire <query> --output <dir>` | PubMed E-utilities search + download | Fetching a fresh biomedical corpus before `/epistract:ingest` |
| `/epistract:domain --input <samples> --name <slug>` | Domain wizard (3-pass LLM schema discovery) | Creating a new domain package from sample documents |
| `/epistract:domain --schema <file.json> --name <slug>` | Domain bypass (no LLM) | Creating a domain from a pre-built schema JSON (reproducibility, large ontologies) |

## Re-run individual stages

| Command | Runs | When to use |
|---|---|---|
| `/epistract:build <dir>` | Graph build only | Re-running the builder on existing extractions |
| `/epistract:view <dir>` | `graph.html` generation only | Re-generating the static viewer |
| `/epistract:validate <dir>` | Molecular / sequence / custom validation only | Re-running domain validators (produces `validation_report.json`) |
| `/epistract:query <dir> <query>` | Entity search | Post-run exploration from the CLI |
| `/epistract:export <dir> <format>` | GraphML / GEXF / CSV / SQLite / JSON export | Handing the graph to downstream tools |
| `/epistract:ask <dir> <question>` | Natural-language Q&A over the graph | One-shot questions without launching the workbench |

## Flags you'll use often

- `/epistract:ingest --domain <name>` — pick a pre-built domain (`drug-discovery`, `contracts`) or a wizard-generated one (`domains/<slug>/`).
- `/epistract:ingest --ocr` — include image formats in discovery (+8 extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`).
- `/epistract:ingest --fail-threshold 0.95` — normalization pass-rate gate. Pipeline aborts before graph build if below threshold (default 0.95).
- `/epistract:epistemic --no-narrate` — skip the LLM narrator. Rule-based `claims_layer.json` still ships. Use for offline runs or no-key environments.
- `/epistract:dashboard --port 8042` — workbench port override (default 8000).
- `/epistract:dashboard --host 0.0.0.0` — bind to all interfaces (for remote demos; default `127.0.0.1`).

## Command details

For the full spec of each command — argument semantics, edge cases, output artifacts, and what the agent does internally — see the per-command files:

```
commands/setup.md
commands/ingest.md
commands/build.md
commands/view.md
commands/validate.md
commands/epistemic.md
commands/query.md
commands/export.md
commands/domain.md
commands/dashboard.md
commands/ask.md
commands/acquire.md
```

Each is a Markdown skill file loaded by Claude Code when you invoke the command.
