# Working with Projects

A **project** is a named, reusable knowledge base. Instead of pointing every command at a
folder path and re-typing it, you create a project once, add documents to it over time, and
refer to it by name from then on. Each project keeps its own corpus, knowledge graph,
epistemic layer, and search index — completely separate from your other projects.

Use projects when you want to:

- Keep **several knowledge bases side by side** — one for a drug program, one for a vendor
  portfolio, one for a literature review — without their data mixing.
- **Grow a knowledge base over time** — add a few papers this week, a few more next week, and
  re-index only the new material.
- **Search and ask questions by name** — `search "semaglutide" --project glp1-research` instead
  of remembering where the output folder lives.

> If you just want to run one corpus through the pipeline once, you don't need projects — the
> classic `/epistract:ingest` → `/epistract:epistemic` → `/epistract:dashboard` flow still works
> exactly as before. Projects are the multi-dataset, keep-and-grow workflow layered on top.

---

## Quick start

This walkthrough builds a project called `glp1-research`, adds documents, indexes it, and
searches it. Commands are shown as Claude Code slash commands; every one also works as a
terminal command (see [Using the terminal](#using-the-terminal) below).

### 1. Create the project

```
/epistract:init glp1-research --domain drug-discovery
```

This creates a project folder (`./glp1-research/` by default) and registers the name. Pick a
domain that matches your documents — `drug-discovery`, `clinicaltrials`, `fda-product-labels`,
or `contracts`. Use `--dir ~/datasets/glp1` to put the project somewhere specific.

### 2. Add documents

Add local files:

```
/epistract:add-files paper1.pdf paper2.pdf trial-protocol.docx --project glp1-research
```

Or pull something from the web:

```
/epistract:add-url https://example.com/press-release.html --project glp1-research
```

You can run these as many times as you like — including days later. Duplicate files are
detected automatically (by content, not just filename) and skipped, so re-adding the same
document never creates a copy.

### 3. Build the knowledge graph

Turn the documents into a graph of entities and relations:

```
/epistract:ingest ./glp1-research/corpus --output ./glp1-research --domain drug-discovery
```

This is the same extraction pipeline as always — it just reads from your project's corpus and
writes the graph back into the project.

### 4. Index for search

```
/epistract:index --project glp1-research
```

Indexing is **incremental**: it only processes documents that are new or changed since the last
run. After you add more files later, re-running `index` picks up just the additions.

### 5. Search and explore

```
/epistract:search "GLP-1 receptor agonist" --project glp1-research
```

Search looks across both the **entities** in your graph and the **text** of your documents,
and ranks the best matches together. Add `--expand` to also surface entities that are connected
to your hits through the graph — useful for "what else is related to this?":

```
/epistract:search "semaglutide" --project glp1-research --expand
```

### 6. Check status any time

```
/epistract:projects list                 # all your projects
/epistract:status --project glp1-research # documents, graph size, index state
```

---

## Managing multiple projects

Every project is independent. A typical setup:

```
/epistract:init glp1-research   --domain drug-discovery
/epistract:init acme-contracts  --domain contracts
/epistract:init fda-class-review --domain fda-product-labels
```

`/epistract:projects list` shows them all. Commands act on the project you name with
`--project`; if you omit it, Epistract uses the project in your current folder (or the one set
in the `EPISTRACT_PROJECT` environment variable).

To remove a project from the list:

```
/epistract:projects delete old-review          # forget it, but keep the files
/epistract:projects delete old-review --purge   # also delete its index + settings
```

Deleting a project **never touches your original source documents** unless you ask for
`--purge`, and even then your corpus files and graph are left in place — only Epistract's own
index and manifest are removed.

---

## Improving graph quality

Once a project's graph is built, you can run automated quality passes over it:

```
/epistract:enhance --project glp1-research
```

This does three things:

- **Merges duplicate entities** — e.g. "GLP-1 Receptor" and "GLP1 receptor" become one node, so
  your graph isn't fragmented by spelling variants.
- **Checks each relation against its evidence** — every relation is scored on how well the
  source quote actually supports it, and weakly-supported ones are flagged.
- **Adds an epistemic layer** — grades how hedged each claim is (a stated fact vs. a "may
  suggest" hypothesis), and when two documents contradict each other, marks the older claim as
  *superseded* by the newer one while keeping both on record.

Run individual passes with `--judge`, `--resolve`, or `--epistemic`. By default it works
offline; add `--llm` to use your configured AI model for more accurate judgments.

Results are written back into the graph and summarized in `enhancement_report.json`.

---

## Where your data lives

Each project is a normal folder you can open, back up, or move:

```
glp1-research/
  corpus/          your added source documents
  ingested/        extracted text
  extractions/     entities + relations per document
  graph_data.json  the knowledge graph
  claims_layer.json, epistemic_narrative.md   the epistemic layer
  .epistract/      the project's manifest + search index
```

The list of projects is kept in `~/.epistract/registry.json`. Set the `EPISTRACT_HOME`
environment variable to keep it somewhere else (e.g. a shared drive).

---

## Using the terminal

Every project command is also available as a plain terminal command after installing Epistract
(`uv pip install -e .` from the repo, or via the plugin's setup):

```bash
epistract init glp1-research --domain drug-discovery
epistract add project acme-contracts --domain contracts   # 'add project' is an alias for 'init'
epistract add files paper1.pdf paper2.pdf --project glp1-research
epistract add url https://example.com/report.html --project glp1-research
epistract index  --project glp1-research
epistract search "semaglutide" --project glp1-research --expand
epistract enhance --project glp1-research
epistract projects list
epistract status --project glp1-research
```

Add `--json` to any command for machine-readable output you can pipe into other tools.

---

## Command reference

| Command | What it does |
|---|---|
| `/epistract:init <name>` | Create a new project (`--domain`, `--dir`) |
| `/epistract:add-files <paths...>` | Add documents to a project's corpus |
| `/epistract:add-url <urls...>` | Fetch web documents into a project |
| `/epistract:index` | Build/refresh the search index (incremental) |
| `/epistract:search <query>` | Hybrid search over entities + documents (`--expand`, `--type`, `-k`) |
| `/epistract:enhance` | Quality passes: merge duplicates, judge relations, epistemic layer |
| `/epistract:projects list\|info\|delete` | Manage the project registry |
| `/epistract:status` | Show a project's documents, graph size, and index state |

Once a project exists, all the classic commands work on it too — point `/epistract:build`,
`/epistract:epistemic`, `/epistract:dashboard`, `/epistract:export`, and `/epistract:ask` at the
project folder.

See also: [COMMANDS.md](COMMANDS.md) for the full command reference, and
[ARCHITECTURE.md](ARCHITECTURE.md) for how the pipeline works.
