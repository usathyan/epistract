---
name: epistract-crosswalk
description: Join two or more built project graphs on shared identifier axes and render the result as a viewable crosswalk knowledge graph with cross-domain findings
---

# Epistract Crosswalk — Cross-Graph Joins as a Viewable Graph

Join two or more *already-built* epistract project graphs on shared identifier
axes, run the cross-domain rules over the join, and render the result as a
knowledge graph the workbench, the graph viewer and every export format can
open — the same way any single-domain graph is opened.

The output is a graph **about the joins**, not a merged graph. Its nodes are
source graphs and canonical keys (typed by axis); its links are membership
(`PRESENT_IN`) and cross-domain findings. Nothing is unioned, so the registry's
one-domain-per-project assumption is never violated: the rendered graph carries
`metadata.domain: crosswalk` and resolves against `domains/crosswalk/`.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage
block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:crosswalk <graph-dir> <graph-dir> [<graph-dir> ...] [options]

Required:
  <graph-dir>            Two or more directories, each containing a built graph_data.json.
                         Use NAME=DIR to override the key a graph is recorded under
                         (defaults to that graph's metadata.domain).

Options:
  --axes <path>          Repo-level axis spec  (default: crosswalks/pharma.yaml)
  --rules <path>         Cross-domain rules spec  (default: crosswalks/pharma-rules.yaml)
  --out <dir>            Output directory to write  (default: ./crosswalk-output)
  --include-advisory     Also run rules flagged advisory: true (skipped by default)
  --no-rules             Build and render the spine only; skip the rules engine
  --dashboard            Launch the workbench on the rendered graph when done

Examples:
  /epistract:crosswalk ~/epistract-pharmacovigilance ~/epistract-clinicaltrials
  /epistract:crosswalk ./a ./b ./c --out ./cw --include-advisory --dashboard
  /epistract:crosswalk labels=~/epistract-product-labels ~/epistract-pharmacovigilance
```

## Arguments

- `<graph-dir>` (required, two or more) — directories containing a built
  `graph_data.json`. Each must resolve to a domain that ships a
  `crosswalk.yaml`; a domain without one contributes nothing and the run says
  so rather than silently joining zero keys. Currently `clinicaltrials`,
  `fda-product-labels` and `pharmacovigilance` ship one.
- `NAME=DIR` form — records the graph under `NAME` instead of its
  `metadata.domain`. **If you use it, the rules spec's `probe` and `reference`
  fields must name the graph by that same key**, or the rules engine rejects the
  spec at load time.
- `--axes <path>` (optional, default `crosswalks/pharma.yaml`) — the single
  canonicalisation authority. One normalizer chain per axis, applied identically
  to every graph.
- `--rules <path>` (optional, default `crosswalks/pharma-rules.yaml`) — the
  cross-domain rules spec.
- `--out <dir>` (optional, default `./crosswalk-output`) — receives
  `spine.json`, `cross_domain_findings.json`, `graph_data.json` and
  `claims_layer.json`.
- `--include-advisory` (optional) — advisory rules are **skipped entirely** by
  default; their stats slot records `{"status": "skipped-advisory"}`. Pass this
  to run them. Every finding they produce is force-graded `advisory` and carries
  a caveat, because their measured noise floor sits above their signal.
- `--no-rules` (optional) — stop after the spine and render the joins alone.
- `--dashboard` (optional) — hand off to `/epistract:dashboard` on the output
  directory when the render succeeds.

## Steps

### Step 1: Validate arguments

- Fewer than two `<graph-dir>` arguments → report that a crosswalk needs at
  least two graphs to join, show the usage block, and stop.
- Any `<graph-dir>` (the `DIR` half of a `NAME=DIR` pair) lacking a
  `graph_data.json` → name the offending directory and stop. Suggest
  `/epistract:build <dir>` if the directory exists but has extractions and no
  graph.
- `--axes` or `--rules` pointing at a missing file → name the path and stop.

### Step 2: Build the spine

```bash
python3 -m core.crosswalk build \
    --graph <dir1> --graph <dir2> [--graph <dirN> ...] \
    --axes <axes-path> \
    --out <out-dir>/spine.json --json
```

Create `<out-dir>` first if it does not exist.

The `--json` flag prints the per-axis stats block. Report it to the user as a
table: axis, total keys, keys per graph, keys shared by 2+ graphs, keys shared
by every declaring graph.

**If every axis reports `shared_by_2_or_more: 0`,** say so plainly — the graphs
loaded but joined nothing. The usual cause is that only one graph declares each
axis (check the `declared_by` list per axis), not a normalisation failure.

On non-zero exit: the error message names the offending config value. Show it
verbatim and stop.

### Step 3: Run the cross-domain rules

Skip this step entirely if `--no-rules` was passed.

```bash
python3 -m core.cross_domain analyze \
    --spine <out-dir>/spine.json \
    --rules <rules-path> \
    --out <out-dir>/cross_domain_findings.json \
    [--include-advisory] --json
```

Report the printed stats per rule. A rule whose slot reads
`{"status": "skipped-advisory"}` was skipped by design — mention that
`--include-advisory` runs it, and mention why it ships advisory.

If this step fails, **do not abort the run.** Report the error, and continue to
Step 4 without the findings file — a spine that joins is still worth viewing.

### Step 4: Render the viewable graph

```bash
python3 -m core.crosswalk_output render \
    --spine <out-dir>/spine.json \
    [--findings <out-dir>/cross_domain_findings.json] \
    --out <out-dir> --json
```

Omit `--findings` when Step 3 was skipped or failed.

Report the summary: node and link counts, canonical keys, how many are shared
by two or more graphs, and how many finding links were drawn. If
`findings_unattached` is non-zero, surface it — those findings referenced a
canonical key the spine does not carry, which almost always means the findings
file and the spine came from different runs.

### Step 5: Tell the user how to look at it

```
Crosswalk graph written to <out-dir>

  View it:    /epistract:dashboard <out-dir>
  Visualize:  /epistract:view <out-dir>
  Export:     /epistract:export <out-dir> --format graphml
```

The domain resolves automatically from `metadata.domain: crosswalk` — no
`--domain` flag is needed on any of the three.

If `--dashboard` was passed, run `/epistract:dashboard <out-dir>` now.

## What the user sees in the workbench

- **Graph panel** — canonical keys coloured by axis (`Trial`, `Drug`,
  `AdverseEvent`, `Indication`, `Outcome`) plus one `Graph` node per source
  corpus. Keys shared across corpora appear as hubs with two or more
  `PRESENT_IN` edges; cross-domain findings appear as edges named after the
  rule that raised them, carrying severity and subtype.
- **Dashboard panel** — entity counts per axis and an Analysis Findings table
  breaking each rule down by severity.
- **Chat panel** — the `crosswalk` persona, with the shared canonical keys and
  every cross-domain finding in its context.

## Notes

- Both config layers are domain-agnostic by construction: `core/crosswalk.py`,
  `core/crosswalk_normalize.py`, `core/cross_domain.py` and
  `core/cross_domain_compare.py` ship no domain vocabulary. Everything specific
  lives in the axis spec, the rules spec, and each domain's `crosswalk.yaml`.
- See `docs/ADDING-DOMAINS.md` for the full `crosswalk.yaml` contract, the
  normalizer primitive table, and the source-kind table.
