# Changelog

All notable changes to epistract are documented here. This project follows [Semantic Versioning](https://semver.org/).

## [2.2.0] — 2026-04-18

**Clinical Trials Domain + External API Enrichment.** A third pre-built domain ships: `clinicaltrials` — 12 entity types and 10 relation types for ClinicalTrials.gov protocol documents, IRB submissions, clinical study reports, and trial publications. New post-build enrichment hook pulls authoritative metadata from the ClinicalTrials.gov v2 API (Trial nodes) and PubChem PUG REST (Compound nodes) when `/epistract:ingest` is invoked with `--enrich`. Non-blocking by design — API failures log counts but never abort the pipeline.

### Highlights

- **Phase 21 — CTDM-01..06 clinicaltrials domain package.** `domains/clinicaltrials/` ships with `domain.yaml` (12 entity types: Trial, Intervention, Condition, Sponsor, Investigator, Outcome, Compound, Biomarker, Cohort, Population, TrialPhase, Site; 10 relation types: tests, treats, sponsored_by, has_outcome, uses_biomarker, enrolls, investigates, targets, is_phase, co_intervention), `SKILL.md` (NCT ID capture, trial phase classification, intervention/condition disambiguation, arm/cohort structure), and `epistemic.py` (trial-phase-based confidence grading, blinding status, enrollment-size epistemic signals).
- **Post-build enrichment via `--enrich` flag (CTDM-04, CTDM-05, CTDM-06).** When `/epistract:ingest` is invoked with `--enrich` and `--domain clinicaltrials` (or aliases `clinicaltrial` / `clinical_trials`), the pipeline runs `domains/clinicaltrials/enrich.py` after graph build. Trial nodes matching `NCT\d{8}` get `ct_overall_status`, `ct_phase`, `ct_enrollment`, `ct_start_date`, `ct_completion_date`, `ct_brief_title`. Compound nodes get `pubchem_cid`, `molecular_formula`, `molecular_weight`, `canonical_smiles`, `inchi`. Results summarized in `<output_dir>/extractions/_enrichment_report.json` with per-entity-type counts and hit rates.
- **Non-blocking by contract.** Enrichment is opt-in (omit `--enrich` and the graph is unchanged). API failures (404, 429 rate limits, timeouts, JSON parse errors) log per-node counts but never raise — the pipeline continues to the viewer step regardless of enrichment success.

### Added

- `domains/clinicaltrials/domain.yaml` — 12 entity types, 10 relation types, clinical-trial nomenclature standards (NCT IDs canonical, INN for drugs, MeSH for conditions)
- `domains/clinicaltrials/SKILL.md` — extraction prompt specialized for ClinicalTrials.gov protocol documents with NCT ID directive and arm/cohort disambiguation
- `domains/clinicaltrials/epistemic.py` — trial-phase confidence grading (Phase III > Phase II > Phase I/observational), blinding status, enrollment-size signals
- `domains/clinicaltrials/enrich.py` — post-build enrichment module (286 lines) with `enrich_graph(output_dir, domain)` entry point, `_fetch_ct_gov()` / `_fetch_pubchem()` non-blocking helpers, exponential backoff on PubChem 429, and `_enrichment_report.json` output
- `--enrich` flag documented in `commands/ingest.md` Step 5.5 with domain-gate check and rate-limit notes
- **Requirements**: CTDM-01 (package), CTDM-02 (SKILL.md), CTDM-03 (epistemic.py), CTDM-04 (CT.gov v2 enrichment), CTDM-05 (PubChem PUG REST enrichment), CTDM-06 (optional non-blocking flag) registered in `.planning/REQUIREMENTS.md`

### Changed

- `.claude-plugin/plugin.json` — version `2.1.0` → `2.2.0`; description lists all three pre-built domains; keywords gain `clinical-trials`, `clinicaltrials`, `pubchem`
- `.claude-plugin/marketplace.json` — version `2.0.0` → `2.2.0` (skipped 2.1.0, which was missed); description names all three domains
- `README.md` — status callout refreshed for v2.2.0; installation section cites version 2.2.0; Pre-built Domains table adds clinicaltrials as the third row (12 entity types, 10 relation types, PDF/DOCX/HTML/TXT/75+ more, CT.gov v2 + PubChem enrichment via `--enrich`)
- `CLAUDE.md` — Project section counts three pre-built domains instead of two; Configuration and Architecture Domain Layer lists add `domains/clinicaltrials/` with 12/10 counts
- `DEVELOPER.md` — Domain Schema Reference intro corrected to list drug-discovery (17/30), contracts (9/9), clinicaltrials (12/10); pre-existing stale 23/46 claim retired
- `docs/ADDING-DOMAINS.md` — new "Domain Enrichment (Optional)" section inserted between the Manual Domain Creation section and the Testing Your Domain section, with clinicaltrials as the worked example

### Fixed

- `DEVELOPER.md` Domain Schema Reference intro — previous claim of "23 entity types and 46 relation types" for drug-discovery was stale (actual YAML: 17/30). Corrected while touching the section for the clinicaltrials addition.

### Test suite

- No new automated tests land in this documentation-refresh release. Validation is manual grep-based consistency check: every surface that lists pre-built domains names clinicaltrials with counts 12/10 and cites the `--enrich` flag.

---

## [2.1.0] — 2026-04-17

**Graph Fidelity & Extraction Pipeline Reliability.** Two reliability phases close silent-data-loss holes in the extraction pipeline. The extraction-load rate jumped from ~70% (axmp-compliance 23-doc run lost 7 documents) to ≥95%, proven end-to-end on a 24-file Bug-4 reproducer (FT-009 at 100%). The `/epistract:domain` wizard now reads PDFs correctly instead of leaking binary headers into generated schemas.

### Highlights

- **Phase 12 — FIDL-01 wizard PDF binary read fix.** `/epistract:domain` was reading PDFs as raw binary (null bytes and `%PDF-` headers leaked into the proposed schema). Wizard now routes sample reads through `sift_kg.ingest.reader.read_document` — the same reader the main ingest pipeline uses — so generated entity type names are derived from real document content.
- **Phase 13 — FIDL-02a/b/c extraction pipeline reliability.** Three-layer defense against silent extraction drop:
  - **Write-time Pydantic validation** in `core/build_extraction.py` catches malformed extractions immediately (missing `document_id`, invalid `entity_type`, schema drift). Honest `--model` / `--cost` / `EPISTRACT_MODEL` provenance threading replaces the hardcoded `claude-opus-4-6` / `0.0` fabrication.
  - **`core/normalize_extractions.py`** — new post-extraction Step 3.5 that renames variant filenames (`*_raw.json`, `*-extraction.json`), infers missing `document_id` from filename stems, dedupes same-doc variants via composite score, coerces schema drift (numeric-string confidence, missing context/evidence/attributes), and emits `_normalization_report.json`. CLI entry-point with `--fail-threshold` (default 0.95) aborts the pipeline before graph build if recovery rate is too low.
  - **`agents/extractor.md` Required-Fields enforcement** — explicit REQUIRED top-level fields block (`document_id`, `entities`, `relations`), stdin fallback for large payloads, ban on direct `Write` tool use, and a `/scripts/`→`/core/` path bug fix.
- **End-to-end acceptance loop** — `tests/test_e2e.py` adds FT-009 (24-file Bug-4 reproducer achieves ≥95% load rate through normalize → build) and FT-010 (10-file below-threshold fixture aborts with exit 1 before `graph_data.json` is written).

### Added

- `core/normalize_extractions.py` — post-extraction normalization module (334 lines) + CLI entry-point with `--fail-threshold` abort gate
- `tests/test_e2e.py` — new end-to-end regression module (FT-009 + FT-010)
- `tests/fixtures/normalization/` — 24-file Bug-4 reproducer corpus (23 logical docs post-dedupe) with variant filenames, missing `document_id` fields, schema drift, and orphan extractions
- `tests/fixtures/normalization_below_threshold/` — 10-file corpus (2 survivors + 8 unrecoverable) for the `--fail-threshold` abort gate
- `tests/fixtures/wizard/` — sample PDFs for the FIDL-01 wizard regression test
- **Requirements**: FIDL-01 (wizard PDF binary read), FIDL-02a (extractor contract enforcement), FIDL-02b (post-extraction normalization + abort gate), FIDL-02c (honest extraction provenance + write-time validation) registered in `.planning/REQUIREMENTS.md`
- **Test IDs**: UT-017..UT-030 (14 new unit tests) + FT-009, FT-010 (2 e2e tests) registered in `tests/TEST_REQUIREMENTS.md`

### Changed

- `core/build_extraction.py` — validates against `sift_kg.extract.models.DocumentExtraction` at write time; accepts `--model` / `--cost` CLI flags and `EPISTRACT_MODEL` environment variable; substitutes sift-kg defaults (`cost_usd=0.0`, `model_used=""`) on disk so direct `write → build` invocation remains sift-kg-loadable without a prior normalize pass
- `core/normalize_extractions.py` — internal `_normalize_fields` helper extended to coerce numeric-string confidence values, missing `context` / `evidence`, and missing `attributes` dictionaries
- `agents/extractor.md` — Required-Fields block enforces the JSON contract; stdin-pipe fallback for payloads exceeding Bash argv limits; corrects the `/scripts/` → `/core/` path reference
- `commands/ingest.md` — inserts Step 3.5 (normalization) between extraction dispatch and `run_sift.py build`; documents the `--fail-threshold` pass-rate gate; exports `EPISTRACT_MODEL` and threads `--model` / `--cost` into `build_extraction.py` invocations
- `core/chunk_document.py` — wizard sample reader routes through sift-kg reader (no more raw binary)
- `scripts/setup.sh` — updated for Python 3.13+ wheel support (`rdkit-pypi` → `rdkit`)
- `examples/workbench` — bypass SOCKS proxy in `httpx.AsyncClient` for enterprise proxy environments

### Fixed

- Wizard extracting null bytes and PDF/EPUB binary headers as candidate entity type names (FIDL-01)
- `sift_kg.graph.builder.load_extractions` silently dropping files with inconsistent filenames or missing `document_id` (FIDL-02a/b)
- Hardcoded `claude-opus-4-6` / `0.0` provenance in written extractions (FIDL-02c)
- UT-013 regression introduced mid-phase by the honest-null-on-disk contract; resolved by symmetric sift-kg default substitution in `write_extraction` so direct `write → build` calls remain sift-kg-loadable

### Test suite

- `.venv/bin/python -m pytest tests/test_unit.py tests/test_e2e.py` — **47 passed + 4 skipped** (RDKit/Biopython optional deps)
- Phase 13 acceptance (FT-009): 24-file reproducer flows through normalize → build at 100% pass_rate with non-empty `graph_data.json`
- Phase 13 abort gate (FT-010): below-threshold fixture aborts with exit 1, no `graph_data.json` created

---

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
- **Three-provider LLM chat panel** — workbench auto-detects credentials for **Azure AI Foundry** (standard resource endpoint OR custom gateway URL), **Anthropic direct**, or **OpenRouter**. Supports both `AZURE_FOUNDRY_*` and `ANTHROPIC_FOUNDRY_*` env var naming conventions for enterprise environments.
- **End-to-end V2 validation** — 6 drug-discovery scenarios re-validated through `/epistract:*` slash commands. Aggregate: **111 documents → 867 nodes, 2,592 links, 39 communities** (+10.7% nodes, +16.2% edges, +18.2% communities vs V1 baseline). All 6 pass regression at the ≥80% threshold. See `docs/showcases/drug-discovery-v2.md`.
- **Pinned regression suite** — `tests/regression/run_regression.py` compares each scenario's output against pinned V1 baselines and reports PASS/FAIL per scenario. V2 baselines written on demand via `--update-baselines`.
- **uv-first install with project-local `.venv`** — `scripts/setup.sh` requires uv, auto-creates `.venv` via `uv venv`, installs `sift-kg` into the project venv (not system Python), and fails loud with remediation steps if PyPI is unreachable.

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
- **Azure AI Foundry** as a third LLM provider for the workbench chat panel. Auto-detected when `AZURE_FOUNDRY_API_KEY` (or alias `ANTHROPIC_FOUNDRY_API_KEY`) is set. Supports two endpoint patterns:
  - **Standard Azure hostname** via `AZURE_FOUNDRY_RESOURCE` → `https://<resource>.services.ai.azure.com/anthropic/v1/messages`
  - **Custom gateway** via `AZURE_FOUNDRY_BASE_URL` (or alias `ANTHROPIC_FOUNDRY_BASE_URL`) for enterprise deployments behind API management, VNet-integrated private endpoints, or reverse proxies on non-standard hostnames. `/v1/messages` is auto-appended if missing.
  - Optional `AZURE_FOUNDRY_DEPLOYMENT` (or alias `ANTHROPIC_FOUNDRY_DEPLOYMENT`) — deployment/model name, defaults to `claude-sonnet-4-6`.
  - Accepts both `AZURE_FOUNDRY_*` and `ANTHROPIC_FOUNDRY_*` env var prefixes for environments that standardize naming around the provider rather than the cloud.
  - Reuses the native Anthropic streaming path (`_stream_anthropic()`) — zero new code paths, same SSE protocol. Foundry's Anthropic-compatible endpoint uses identical headers (`x-api-key`, `anthropic-version`) and request/response shapes.
- `_ensure_messages_suffix()` helper in `api_chat.py` — normalizes Foundry base URLs so `.../anthropic`, `.../anthropic/v1`, and `.../anthropic/v1/messages` all resolve to the canonical form.
- `/api/health` now reports `llm_provider` field (`azure-foundry` | `azure-foundry-custom` | `anthropic` | `openrouter` | `null`) for ops visibility.

### Changed

- **README rewritten** — framework-first pitch, three quick-start paths (pre-built domain / PubMed acquire / custom domain wizard), V2 showcase gallery, slash-command map split between full-pipeline and single-stage commands, interactive workbench section with 4 live screenshots
- **`/epistract:ingest` is the full pipeline** — reads → chunks → extracts → validates → builds graph → generates viewer in one command. Do **not** also invoke `/epistract:build` or `/epistract:view` afterward; they are only for re-running individual stages on existing output.
- **`/epistract:epistemic` is a separate command** — runs after ingest, reads `graph_data.json`, writes `claims_layer.json`. Produces contradictions, hypotheses, and (for drug-discovery patent corpora) prophetic claims.
- **Per-document parallel extraction** — one `epistract:extractor` subagent per document instead of shared-context batches. Cleaner context isolation, higher per-doc entity yield, 111 parallel subagents validated across 6 scenarios with zero failures.
- **Regression runner transition support** — `tests/regression/run_regression.py` prefers `output-v2/` when present and falls back to `output/`, allowing V1 baselines to remain pinned while V2 validation runs in parallel.
- **`scripts/launch_workbench.py`** — now parses `--domain` and passes it through to `create_app()` (was previously ignored). Boot banner reads the domain title from `load_template(domain)` instead of hardcoding "Sample Contract Analysis Workbench".
- **Workbench sidebar legend** is now data-driven from `claims_layer.json` — the Severity section only shows when the current domain emits severity-tagged claims (contracts). Drug-discovery never sees it.
- **`scripts/setup.sh` rewritten** — now requires `uv` up front (errors with install instructions if missing), auto-creates project-local `.venv` via `uv venv`, resolves Python from the venv via `BASH_SOURCE`-based project root detection (works from any cwd), and no longer falls back to plain `pip` on failure. Supports `--check` mode for non-mutating verification. Warns on Python 3.14+ (untested).
- **README Installation section** — rewritten with explicit two-step plugin install flow (`/plugin marketplace add ./` + `/plugin install epistract@epistract`), project `.venv` rationale, supported Python version range (3.11–3.13), and a Troubleshooting subsection covering the four most common failure modes (SSL proxy, missing `./` prefix, wrong-env sift-kg, Python 3.14).
- **README LLM Provider section** — documents all three providers with Azure Foundry standard + custom gateway examples, both env var naming conventions, and the fail-loud behavior on missing resource/base-URL.

### Fixed

- **`examples/workbench/server.py` `/api/dashboard` returning 500 on drug-discovery** — Pydantic's `WorkbenchTemplate.dashboard` defaults to `None`; `dict.get(k, default)` doesn't honor `default` when the value is `None`. Chained `.get("title", ...)` raised AttributeError. Fixed with `template.get("dashboard") or {}`.
- **`scripts/launch_workbench.py` silently loaded the generic template regardless of `--domain`** — launcher parsed `--port` and `--host` but never extracted `--domain` from argv and never passed it to `create_app()`. Every domain ended up running the generic fallback persona, colors, and starter questions. Fixed.
- **Severity sidebar legend visually clashed with entity-type colors** — hardcoded Critical/Warning/Info dots (red/orange/blue) looked identical to entity-type dots (Disease red, Gene orange, Document blue). Fixed by default-hiding `#severity-section` and `#severity-filter` in `index.html` and revealing them via `configureSeverityVisibility()` in `app.js` only when `/api/graph/claims` returns items with a `severity` field.
- **`/epistract:dashboard` command was a static AKKA portfolio summary** — had been repurposed during a demo session and never restored to its intended workbench launcher role. Rewrote `commands/dashboard.md` as a proper generic workbench launcher that shells out to `scripts/launch_workbench.py` with domain forwarding.
- **`tests/regression/run_regression.py._resolve_output_dir` hardcoded `scenario/output/`** — blocked V2 validation runs that wrote to `scenario/output-v2/`. Fixed with a fallback list `(output-v2, output)` for drug-discovery scenarios and a parallel fallback list for the contracts scenario.
- **`scripts/setup.sh` checked wrong module name** — line 26 did `import sift` instead of `import sift_kg`, so the script always thought `sift-kg` was missing and tried to reinstall on every run. Fixed with `import sift_kg`.
- **`scripts/setup.sh` used bare `python3`** — resolved to system Python (often 3.14) rather than the project `.venv` (3.13). Packages got installed to the wrong environment, causing "sift-kg is installed but the viewer can't find it" confusion. Fixed by explicitly using `.venv/bin/python3` after `cd PROJECT_ROOT`.
- **`scripts/setup.sh` silently fell back to plain `pip` on uv failure** — on corporate networks with SSL-inspection proxies, `uv pip install sift-kg` would fail, the error was swallowed by `2>/dev/null`, and plain `pip` installed into the wrong Python environment. Fixed by removing the pip fallback entirely — the script now exits non-zero with three remediation options (SSL cert bundle, network check, Python version) so users can see the real failure.
- **README `/plugin marketplace add .` instruction failed** — Claude Code requires the `./` prefix for local paths (a bare `.` fails with "source not found"). Fixed in the README and called out in a blockquote + troubleshooting entry.
- **README didn't document Python version range or `.venv` setup** — users cloning fresh had no idea where the venv would come from or which Python versions were supported. README now says "3.11, 3.12, or 3.13 — tested primarily on 3.13" and Step 2 explains the project-local venv flow end-to-end.

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
- **Python version:** epistract supports 3.11–3.13. If you're on 3.14, pin the venv to 3.13 with `uv venv --python 3.13` or expect `WARN: Python 3.14.x is newer than the tested range` during setup.
- **Setup script now fails loud on corporate proxies:** if `uv pip install sift-kg` can't reach PyPI through an SSL-inspection proxy, the script exits non-zero with three remediation steps instead of silently falling through to plain `pip`. Set `SSL_CERT_FILE` or `REQUESTS_CA_BUNDLE` to your corporate CA bundle and re-run.

### Known Gaps (deferred to v2.1)

- **Structural biology documents classified as `document_type: unknown`** — the drug-discovery epistemic classifier only recognizes `paper` and `patent` signatures. Structural documents like `structural_sotorasib.txt` (S2 KRAS) and `structural_nivolumab_sequence.txt` (S4 Immuno-Oncology) appear in the claims layer with `unknown` doctype. Low severity; no misclassifications occur, only the doctype breakdown in the summary is incomplete. Tracked as Phase 12 in the roadmap.

### Credits

- **Chris Davidson** — `/epistract:acquire` PubMed acquisition pipeline (PR #2)
- **Umesh Bhatt** — framework architecture, drug-discovery + contracts domains, workbench, epistemic layer, V2 validation, release engineering

---

## [1.0.0] — 2026-04-02

Initial release. Single-domain (contracts) knowledge graph extraction pipeline for event contract analysis. Served as the proof-of-concept that became the v2.0 cross-domain framework.
