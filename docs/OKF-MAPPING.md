# OKF Export

Epistract can export a project's knowledge graph as an **OKF (Open Knowledge
Format) bundle** — a directory of markdown "concept" files with YAML
frontmatter, where file paths double as concept IDs and markdown links form
an untyped graph. OKF is Google's formalization of the "LLM-wiki" pattern:
knowledge published for consumption by AI agents and humans alike, git-
versionable and tool-agnostic. Spec (v0.1):
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

This is a **publication surface**, not a new internal model — `graph_data.json`
remains epistract's source of truth. Only **export** (epistract → OKF) is
implemented; see [Deferred](#deferred) below. Design rationale, use-case
grid, and risk register: [docs/plans/2026-07-14-okf-export-decision.md](plans/2026-07-14-okf-export-decision.md).

Implementation: `core/okf_export.py` (`export_okf()`). Invoke it via the
multi-project CLI (`python3 -m core.cli export --format okf`) or directly as
a script — see [CLI](#cli).

## Mapping

| Epistract | OKF |
|---|---|
| Node `id` (e.g. `party:acme`) | File `<type-slug>/<name-slug>.md`; original id preserved as `epistract_id` frontmatter key |
| `entity_type` | Frontmatter `type`; also the directory name (`_slugify(entity_type)`) |
| `name` | `title` |
| `context` (first sentence) — falls back to `"{name} ({entity_type})."` if no context | `description` (frontmatter key **and** first line of body) |
| `attributes{}` | `# Attributes` body table (`\| Key \| Value \|`) |
| Outgoing typed relations (all `relation_type`s except `MENTIONED_IN`) | `# Relations` body table: one row per edge — markdown link to target, `confidence` (2dp), `epistemic_status`, and (unless redacted) a 160-char evidence excerpt |
| `confidence` | Frontmatter `epistract_confidence` |
| `source_documents` (list of document keys, on non-DOCUMENT nodes) | Frontmatter `epistract_source_documents`, **and** rendered as a `# Citations` body section — one numbered link per key, resolved against DOCUMENT nodes (see below) |
| `epistemic_status` | Per-relation: `Status` column in the Relations table. Node-level: if the node is source/target of any edge with status `contested` or `superseded`, that status is added to the node's `tags` (other statuses — `asserted`, `hypothesized`, `prophetic`, etc. — appear only in the Relations table, not as tags) |
| `community` (node field, or fallback lookup in `communities.json` by node id) | Slugified into `tags`; **never** a directory (communities churn on re-resolution, types don't) |
| `DOCUMENT` nodes | `sources/<name-slug>.md` concepts. `type: "Source Document"` (not the literal `DOCUMENT` entity type). `resource` frontmatter key = first non-empty of `attributes.url` / `attributes.source_url` / `attributes.origin_url` / `attributes.origin`, else `attributes.path` |
| `MENTIONED_IN` edges | Excluded entirely from Relations tables. Citations are built from each node's own `source_documents` list, not by walking these edges (see `mentions` sidecar note below) |
| `claims_layer.json` → `super_domain.conflicts` / `.coverage_gaps` / `.risks` | One concept per item under `claims/`, typed `Conflict` / `Coverage Gap` / `Risk`. `severity` → `tags`; every other item field (except `id`/`type`/`severity`/`description`) → `epistract_<field>` frontmatter key; `entities_involved` → `# Related Concepts` links; `contracts_involved` or `contracts_affected` → `# Related Sources` links |
| Bi-temporal `superseded` edges (`invalid_at`, `superseded_by`) | `log.md` — one `**Deprecation**` bullet per superseded edge, grouped under a `## YYYY-MM-DD` heading taken from `invalid_at` (falls back to `metadata.updated_at`, then `created_at`) |
| Full-fidelity graph | **Sidecar:** verbatim (or redacted) copy of `graph_data.json`, and `claims_layer.json` if present, written at the bundle root |
| `metadata.domain`, entity/relation counts | Root `index.md` heading (`# {domain} Knowledge Graph`, or `# Knowledge Graph` if `domain` is unset) and `log.md`'s `**Initialization**` entry |

**Known limitation — claims schema coupling.** The `claims/` mapping above
only fires for a `claims_layer.json` whose `super_domain` uses the
`conflicts` / `coverage_gaps` / `risks` shape (the contracts domain's
epistemic layer). Domains whose epistemic layer emits the older
`contradictions` / `hypotheses` / `contested_claims` shape (e.g.
drug-discovery) currently produce **zero** files under `claims/` — the keys
simply don't match and no warning is raised. Confirmed against
`tests/corpora/smoke_glp1/output/claims_layer.json` (drug-discovery shape)
vs. `tests/corpora/09_pharmacovigilance/output/claims_layer.json` (conflicts
shape). Treat OKF claims export as contracts-domain-only until this is
generalized.

## Bundle layout

Example tree for a two-entity-type graph with one document, one relation,
and one claim (names illustrative, not drawn from any real project):

```
okf/
├── index.md                  # root index: okf_version frontmatter, links to each dir
├── log.md                    # initialization + deprecation entries
├── graph_data.json           # sidecar: verbatim (or redacted) copy of the graph
├── claims_layer.json         # sidecar: verbatim (or redacted), only if present
├── party/
│   ├── index.md
│   └── acme-corp.md
├── obligation/
│   ├── index.md
│   └── deliver-goods-by-q3.md
├── sources/
│   ├── index.md
│   └── master-services-agreement.md
└── claims/
    ├── index.md
    └── risk-001.md
```

A concept file looks like:

```markdown
---
type: "PARTY"
title: "Acme Corp"
description: "Acme Corp (PARTY)."
tags: ["acme-master-agreement-cluster"]
timestamp: "2026-04-01T19:01:18.992576"
epistract_id: "party:acme_corp"
epistract_confidence: 0.95
epistract_source_documents: ["master_services_agreement"]
---

Acme Corp (PARTY).

# Attributes

| Key | Value |
| --- | --- |
| role | Vendor |

# Relations

| Relation | Target | Confidence | Status | Evidence |
| --- | --- | --- | --- | --- |
| OBLIGATES | [Deliver goods by Q3](/obligation/deliver-goods-by-q3.md) | 0.95 | asserted | Acme shall deliver… |

# Citations

[1] [master_services_agreement](/sources/master-services-agreement.md)
```

Relation and citation links are **bundle-root-relative** (leading `/`,
e.g. `/obligation/deliver-goods-by-q3.md`), not filesystem-absolute and not
relative to the linking file. Per-directory `index.md` entries link with a
bare filename instead, since they're already co-located with their targets.

## Extension frontmatter keys

OKF v0.1 requires consumers to preserve unknown frontmatter keys, so
epistract-specific fields survive round-trips through generic OKF tooling.
Registry:

| Key | Applies to | Type | Semantics |
|---|---|---|---|
| `epistract_id` | Every concept | string | The original epistract graph node id (or claim `id`) — the stable join key back to `graph_data.json` / `claims_layer.json` |
| `epistract_confidence` | Entity and document concepts | float \| omitted | The node's `confidence` score. Omitted entirely (not written as `null`) when the node has no confidence value |
| `epistract_source_documents` | Entity concepts (not documents, not claims) | list[string] \| omitted | The node's `source_documents` list. Omitted when empty |
| `epistract_<field>` | Claim concepts | varies | Every other field on the claims-layer item (e.g. `epistract_suggested_action`, `epistract_contracts_affected`, `epistract_source_type`) — passed through verbatim except `id`, `type`, `severity`, `description` (which map to reserved OKF keys) and `evidence` (dropped when redacted) |

Frontmatter omits any key whose value is `None`, or an empty list/dict —
concept files stay free of `key: null` / `key: []` clutter.

## Redaction

`include_evidence=False` (CLI: `--no-evidence`) strips:

- The `Evidence` column from every `# Relations` table.
- Verbatim `evidence` text from the `graph_data.json` sidecar (top-level
  `links[].evidence` and each `links[].mentions[].evidence`).
- `evidence` from the `claims_layer.json` sidecar (set to `{}` if the field
  is a dict, else `""`).

**Use this for any confidential corpus before publishing a bundle.** The
contracts domain in particular embeds verbatim contract text in relation
evidence — an unredacted bundle republishes source-document quotes outside
the original access boundary. Export itself is local-only; redaction is
what makes the *output* safe to share, so treat `--no-evidence` as required,
not optional, whenever the bundle leaves your machine and the corpus isn't
already public.

Note the same schema-coupling limitation as above applies here: redaction
of `claims_layer.json` only touches the `conflicts` / `coverage_gaps` /
`risks` shape's `evidence` field, not the `contradictions` / `hypotheses` /
`contested_claims` shape used by other domains.

## Sidecar rationale

Every export writes a verbatim (or redacted) copy of `graph_data.json` —
and `claims_layer.json` if present — at the bundle root. OKF consumers
ignore non-`.md` files, so this costs nothing on the OKF side, and buys:

- **Lossless fidelity.** The markdown mapping is lossy by design (typed
  relations become table rows, not first-class OKF concepts; edge
  attributes like `support_count` aren't rendered at all). The sidecar
  keeps the full native representation next to the human/agent-readable
  view.
- **Future import.** If/when OKF → epistract import is built (see
  [Deferred](#deferred)), a bundle produced by epistract itself can be
  round-tripped exactly via the sidecar, rather than lossily reconstructed
  by parsing markdown tables.

## Determinism

- All concept `timestamp` fields (and the `log.md` initialization entry)
  use a single value taken from `graph_data.json`'s
  `metadata.updated_at` → `metadata.created_at` → `1970-01-01T00:00:00+00:00`
  fallback chain — **never wall-clock time at export time.**
- The output directory is wiped (`shutil.rmtree`) and recreated on every
  export, so stale files from previously-deleted entities never linger.
- Given the same `graph_data.json` (and `claims_layer.json`,
  `communities.json`) input, `export_okf()` produces byte-identical output:
  node/link/claim processing order follows JSON array order (not set/dict
  iteration), and there is no randomness anywhere in the export path.

## Slugs

- `_slugify()`: Unidecode (ASCII-fold) → lowercase → collapse anything
  that isn't `[a-z0-9]` into a single `-` → strip leading/trailing `-`.
  Never returns an empty string (falls back to `"item"`).
- Collisions are resolved with a numeric suffix — `base`, `base-2`,
  `base-3`, … — scoped **per directory**: `party/acme.md` and
  `venue/acme.md` don't collide with each other, but two parties both
  named "Acme" do. Claim slugs (conflicts, coverage gaps, risks) share one
  collision namespace across all three claim types.

## License constraint

Epistract is **MIT**; the knowledge-catalog repo (OKF spec, reference code,
sample bundles) is **Apache 2.0**. Implementing a published spec is not a
derivative work, but to keep this repo purely MIT:

- No code or prose was copied from `GoogleCloudPlatform/knowledge-catalog`.
  The spec was read (via fetch) for understanding only.
- Every fixture, example bundle, and test corpus for OKF export is
  self-authored — Google's sample bundles are never vendored into this
  repo, including in tests.
- Design language borrowed from their public writeups (e.g. "LLM-wiki") is
  used as attributed description, not copied text.

## Deferred

- **Import (OKF → epistract).** A deterministic markdown → graph import
  would yield untyped edges with no confidence or evidence — exactly the
  signal epistract's epistemic layer depends on. A quality import needs an
  LLM link-typing + enrichment pass, and ingesting arbitrary third-party
  bundles carries prompt-injection risk. Revisit once export has proven
  out in practice.
- **Bidirectional sync / living bundles.** Out of scope until one-way
  export has proven out — merge semantics and two-sources-of-truth drift
  are the highest-risk parts of this design space.

Full reasoning, value/effort/risk grid, and risk register:
[docs/plans/2026-07-14-okf-export-decision.md](plans/2026-07-14-okf-export-decision.md).

## CLI

Two equivalent entry points:

```
# Multi-project CLI — resolves a registered project by name (or nearest
# .epistract/project.json ancestor), same flag names as export_okf():
python3 -m core.cli export --format okf [--project NAME] [--out DIR] \
                            [--no-evidence] [--min-confidence F]

# core/okf_export.py directly against any project_root — no registry lookup:
python core/okf_export.py <project_root> [--out <dir>] [--no-evidence] \
                           [--min-confidence <float>] [--json]
```

`--format okf` is the only format `core.cli export` handles; other formats
(graphml, gexf, csv, sqlite, json) still go through
`core/run_sift.py export` / `/epistract:export` (see `commands/export.md`),
which operates on a bare output directory rather than a registered project.

`--min-confidence` filters non-`MENTIONED_IN` edges below the threshold out
of Relations tables (the count is reported in the summary as
`skipped_edges`); it does not remove concept files.
