<!-- GSD:project-start source:PROJECT.md -->
## Project

**Epistract Cross-Domain Knowledge Graph Framework**

Epistract evolves from a biomedical-specific literature extraction tool into a **cross-domain knowledge graph framework** with a pluggable domain configuration system. The first cross-domain application (Scenario 7) extracts structured knowledge from 62+ Sample 2026 event contracts (PDFs, XLS, emails) to build an interactive analysis dashboard and Telegram-connected chat interface for event planning intelligence.

**Core Value:** **Contracts are the source of truth.** Every obligation, deadline, cost, and party relationship across 62+ vendor contracts must be extractable, queryable, and cross-referenced — so event organizers can spot conflicts, gaps, and risks before they become problems on-site at the Pennsylvania Convention Center.

### Constraints

- **Tech stack**: Python 3.11+, uv for package management, existing epistract architecture
- **Contract formats**: Primarily PDF (60 files), 1 XLS, 1 EML — need robust document parsing
- **Large files**: Some contracts are 12-31 MB PDFs — extraction must handle large documents
- **Telegram**: Bot API integration for chat interface, existing MCP server available
- **Timeline**: Event is Sep 4-6, 2026 — contract analysis should be actionable well before event
- **Existing codebase**: Must preserve backward compatibility with biomedical scenarios
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.11+ - Core runtime for knowledge graph building, molecular validation, plugin integration
- Bash - Setup and utility scripts
- YAML - Domain schema and configuration
## Runtime
- Python 3.11 or later (enforced in `scripts/setup.sh`)
- Claude Code plugin runtime (runs as Claude Code marketplace plugin)
- `uv` (preferred) - For installing Python dependencies
- `pip` (fallback) - Alternative package management
## Frameworks
- **sift-kg** ≥0.9.0 - Knowledge graph construction, document ingestion, entity resolution, visualization, export
- **Kreuzberg** ≥4.0 - Text extraction from 75+ document formats (PDF, DOCX, HTML, TXT, etc.) with OCR support for scans
- **pdfplumber** ≥0.10 - Legacy PDF extraction backend
- **Pydantic** ≥2.5 - Validation and serialization for DocumentExtraction models (entities, relations, attributes)
- **NetworkX** ≥3.2 - Graph data structure (MultiDiGraph) for knowledge graph nodes and edges
- **pytest** - Unit test framework (run: `python -m pytest tests/test_unit.py -v`)
- **ruff** - Linting and code formatting (`ruff check`, `ruff format`)
## Key Dependencies
- **sift-kg** ≥0.9.0 - Foundation of pipeline: ingestion → graph building → entity resolution → export → visualization
- **LiteLLM** ≥1.0 - Multi-provider LLM client used by sift-kg for entity resolution and narration
- **Pydantic** ≥2.5 - DocumentExtraction JSON schema validation and serialization
- **Kreuzberg** ≥4.0 - Multi-format document reader, OCR (Tesseract backend)
- **python-docx** ≥1.0 - DOCX parsing
- **BeautifulSoup4** ≥4.12 - HTML parsing
- **pdfplumber** ≥0.10 - PDF text extraction fallback
- **NetworkX** ≥3.2 - Graph operations (MultiDiGraph)
- **SemHash** ≥0.4 - Fuzzy string deduplication for entity matching
- **pyvis** ≥0.3 - Interactive HTML graph visualization
- **Unidecode** ≥1.3 - Unicode normalization for entity names
- **inflect** ≥7.0 - Singularization for deduplication heuristics
- **Rich** ≥13.0 - Terminal formatting for progress output
- **Typer** ≥0.9 - CLI framework for sift-kg command-line tools
- **PyYAML** ≥6.0 - YAML parsing for domain schemas
- **requests** - HTTP library used in test corpus assembly (PubMed E-utilities, SerpAPI calls)
- **RDKit** (rdkit-pypi) ~50MB - SMILES validation, canonicalization, molecular properties (Lipinski analysis)
- **Biopython** ~20MB - DNA/RNA/protein sequence validation, GC content, isoelectric point, molecular weight
- **sentence-transformers** ~2GB (PyTorch) - Semantic clustering for entity resolution (`sift-kg[embeddings]`)
- **google-cloud-vision** ~20MB - Google Cloud Vision OCR (`sift-kg[ocr]`)
## Configuration
- Configured via shell environment variables (not .env file in repository — users set in their environment)
- **For sift-kg entity resolution:**
- **For test corpus assembly:**
- `skills/drug-discovery-extraction/domain.yaml` - YAML schema defining 17 entity types and 30 relation types
- `Makefile` - Standard targets: `help`, `setup`, `setup-all`, `test`, `lint`, `format`, `clean`
- `scripts/setup.sh` - Installation script: checks Python ≥3.11, installs sift-kg, optional RDKit/Biopython
## Platform Requirements
- Python 3.11+
- macOS, Linux, or Windows (tested on macOS)
- Claude Code runtime (latest)
- Python 3.11+ with pip/uv
- Network access for:
- Disk space: ~100MB for sift-kg + dependencies, ~50MB additional for RDKit, ~20MB for Biopython
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Language & Tooling
- Tool: `ruff format`
- Commands: `ruff format scripts/ tests/` in Makefile
- No explicit `.ruff.toml` found — uses ruff defaults
- Tool: `ruff check`
- Command: `ruff check scripts/ tests/` in Makefile
- Enforces standard Python conventions
## Naming Patterns
- Descriptive snake_case: `validate_smiles.py`, `scan_patterns.py`, `build_extraction.py`
- Scripts in `scripts/` prefix with action verb: `run_sift.py`, `label_communities.py`, `label_epistemic.py`
- Validation scripts in `skills/drug-discovery-extraction/validation-scripts/`
- snake_case throughout
- Descriptive: `write_extraction()`, `validate_smiles()`, `scan_text()`, `detect_type()`
- Private functions prefixed with single underscore: `_normalize_fields()`, `_import_sift()`, `_generate_label()`, `_clean_name()`
- Commands in sift wrapper use prefix: `cmd_build()`, `cmd_view()`, `cmd_export()`, `cmd_info()`, `cmd_search()`
- snake_case: `output_dir`, `entity_type`, `pattern_type`, `doc_id`, `smiles`
- Type hints used throughout: `entities: list[dict]`, `text: str`, `pattern: re.Pattern`
- Acronyms expanded in longer forms: `RDKIT_AVAILABLE`, `BIOPYTHON_AVAILABLE`, `HAS_SIFTKG`
- SCREAMING_SNAKE_CASE: `PATTERNS`, `DNA_CHARS`, `RNA_CHARS`, `PROTEIN_CHARS`, `HEDGING_PATTERNS`, `PATENT_PATTERN`
- Pattern definitions: `PATTERNS: list[tuple[str, re.Pattern, str]]`
- Availability flags: `HAS_SIFTKG`, `HAS_RDKIT`, `HAS_BIOPYTHON`, `RDKIT_AVAILABLE`, `BIOPYTHON_AVAILABLE`
- Classes rarely used; dicts preferred for structured data
- Type hints with Union/Optional: `seq_type: str | None`, `domain_path: str | None`
- Generics: `list[dict]`, `dict[str, str]`, `tuple[str, re.Pattern, str]`
## Import Organization
- Use `pathlib.Path` throughout: `Path(file_path)`, `Path(__file__).parent`, `Path(output_dir) / "subdir" / "file.json"`
- Avoid os.path — always Path
- Wrap optional dependencies in try/except at module level
- Set availability flags: `HAS_RDKIT = True`
- Pattern in `validate_molecules.py` (line 30-48):
## Code Style
- Function: Triple-quoted block with description, Args, Returns
- Module: Triple-quoted at top with usage examples
- Example from `validate_smiles.py`:
- Appears to be ~90-100 chars (not strictly enforced)
- Ruff will apply default formatting
- Single-line comments with `#` for clarification
- Block separators with comment lines (79 dashes):
- Inline comments explain patterns or heuristics (e.g., line 82-83 in `scan_patterns.py`)
- 2 blank lines between top-level functions/sections
- 1 blank line between methods within section
- Horizontal rule comments divide major sections
## Error Handling
- Optional libraries fail at import, not runtime
- Functions return error dict instead of raising
- Example from `validate_smiles.py` (line 29-33):
- All validation functions return dict with consistent structure:
- Example from `validate_sequences.py` (line 106-120):
- Wrapper functions catch ImportError and provide help text
- Example from `run_sift.py` (line 17-28):
- LLM outputs may use non-standard field names
- Normalize before processing: `_normalize_fields()` in `build_extraction.py` (line 13-24)
## JSON & Data Structures
- Indented with 2 spaces: `json.dumps(data, indent=2)`
- Always use `indent=2` for readability
- ISO format for timestamps: `datetime.now(timezone.utc).isoformat()`
- Entities: `{"name": str, "entity_type": str, "confidence": float, "context": str}`
- Relations: `{"source_entity": str, "target_entity": str, "relation_type": str, "confidence": float, "evidence": str}`
- Extractions: `{"document_id": str, "entities": list, "relations": list, "extracted_at": str, "domain_name": str}`
- Preferred over loops for clarity
- Example from `label_communities.py` (line 38-39):
## Regex Patterns
- Define at module level as list/dict of tuples with metadata
- Compile with flags: `re.compile(pattern, re.IGNORECASE)`
- Example from `label_epistemic.py`:
## CLI/Main Pattern
- Manual `sys.argv` parsing (no argparse in main scripts)
- Check for flags: `if "--json" in sys.argv`
- Get next arg: `sys.argv[sys.argv.index("--flag") + 1]`
## Type Hints
- Use `|` for Union: `str | None` (not `Optional[str]`)
- Use `from __future__ import annotations` for forward references
- Example from `validate_sequences.py`:
- Functions returning validation results always return `dict`
- Functions with side effects return `str` (file path) or `None`
- Type hints on all function signatures
## Testing Conventions (see TESTING.md for detail)
- Tests are in `/tests/test_unit.py`
- Use `pytest` with conditional skip decorators
- Assertions with descriptive messages: `assert condition, f"Expected X, got {actual}"`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- **Claude-as-extractor**: LLM reads documents and produces `DocumentExtraction` JSON format (entities + relations)
- **Validation-enrichment layer**: Python scripts validate molecular identifiers (SMILES, sequences) and enrich with structural nodes
- **sift-kg wrapper**: Orchestrates graph building, community detection, epistemic analysis, and visualization via Python API
- **Schema-driven**: All extraction constrained by drug discovery domain YAML with 17 entity types and 30 relation types
- **Multi-document parallel**: Agent dispatcher handles 4+ documents concurrently to reduce latency
## Layers
- Purpose: User-facing interface via `/epistract-*` slash commands
- Location: `/.claude-plugin/plugin.json`, `/commands/*.md`
- Contains: Command definitions, agent specifications, skill manifests
- Depends on: Claude Code runtime, bash tool, Python environment
- Used by: Users running `/epistract-ingest`, `/epistract-query`, etc.
- Purpose: Define domain schema and extraction rules that guide LLM agents
- Location: `/skills/drug-discovery-extraction/SKILL.md` (detailed prompt), `/skills/drug-discovery-extraction/domain.yaml` (sift-kg schema)
- Contains: Entity type definitions, relation types, nomenclature rules (HGNC for genes, INN for drugs, MeSH for diseases)
- Depends on: Biomedical ontology standards (40+ sources: DrugBank, ChEMBL, HGNC, UniProt, MedDRA, etc.)
- Used by: Extraction agents, sift-kg graph builder
- Purpose: Claude instances read documents chunk-by-chunk and extract structured JSON
- Location: `/agents/extractor.md` (extraction agent), `/agents/validator.md` (validation agent)
- Contains: Agent task definitions, chunking strategy, entity/relation examples
- Depends on: SKILL.md knowledge, Claude's understanding of drug discovery
- Used by: `/epistract-ingest` command; spawned 1 per document (4+ → async dispatch via Agent tool)
- Purpose: Validate molecular identifiers and enrich graph with structural nodes
- Location: `/scripts/validate_molecules.py` (orchestrator), `/skills/drug-discovery-extraction/validation-scripts/*.py`
- Contains: Pattern scanning (regex), RDKit validation (SMILES), Biopython validation (DNA/RNA/protein sequences), enrichment logic
- Depends on: Optional RDKit (~50MB), optional Biopython (~20MB)
- Used by: `/epistract-ingest` pipeline post-extraction; reads `extractions/*.json`, outputs validated results + CHEMICAL_STRUCTURE/NUCLEOTIDE_SEQUENCE nodes
- Purpose: Build deduplicated knowledge graph, detect communities, generate labels, analyze epistemics
- Location: `/scripts/run_sift.py` (wrapper), `/scripts/label_communities.py`, `/scripts/label_epistemic.py`
- Contains: Graph builder invocation, community labeling logic, epistemic status classification
- Depends on: sift-kg library (≥0.9.0), NetworkX, Pydantic, LiteLLM
- Used by: `/epistract-ingest` post-validation; outputs `graph_data.json`, `communities.json`, `claims_layer.json`
- Purpose: Interactive graph browser in user's browser
- Location: `/lib/vis-9.1.2/` (vis.js dependency), output HTML generated by sift-kg
- Contains: JavaScript graph renderer, DOM interaction handlers
- Depends on: sift-kg's `run_view()` which invokes pyvis + custom HTML
- Used by: `/epistract-view` command opens HTML in browser
## Data Flow
- **Working directory**: User-provided output directory (default: `./epistract-output/`)
- **Structure**:
- **Persistence**: All JSON outputs written to disk; graph reloaded for subsequent queries (search, export, view neighborhood)
## Key Abstractions
- Purpose: Interchange format between Claude extraction and sift-kg graph builder
- Examples: `scripts/build_extraction.py` produces this; `run_sift.py build` consumes it
- Pattern: `{"document_id": str, "entities": [ExtractedEntity], "relations": [ExtractedRelation], "chunks_processed": int, "extracted_at": ISO timestamp}`
- Purpose: Represent drug discovery concepts (compounds, genes, diseases, etc.)
- Examples: Nodes with `id: "compound:sotorasib"`, `entity_type: "COMPOUND"`, `name: "sotorasib"`, `confidence: 0.97`
- Pattern: Canonicalized names (INN for drugs, HGNC for genes, MeSH for diseases), source_documents tracking provenance, community assignment
- Purpose: Capture chemical/sequence data with validation status
- Examples: SMILES structure → validated by RDKit → stored in CHEMICAL_STRUCTURE node; DNA sequence → validated by Biopython → stored in NUCLEOTIDE_SEQUENCE node
- Pattern: Parent entity links to structural node via HAS_STRUCTURE/HAS_SEQUENCE; node carries validation status (valid/invalid/unvalidated)
- Purpose: Annotate relations with confidence level and source epistemology
- Examples: Link has `epistemic_status: "asserted"` if high confidence + no hedging; `"hypothesized"` if text contains "may/might/could"; `"prophetic"` if patent-sourced
- Pattern: Overlaid on graph_data.json edges; enables filtering by evidence strength + source document type
## Entry Points
- `epistract-setup`: Installs sift-kg + optional molecular validation libraries. Calls `scripts/setup.sh`
- `epistract-ingest`: Main ingest pipeline. Orchestrates document reading → extraction → validation → graph building → visualization
- `epistract-query`: Search/filter graph. Uses `run_sift.py search` to find entities by name/type
- `epistract-export`: Export graph to multiple formats (GraphML, CSV, SQLite, JSON). Uses `run_sift.py export`
- `epistract-view`: Open existing graph viewer. Uses `run_sift.py view`
- `epistract-validate`: Run molecular validation on extractions. Uses `scripts/validate_molecules.py`
- `epistract-build`: Rebuild graph from existing extractions (skips extraction). Uses `run_sift.py build`
- `epistract-epistemic`: Label epistemic status. Uses `scripts/label_epistemic.py`
- `scripts/build_extraction.py`: Called by extraction agents via `echo JSON | python build_extraction.py <doc_id> <output_dir>`
- `scripts/validate_molecules.py`: Called by ingest pipeline; scans extraction JSONs, validates, enriches
- `scripts/run_sift.py`: Wrapper around sift-kg Python API; dispatches build/view/export/search/info commands
- `scripts/label_communities.py`: Called during build to auto-label communities with semantic names
- `scripts/label_epistemic.py`: Called post-build to analyze epistemic status across relations
- `agents/extractor.md`: Spawned by `/epistract-ingest` for each document (or batch of chunks). Reads document, produces extraction JSON
- `agents/validator.md`: Runs after extraction; validates molecular identifiers and reports coverage
## Error Handling
- **Missing optional libraries** (RDKit, Biopython): Validation scripts check availability; if missing, flag as "unvalidated" but continue. User gets install instructions
- **Extraction JSON validation**: `build_extraction.py` normalizes field names ('type' → 'entity_type'/'relation_type') to tolerate LLM variations
- **sift-kg import errors**: `run_sift.py` catches ImportError, suggests `uv pip install sift-kg` with clear messaging
- **Document read errors**: Kreuzberg engine silently skips unreadable files; epistract reports count of successfully read documents
- **Graph build failures**: `run_sift.py build` exits with JSON error message; `/epistract-ingest` command catches and reports
- **Validation enrichment**: If HAS_STRUCTURE/HAS_SEQUENCE enrichment fails, falls back to storing identifiers as attributes on parent node rather than creating new nodes
## Cross-Cutting Concerns
- Domain schema enforced by sift-kg's schema loader (validates against domain.yaml)
- Entity confidence scores calibrated: 0.9–1.0 = explicit, 0.7–0.89 = supported, 0.5–0.69 = inferred, <0.5 = speculative
- Molecular validation: RDKit parses SMILES + computes canonical form; Biopython parses sequences + computes properties
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
