# Architecture Patterns

**Domain:** Cross-domain KG extraction framework (biomedical + contracts)
**Researched:** 2026-03-29

## Recommended Architecture

Extend the existing three-layer pipeline (extraction -> validation -> graph construction) with two new architectural concepts: a **domain configuration layer** that swaps ontologies, and a **presentation layer** that adds web reports and Telegram chat on top of the graph.

### High-Level Component Map

```
                   +---------------------------+
                   |   User Interfaces          |
                   |  - Claude Code commands     |
                   |  - Web report dashboard     |
                   |  - Telegram bot             |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Query / Analysis Layer    |
                   |  - Graph search             |
                   |  - Cross-reference engine   |
                   |  - Risk detection           |
                   |  - NL query (Telegram)      |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Graph Store               |
                   |  - NetworkX (in-memory)     |
                   |  - graph_data.json (disk)   |
                   |  - communities.json         |
                   |  - claims_layer.json        |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Graph Construction        |
                   |  - sift-kg build            |
                   |  - Deduplication (SemHash)  |
                   |  - Community detection      |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Domain Validation         |
                   |  - Biomedical: RDKit etc.   |
                   |  - Contracts: obligation    |
                   |    consistency checker       |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Extraction Layer          |
                   |  - Claude agents per doc    |
                   |  - Domain-aware prompts     |
                   |  - DocumentExtraction JSON  |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Document Ingestion        |
                   |  - Kreuzberg (PDF/XLS/EML)  |
                   |  - Large file chunking      |
                   +------------+--------------+
                                |
                   +------------v--------------+
                   |   Domain Configuration      |
                   |  - domain.yaml per domain   |
                   |  - SKILL.md per domain      |
                   |  - Validation script set    |
                   +---------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | New vs Existing |
|-----------|---------------|-------------------|-----------------|
| **Domain Config** | Define entity types, relation types, extraction hints, system prompts per domain | Extraction Layer, Validation Layer, Graph Construction | NEW -- core enabler |
| **Document Ingestion** | Read PDF/XLS/EML, OCR scans, chunk text | Extraction Layer | EXISTING (Kreuzberg) -- extend for large contracts |
| **Extraction Layer** | Claude reads chunks, produces structured JSON per domain schema | Domain Config (reads schema), Document Ingestion (reads text), Graph Construction (writes JSON) | EXISTING -- parameterize by domain |
| **Domain Validation** | Domain-specific post-extraction checks | Extraction Layer (reads JSON), Graph Construction (writes enriched JSON) | EXISTING (biomedical) + NEW (contract validator) |
| **Graph Construction** | Build deduplicated NetworkX graph, detect communities | Validation Layer (reads JSON), Domain Config (reads schema) | EXISTING (sift-kg) -- no changes needed |
| **Cross-Reference Engine** | Analyze obligations across vendors, detect conflicts/gaps | Graph Store (reads graph) | NEW -- contract-specific analysis |
| **Risk Detection** | Flag contradictions, missing coverage, timeline conflicts | Cross-Reference Engine, Graph Store | NEW -- builds on epistemic analysis pattern |
| **Web Report** | Interactive filterable dashboard with drill-down | Graph Store, Cross-Reference Engine | NEW |
| **Telegram Bot** | NL query interface to graph | Graph Store, Query Layer | NEW |
| **Claude Code Commands** | User-facing slash commands | All layers (orchestration) | EXISTING -- extend with new commands |

### Data Flow

**Contract Extraction Pipeline (Scenario 7):**

```
1. /epistract-ingest --domain contracts data/ub/STA-2026/
   |
   v
2. Domain Config Resolver
   - Loads skills/contract-extraction/domain.yaml
   - Loads skills/contract-extraction/SKILL.md
   |
   v
3. Kreuzberg reads 62+ files (PDF, XLS, EML)
   - Large PDFs (12-31 MB) chunked at paragraph boundaries
   - Output: (doc_id, chunk_text) tuples
   |
   v
4. Claude Extraction Agents (1 per document, up to 4 concurrent)
   - Reads chunk + contract SKILL.md + contract domain.yaml
   - Extracts: Party, Obligation, Deadline, Cost, Clause, Venue, Service entities
   - Extracts: OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS relations
   - Output: extractions/{vendor_name}.json
   |
   v
5. Contract Validation (NEW)
   - Validates date formats, currency amounts, party name normalization
   - Cross-checks: does every Obligation have a Party and Deadline?
   - No molecular validation (skip RDKit/Biopython)
   |
   v
6. sift-kg Graph Build (UNCHANGED)
   - Reads contract domain.yaml for schema
   - Deduplicates entities (e.g., "PCC" = "Pennsylvania Convention Center")
   - Community detection groups related contracts
   |
   v
7. Cross-Reference Analysis (NEW)
   - Queries built graph for obligation overlaps
   - Detects: timeline conflicts, cost gaps, contradictory terms
   - Detects: coverage gaps (e.g., no security vendor for Sunday teardown)
   - Output: cross_references.json
   |
   v
8. Risk Report Generation (NEW)
   - Combines graph_data.json + cross_references.json
   - Generates interactive HTML dashboard
   - Output: report/index.html
   |
   v
9. Telegram Bot (NEW, optional)
   - Loads graph_data.json + cross_references.json
   - Answers NL queries via Claude with graph context
```

**Key data artifacts and their formats:**

| Artifact | Format | Producer | Consumers |
|----------|--------|----------|-----------|
| `domain.yaml` | YAML | Human-authored | Extraction agents, sift-kg, validation |
| `SKILL.md` | Markdown | Human-authored | Extraction agents |
| `extractions/*.json` | DocumentExtraction JSON | Extraction agents | Validation, graph builder |
| `graph_data.json` | sift-kg graph JSON | sift-kg build | All downstream: query, analysis, viz, Telegram |
| `communities.json` | Community labels JSON | label_communities.py | Web report, query |
| `cross_references.json` | Analysis results JSON | Cross-reference engine | Web report, Telegram, risk detection |
| `report/index.html` | Static HTML + JS | Report generator | Browser |

## Patterns to Follow

### Pattern 1: Domain Configuration as a Skill Directory

**What:** Each domain is a directory under `skills/` with a standard structure:
```
skills/
  drug-discovery-extraction/    # existing
    domain.yaml
    SKILL.md
    validation-scripts/
  contract-extraction/           # new
    domain.yaml
    SKILL.md
    validation-scripts/
```

**When:** Adding any new domain to epistract.

**Why:** The existing biomedical pipeline already uses `domain.yaml` + `SKILL.md`. Making this pattern explicit and discoverable means new domains are added by creating a directory, not by modifying core code.

**Implementation:**
```python
# Domain resolver -- new utility
def resolve_domain(domain_name: str) -> tuple[Path, Path]:
    """Return (domain_yaml_path, skill_md_path) for a named domain."""
    skills_dir = Path(__file__).parent.parent / "skills"
    domain_dir = skills_dir / f"{domain_name}-extraction"
    if not domain_dir.exists():
        raise ValueError(f"Unknown domain: {domain_name}. "
                        f"Available: {[d.name for d in skills_dir.iterdir() if d.is_dir()]}")
    return domain_dir / "domain.yaml", domain_dir / "SKILL.md"
```

**Confidence:** HIGH -- this follows the existing pattern exactly.

### Pattern 2: Domain-Specific Validation as Pluggable Scripts

**What:** Each domain's `validation-scripts/` directory contains Python scripts that run post-extraction. The biomedical domain has RDKit/Biopython validators. The contract domain would have date/currency/party normalizers.

**When:** Validation logic differs by domain (it always will).

**Why:** Keeps domain-specific logic out of the core pipeline. `validate_molecules.py` already serves this role for biomedical; the contract equivalent validates obligations, deadlines, and cost consistency.

**Confidence:** HIGH -- mirrors existing pattern.

### Pattern 3: Cross-Reference as a Post-Build Analysis Layer

**What:** Cross-reference analysis runs AFTER graph construction, querying the built graph rather than raw extractions.

**When:** Analysis requires relationships across multiple documents.

**Why:** The graph already has deduplicated entities and resolved references. Querying the graph (not raw extractions) avoids re-implementing deduplication logic. This also mirrors how epistemic analysis (`claims_layer.json`) works as a post-build overlay.

```python
# Cross-reference analysis runs on built graph
def analyze_cross_references(graph_path: Path) -> dict:
    kg = KnowledgeGraph.load(graph_path)
    conflicts = find_timeline_conflicts(kg)
    gaps = find_coverage_gaps(kg)
    cost_overlaps = find_cost_overlaps(kg)
    return {"conflicts": conflicts, "gaps": gaps, "cost_overlaps": cost_overlaps}
```

**Confidence:** HIGH -- follows the epistemic analysis precedent.

### Pattern 4: Web Report as Static HTML Generation

**What:** Generate a self-contained HTML report (HTML + embedded JS + CSS) from the graph and analysis data. No server process.

**When:** The web report needs to work offline, be shareable, and not require a running server.

**Why:** The existing visualization already uses this pattern (pyvis generates a self-contained HTML file). A static report can be opened by committee chairs without installing anything. Shared via email or Telegram as a file.

**Technology:** Use a Python template engine (Jinja2) to render HTML from graph data. Embed a JS table library (DataTables or AG Grid community) and the existing vis.js for graph visualization.

**Confidence:** MEDIUM -- static HTML works for initial version but may need a lightweight server (FastAPI) if interactive queries are needed beyond client-side filtering.

### Pattern 5: Telegram Bot as Graph Query Proxy

**What:** A Telegram bot that receives NL questions, queries the graph, and returns formatted answers. Runs as a long-lived process or webhook.

**When:** Users need mobile/on-the-go access to contract intelligence.

**Architecture:**
```
User message -> Telegram Bot API -> Bot process
  -> Claude interprets question
  -> Translates to graph query (entity search, neighborhood, path finding)
  -> Formats result as Telegram message
  -> Sends reply
```

**Why:** The user already has Telegram MCP integration. A dedicated bot process (using python-telegram-bot library) is more reliable than routing through Claude Code sessions.

**Confidence:** MEDIUM -- the existing Telegram MCP plugin handles message routing, but a standalone bot process for always-on availability is a separate concern. Start with MCP integration, consider standalone bot later.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Modifying Core sift-kg Wrapper for Domain Logic

**What:** Adding contract-specific code to `run_sift.py` or `build_extraction.py`.

**Why bad:** These files are domain-agnostic wrappers. Adding `if domain == "contracts": ...` creates coupling that breaks as domains grow. The existing `--domain` flag on `run_sift.py build` already supports loading arbitrary domain.yaml files.

**Instead:** Put all contract-specific logic in `skills/contract-extraction/` and `scripts/contract_*.py` files. The core pipeline stays clean.

### Anti-Pattern 2: Building a Full Web Application

**What:** Using React/Next.js or a SPA framework for the dashboard.

**Why bad:** Adds massive dependency surface, build tooling, and maintenance burden for what is fundamentally a reporting view. The team is Python-focused. The dashboard needs to be sharable as a file.

**Instead:** Static HTML generation via Jinja2 templates with embedded JS libraries (DataTables, vis.js). If interactivity needs grow, upgrade to a minimal FastAPI + HTMX setup, not a full SPA.

### Anti-Pattern 3: Separate Graph Store for Contracts

**What:** Using Neo4j or a different graph database alongside NetworkX.

**Why bad:** 62 contracts is small data. NetworkX handles this trivially. Adding a database server creates deployment complexity and diverges from the biomedical pipeline. The entire point is demonstrating the SAME pipeline works across domains.

**Instead:** Keep NetworkX + JSON files. If scale demands it later (thousands of contracts), migrate then.

### Anti-Pattern 4: Real-Time Extraction

**What:** Setting up file watchers or webhooks to auto-extract when new contracts arrive.

**Why bad:** Contracts change rarely. The event has a fixed set of 62+ documents. Batch processing is appropriate. Real-time adds complexity for no benefit in this use case.

**Instead:** Batch extraction triggered manually via `/epistract-ingest`.

## Component Build Order (Dependencies)

The dependency chain dictates build order:

```
Phase 1: Domain Configuration Layer
  - contract domain.yaml (entity types, relation types)
  - contract SKILL.md (extraction prompts, disambiguation rules)
  - Domain resolver utility (resolve_domain function)
  - Modify /epistract-ingest to accept --domain flag
  WHY FIRST: Everything downstream depends on the schema.
  DEPENDENCY: None (pure authoring + small utility code)

Phase 2: Document Parsing + Extraction
  - Test Kreuzberg on actual contract PDFs (12-31 MB files)
  - Run extraction on a few sample contracts
  - Contract validation scripts (date/currency/party normalization)
  WHY SECOND: Need extraction results before graph analysis.
  DEPENDENCY: Domain config (Phase 1)

Phase 3: Graph Construction + Cross-Reference Analysis
  - Build graph from contract extractions (sift-kg, unchanged)
  - Cross-reference analysis engine
  - Risk/conflict detection
  WHY THIRD: Analysis requires a built graph.
  DEPENDENCY: Extractions (Phase 2)

Phase 4: Web Report Dashboard
  - Jinja2 templates for report HTML
  - Filterable tables (by vendor, obligation type, deadline)
  - Embedded graph visualization
  - Drill-down to source contract text
  WHY FOURTH: Needs analysis results to display.
  DEPENDENCY: Cross-reference analysis (Phase 3)

Phase 5: Telegram Chat Interface
  - Bot setup and graph loading
  - NL query interpretation
  - Response formatting
  WHY LAST: Optional enhancement. Everything works without it.
  DEPENDENCY: Graph store (Phase 3), can run in parallel with Phase 4
```

### Critical Path

```
Domain Config -> Extraction -> Graph Build -> Cross-Ref Analysis -> Web Report
                                                                  \-> Telegram (parallel)
```

The domain config is the critical enabler. Without it, nothing else can begin. Extraction is the longest phase (processing 62+ documents). The web report and Telegram bot can be developed in parallel once the graph exists.

## Integration Points with Existing Codebase

### What Changes

| File/Component | Change | Risk |
|----------------|--------|------|
| `scripts/run_sift.py` | Add `--domain` flag to `cmd_build` (already partially supports it) | LOW -- additive change |
| `scripts/build_extraction.py` | Make `domain_name` field dynamic (currently hardcoded "Drug Discovery") | LOW -- one-line change |
| `/commands/*.md` | Add `--domain` parameter to ingest command | LOW -- additive |
| `skills/` directory | Add `contract-extraction/` alongside `drug-discovery-extraction/` | NONE -- no existing code touched |

### What Does NOT Change

| File/Component | Why Unchanged |
|----------------|---------------|
| `scripts/validate_molecules.py` | Only runs for biomedical domain; contract domain has its own validators |
| `scripts/label_communities.py` | Domain-agnostic community labeling works for any graph |
| `scripts/label_epistemic.py` | Epistemic analysis applies to contracts too (asserted vs. conditional clauses) |
| `skills/drug-discovery-extraction/` | Existing biomedical domain untouched |
| `agents/extractor.md` | Agent reads SKILL.md dynamically; contract SKILL.md changes its behavior |
| sift-kg library | Already accepts arbitrary domain.yaml; no patches needed |

### New Files

| File | Purpose |
|------|---------|
| `skills/contract-extraction/domain.yaml` | Contract entity/relation type definitions |
| `skills/contract-extraction/SKILL.md` | Contract extraction prompt, disambiguation rules, confidence calibration |
| `skills/contract-extraction/validation-scripts/validate_contracts.py` | Date, currency, party name validation |
| `scripts/cross_reference.py` | Post-build cross-reference analysis engine |
| `scripts/risk_detection.py` | Conflict and gap detection on top of cross-references |
| `scripts/generate_report.py` | Jinja2-based static HTML report generator |
| `templates/report/` | HTML/CSS/JS templates for the dashboard |
| `scripts/telegram_bot.py` | Telegram bot for NL graph queries |
| `commands/epistract-contracts.md` | New command: contract-specific analysis workflow |

## Scalability Considerations

| Concern | 62 contracts (current) | 500 contracts | 5,000 contracts |
|---------|------------------------|---------------|-----------------|
| Extraction time | ~2 hrs (serial) / ~30 min (4x parallel) | ~8 hrs parallel | NetworkX bottleneck; consider chunked builds |
| Graph size | ~5K nodes, ~15K edges -- trivial for NetworkX | ~40K nodes -- still fine | Consider SQLite-backed graph or Neo4j |
| Report load time | Instant (static HTML) | May need pagination | Server-side rendering required |
| Telegram query latency | <2s (in-memory graph) | <5s | Need indexed store |
| Storage | ~50 MB total | ~400 MB | ~4 GB; consider compressed storage |

For the current scope (62 contracts), all components work with simple file-based storage and in-memory processing. No infrastructure changes needed.

## Sources

- Existing codebase analysis (epistract repository, 2026-03-29)
- [sift-kg GitHub repository](https://github.com/juanceresa/sift-kg) -- document-to-KG pipeline with schema support
- Existing `run_sift.py` already accepts `--domain` flag for arbitrary domain.yaml paths
- Existing `domain.yaml` structure provides the template for contract domain schema

---

*Architecture research: 2026-03-29*
