# Changelog

All notable changes to epistract are documented here. This project follows [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-04-14

**Cross-Domain Knowledge Graph Framework.** The v1.0 drug-discovery / contracts codebase is refactored into a domain-agnostic framework. Plug in a domain schema (YAML + extraction prompt + epistemic rules), point at a document corpus, and get a structured two-layer knowledge graph. Ships with pre-built drug-discovery and contracts domain packages, a domain creation wizard, and an interactive web workbench.

### Highlights

- **Cross-domain framework** — `core/` (domain-agnostic pipeline) + `domains/` (pluggable packages) + `examples/` (consumer applications). The same pipeline runs against any schema. Adding a new domain requires only `domain.yaml` + `SKILL.md` + `epistemic.py`; no pipeline code changes.
- **Two pre-built domains ship with the framework:**
  - **drug-discovery** — 17 entity types, 30 relation types, molecular validation via RDKit/Biopython, patent-vs-paper epistemic classification (asserted / hypothesized / prophetic / contradictory)
  - **contracts** — 11 entity types, 11 relation types, cross-contract conflict detection, obligation gap scoring, risk indicators (ships as schema scaffold without bundled corpus — bring your own)
- **`/epistract:domain` wizard** — auto-generates a starter domain package from a sample corpus. Analyzes documents, proposes entity/relation types, writes `domain.yaml` + `SKILL.md` + `epistemic.py`.
- **`/epistract:acquire` PubMed pipeline** — search PubMed and download articles into a local corpus in one command (Chris Davidson, PR #2).
- **Interactive workbench** — FastAPI-backed three-panel UI (dashboard / chat / graph) with domain-aware persona, entity-type filter pills, natural-language chat grounded to source documents, domain-specific starter questions, and a force-directed graph canvas.
- **End-to-end V2 validation** — 6 drug-discovery scenarios re-validated through `/epistract:*` slash commands. Aggregate: **111 documents → 867 nodes, 2,592 links, 39 communities** (+10.7% nodes, +16.2% edges, +18.2% communities vs V1 baseline). All 6 pass regression at the ≥80% threshold. See `docs/showcases/drug-discovery-v2.md`.
- **Pinned regression suite** — `tests/regression/run_regression.py` compares each scenario's output against pinned V1 baselines and reports PASS/FAIL per scenario. V2 baselines written on demand via `--update-baselines`.

### Added

- `core/` — domain-agnostic pipeline engine
  - `domain_resolver.py` — loads domain packages by name or alias from `domains/`
  - `run_sift.py` — wraps sift-kg build/view/export/search/info as the plugin's Python entry point
  - `build_extraction.py` — writes extraction JSON in the `DocumentExtraction` interchange format
  - `label_epistemic.py` — dispatches epistemic analysis to the domain-specific module
  - `label_communities.py` — Louvain detection + auto-labeling
  - `domain_wizard.py` — drives `/epistract:domain` package generation
- `domains/` — pluggable domain packages
  - `drug-discovery/` — full package with 17 entity types, 30 relation types, RDKit/Biopython validation, and domain-specific epistemic rules including patent/prophetic detection
  - `contracts/` — schema scaffold (no bundled corpus) with 11 entity types, 11 relation types, and cross-contract conflict/gap/risk rules
- `examples/workbench/` — FastAPI workbench with chat (SSE streaming via Anthropic or OpenRouter), force-directed graph (vis.js), entity-type filters, source-document drill-through, and domain-configurable persona
- `examples/telegram_bot/` — Telegram chat interface backed by the same graph data
- `commands/` — 12 Claude Code slash commands: `setup`, `ingest`, `build`, `view`, `validate`, `epistemic`, `query`, `export`, `domain`, `dashboard`, `ask`, `acquire`
- `agents/` — 3 Claude Code subagents: `extractor`, `acquirer`, `validator`
- `tests/scenarios/scenario-0[1-6]-*-v2.md` — 6 per-scenario V2 reports with V1→V2 delta tables, entity/relation breakdowns, community analysis, and domain insights
- `tests/scenarios/screenshots/scenario-0[1-6]-graph-v2.png` — rendered force-directed graphs for each drug-discovery scenario
- `tests/regression/run_regression.py` + `tests/regression/compare_baselines.py` — pinned regression suite with threshold-based comparison
- `tests/baselines/v1/*.json` — 7 pinned V1 baselines (6 drug-discovery + 1 contracts) with scenario counts and epistemic thresholds
- `docs/showcases/drug-discovery-v2.md` — master V2 showcase with 6-scenario gallery, aggregate metrics, and 7 framework-level insights
- `docs/showcases/contracts.md` — cross-domain demonstration page (shared-vs-domain-specific separation table)
- `docs/screenshots/workbench-0[1-4]-*.png` — 4 live workbench screenshots (dashboard, chat welcome, graph view, epistemic query)
- `docs/diagrams/` — architecture SVGs (Mermaid-rendered)
- `docs/ADDING-DOMAINS.md` — wizard-first guide to creating new domain packages

### Changed

- **README rewritten** — framework-first pitch, three quick-start paths (pre-built domain / PubMed acquire / custom domain wizard), V2 showcase gallery, slash-command map split between full-pipeline and single-stage commands, interactive workbench section with 4 live screenshots
- **`/epistract:ingest` is the full pipeline** — reads → chunks → extracts → validates → builds graph → generates viewer in one command. Do **not** also invoke `/epistract:build` or `/epistract:view` afterward; they are only for re-running individual stages on existing output.
- **`/epistract:epistemic` is a separate command** — runs after ingest, reads `graph_data.json`, writes `claims_layer.json`. Produces contradictions, hypotheses, and (for drug-discovery patent corpora) prophetic claims.
- **Per-document parallel extraction** — one `epistract:extractor` subagent per document instead of shared-context batches. Cleaner context isolation, higher per-doc entity yield, 111 parallel subagents validated across 6 scenarios with zero failures.
- **Regression runner transition support** — `tests/regression/run_regression.py` prefers `output-v2/` when present and falls back to `output/`, allowing V1 baselines to remain pinned while V2 validation runs in parallel.
- **`scripts/launch_workbench.py`** — now parses `--domain` and passes it through to `create_app()` (was previously ignored). Boot banner reads the domain title from `load_template(domain)` instead of hardcoding "Sample Contract Analysis Workbench".
- **Workbench sidebar legend** is now data-driven from `claims_layer.json` — the Severity section only shows when the current domain emits severity-tagged claims (contracts). Drug-discovery never sees it.

### Fixed

- **`examples/workbench/server.py` `/api/dashboard` returning 500 on drug-discovery** — Pydantic's `WorkbenchTemplate.dashboard` defaults to `None`; `dict.get(k, default)` doesn't honor `default` when the value is `None`. Chained `.get("title", ...)` raised AttributeError. Fixed with `template.get("dashboard") or {}`.
- **`scripts/launch_workbench.py` silently loaded the generic template regardless of `--domain`** — launcher parsed `--port` and `--host` but never extracted `--domain` from argv and never passed it to `create_app()`. Every domain ended up running the generic fallback persona, colors, and starter questions. Fixed.
- **Severity sidebar legend visually clashed with entity-type colors** — hardcoded Critical/Warning/Info dots (red/orange/blue) looked identical to entity-type dots (Disease red, Gene orange, Document blue). Fixed by default-hiding `#severity-section` and `#severity-filter` in `index.html` and revealing them via `configureSeverityVisibility()` in `app.js` only when `/api/graph/claims` returns items with a `severity` field.
- **`/epistract:dashboard` command was a static AKKA portfolio summary** — had been repurposed during a demo session and never restored to its intended workbench launcher role. Rewrote `commands/dashboard.md` as a proper generic workbench launcher that shells out to `scripts/launch_workbench.py` with domain forwarding.
- **`tests/regression/run_regression.py._resolve_output_dir` hardcoded `scenario/output/`** — blocked V2 validation runs that wrote to `scenario/output-v2/`. Fixed with a fallback list `(output-v2, output)` for drug-discovery scenarios and a parallel fallback list for the contracts scenario.

### Security

- **`.claude/settings.local.json` purged from all 318+ commits via `git filter-repo`** — contained an OpenRouter API key (since disabled by the provider) and a Telegram bot token. The force-push cleared GitGuardian alerts on the feature branch.
- **AKKA confidential content scrubbed from 424 commits** — deleted `domains/contracts/workbench/dashboard.html` (real vendor portfolio with dollar amounts and person names), `tests/fixtures/sample_ingested/pcc_license_agreement.txt`, `tests/fixtures/sample_ingested/marriott_contract.txt`, and `docs/plans/2026-04-01-contract-kg-pipeline-TODO.md` via `filter-repo --invert-paths`. Replaced AKKA / Kannada / person-name strings across all remaining commits via `filter-repo --replace-text`.
- **`.gitignore` hardened** — `.claude/` (entire directory), `*.local.<ext>` patterns for private variants alongside public files, `sample-contracts/`, `sample-output/`, `sample-output-v2/`, `private-corpus/`.
- **Contracts domain ships as schema scaffold only** — no sample corpus, no pre-extracted graph data, no dashboard.html. Bring your own contracts to reproduce.

### Removed

- `domains/contracts/workbench/dashboard.html` — real vendor portfolio (purged from history)
- `tests/fixtures/sample_ingested/pcc_license_agreement.txt` — real contract text (purged from history)
- `tests/fixtures/sample_ingested/marriott_contract.txt` — real contract text (purged from history)
- `docs/plans/2026-04-01-contract-kg-pipeline-TODO.md` — planning doc with personal names and local file paths (purged from history)
- Hardcoded severity legend in `examples/workbench/static/index.html` — replaced with data-driven visibility controlled by `app.js`
- `package-lock.json`, stale 999.x backlog `.gitkeep` files
- `umesh-todo.md` — all items complete

### Migration Notes

- **V1 users:** The `commands/dashboard.md` slash command no longer returns a static contract portfolio summary. It now launches the interactive workbench. If you were relying on the old behavior, migrate to `/epistract:ask` or build a custom command.
- **Contract domain users:** `domains/contracts/` no longer ships with `dashboard.html` or sample fixtures. The schema, SKILL.md, references, and epistemic rules remain. To reproduce the workbench dashboard view, ship a private `dashboard.local.html` alongside the tracked files (now ignored by `.gitignore`'s `*.local.<ext>` rule).
- **OpenRouter users:** If you had `OPENROUTER_API_KEY` set in a previous `.claude/settings.local.json`, re-export it from `~/.zshrc` or an equivalent location — `.claude/` is now entirely gitignored.
- **Regression baselines:** V2 baselines are written on demand by `run_regression.py --update-baselines` to `tests/baselines/v2/`. The V2 baselines directory is gitignored (it's a generated artifact). V1 baselines in `tests/baselines/v1/` remain pinned for regression comparison.

### Known Gaps (deferred to v2.1)

- **Structural biology documents classified as `document_type: unknown`** — the drug-discovery epistemic classifier only recognizes `paper` and `patent` signatures. Structural documents like `structural_sotorasib.txt` (S2 KRAS) and `structural_nivolumab_sequence.txt` (S4 Immuno-Oncology) appear in the claims layer with `unknown` doctype. Low severity; no misclassifications occur, only the doctype breakdown in the summary is incomplete. Tracked as Phase 12 in the roadmap.

### Credits

- **Chris Davidson** — `/epistract:acquire` PubMed acquisition pipeline (PR #2)
- **Umesh Bhatt** — framework architecture, drug-discovery + contracts domains, workbench, epistemic layer, V2 validation, release engineering

---

## [1.0.0] — 2026-04-02

Initial release. Single-domain (contracts) knowledge graph extraction pipeline for event contract analysis. Served as the proof-of-concept that became the v2.0 cross-domain framework.
