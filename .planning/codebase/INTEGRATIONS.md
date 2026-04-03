# External Integrations

**Analysis Date:** 2026-03-29

## APIs & External Services

**LLM Providers (via LiteLLM):**
- **OpenRouter** - Multi-model LLM provider; preferred for entity resolution in sift-kg
  - SDK/Client: LiteLLM (transparent proxy)
  - Auth: `OPENROUTER_API_KEY` environment variable (no prefix)
  - Used by: sift-kg entity resolution module for deduplication and narration

- **OpenAI** - GPT-4/GPT-4o models
  - SDK/Client: LiteLLM
  - Auth: `SIFT_OPENAI_API_KEY` (SIFT_ prefix required)
  - Used by: sift-kg entity resolution

- **Anthropic** - Claude models
  - SDK/Client: LiteLLM
  - Auth: `SIFT_ANTHROPIC_API_KEY` (SIFT_ prefix required)
  - Used by: sift-kg entity resolution

- **Google Gemini** - Gemini models
  - SDK/Client: LiteLLM
  - Auth: `SIFT_GEMINI_API_KEY` (SIFT_ prefix required)
  - Used by: sift-kg entity resolution

- **AWS Bedrock** - Claude, Llama, Mistral
  - SDK/Client: LiteLLM (transparent)
  - Auth: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME`
  - Used by: sift-kg entity resolution

- **Ollama** - Local models (no API key needed)
  - SDK/Client: LiteLLM
  - Auth: None (local service)
  - Used by: sift-kg entity resolution when `ollama serve` is running

**Document Corpus Assembly:**
- **PubMed E-utilities** - NCBI public API for PubMed search and retrieval
  - Endpoint: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
  - Auth: None (public)
  - Used by: `tests/corpora/06_glp1_landscape/assemble_corpus.py` for Scenario 6 corpus
  - Methods: `/esearch.fcgi` (search), `/efetch.fcgi` (fetch abstracts as XML)

- **SerpAPI** - Google Scholar and Google Patents search
  - Endpoints: `https://serpapi.com/search`
  - Auth: `SERPAPI_API_KEY` environment variable
  - Used by: Scenario 6 multi-source corpus assembly
    - Google Scholar: `as_sdt=7` filter includes patents
    - Google Patents: `assignee`, `country`, `status` filters for competitive intelligence
  - Files: `tests/corpora/06_glp1_landscape/assemble_corpus.py`, `scholar_rerun.py`, `patents_rerun.py`

## Data Storage

**Databases:**
- Not detected - No persistent database configured in current phase
- Data outputs stored as JSON files in `epistract-output/` directory (sift-kg native format)

**File Storage:**
- Local filesystem only
  - Document ingestion: reads from user-provided directory
  - Outputs: `epistract-output/` subdirectory structure:
    - `extractions/` - Per-document DocumentExtraction JSON files
    - `graph_data.json` - Knowledge graph (sift-kg format)
    - `communities.json` - Community assignments
    - `validation/` - Molecular validation results
    - `exports/` - GraphML, GEXF, CSV, SQLite formats

**Caching:**
- None detected - No caching layer; all computations run fresh

## Authentication & Identity

**Auth Provider:**
- Custom environment variable based
- Supports multiple LLM providers via LiteLLM configuration
- No user authentication system; runs within Claude Code plugin context
- API keys passed via environment variables or SIFT_ prefixed configuration

## Monitoring & Observability

**Error Tracking:**
- Not detected - No external error tracking integrated
- Errors logged to stderr and plugin logs

**Logs:**
- `Rich` terminal formatting for user-facing progress output
- Verbose mode available in sift-kg (`--verbose` flag in run_sift.py)
- Test output captured in `.pytest_cache/` during unit testing

## CI/CD & Deployment

**Hosting:**
- Claude Code plugin marketplace (cloud-hosted execution)
- Plugin runs in user's Claude Code session environment

**CI Pipeline:**
- Not detected - No external CI/CD service configured
- Local testing via `pytest` (Makefile target: `make test`)
- Linting via `ruff` (Makefile target: `make lint`)

## Environment Configuration

**Required env vars for full functionality:**
- **For entity resolution:**
  - One of: `OPENROUTER_API_KEY` OR `SIFT_OPENAI_API_KEY` OR `SIFT_ANTHROPIC_API_KEY` OR `SIFT_GEMINI_API_KEY` OR `AWS_*` credentials OR local Ollama
  - `SIFT_DEFAULT_MODEL` (optional) - Specify LLM model string

- **For Scenario 6 corpus assembly:**
  - `SERPAPI_API_KEY` - Required to fetch from Google Scholar and Google Patents

**Secrets location:**
- User's environment (`.bashrc`, `.zshrc`, or exported in terminal session)
- Never committed to repository (`.gitignore` includes `.env`, `*.env`)

## Webhooks & Callbacks

**Incoming:**
- Not detected - No webhook receivers configured

**Outgoing:**
- Not detected - No webhook publishers configured

## External Knowledge Bases & Reference Data

**Biomedical Ontologies & Standards** (consulted during extraction, not API calls):
- **HGNC** (https://www.genenames.org/) - Gene symbol normalization
- **UniProtKB** (https://www.uniprot.org/) - Protein reference
- **MeSH** (https://meshb.nlm.nih.gov/) - Disease terminology
- **DrugBank** (https://go.drugbank.com/) - Drug-target interactions
- **ChEBI** (https://www.ebi.ac.uk/chebi/) - Chemical classification
- **ChEMBL** (https://www.ebi.ac.uk/chembl/) - Bioactivity data
- **PubChem** (https://pubchem.ncbi.nlm.nih.gov/) - Chemical structure search
- **Biolink Model** (https://biolink.github.io/biolink-model/) - KG schema standard

These are consulted by Claude during extraction via the `drug-discovery-extraction` skill but are not accessed via API.

## Molecular Structure Services

**SMILES/InChI Validation:**
- **RDKit** (local library, not a service) - Validates and canonicalizes chemical structures
  - Used by: `scripts/validate_molecules.py`
  - Computes: canonical SMILES, InChI, InChIKey, molecular properties (MW, LogP, HBD, HBA, TPSA)
  - Optional dependency

**Sequence Validation:**
- **Biopython** (local library) - Validates and analyzes biological sequences
  - Used by: `scripts/validate_molecules.py`
  - Computes: sequence type detection, GC content, molecular weight, isoelectric point
  - Optional dependency

---

*Integration audit: 2026-03-29*
