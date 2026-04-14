# Epistract

**Turn any document corpus into a structured knowledge graph.**

Epistract is a domain-agnostic knowledge graph framework that runs as a [Claude Code](https://claude.ai/claude-code) plugin. Point it at a folder of documents, specify a domain schema, and it builds a two-layer knowledge graph: brute-force entity/relation extraction grounded to domain ontologies, then domain-specific epistemic analysis that surfaces conflicts, gaps, risks, and confidence levels across your corpus.

Ship with a pre-built domain, create your own with the domain wizard, or acquire a fresh corpus from PubMed in one command.

> **v2.0 status (2026-04-13):** All 6 drug-discovery scenarios and the contracts scenario have been re-validated end-to-end through the V2 plugin pipeline. Regression suite passes against V1 baselines. See [V2 Showcase](docs/showcases/drug-discovery-v2.md).

## The Name

From Greek **episteme** (ἐπιστήμη) — structured scientific knowledge, the highest form of knowledge in Aristotle's epistemological hierarchy — combined with **extract**. Episteme is not opinion or belief; it is knowledge grounded in evidence, demonstration, and systematic understanding. That is what this tool produces: not a bag of keywords, but a structured representation of how concepts relate to each other, traceable back to the source text.

## Quick Start

Requires [Claude Code](https://claude.ai/claude-code) and Python 3.11+.

### Path A: Use a Pre-Built Domain

Three commands to your first graph:

```
/epistract:setup
```

Install the framework and dependencies.

```
/epistract:ingest ./my-papers/ --output ./graph-output --domain drug-discovery
```

Parse documents and extract entities/relations using the drug discovery schema. This single command runs the full pipeline — read → chunk → extract → validate → build graph → generate viewer. You do **not** need to separately invoke `/epistract:build`, `/epistract:validate`, or `/epistract:view` after a fresh ingest.

```
/epistract:epistemic ./graph-output
```

Run domain-specific epistemic analysis — produces `claims_layer.json` with contradictions, hypotheses, prophetic claims (from patents), and contested findings.

Then open the interactive viewer:

```
/epistract:view ./graph-output
```

### Path B: Acquire a Corpus from PubMed First

New in v2 — fetch articles directly from PubMed and ingest in two commands:

```
/epistract:acquire "PICALM Alzheimer disease" --output ./my-papers/ --max 20
/epistract:ingest ./my-papers/ --output ./graph-output --domain drug-discovery
```

`/epistract:acquire` uses NCBI E-utilities to search PubMed, download abstracts, and write them as plain-text files that `/epistract:ingest` can consume without modification. An NCBI API key improves rate limits. See [`commands/acquire.md`](commands/acquire.md) for full options.

### Path C: Create Your Own Domain

Five steps from zero to a custom knowledge graph:

1. **Install** — `/epistract:setup`
2. **Create domain** — `/epistract:domain --input ./sample-docs/` — the wizard analyzes your documents, proposes entity types, relation types, and epistemic rules, and generates a full domain package (`domain.yaml` + `SKILL.md` + `epistemic.py`)
3. **Review** — confirm the generated domain configuration; edit type definitions or naming standards if needed
4. **Ingest** — `/epistract:ingest ./corpus/ --output ./graph-output --domain your-domain`
5. **Explore** — `/epistract:view ./graph-output`

See [Adding New Domains](docs/ADDING-DOMAINS.md) for the wizard-first guide and [the domain developer guide](docs/DEVELOPER.md) if it exists for a deeper walkthrough.

## How It Works

Epistract builds knowledge graphs in two layers. The first layer extracts brute facts — entities and relations pulled from documents by LLM agents, constrained by a domain schema grounded in established ontologies. The second layer applies epistemic analysis — domain-specific rules that detect what is asserted versus hypothesized, what contradicts across documents, what is missing, and where risks lie.

![Architecture](docs/diagrams/architecture.svg)

### Two-Layer Knowledge Graph

- **Layer 1 — Brute Facts:** Entities and relations extracted from documents via LLM agents, constrained by domain schema. Each entity is typed and grounded to domain standards. Each relation carries a confidence score and evidence passage.
- **Layer 2 — Epistemic Analysis:** Domain-specific rules detect conflicts, gaps, confidence levels, and risks across the graph. The epistemic machinery is the same regardless of domain — only the rules change. Drug discovery rules classify relations as *asserted* / *hypothesized* / *prophetic* (patent-sourced forward claims) and flag cross-document contradictions. Contract rules detect cross-contract conflicts, obligation gaps, and risk indicators.

### Domain Pluggability

New domains are added by creating a configuration package:

- `domain.yaml` — entity types, relation types, naming standards, canonical names
- `SKILL.md` — extraction prompt with domain expertise
- `epistemic.py` — rules for conflict detection, gap analysis, risk scoring

No pipeline code changes required. Use the wizard (`/epistract:domain`) to auto-generate all three from a sample corpus, or create them manually. The domain resolver (`core/domain_resolver.py`) loads packages by name or alias from `domains/`.

### Plugin Command Anatomy

Slash commands split into two groups — **full-pipeline commands** that do everything needed for a scenario, and **single-stage re-run commands** that operate on existing output. For a fresh scenario you only need two commands: `/epistract:ingest` and `/epistract:epistemic`.

| Slash command | Runs | When to use |
|---|---|---|
| `/epistract:ingest <docs> --output <dir> --domain <name>` | read → chunk → extract → validate → build → viewer | **Fresh scenario run** — start here |
| `/epistract:epistemic <dir>` | Epistemic classification → `claims_layer.json` | After every fresh `ingest` — separate because it reads the built graph |
| `/epistract:build <dir>` | Graph build only | Re-running the builder on existing extractions |
| `/epistract:view <dir>` | `graph.html` generation only | Re-generating the viewer |
| `/epistract:validate <dir>` | Molecular validation only | Re-running SMILES/sequence validation |
| `/epistract:query <dir> <query>` | Entity search | Post-run exploration |
| `/epistract:export <dir> <format>` | GraphML / GEXF / CSV / SQLite export | Post-run data handoff |
| `/epistract:acquire <query> --output <dir>` | PubMed search + download | Fetching a fresh corpus (see Path B) |
| `/epistract:domain --input <samples>` | Domain wizard | Creating a new domain package (Path C) |
| `/epistract:dashboard` | Web workbench | Interactive chat + graph exploration |
| `/epistract:ask <question>` | Natural-language Q&A | Ask the graph questions directly |
| `/epistract:setup` | Dependency installer | First-time setup, re-run after upgrades |

## Pre-built Domains

| Domain | Entity Types | Relation Types | Document Formats | Description |
|--------|-------------|----------------|------------------|-------------|
| drug-discovery | 17 | 30 | PDF, DOCX, HTML, TXT, 75+ more | Biomedical literature analysis with molecular validation, patent epistemic classification, and integration with RDKit / Biopython |
| contracts | 11 | 11 | PDF, XLS, EML, 75+ more | Event/vendor contract analysis with cross-contract conflict detection, obligation gap scoring, and risk indicators |

Both domains live in `domains/` as self-contained packages. Inspect `domains/drug-discovery/domain.yaml` and `domains/contracts/domain.yaml` to see how schemas are declared.

## Showcase

### Drug Discovery Literature Analysis

Epistract was evaluated across six drug discovery research scenarios spanning genetic target validation (PICALM/Alzheimer's), competitive intelligence (KRAS G12C), due diligence (rare disease), combinations (immuno-oncology), cardiology, and patent-heavy CI (GLP-1). The v2.0 framework re-ran all six scenarios end-to-end through `/epistract:*` slash commands in April 2026 and passed regression against pinned V1 baselines (≥80% of V1 node/edge counts on all six).

![GLP-1 Competitive Intelligence V2 Knowledge Graph](tests/scenarios/screenshots/scenario-06-graph-v2.png)

*Scenario 6 — GLP-1 Competitive Intelligence. 193 nodes, 619 links, 9 communities built from 34 documents (24 PubMed abstracts + 10 patents). The largest V2 scenario and the only one to produce prophetic epistemic claims from patent forward-looking language.*

**Aggregate V2 results (2026-04-13):** 111 documents → 867 nodes, 2,592 links, 39 communities — **+10.7% nodes, +16.2% edges, +18.2% communities over V1 aggregate totals.**

| # | Scenario | Focus | Docs | V2 Nodes | V2 Edges | V2 Communities | Status |
|---|---|---|---:|---:|---:|---:|:---:|
| 1 | PICALM / Alzheimer's | Target validation | 15 | 183 | 478 | 7 | ✅ PASS |
| 2 | KRAS G12C Landscape | Competitive intelligence | 16 | 140 | 432 | 5 | ✅ PASS |
| 3 | Rare Disease Therapeutics | Due diligence | 15 | 110 | 278 | 5 | ✅ PASS |
| 4 | Immuno-Oncology Combinations | Checkpoint + validator enrichment | 16 | 151 | 440 | 5 | ✅ PASS |
| 5 | Cardiovascular & Inflammation | Cardiology + autoimmune | 15 | 90 | 245 | 4 | ✅ PASS |
| 6 | GLP-1 Competitive Intelligence | Patents + papers multi-source | 34 | 193 | 619 | 9 | ✅ PASS |

#### Scenario Gallery

<table>
<tr>
<td width="33%"><a href="tests/scenarios/scenario-01-picalm-alzheimers-v2.md"><img src="tests/scenarios/screenshots/scenario-01-graph-v2.png" alt="S1 PICALM/Alzheimer's"/></a><br/><sub><b>S1:</b> PICALM / Alzheimer's — 183/478/7</sub></td>
<td width="33%"><a href="tests/scenarios/scenario-02-kras-g12c-landscape-v2.md"><img src="tests/scenarios/screenshots/scenario-02-graph-v2.png" alt="S2 KRAS G12C"/></a><br/><sub><b>S2:</b> KRAS G12C Landscape — 140/432/5</sub></td>
<td width="33%"><a href="tests/scenarios/scenario-03-rare-disease-v2.md"><img src="tests/scenarios/screenshots/scenario-03-graph-v2.png" alt="S3 Rare Disease"/></a><br/><sub><b>S3:</b> Rare Disease Therapeutics — 110/278/5</sub></td>
</tr>
<tr>
<td width="33%"><a href="tests/scenarios/scenario-04-immunooncology-v2.md"><img src="tests/scenarios/screenshots/scenario-04-graph-v2.png" alt="S4 Immuno-Oncology"/></a><br/><sub><b>S4:</b> Immuno-Oncology Combinations — 151/440/5</sub></td>
<td width="33%"><a href="tests/scenarios/scenario-05-cardiovascular-v2.md"><img src="tests/scenarios/screenshots/scenario-05-graph-v2.png" alt="S5 Cardiovascular"/></a><br/><sub><b>S5:</b> Cardiovascular & Inflammation — 90/245/4</sub></td>
<td width="33%"><a href="tests/scenarios/scenario-06-glp1-landscape-v2.md"><img src="tests/scenarios/screenshots/scenario-06-graph-v2.png" alt="S6 GLP-1"/></a><br/><sub><b>S6:</b> GLP-1 Competitive Intelligence — 193/619/9</sub></td>
</tr>
</table>

Each thumbnail links to its per-scenario V2 report with community breakdown, entity/relation type distribution, V1→V2 delta, and domain-specific insights.

**V2 uncovered new findings that V1 missed:**

- **S1** — V2 found a **7th community** (Clathrin-Mediated Endocytosis: FCHO1, BIN1, DNM2) that V1 merged into the autophagy cluster. V2 also flagged **1 epistemic contradiction** on SORL1 between Karch 2015 and Chouraki 2014 — a real framing difference that deserves human review.
- **S2** — V2 split V1's coarse "adagrasib/ICI" community into a dedicated **PD-1 Checkpoint Blockade** cluster and a **Scribble/Hippo Pathway** cluster capturing adaptive YAP/TAZ-mediated resistance biology. +41% edges driven by richer `CONFERS_RESISTANCE_TO` and `HAS_MECHANISM` relations.
- **S3** — New standalone **Hepatocyte Gene Transfer** community cleanly factors out AAV-delivered gene therapy (valoctocogene roxaparvovec) from the PKU enzyme replacement cluster. **2 hypotheses** flagged — highest of any V2 scenario.
- **S4** — **First scenario with validator enrichment**: RDKit/Biopython auto-added 11 entities and 11 relations from nivolumab sequence data. Surfaced a new `PEPTIDE_SEQUENCE` entity type. **32 clinical trials** extracted — the most of any V2 scenario.
- **S5** — V2 merged V1's two cardiac myosin clusters into a unified **Heart Failure — Cardiac Myosin, CYP2C19, CYP3A4** community, surfacing the CYP metabolism dimension that V1 buried. Tightest V2/V1 delta but still passing.
- **S6** — **First V2 scenario with prophetic epistemic claims** — the domain's epistemic layer correctly classified **15 forward-looking patent claims** ("the compounds of the invention are useful for treating obesity") across 10 GLP-1 patents from Novo Nordisk, Eli Lilly, Pfizer, and Zealand Pharma. New **Substance Use Disorder** community captures GLP-1's emerging use in alcohol and opioid addiction — a 2024-2025 finding not present in V1.

**Broader observations from the V2 run:**

1. **Per-document parallelism scales cleanly.** V2 dispatches one `epistract:extractor` subagent per document instead of V1's shared-context batches. This produced higher raw entity yield per document (17-23 avg vs V1's 15-20) and let the drug-discovery domain SKILL.md flow through each agent in isolation. 34 parallel subagents completed successfully for S6 with zero failures.
2. **Canonical naming does the heavy lifting on dedup.** 354 raw entities → 183 graph nodes on S1 (48% collapse) is almost entirely driven by `domain_canonical_entities` during `build_graph` postprocess. Without the canonical map, V2 would produce 2-3× too many nodes.
3. **Competitive-intelligence corpora exercise the schema more comprehensively.** S2 used 20 distinct relation types (vs S1's 11) because every KRAS paper mentions drugs, trials, resistance, and approvals. Genetics corpora (S1) and rare disease corpora (S3) use fewer relation types but more entities per type.
4. **The epistemic layer discriminates document types.** S6 classified 595 relations as *asserted* (paper-sourced), 15 as *prophetic* (patent-sourced forward claims), and 5 as *hypothesized* (hedged language in either source). Same layer, different rules per doctype.
5. **V2 community factorization is finer.** All 6 scenarios produced either more communities than V1 (S1 +1, S2 +1, S3 +1) or the same count with different boundaries (S4, S5, S6). None produced fewer *and* coarser. The extra density from per-document agents tightens intra-community cohesion, letting Louvain draw cleaner partitions.
6. **Validator enrichment is latent until real molecular data appears.** S1/S2/S3 had `entities_added: 0` because their corpora were genetics/CI with no real SMILES or sequences. S4 (nivolumab) and S6 (GLP-1 patents) triggered RDKit/Biopython enrichment for the first time, auto-adding 4-11 entities per scenario with computed molecular properties.
7. **Regression thresholds (≥80% of V1) caught no regressions.** V2 exceeded V1 on 4 of 6 scenarios and matched it on the other 2. The tight margins on S5 (96% nodes, 99.6% edges) and S6 (94% nodes, 98% edges) reflect cleaner partitioning, not degraded extraction.

[Read the full V2 evaluation →](docs/showcases/drug-discovery-v2.md) · [Original V1 evaluation →](docs/showcases/drug-discovery.md)

### Event Contract Management

Applied to a corpus of 62 event planning contracts across multiple formats (PDF, XLS, EML). Extraction produced 341 nodes across 11 entity types and 663 edges across 11 relation types. The epistemic analysis layer detected 53 cross-contract conflicts, identified scheduling gaps, and scored vendor obligation risks — enabling event organizers to spot issues across a complex multi-vendor landscape before they become operational problems.

The contracts domain demonstrates that epistract is truly cross-domain: the same pipeline, different schema, different epistemic rules. The drug-discovery and contracts domains share zero extraction or build code — only the configuration differs.

[Read the full contracts evaluation →](docs/showcases/contracts.md)

> **Note on the contracts corpus:** The evaluation above used a private corpus for initial validation. This public branch does not include contract documents — the `contracts` domain package (`domains/contracts/`) ships with schema, SKILL.md, and epistemic rules, but no sample corpus. Bring your own contracts to reproduce the results.

## Commands Reference

| Command | Description |
|---------|-------------|
| `/epistract:setup` | Install framework and dependencies (idempotent) |
| `/epistract:acquire <query>` | Search PubMed and download articles into a local corpus (NCBI E-utilities) |
| `/epistract:ingest <docs>` | Full pipeline: parse documents, extract entities/relations, validate, build graph, generate viewer |
| `/epistract:epistemic <dir>` | Run epistemic analysis (conflicts, hypotheses, prophetic claims, risks) on an existing graph |
| `/epistract:build <dir>` | Rebuild graph from existing extractions (skip extraction step) |
| `/epistract:view <dir>` | Re-generate interactive graph visualization |
| `/epistract:validate <dir>` | Re-run molecular validation (RDKit, Biopython) on extractions |
| `/epistract:query <dir> <query>` | Search and filter entities in the knowledge graph |
| `/epistract:export <dir> <format>` | Export graph to GraphML, GEXF, CSV, SQLite, or JSON |
| `/epistract:domain --input <samples>` | Create a new domain via the interactive wizard |
| `/epistract:dashboard` | Launch the interactive web dashboard (chat + graph panels) |
| `/epistract:ask` | Chat with your knowledge graph via natural language |

## Contributing / Development

### Setup

```bash
git clone https://github.com/usathyan/epistract.git
cd epistract
uv pip install -e ".[dev]"
```

### Testing

```bash
make test            # unit tests
make test-integ      # integration tests
make regression      # scenario regression (V2 baselines in tests/baselines/v2/)
```

The regression runner (`tests/regression/run_regression.py`) compares each scenario's `output-v2/` against pinned baselines and reports PASS/FAIL per scenario. Fresh V2 baselines can be written with `--update-baselines`.

### Project Structure

```
core/                  # Domain-agnostic pipeline engine
  domain_resolver.py   # Loads domain packages by name
  run_sift.py          # Wraps sift-kg build/view/export/search/info
  build_extraction.py  # Writes extraction JSON (LLM → sift-kg interchange format)
  label_epistemic.py   # Dispatches epistemic analysis per domain
  label_communities.py # Louvain detection + auto-labeling
domains/               # Pluggable domain configurations
  drug-discovery/      # 17 entity types, 30 relation types, molecular validation
  contracts/           # 11 entity types, 11 relation types, conflict detection
examples/              # Consumer applications
  workbench/           # FastAPI dashboard with chat + graph panels
  telegram_bot/        # Telegram chat interface
commands/              # Claude Code slash commands
agents/                # Agent prompts (extractor, acquirer, validator)
tests/                 # Test suite + baselines + regression runner
  corpora/             # Drug-discovery test scenarios (6 scenarios)
  baselines/v1/        # V1 pinned baselines (regression targets)
  baselines/v2/        # V2 baselines (written by --update-baselines)
  scenarios/           # Per-scenario V1 and V2 reports
  regression/          # Regression runner + baseline comparator
docs/                  # Documentation and diagrams
  showcases/           # V1 and V2 showcase pages (drug-discovery, contracts)
  diagrams/            # Architecture SVGs
```

See [CLAUDE.md](CLAUDE.md) for AI-assisted development conventions.

## Technical Documentation

- **[Adding Domains](docs/ADDING-DOMAINS.md)** — Wizard-first guide to creating new domain packages
- **[Drug Discovery Showcase (V2)](docs/showcases/drug-discovery-v2.md)** — Full V2 evaluation across 6 scenarios with per-scenario reports, delta analysis, and epistemic findings
- **[Drug Discovery Showcase (V1)](docs/showcases/drug-discovery.md)** — Original V1 evaluation (preserved as regression baseline)
- **[Contracts Showcase](docs/showcases/contracts.md)** — Cross-domain validation on event planning contracts
- **[Architecture Diagrams](docs/diagrams/)** — Framework architecture, data flow, and domain package anatomy
- **[Test Scenarios](tests/MANUAL_TEST_SCENARIOS.md)** — 6 drug discovery scenarios with curated corpora
- **[Per-scenario V2 reports](tests/scenarios/)** — Detailed per-scenario findings, community breakdowns, and insights

## License

MIT
