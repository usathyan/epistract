---
name: crosswalk
description: Read a rendered crosswalk graph -- canonical keys, joins across independently-built knowledge graphs, and cross-domain findings. Not an extraction domain.
---

# Crosswalk

**This domain does not extract anything.** No agent reads a document against
this schema, and `/epistract:ingest --domain crosswalk` is not a meaningful
command. Every other `domains/*/SKILL.md` in this repository is an extraction
prompt; this one is a reading guide.

A crosswalk graph is produced by `/epistract:crosswalk` from two or more
*already-built* project graphs. The pipeline is three modules deep:

1. `core/crosswalk.py build` — joins the graphs on shared identifier axes and
   writes `spine.json`, a join table mapping a canonical key per axis to the
   node IDs holding that key in each graph.
2. `core/cross_domain.py analyze` — reads that spine plus the graphs it was
   built from and writes `cross_domain_findings.json`: assertions one graph
   makes that another does not.
3. `core/crosswalk_output.py render` — renders both into a `graph_data.json`
   and `claims_layer.json` with `metadata.domain: crosswalk`, which is what
   makes the result loadable by the workbench, the graph viewer, and every
   `/epistract:export` format.

## What the nodes mean

| Entity type | What it is |
|---|---|
| `Graph` | A whole source knowledge graph that fed the spine. Named by the key the spine recorded — `metadata.domain`, unless the spine was built with a `NAME=DIR` override. |
| `Trial`, `Drug`, `AdverseEvent`, `Indication`, `Outcome` | One canonical key on the axis of that name. |

A canonical key is the value **after** the axis spec's normalizer chain has
run — `crosswalks/pharma.yaml` lowercases drug names and strips salt and
hydrate suffixes, folds British adverse-event orthography onto US spelling,
and extracts bare `NCT########` identifiers. So a canonical key often matches
no single source document's wording exactly. The member node IDs that
canonicalise to it are carried on the node's `members` attribute and on each
`PRESENT_IN` link.

## What the links mean

`PRESENT_IN` — a canonical key held by a source graph. **A key with two or
more of these is a join**: the same real-world entity, independently surfaced
by two separate corpora. That is the primary signal in the graph.

A key with exactly one `PRESENT_IN` link is not a defect. Most keys
legitimately appear in one corpus only, either because the other corpus does
not cover that entity or because it does not declare that axis at all.
`domains/clinicaltrials/crosswalk.yaml`, for instance, deliberately declares
no `adverse_event` axis — that graph holds zero AE-typed entities.

Every other relation type is a **cross-domain finding**, named after the rule
that produced it. Each carries a severity and a subtype:

- Severity is `high` / `medium` / `low` / `advisory` (lowercase — this vocabulary
  differs from the uppercase single-graph one on purpose; these rules need a
  graded band).
- `advisory` means the rule's measured noise floor sits above its signal. It is
  skipped entirely unless `--include-advisory` was passed, and when it does run
  every finding is force-graded `advisory` and carries a caveat string. Never
  present an advisory finding beside a graded one at equal confidence.

### The three `spine_keys` subtypes, strongest first

| Subtype | Reading |
|---|---|
| `attributed_elsewhere` | The reference corpus knows the term — it just never attaches it to this subject. The most interesting case (a class-effect candidate). |
| `absent` | The reference corpus does not hold the term at all. |
| `granularity_variant` | The probe key is a sub- or superstring of a key the reference already attaches to the same subject (`abdominal pain upper` vs `abdominal pain`). A vocabulary artifact, not a signal. |

## How to answer questions about one

- Lead with the join structure: which axes joined, how many keys were shared,
  and by which graphs.
- Name the axis, the canonical key, and the graphs whenever you cite something.
- Distinguish "not shared" from "flagged" — only a finding link is a claim that
  something is missing.
- Report severity and subtype on every finding, and caveat the advisory ones.
- If the question needs the underlying documents, say so and name which source
  graph to open — the crosswalk graph holds node IDs, not document text.

## Extending it

Adding an axis to an axis spec (`crosswalks/*.yaml`) means adding the matching
entity type to `domain.yaml` and a legend colour to `workbench/template.yaml`.
The graph renders either way; an undeclared axis just falls back to the
workbench's rotating default palette. Which entity types and value sources feed
an axis is declared per domain in `<domain_dir>/crosswalk.yaml`. See
`docs/ADDING-DOMAINS.md` for the full two-layer config contract.
