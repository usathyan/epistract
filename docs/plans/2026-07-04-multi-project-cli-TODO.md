# Multi-Project CLI + KG Quality Upgrades — Roadmap

Goal: `epistract init / add / index / search / query` over named, persistent, incrementally
growable projects (datasets), plus research-backed quality upgrades to extraction, entity
resolution, retrieval, and the epistemic layer. Full review + citations in the 2026-07-04
session summary; friction points below reference the codebase audit.

## Target CLI surface

```
epistract init <name> [--domain <d>] [--dir <path>]   # create project + manifest
epistract projects list|info|delete <name>            # registry lifecycle (mirror manage_domains.py)
epistract add files <project> <paths...>              # register + hash sources into corpus
epistract add url <project> <url...>                  # fetch → corpus (reuse acquire machinery)
epistract index <project>                             # incremental: extract deltas, merge graph, refresh FTS+vector index
epistract search <project> <query> [--type] [--k]     # hybrid BM25+vector (RRF) → optional graph expansion
epistract ask <project> "<question>"                  # dual-level routing + PPR subgraph → answer
epistract export|view|epistemic <project> ...         # existing commands, project-resolved
```

Dual exposure: `[project.scripts] epistract = epistract.cli:main` (Typer) AND thin
`/epistract:*` slash commands that call the same CLI. One code path, two surfaces.

## Storage model

- Global registry: `~/.epistract/registry.json` → name → {root, domain, created_at}
- Per-project: `<root>/.epistract/project.yaml` (domain, sources w/ content hashes + timestamps)
  plus existing layout (ingested/, extractions/, graph_data.json, claims_layer.json)
- New per-project `index.db`: SQLite with FTS5 (BM25) + sqlite-vec tables over entities,
  evidence sentences, chunks; fuse with reciprocal-rank fusion in SQL. Zero-server.

## Phase 1 — Packaging + registry foundations

- [x] `core/registry.py`: create/list/resolve/delete projects (global `~/.epistract/registry.json`
      + per-project `.epistract/project.json` manifest with sha256-hashed sources)
- [x] `pyproject.toml`: `[project.scripts] epistract = cli:main` entry point (installs the `epistract`
      binary; verified via `uv pip install -e .`)
- [x] `core/cli.py` (argparse): init / add project|files|url / index / search / projects / status
- [x] Project resolution layer: `--project` flag > `EPISTRACT_PROJECT` env > cwd `.epistract/` walk-up
- [x] Slash commands: init, add-files, add-url, index, search, projects
- [ ] Replace hand-rolled `sys.argv.index()` parsing in the OLDER core scripts (run_sift, ingest_documents, ...)
- [ ] Make `domain_resolver.DOMAINS_DIR` overridable (`EPISTRACT_DOMAINS_DIR`) — align with manage_domains.py:27
- [ ] Fix version skew (plugin.json 3.2.2 vs pyproject 3.0.0 vs marketplace.json 2.0.0)
- [ ] Wire `epistract index` to also drive extraction + `run_sift build` (currently indexes corpus text
      + existing graph entities; graph build is still a separate `/epistract:build` step)

## Phase 2 — Core hygiene (unblocks "any domain" promise)

- [ ] Move contracts logic out of core: `entity_resolution.py` PROTECTED_NAMES, `ingest_documents.KNOWN_CATEGORIES`,
      `label_communities.py` hardcoded biomedical/contract label branches → domain packages
- [ ] Fix `commands/ingest.md:135` + `build.md:34` hardcoded drug-discovery domain.yaml
- [ ] Fix `commands/ask.md:62-85` hardcoded PCC contract persona → load from domain workbench template
- [ ] `commands/validate.md`: dispatch validator by active domain, not always drug-discovery
- [ ] Fix `examples/workbench/system_prompt.py:46` — reads "edges", sift-kg writes "links" (relationship count = 0)

## Phase 3 — Index + hybrid search (`epistract index` / `search`)

- [x] `core/index_db.py`: SQLite FTS5 schema; index entities (from graph) + document chunks
- [x] RRF hybrid search fusing entity + chunk BM25 lists; `--type` / project filters (`search_index`)
- [x] Content-hash manifest → `index` only re-indexes new/changed documents (delta detection)
- [x] `core/graph_retrieval.py`: personalized-PageRank graph expansion (`--expand`), HippoRAG 2 (2502.14802)
- [ ] Add sqlite-vec vector column for semantic recall (currently BM25-only; RRF already fuses two lists)
- [ ] Graph merge without full rebuild: match-before-insert against existing graph
      (iText2KG pattern, arXiv 2409.03284; LightRAG union-merge, 2410.05779)

## Phase 4 — Retrieval quality (chat/ask upgrade)

- [x] Personalized PageRank retrieval: `core/graph_retrieval.py`, seeded from hybrid search hits,
      exposed via `epistract search --expand` (HippoRAG 2, arXiv 2502.14802)
- [ ] Dual-level query routing: one cheap LLM call → low-level (entity) + high-level (theme)
      keywords (LightRAG, 2410.05779)
- [ ] Lazy query-time community/claim summarization under token budget — never pre-summarize
      at ingest (LazyGraphRAG, MSR 2024/2025)

## Phase 5 — Extraction + graph quality

- [x] LLM-as-judge triple gate: `core/triple_judge.py` — judges each triple against its evidence
      span, stores verdict/score/gated on edge; lexical fallback + injectable LLM judge
      (GraphJudge 2411.17388, GraphEval 2407.10793). Exposed via `epistract enhance --judge`.
- [x] Two-stage entity resolution: `core/entity_resolution_v2.py` — type blocking → char/token/
      embedding similarity → borderline-only verify_fn hook (ComEM 2405.16884, BoostER 2401.03426).
      Exposed via `epistract enhance --resolve`.
- [ ] MINE-style coverage regression: sample ~10 atomic facts/doc at ingest, assert KG entails ≥X%
      (KGGen 2502.09956); report hallucination/omission rates (2502.05239)
- [ ] Add sqlite-vec / sentence-transformer embeddings to make the ER embed_fn + search vector path live

## Phase 6 — Epistemic layer v2 ("Super Domain")

- [x] Bi-temporal edges: `core/epistemic_temporal.py` — valid_at/invalid_at/superseded_by;
      contradicting newer edge invalidates (never deletes) the older, with provenance
      (Graphiti/Zep, arXiv 2501.13956). Exposed via `epistract enhance --epistemic`.
- [x] Contradiction cascade: lexical antonym-relation + negation-polarity detection with an
      injectable `adjudicate_fn` for NLI/LLM on the flagged set (LegalWiz 2510.03418,
      ContraCrow/PaperQA2 2409.13740). NLI model hookup still TODO.
- [x] Graded hedge score: `core/hedging.py` — weighted cue density + certainty discount +
      injectable classifier, replaces binary regex (2405.13319, UnScientify)
- [ ] "Nanopub-lite" claim record: assertion + provenance + epistemic status + supporting/conflicting
      evidence lists (RDF-star/nanopublications, 2606.15246)
- [ ] Wire domain-specific `_ANTONYM_RELATIONS` from each domain.yaml instead of the built-in set

## Phase 7 — Domain wizard upgrade

- [ ] Schema-induction bootstrap: open-extract sample corpus → conceptualize into candidate
      types → embedding-canonicalize definitions into proposed domain.yaml
      (AutoSchemaKG 2505.23628, EDC 2404.03868)

## Open decisions (owner input)

1. Registry home: `~/.epistract/` global registry vs repo-local `.epistract/` only (portability vs discoverability)
2. Standalone pip CLI + thin slash commands (recommended) vs slash-command-only
3. sqlite-vec now vs LanceDB from the start (sqlite-vec fine to ~1M vectors; LanceDB if larger)
