<!-- GSD:project-start source:PROJECT.md -->
## Project

**Epistract — Domain-Agnostic Knowledge Graph Framework**

Epistract is a domain-agnostic knowledge graph framework. Plug in a domain schema (YAML + extraction prompts + epistemic rules), point at a document corpus, and get a structured knowledge graph with an epistemic analysis layer. It runs as a [Claude Code](https://claude.ai/claude-code) plugin.

**Core Value:** **Extract knowledge, not information.** Any corpus, any domain — plug in a schema, get a knowledge graph with epistemic layer that reveals what documents say, what they contradict, and what they are missing.

Two pre-built domains demonstrate the framework:
- **drug-discovery** — 17 entity types, 30 relation types for biomedical literature analysis
- **contracts** — 11 entity types, 11 relation types for event/vendor contract analysis

### Constraints

- **Tech stack**: Python 3.11+, uv for package management
- **Document formats**: PDF, DOCX, HTML, TXT, XLS, EML — 75+ formats via Kreuzberg with OCR fallback
- **Large files**: Some documents are 12-31 MB — extraction must handle large documents
- **Domain pluggability**: New domains added via configuration package (domain.yaml + SKILL.md + epistemic.py), no pipeline code changes
- **Existing codebase**: Must preserve backward compatibility with all existing domains
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
- **chonkie** ≥1.0 - Pure-Python sentence-aware chunker with built-in overlap; used by `core/chunk_document.py` for character-tokenized chunking at chunk boundaries (Phase 14 FIDL-03)
- **SemHash** ≥0.4 - Fuzzy string deduplication for entity matching
- **pyvis** ≥0.3 - Interactive HTML graph visualization
- **Unidecode** ≥1.3 - Unicode normalization for entity names
- **inflect** ≥7.0 - Singularization for deduplication heuristics
- **Rich** ≥13.0 - Terminal formatting for progress output
- **Typer** ≥0.9 - CLI framework for sift-kg command-line tools
- **PyYAML** ≥6.0 - YAML parsing for domain schemas
- **requests** - HTTP library used in test corpus assembly (PubMed E-utilities, SerpAPI calls)
- **RDKit** (rdkit) ~50MB - SMILES validation, canonicalization, molecular properties (Lipinski analysis)
- **Biopython** ~20MB - DNA/RNA/protein sequence validation, GC content, isoelectric point, molecular weight
- **sentence-transformers** ~2GB (PyTorch) - Semantic clustering for entity resolution (`sift-kg[embeddings]`)
- **google-cloud-vision** ~20MB - Google Cloud Vision OCR (`sift-kg[ocr]`)
## Configuration
- Configured via shell environment variables (not .env file in repository — users set in their environment)
- **For sift-kg entity resolution:**
- **For test corpus assembly:**
- `domains/drug-discovery/domain.yaml` - YAML schema defining 17 entity types and 30 relation types
- `domains/contracts/domain.yaml` - YAML schema defining 11 entity types and 11 relation types
- `Makefile` - Standard targets: `help`, `setup`, `setup-all`, `test`, `lint`, `format`, `clean`
- `scripts/setup.sh` - Installation script: checks Python ≥3.11, installs sift-kg, optional RDKit/Biopython
## Platform Requirements
- Python 3.11+
- macOS, Linux, or Windows (tested on macOS)
- Claude Code runtime (latest)
- Python 3.11+ with pip/uv
- Network access for:
- Disk space: ~100MB for sift-kg + dependencies, ~5MB for chonkie, ~50MB additional for RDKit, ~20MB for Biopython
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
- Validation scripts in `domains/drug-discovery/validation-scripts/`
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
- **Three-layer architecture**: `core/` (domain-agnostic pipeline engine), `domains/` (pluggable domain configurations), `examples/` (consumer applications)
- **Claude-as-extractor**: LLM reads documents and produces `DocumentExtraction` JSON format (entities + relations), constrained by domain schema
- **Two-layer knowledge graph**: Layer 1 (brute facts — entities/relations from documents), Layer 2 (epistemic analysis — conflicts, gaps, risks, confidence)
- **Domain pluggability**: New domains added via configuration package (domain.yaml + SKILL.md + epistemic.py), no pipeline code changes
- **sift-kg engine**: Orchestrates graph building, community detection, entity resolution, and visualization via Python API
- **Multi-document parallel**: Agent dispatcher handles 4+ documents concurrently to reduce latency
## Layers
### Core Layer (domain-agnostic pipeline)
- Purpose: Domain-agnostic extraction engine, graph builder, epistemic dispatcher
- Location: `core/` — `domain_resolver.py`, `ingest_documents.py`, `build_extraction.py`, `run_sift.py`, `epistemic.py`, `domain_wizard.py`
- Contains: Document ingestion, extraction orchestration, graph construction, epistemic dispatch, domain resolution
- Depends on: sift-kg, Kreuzberg, NetworkX, Pydantic, LiteLLM
- Used by: All `/epistract:*` commands
### Domain Layer (pluggable configurations)
- Purpose: Define domain-specific schema, extraction rules, and epistemic analysis
- Location: `domains/` — each domain is a self-contained package
  - `domains/drug-discovery/` — domain.yaml (17 entity types, 30 relation types), SKILL.md, epistemic.py, validation-scripts/
  - `domains/contracts/` — domain.yaml (11 entity types, 11 relation types), SKILL.md, epistemic.py, workbench/
- Contains: Entity type definitions, relation types, nomenclature rules, epistemic analysis rules
- Depends on: Domain-specific ontology standards
- Used by: Core pipeline via domain_resolver.py
### Consumer Layer (example applications)
- Purpose: Applications that consume the knowledge graph
- Location: `examples/`
  - `examples/workbench/` — Interactive web dashboard with chat + graph panels
  - `examples/telegram_bot/` — Telegram chat interface via Bot API
- Contains: UI components, API endpoints, chat handlers
- Depends on: Core pipeline output (graph_data.json, communities.json)
- Used by: End users exploring the knowledge graph
### Plugin Layer (Claude Code interface)
- Purpose: User-facing interface via `/epistract:*` slash commands
- Location: `.claude-plugin/plugin.json`, `commands/*.md`
- Contains: Command definitions, agent specifications
- Depends on: Claude Code runtime, bash tool, Python environment
- Used by: Users running `/epistract:ingest`, `/epistract:query`, etc.
### Agent Layer (extraction workers)
- Purpose: Claude instances read documents chunk-by-chunk and extract structured JSON
- Location: `agents/extractor.md` (extraction agent), `agents/validator.md` (validation agent)
- Contains: Agent task definitions, chunking strategy, entity/relation examples
- Depends on: Domain SKILL.md knowledge, Claude's domain understanding
- Used by: `/epistract:ingest` command; spawned 1 per document (4+ dispatched concurrently)
## Data Flow
- **Working directory**: User-provided output directory (default: `./epistract-output/`)
- **Pipeline**: documents → Kreuzberg text extraction → LLM entity/relation extraction → domain-specific validation → sift-kg graph construction → epistemic analysis → visualization/export
- **Persistence**: All JSON outputs written to disk; graph reloaded for subsequent queries (search, export, view neighborhood)
## Key Abstractions
- **DocumentExtraction**: Interchange format between Claude extraction and sift-kg graph builder. Pattern: `{"document_id": str, "entities": [ExtractedEntity], "relations": [ExtractedRelation], "chunks_processed": int, "extracted_at": ISO timestamp}`
- **Domain Package**: Self-contained domain configuration. Contains domain.yaml (schema), SKILL.md (extraction prompt), epistemic.py (analysis rules). Resolved by `core/domain_resolver.py`
- **Epistemic Layer**: Annotates relations with confidence level and source epistemology. Status values: "asserted" (high confidence), "hypothesized" (hedging language), "prophetic" (patent-sourced)
- **Domain Resolver**: `core/domain_resolver.py` locates and loads domain packages by name or alias. Returns schema, SKILL path, epistemic module
## Entry Points
- `/epistract:setup`: Installs sift-kg + optional validation libraries
- `/epistract:ingest`: Main ingest pipeline — document reading, extraction, validation, graph building, visualization
- `/epistract:query`: Search/filter graph by entity name or type
- `/epistract:export`: Export graph to GraphML, CSV, SQLite, JSON
- `/epistract:view`: Open interactive graph viewer in browser
- `/epistract:validate`: Run molecular validation on extractions
- `/epistract:build`: Rebuild graph from existing extractions (skip extraction)
- `/epistract:epistemic`: Run epistemic analysis on graph
- `/epistract:domain`: Create new domain via interactive wizard — analyzes sample corpus, generates domain.yaml + SKILL.md + epistemic.py
- `/epistract:dashboard`: Launch web dashboard for a domain
- `/epistract:ask`: Chat with knowledge graph via natural language
- `core/build_extraction.py`: Called by extraction agents to write extraction JSON
- `core/run_sift.py`: Wrapper around sift-kg Python API; dispatches build/view/export/search/info commands
- `core/epistemic.py`: Dispatches epistemic analysis to domain-specific epistemic module
- `core/domain_wizard.py`: Analyzes sample corpus and generates domain configuration package
- `agents/extractor.md`: Spawned by `/epistract:ingest` for each document
- `agents/validator.md`: Runs after extraction; validates identifiers and reports coverage
## Error Handling
- **Missing optional libraries** (RDKit, Biopython): Validation scripts check availability; if missing, flag as "unvalidated" but continue. User gets install instructions
- **Extraction JSON validation**: `build_extraction.py` normalizes field names ('type' -> 'entity_type'/'relation_type') to tolerate LLM variations
- **sift-kg import errors**: `run_sift.py` catches ImportError, suggests `uv pip install sift-kg` with clear messaging
- **Document read errors**: Kreuzberg engine silently skips unreadable files; epistract reports count of successfully read documents
- **Graph build failures**: `run_sift.py build` exits with JSON error message; command layer catches and reports
- **Domain resolution**: `domain_resolver.py` raises clear error if domain not found, lists available domains
## Cross-Cutting Concerns
- Domain schema enforced by sift-kg's schema loader (validates against domain.yaml)
- Entity confidence scores calibrated: 0.9-1.0 = explicit, 0.7-0.89 = supported, 0.5-0.69 = inferred, <0.5 = speculative
- Domain-specific validation: drug-discovery uses RDKit/Biopython; contracts uses obligation/deadline validation
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
