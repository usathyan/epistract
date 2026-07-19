# Decision: OKF (Open Knowledge Format) Export Support

**Date:** 2026-07-14
**Status:** Approved — export only; import deferred
**Spec:** https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md (v0.1)
**Blog:** https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing

## Summary

Epistract will export knowledge graphs as OKF bundles — directories of markdown
concept files with YAML frontmatter, where file paths are concept IDs and
markdown links form an untyped graph. OKF is Google's formalization of the
"LLM-wiki" pattern: knowledge published for consumption by AI agents and humans
alike, git-versionable, tool-agnostic.

OKF is a *publication surface*, not a new internal model. `graph_data.json`
remains the source of truth.

## Scope decision

- **Export (epistract → OKF): BUILD NOW.** One implementation unlocks:
  publishable/browsable knowledge bases, agent context feeds (progressive
  disclosure via index.md), GCP Knowledge Catalog ingestion, PR-reviewable
  knowledge deliverables, and git-native temporal audit.
- **Import (OKF → epistract): DEFERRED.** Deterministic import yields a
  low-quality graph (untyped edges, no confidence/evidence) that would pollute
  epistemic analysis. The valuable version requires an LLM link-typing +
  enrichment pass and carries prompt-injection risk from untrusted bundles.
  Revisit after export proves out. The sidecar (below) keeps future import of
  our own bundles lossless.
- **Bidirectional sync / living bundles: OUT OF SCOPE** until one-way flows
  prove out (highest-risk scenarios: merge semantics, two-sources-of-truth
  drift).

## License constraint (hard requirement)

Epistract is MIT. The knowledge-catalog repo (spec, reference code, sample
bundles) is **Apache 2.0**. Implementing a spec is not a derivative work of the
spec, so an MIT-licensed implementation is clean — but to keep the repo purely
MIT:

- **No code or text vendored** from GoogleCloudPlatform/knowledge-catalog.
- Reference code may be read for understanding only; write original code.
- **Test fixtures are self-authored** (do not commit Google's sample bundles).
- Agent prompts from their repo: design insight only, never copied verbatim.

## Mapping design

Bundle written to `<project_root>/okf/` by default (`core/okf_export.py`).

| Epistract | OKF |
|---|---|
| Node id `party:acme` | File `<type-slug>/<name-slug>.md`; original id preserved as `epistract_id` frontmatter key |
| `entity_type` | Frontmatter `type`; also the directory (stable IDs — types don't churn, communities do) |
| `name` / `context` | `title` / `description` |
| `attributes{}` | `# Attributes` body table |
| Typed relations | `# Relations` body table: markdown link per target + relation_type, confidence, epistemic_status, evidence excerpt |
| `confidence`, `source_documents` | Extension frontmatter keys (`epistract_confidence`, `epistract_source_documents`) — spec requires consumers to preserve unknown keys |
| `epistemic_status` | Extension key per relation **and** expressed via `tags`/prose so generic consumers and LLMs still see it |
| `community` | `tags` + grouped sections in `index.md` (never directories) |
| DOCUMENT nodes | `sources/<slug>.md` concepts, `resource:` = corpus path/origin |
| `MENTIONED_IN` edges | `# Citations` sections (not relations) |
| `claims_layer.json` conflicts/gaps/risks | `claims/` concept docs |
| Bi-temporal `superseded` edges (`invalid_at`) | `log.md` deprecation entries |
| Full-fidelity graph | **Sidecar:** copy of `graph_data.json` (+ `claims_layer.json`) at bundle root; non-`.md` files are ignored by OKF consumers |

Conventions: slugs via Unidecode + kebab-case with collision suffixes;
per-directory `index.md` with descriptions; timestamps from graph metadata (not
wall clock) for deterministic output.

**Redaction (risk R3):** `--no-evidence` / `include_evidence=False` strips
evidence text and mention excerpts — required before publishing bundles from
confidential corpora (contracts domain embeds verbatim contract text in
evidence).

## Use-case value/effort/risk grid

| Scenario | Value | Effort | Risk | Verdict |
|---|---|---|---|---|
| Publishable knowledge base | High | Low | Low | Build |
| Agent context feed (LLM-wiki) | Very high | Low | Low | Build |
| GCP Knowledge Catalog ingestion | Medium | Low | Medium | Free rider |
| PR-reviewable knowledge deliverable | High | Low | Medium | Build |
| Git temporal audit | Medium | Low | Low | Free rider |
| Epistemic audit of foreign bundles | Very high | Med-High | Medium | Deferred (import) |
| Prior-knowledge seeding | High | Medium | Medium | Deferred (import) |
| Bundle-as-corpus | Medium | Trivial | Low | Deferred (import) |
| Human curation loop | High | High | High | Out of scope |
| Living bundle sync | High | High | High | Out of scope |
| Knowledge CI | Medium | Low | Low | Follow-on |

## Risk register (export-relevant)

| # | Risk | Mitigation |
|---|---|---|
| R1 | Spec churn / abandonment (v0.1, weeks old) | Isolate in `core/okf_export.py`; sidecar keeps native format authoritative |
| R3 | Confidential data leakage in published bundles | Evidence redaction flag; export is local-only; publishing is a separate act |
| R5 | Entity-ID instability (entity resolution renames) | Stable slugs from names; `epistract_id` key; revisit aliases if needed |
| R6 | Scale (10k entities → 10k files) | Type-sharded dirs; `--min-confidence` filter |
| R8 | Extension keys invisible to other consumers | Also express epistemic status via `tags` + prose |
| R9 | Mapping drift as data model evolves | This doc + conformance tests |

(R2 prompt-injection applies to import only — removed from scope with this decision.)

## TODO

- [ ] `core/okf_export.py` — graph_data.json (+ claims_layer.json, communities) → bundle tree
- [ ] CLI wiring: `epistract export --format okf` in `core/cli.py` (+ update export command doc if present)
- [ ] Self-authored test fixtures + `tests/test_okf_export.py` (conformance, link integrity, redaction, collisions, sidecar)
- [ ] `docs/OKF-MAPPING.md` — mapping conventions + extension-key registry
- [ ] Review + verify + lint/test pass
- [ ] Later: deterministic import, LLM link-typing import, knowledge CI
