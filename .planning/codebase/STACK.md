# Technology Stack

**Analysis Date:** 2026-03-29

## Languages

**Primary:**
- Python 3.11+ - Core runtime for knowledge graph building, molecular validation, plugin integration

**Secondary:**
- Bash - Setup and utility scripts
- YAML - Domain schema and configuration

## Runtime

**Environment:**
- Python 3.11 or later (enforced in `scripts/setup.sh`)
- Claude Code plugin runtime (runs as Claude Code marketplace plugin)

**Package Manager:**
- `uv` (preferred) - For installing Python dependencies
- `pip` (fallback) - Alternative package management

## Frameworks

**Core:**
- **sift-kg** ≥0.9.0 - Knowledge graph construction, document ingestion, entity resolution, visualization, export
  - Replaces raw LLM calls with Claude's extraction capability
  - Handles graph building, deduplication, community detection, interactive viewer

**Document Processing:**
- **Kreuzberg** ≥4.0 - Text extraction from 75+ document formats (PDF, DOCX, HTML, TXT, etc.) with OCR support for scans
- **pdfplumber** ≥0.10 - Legacy PDF extraction backend

**Data Models:**
- **Pydantic** ≥2.5 - Validation and serialization for DocumentExtraction models (entities, relations, attributes)
- **NetworkX** ≥3.2 - Graph data structure (MultiDiGraph) for knowledge graph nodes and edges

**Testing:**
- **pytest** - Unit test framework (run: `python -m pytest tests/test_unit.py -v`)

**Build/Dev:**
- **ruff** - Linting and code formatting (`ruff check`, `ruff format`)

## Key Dependencies

**Critical:**
- **sift-kg** ≥0.9.0 - Foundation of pipeline: ingestion → graph building → entity resolution → export → visualization
  - Used via Python API: `run_build()`, `run_resolve()`, `run_apply_merges()`, `run_export()`, `run_view()`, `load_domain()`
  - Manages sift-kg subprocess for entity resolution using LiteLLM
- **LiteLLM** ≥1.0 - Multi-provider LLM client used by sift-kg for entity resolution and narration
  - Supports OpenRouter, OpenAI, Anthropic, Google Gemini, AWS Bedrock, Ollama
  - Not used for extraction (Claude replaces this)
- **Pydantic** ≥2.5 - DocumentExtraction JSON schema validation and serialization

**Document Processing:**
- **Kreuzberg** ≥4.0 - Multi-format document reader, OCR (Tesseract backend)
- **python-docx** ≥1.0 - DOCX parsing
- **BeautifulSoup4** ≥4.12 - HTML parsing
- **pdfplumber** ≥0.10 - PDF text extraction fallback

**Graph & Deduplication:**
- **NetworkX** ≥3.2 - Graph operations (MultiDiGraph)
- **SemHash** ≥0.4 - Fuzzy string deduplication for entity matching
- **pyvis** ≥0.3 - Interactive HTML graph visualization

**Utilities:**
- **Unidecode** ≥1.3 - Unicode normalization for entity names
- **inflect** ≥7.0 - Singularization for deduplication heuristics
- **Rich** ≥13.0 - Terminal formatting for progress output
- **Typer** ≥0.9 - CLI framework for sift-kg command-line tools
- **PyYAML** ≥6.0 - YAML parsing for domain schemas
- **requests** - HTTP library used in test corpus assembly (PubMed E-utilities, SerpAPI calls)

**Optional: Molecular Validation**

Install with `make setup-all` or `bash scripts/setup.sh --all`:
- **RDKit** (rdkit) ~50MB - SMILES validation, canonicalization, molecular properties (Lipinski analysis)
  - Provides: canonical SMILES, InChI, InChIKey, molecular formula, MW, LogP, HBD, HBA, TPSA
- **Biopython** ~20MB - DNA/RNA/protein sequence validation, GC content, isoelectric point, molecular weight
  - Provides: sequence validation, type detection, reverse complement, translation, physiochemical properties

**Optional: sift-kg Extras**

For vector embeddings and OCR backends:
- **sentence-transformers** ~2GB (PyTorch) - Semantic clustering for entity resolution (`sift-kg[embeddings]`)
- **google-cloud-vision** ~20MB - Google Cloud Vision OCR (`sift-kg[ocr]`)

## Configuration

**Environment:**
- Configured via shell environment variables (not .env file in repository — users set in their environment)
- **For sift-kg entity resolution:**
  - `OPENROUTER_API_KEY` - OpenRouter (recommended, reads directly)
  - `SIFT_OPENAI_API_KEY` - OpenAI (SIFT_ prefix required)
  - `SIFT_ANTHROPIC_API_KEY` - Anthropic (SIFT_ prefix required)
  - `SIFT_GEMINI_API_KEY` - Google Gemini (SIFT_ prefix required)
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME` - AWS Bedrock
  - `SIFT_DEFAULT_MODEL` - Default model selection (e.g., `openai/gpt-4o-mini`, `anthropic/claude-haiku`, `ollama/llama3.3`)
- **For test corpus assembly:**
  - `SERPAPI_API_KEY` - SerpAPI key for Google Scholar and Google Patents searches (Scenario 6)

**Domain:**
- `skills/drug-discovery-extraction/domain.yaml` - YAML schema defining 17 entity types and 30 relation types
  - Loaded by `scripts/run_sift.py` and plugin agents
  - Parsed by sift-kg's `load_domain()` function

**Build:**
- `Makefile` - Standard targets: `help`, `setup`, `setup-all`, `test`, `lint`, `format`, `clean`
- `scripts/setup.sh` - Installation script: checks Python ≥3.11, installs sift-kg, optional RDKit/Biopython

## Platform Requirements

**Development:**
- Python 3.11+
- macOS, Linux, or Windows (tested on macOS)
- Claude Code runtime (latest)

**Production:**
- Python 3.11+ with pip/uv
- Network access for:
  - LiteLLM API calls to OpenAI, Anthropic, OpenRouter, Google, AWS, or local Ollama
  - PubMed E-utilities (public, no auth)
  - SerpAPI (requires SERPAPI_API_KEY for Google Scholar/Patents)
- Disk space: ~100MB for sift-kg + dependencies, ~50MB additional for RDKit, ~20MB for Biopython

---

*Stack analysis: 2026-03-29*
