# Codebase Structure

**Analysis Date:** 2026-03-29

## Directory Layout

```
epistract/
├── .claude/                     # Claude Code plugin metadata
│   ├── settings.local.json
│   └── skills/                  # Claude Code skills (auxiliary tools)
├── .claude-plugin/              # Plugin package metadata
│   ├── plugin.json              # Plugin name, version, description
│   └── marketplace.json
├── .planning/                   # GSD codebase analysis outputs
│   └── codebase/                # This directory
├── commands/                    # Plugin slash command definitions
│   ├── epistract-setup.md
│   ├── epistract-ingest.md
│   ├── epistract-query.md
│   ├── epistract-export.md
│   ├── epistract-view.md
│   ├── epistract-validate.md
│   ├── epistract-build.md
│   └── epistract-epistemic.md
├── agents/                      # Agent task definitions (spawned by commands)
│   ├── extractor.md             # Document extraction agent
│   └── validator.md             # Molecular validation agent
├── skills/
│   └── drug-discovery-extraction/  # Extraction skill (knowledge + schema)
│       ├── SKILL.md             # Detailed extraction instructions for Claude
│       ├── domain.yaml          # sift-kg domain schema (entity + relation types)
│       ├── references/          # Ontology reference documents
│       └── validation-scripts/  # Python validation engines
│           ├── scan_patterns.py         # Regex pattern scanning (SMILES, CAS, NCT, etc.)
│           ├── validate_smiles.py       # RDKit-based SMILES validation
│           └── validate_sequences.py    # Biopython-based sequence validation
├── scripts/                     # Python orchestration & utility scripts
│   ├── build_extraction.py      # Write extraction JSON in sift-kg DocumentExtraction format
│   ├── validate_molecules.py    # Molecular validation orchestrator (RDKit + Biopython)
│   ├── run_sift.py              # sift-kg Python API wrapper (build, view, export, search)
│   ├── label_communities.py     # Community semantic labeling (post graph-build)
│   ├── label_epistemic.py       # Epistemic analysis (Super Domain overlay)
│   └── setup.sh                 # Dependency installation (sift-kg + optional libs)
├── tests/                       # Test scenarios + test infrastructure
│   ├── test_unit.py             # Unit tests (UT-001 through UT-014)
│   ├── corpora/                 # Six drug discovery test scenarios
│   │   ├── 01_picalm_alzheimers/        # Scenario 1: PICALM + Alzheimer's
│   │   ├── 02_kras_g12c_landscape/      # Scenario 2: KRAS G12C inhibitors
│   │   ├── 03_rare_disease/             # Scenario 3: Rare disease
│   │   ├── 04_immunooncology/           # Scenario 4: Immuno-oncology
│   │   ├── 05_cardiovascular/           # Scenario 5: Cardiovascular
│   │   └── 06_glp1_landscape/           # Scenario 6: GLP-1 multi-source
│   │       ├── output/                  # Built graph artifacts
│   │       │   ├── extractions/         # Raw extraction JSONs per document
│   │       │   ├── graph_data.json      # Final deduplicated graph
│   │       │   ├── communities.json     # Community assignments + labels
│   │       │   └── claims_layer.json    # Epistemic analysis overlay
│   │       └── *.py                     # Scenario-specific corpus assembly scripts
│   └── scenarios/                       # Test execution outputs & screenshots
├── lib/                         # Third-party dependencies
│   ├── bindings/                # Language binding helpers
│   ├── tom-select/              # HTML select widget (visualization)
│   └── vis-9.1.2/               # vis.js dependency (graph rendering)
├── docs/                        # Documentation & analysis outputs
│   ├── analysis/                # Knowledge graph analysis outputs
│   │   └── screenshots/         # Test scenario screenshots
│   ├── demo/                    # Demo video & supporting materials
│   ├── diagrams/                # Architecture & flow diagrams
│   ├── plans/                   # Implementation plans & TODOs
│   └── superpowers/             # Research prototypes & extended features
├── paper/                       # Academic paper (KG construction methodology)
│   ├── main.pdf                 # Compiled paper
│   ├── figures/                 # Figure generation scripts & source
│   │   └── gen_fig*.py          # Scenario result visualizations
│   └── sections/                # LaTeX source sections
├── medium/                      # Medium.com blog post drafts
├── poster/                      # Conference poster sources
├── Makefile                     # Build targets (setup, test, lint, format, clean)
├── README.md                    # User guide & quick start
├── DEVELOPER.md                 # Technical reference & architecture detail
└── LICENSE                      # MIT license
```

## Directory Purposes

**`.claude/`**
- Purpose: Claude Code plugin runtime configuration
- Contains: Local settings, auxiliary skills for plugin lifecycle
- Key files: `settings.local.json` (user preferences)

**`.claude-plugin/`**
- Purpose: Plugin package metadata (consumed by Claude Code marketplace)
- Contains: `plugin.json` (name, version, description, keywords), `marketplace.json` (registry metadata)
- Key files: `plugin.json` defines the plugin identity; version bumped on release

**`.planning/codebase/`**
- Purpose: GSD (Goal-State-Design) codebase analysis outputs
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md
- Key files: Created by `/gsd:map-codebase` orchestrator; consumed by `/gsd:plan-phase` and `/gsd:execute-phase`

**`commands/`**
- Purpose: Define plugin slash commands (user entry points)
- Contains: Markdown files, each with frontmatter `name` and `description`, followed by task instructions
- Key files:
  - `ingest.md`: Main pipeline (document reading → extraction → validation → graph building → visualization)
  - `setup.md`: Install dependencies
  - `query.md`, `export.md`, `view.md`: Graph post-processing commands
  - `build.md`, `validate.md`, `epistemic.md`: Standalone re-run commands

**`agents/`**
- Purpose: Define agent task descriptions (spawned by commands for parallel work)
- Contains: Agent specs for Claude instances
- Key files:
  - `extractor.md`: Read document chunks, extract entities/relations in JSON format
  - `validator.md`: Validate molecular identifiers (SMILES, sequences, CAS numbers)

**`skills/drug-discovery-extraction/`**
- Purpose: Knowledge + schema for drug discovery entity extraction
- Contains: Extraction instructions, sift-kg schema, validation engines
- Key files:
  - `SKILL.md` (~43KB): Detailed prompt covering 17 entity types, 30 relation types, 40+ biomedical ontologies, naming standards, disambiguation rules, confidence calibration
  - `domain.yaml` (~19KB): sift-kg YAML schema; parsed by `load_domain()` in `run_sift.py build`
  - `validation-scripts/`: Python engines for pattern scanning, SMILES validation (RDKit), sequence validation (Biopython)

**`scripts/`**
- Purpose: Python orchestration & utility functions
- Contains: Core pipeline logic (independent of Claude Code runtime)
- Key files:
  - `build_extraction.py`: Converts Claude's JSON output to sift-kg `DocumentExtraction` format; writes to `extractions/<doc_id>.json`
  - `validate_molecules.py` (~500 LOC): Orchestrates RDKit/Biopython validation; enriches extractions with CHEMICAL_STRUCTURE/NUCLEOTIDE_SEQUENCE nodes
  - `run_sift.py`: Thin wrapper around sift-kg Python API (build, view, export, search, info commands)
  - `label_communities.py` (~200 LOC): Post-build community semantic labeling (e.g., "EGFR pathway + phosphorylation" → "EGFR Kinase Domain Mutations")
  - `label_epistemic.py` (~400 LOC): Classify relations as asserted/hypothesized/speculative/prophetic based on hedging language + document type

**`tests/`**
- Purpose: Unit tests + integration test scenarios
- Contains: Test code, six complete drug discovery KG examples, test outputs
- Key files:
  - `test_unit.py` (~300 LOC): Unit tests UT-001 through UT-014 (domain loading, pattern scanning, SMILES validation, sequence detection, extraction building, etc.)
  - `corpora/*/output/`: Example graph outputs (graph_data.json, communities.json, claims_layer.json) used for validation
  - `corpora/*/assemble_corpus.py`: Scenario-specific document corpus assembly (e.g., fetch papers from PubMed, patents from Google Patents, combine via SerpAPI)

**`lib/`**
- Purpose: Third-party JavaScript/CSS dependencies for visualization
- Contains: vis.js graph renderer, tom-select dropdown widget
- Generated: Yes (installed via npm/manual download); committed to repo for offline use

**`docs/`**
- Purpose: User-facing documentation, research outputs, planning artifacts
- Contains:
  - `analysis/`: KG analysis outputs (entity distribution, relation heatmaps) + screenshots of visualization
  - `diagrams/`: Mermaid diagrams (architecture, data flow)
  - `plans/`: Implementation plans, task tracking (YYYY-MM-DD-<feature>-TODO.md)
  - `superpowers/`: Experimental features (phase 2: Neo4j + vector RAG, graph-grounded conversational RAG)

**`paper/`**
- Purpose: Academic paper repository (KG construction methodology)
- Contains: LaTeX source, figures, compiled PDF
- Key files:
  - `main.pdf`: Published paper "Beyond RAG: Domain-Specific Agentic Architecture for Biomedical Knowledge Graph Construction"
  - `figures/gen_fig*.py`: Scripts to generate result tables/diagrams from test scenario outputs
  - `sections/`: LaTeX source files (split by section for git conflict reduction)

**`medium/`, `poster/`**
- Purpose: Supplementary materials (blog posts, conference posters)
- Contains: Markdown drafts, poster source files
- Key files: Blog posts referencing paper methodology; poster summarizing approach

## Key File Locations

**Entry Points:**

- `/.claude-plugin/plugin.json`: Plugin identity (name "epistract", version, keywords)
- `/commands/`: All user-facing slash commands (`/epistract-setup`, `/epistract-ingest`, etc.)
- `/commands/ingest.md`: Main pipeline orchestration (calls agents, scripts, sift-kg API)

**Configuration:**

- `/skills/drug-discovery-extraction/domain.yaml`: sift-kg domain schema (17 entity types, 30 relations, fallback relation)
- `/skills/drug-discovery-extraction/SKILL.md`: Extraction rules (nomenclature, disambiguation, confidence calibration, 40+ ontologies)
- `/Makefile`: Build targets (setup, test, lint, format, clean)
- `/scripts/setup.sh`: Dependency installation (sift-kg, optional RDKit/Biopython)

**Core Logic:**

- `/scripts/build_extraction.py`: Converts LLM extraction JSON to sift-kg format
- `/scripts/validate_molecules.py`: Validates SMILES/sequences, enriches with structural nodes
- `/scripts/run_sift.py`: Wraps sift-kg Python API (build, view, export, search)
- `/scripts/label_communities.py`: Auto-labels communities with semantic names
- `/scripts/label_epistemic.py`: Analyzes epistemic status (asserted/hypothesized/speculative/prophetic)

**Testing:**

- `/tests/test_unit.py`: Unit tests (pattern scanning, SMILES validation, extraction building)
- `/tests/corpora/*/output/`: Example graph outputs (used for regression testing)

**Documentation:**

- `/README.md`: User quick start guide
- `/DEVELOPER.md`: Technical reference (architecture, dependencies, domain schema, sift-kg integration)

## Naming Conventions

**Files:**

- Commands: `epistract-<action>.md` (e.g., `epistract-ingest.md`)
- Agents: `<agent_type>.md` (e.g., `extractor.md`, `validator.md`)
- Scripts: `<verb>_<noun>.py` (e.g., `build_extraction.py`, `validate_molecules.py`)
- Test corpora: `NN_<domain_name>/` (e.g., `02_kras_g12c_landscape/`)
- Tests: `test_<module>.py` (e.g., `test_unit.py`)

**Directories:**

- Plugin metadata: `.claude*` (dot-prefix for hidden system directories)
- Output artifacts: `output/` (sibling to source documents in test scenarios)
- Scripts: `*-scripts/` or just `scripts/` (flat directory per module)
- Documentation: `docs/`, `paper/`, `medium/` (flat structure; no nesting for searchability)

## Where to Add New Code

**New Feature (End-to-End):**
- Primary code: Command in `/commands/<feature>.md`; agents in `/agents/` if parallelizable; scripts in `/scripts/`
- Tests: Unit tests in `/tests/test_unit.py`; integration test scenario in `/tests/corpora/NN_<feature>/`
- Documentation: Update `/DEVELOPER.md` architecture section; add task tracking in `/docs/plans/YYYY-MM-DD-<feature>-TODO.md`

**New Component/Module:**
- Implementation: `/scripts/<name>.py` if orchestration/utility; `/agents/<name>.md` if agent task; `/skills/drug-discovery-extraction/` if schema/skill knowledge
- Testing: Add unit test in `/tests/test_unit.py` following pattern `def test_utXXX_<component>():`
- Integration: Add corpus scenario in `/tests/corpora/NN_<name>/` to validate end-to-end behavior

**New Agent-Based Command:**
- Command definition: `/commands/epistract-<action>.md` with frontmatter `name` and `description`
- Agent: `/agents/<action>.md` with task description + output format
- Orchestration: Invoke agent from command via `Agent` tool (Claude Code); handle JSON results in command

**Utilities (Shared Helpers):**
- Shared Python: `/scripts/<module>.py` if used by multiple scripts; else inline in calling script
- Shared prompts: `/skills/drug-discovery-extraction/SKILL.md` for domain knowledge; `/agents/` for repeatable agent tasks
- Shared validation: `/skills/drug-discovery-extraction/validation-scripts/` for pattern matching, molecular validation

## Special Directories

**`/tests/corpora/*/output/`**
- Purpose: Built graph artifacts for each test scenario
- Generated: Yes (via `/epistract-ingest` command run on corpus)
- Committed: Yes (enables regression testing and paper figure generation without rerunning)
- Structure:
  ```
  output/
  ├── extractions/           # Raw DocumentExtraction JSONs per document
  │   ├── pmid_*.json
  │   ├── patent_*.json
  │   └── ...
  ├── graph_data.json        # Final deduplicated graph (nodes + edges)
  ├── communities.json       # Detected communities + semantic labels
  ├── claims_layer.json      # Epistemic analysis (Super Domain overlay)
  └── index.html             # sift-kg HTML visualization (optionally committed)
  ```

**`/lib/`**
- Purpose: Third-party JavaScript/CSS for visualization
- Generated: No (checked in manually for offline availability)
- Committed: Yes (reduces external dependency on CDNs)
- Contents: vis.js graph library, tom-select widget

**`.pytest_cache/`**
- Purpose: Pytest runtime cache
- Generated: Yes (during test runs)
- Committed: No (.gitignore)

**`/docs/plans/`**
- Purpose: Implementation task tracking (persists across context switches)
- Generated: Manually via `/gsd:plan-phase` and developer updates
- Committed: Yes (tracks active work)
- Format: YYYY-MM-DD-<feature>-TODO.md with checkbox progress

---

*Structure analysis: 2026-03-29*
