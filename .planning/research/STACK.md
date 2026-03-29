# Technology Stack: Cross-Domain Contract KG Extension

**Project:** Epistract Scenario 7 (Contract Analysis)
**Researched:** 2026-03-29
**Scope:** New components only -- existing biomedical stack is unchanged

## Recommended Stack

### Document Parsing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Kreuzberg** | >=4.6 | PDF, XLS, XLSX, EML extraction | Already in stack. v4.6.3 supports 91+ formats including XLS, XLSX, EML natively. Rust core handles large files (12-31 MB PDFs) efficiently. No new dependency needed. | HIGH |
| **pymupdf4llm** | >=1.27 | LLM-optimized PDF-to-Markdown for contract clause extraction | Outputs clean Markdown with table preservation, header hierarchy, and reading-order correction. Critical for feeding contract text to Claude for entity extraction. Kreuzberg extracts raw text; pymupdf4llm preserves document structure as Markdown that LLMs parse better. | HIGH |
| **openpyxl** | >=3.1 | XLS/XLSX reading (fallback for structured data) | Only needed if Kreuzberg's table extraction from XLS is insufficient for preserving cell structure. Pure Python, read-only mode handles large files. xlrd is unmaintained -- do not use. | MEDIUM |

**Decision: Kreuzberg + pymupdf4llm dual pipeline.** Kreuzberg handles format detection, OCR fallback, and EML/XLS parsing. pymupdf4llm handles PDF-to-Markdown conversion specifically for LLM consumption. Use Kreuzberg for non-PDF formats; pymupdf4llm for PDFs where structural fidelity matters for clause extraction.

### Domain Configuration System

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **PyYAML** | >=6.0 | Domain schema parsing | Already in stack. Existing `domain.yaml` pattern proven with drug-discovery domain (17 entity types, 30 relation types). Extend, don't replace. | HIGH |
| **Pydantic** | >=2.5 | Domain schema validation | Already in stack. Validate domain configs at load time. Type-safe entity_type and relation_type enums generated from YAML. | HIGH |
| **sift-kg** | >=0.9.0 | `load_domain()` API | Already in stack. sift-kg's domain loading already parses YAML into extraction configs. New domains just need new YAML files. | HIGH |

**Decision: No new dependencies.** The domain config system is an architectural pattern, not a library choice. Create `skills/contract-analysis/domain.yaml` following the existing drug-discovery pattern. sift-kg's `load_domain()` already supports arbitrary domains.

### Interactive Web Report

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Streamlit** | >=1.55 | Dashboard framework | Best Python dashboard framework for data-heavy apps with filters, tables, and drill-down. Single-file deployable. Committee chairs need to explore contracts, not read static PDFs. Gradio is ML-demo-focused; Panel has worse DX. | HIGH |
| **pyvis** | >=0.3 | Interactive graph visualization | Already in stack. Renders NetworkX graphs as interactive HTML. Drag-and-filter nodes. Embeds in Streamlit via `components.html()`. | HIGH |
| **Plotly** | >=6.0 | Charts (budget breakdowns, timelines) | Native Streamlit integration via `st.plotly_chart()`. Gantt charts for deadlines, sunburst for cost hierarchies, sanity charts for obligation flows. | MEDIUM |
| **streamlit-aggrid** | >=1.0 | Filterable data tables | AG Grid in Streamlit. Committee chairs need to filter obligations by vendor, deadline, cost. Built-in `st.dataframe` lacks advanced filtering. | MEDIUM |

**Decision: Streamlit + pyvis + Plotly.** Streamlit is the clear winner for Python data dashboards. pyvis is already in the stack for graph visualization. Plotly adds timeline/budget charts. streamlit-aggrid only if built-in tables prove insufficient.

### Telegram Bot Integration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **python-telegram-bot** | >=22.7 | Telegram Bot API wrapper | Simpler than aiogram, adequate for this use case (query/response, not high-concurrency). 22.7 is current (March 2026). Good docs, large community. The existing MCP Telegram plugin handles message routing -- the bot just needs to receive queries and return KG answers. | HIGH |

**Decision: python-telegram-bot over aiogram.** aiogram is async-first and better for high-concurrency bots, but this is a query-response bot for ~10 committee chairs, not a public bot serving thousands. python-telegram-bot's simpler sync/async hybrid model is easier to integrate with the existing epistract pipeline. The MCP Telegram plugin already handles transport -- this is about the bot logic layer.

### KG Query & Reasoning

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **NetworkX** | >=3.2 | Graph queries | Already in stack. MultiDiGraph supports the query patterns needed: find all obligations for vendor X, find deadline conflicts, trace dependency chains. | HIGH |
| **LiteLLM** | >=1.0 | Natural language KG querying | Already in stack (used by sift-kg). For Telegram queries: user question -> LiteLLM generates graph query -> NetworkX executes -> LiteLLM formats answer. | HIGH |

**Decision: No graph database.** Neo4j/ArangoDB are overkill for 62 contracts producing ~500-2000 nodes. NetworkX in-memory graph is fast enough and avoids infrastructure complexity. If the cross-domain framework scales to thousands of documents later, revisit with a graph database.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| PDF parsing | Kreuzberg + pymupdf4llm | Camelot, Tabula | Camelot needs Ghostscript dependency; Tabula needs Java. Both are table-only extractors, not full document parsers. |
| PDF parsing | pymupdf4llm | pdfplumber (already in stack) | pdfplumber is good for tables but doesn't output LLM-optimized Markdown. pymupdf4llm's Markdown output preserves headers, lists, and reading order -- critical for Claude to parse contract clauses. |
| Dashboard | Streamlit | Gradio | Gradio is ML demo focused. Lacks proper table filtering, drill-down navigation, and multi-page layouts needed for contract analysis. |
| Dashboard | Streamlit | Panel | Panel is more flexible but worse DX. Streamlit's widget model (filters -> rerun) maps perfectly to "filter contracts by vendor/deadline/cost". |
| Dashboard | Streamlit | FastAPI + React | Massively higher complexity for a ~10-user internal tool. Streamlit ships a working dashboard in days, not weeks. |
| Telegram | python-telegram-bot | aiogram | aiogram's async complexity not justified for <20 concurrent users. python-telegram-bot is simpler and well-documented. |
| Graph DB | NetworkX (in-memory) | Neo4j | 62 contracts -> ~500-2000 nodes. No need for a database server. NetworkX loads the full graph in <1 second. |
| XLS parsing | Kreuzberg (built-in) | pandas | pandas is heavy for just reading one XLS file. Kreuzberg already handles it. |
| Contract NLP | Claude via sift-kg | spaCy Legal NER, John Snow Labs | Pre-trained legal NER models extract named entities but not contractual obligations, deadlines, or cross-references. Claude with domain-specific prompts (via domain.yaml) handles the semantic extraction that rule-based NER cannot. This is the same approach that works for drug discovery -- prompt-driven extraction, not model-driven. |
| EML parsing | Kreuzberg (built-in) | eml-parser, emaildata | Kreuzberg already supports EML. Adding another library is unnecessary. |

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| **LangChain / LlamaIndex** | Adds abstraction layers over what sift-kg + LiteLLM already do. Epistract's extraction pipeline is simpler and more controllable. |
| **Neo4j / ArangoDB** | Infrastructure overhead for a small graph. Revisit only if graph exceeds 10K nodes. |
| **spaCy Legal NER** | Pre-trained models don't extract obligations/deadlines/cross-references. Claude does this better with domain prompts. |
| **Camelot** | Requires Ghostscript system dependency. Table-only -- doesn't handle full contract text extraction. |
| **Tabula** | Requires Java runtime. Same limitations as Camelot. |
| **Gradio** | Wrong tool. Designed for ML model demos, not data exploration dashboards. |
| **Django / Flask** | Full web frameworks are overkill. Streamlit handles the dashboard requirement with zero boilerplate. |
| **xlrd** | Unmaintained. Only reads .xls, not .xlsx. Kreuzberg handles both. |
| **aiogram** | Async complexity not warranted for this scale. |

## Installation

```bash
# New dependencies only (existing stack unchanged)

# Document parsing (pymupdf4llm for LLM-optimized PDF extraction)
uv pip install "pymupdf4llm>=1.27"

# Dashboard
uv pip install "streamlit>=1.55" "plotly>=6.0"
# Optional: uv pip install "streamlit-aggrid>=1.0"

# Telegram bot
uv pip install "python-telegram-bot>=22.7"

# Already in stack (no action needed):
# kreuzberg>=4.0, pydantic>=2.5, networkx>=3.2, pyvis>=0.3,
# litellm>=1.0, pyyaml>=6.0, sift-kg>=0.9.0
```

## New Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token (from @BotFather) | Yes, for Telegram feature |
| `TELEGRAM_ALLOWED_CHAT_IDS` | Comma-separated chat IDs allowed to query the bot | Yes, for security |

No new LLM API keys needed -- reuses existing sift-kg/LiteLLM configuration.

## Stack Summary

**New dependencies: 3** (pymupdf4llm, streamlit, python-telegram-bot)
**Optional: 2** (plotly, streamlit-aggrid)
**Reused from existing stack: 8** (kreuzberg, pydantic, networkx, pyvis, litellm, pyyaml, sift-kg, rich)

The key insight: epistract's existing architecture handles most of this. The domain config system is a YAML file. Document parsing is mostly covered by Kreuzberg (already installed). The real new work is the Streamlit dashboard and Telegram bot -- both are lightweight additions.

## Sources

- [Kreuzberg PyPI](https://pypi.org/project/kreuzberg/) - v4.6.3, 91+ format support including XLS/EML (verified March 2026)
- [pymupdf4llm PyPI](https://pypi.org/project/pymupdf4llm/) - v1.27.2.2 (verified March 2026)
- [python-telegram-bot PyPI](https://pypi.org/project/python-telegram-bot/) - v22.7 (verified March 2026)
- [Streamlit PyPI](https://pypi.org/project/streamlit/) - v1.55.0 (verified March 2026)
- [Streamlit 2026 Release Notes](https://docs.streamlit.io/develop/quick-reference/release-notes/2026)
- [PyMuPDF4LLM Documentation](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [Kreuzberg Features](https://docs.kreuzberg.dev/features/)
- [python-telegram-bot vs aiogram comparison](https://www.restack.io/p/best-telegram-bot-frameworks-ai-answer-python-telegram-bot-vs-aiogram-cat-ai)
