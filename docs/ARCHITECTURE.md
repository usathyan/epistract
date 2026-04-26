# Architecture

Epistract is positioned as a **workspace pattern** inside [Claude Code](https://claude.ai/claude-code): a scientist starts with a question, identifies the corpus that can answer it, picks a domain whose schema and persona match the analytical frame, and the framework constructs a graph specifically for that question. The graph is bespoke — a different question, with a different corpus and possibly a different domain, produces a different graph. The framework's value is not in producing one canonical KG of biomedicine or contracts; it is in supporting the construction of many specialized KGs grounded to specific use cases. The scientist stays in the loop throughout. The architecture below describes the framework's mechanics.

Epistract builds knowledge graphs in two layers. The first layer extracts brute facts — entities and relations pulled from documents by LLM agents, constrained by a domain schema grounded in established ontologies. The second layer applies epistemic analysis — domain-specific rules plus an LLM narrator that detect what is asserted versus hypothesized, what contradicts across documents, what is missing, and where risks lie.

## Two-Layer Knowledge Graph

- **Layer 1 — Brute Facts.** Entities and relations extracted from documents via LLM agents, constrained by the domain schema. Each entity is typed and grounded to domain standards (INN for drugs, HGNC for genes, MedDRA for adverse events, etc.). Each relation carries a confidence score and a verbatim evidence passage. Extraction is Pydantic-validated at write time — malformed extractions fail loud rather than silently dropping.

- **Layer 2 — Epistemic Super Domain.** Domain-specific rules detect conflicts, gaps, confidence levels, and risks across the graph. The epistemic machinery is the same regardless of domain — only the rules change. Drug-discovery rules classify relations as *asserted* / *hypothesized* / *prophetic* (patent-sourced forward claims) / *contested* / *contradictions* / *negative* / *speculative*. Contract rules detect cross-contract conflicts, obligation gaps, and risk indicators. On top of the rule engine, an LLM analyst narrator reads the classified graph and writes `epistemic_narrative.md` — a structured briefing an analyst would produce.

  **Predefined defaults, customizable per domain.** Every pre-built domain ships with a starter rule set: the seven-status taxonomy above, hedging-pattern regex rules that catch common research-language constructions, document-type inference defaults (patents, trial protocols, FDA labels, peer-reviewed papers), and the cross-source aggregation rule that flags `contested` edges. These defaults are the floor, not the ceiling. Customize per domain by editing `domains/<name>/epistemic.py`: add hedging patterns (one-line additions to `HEDGING_PATTERNS`), add domain-specific status types (clinicaltrials adds phase-based grading; fda-product-labels adds a four-level `established`/`reported`/`theoretical`/`asserted` classifier), or override cross-source thresholds. The wizard (`/epistract:domain`) generates a starter `epistemic.py` pre-populated with the shared taxonomy so authors edit rather than write from scratch.

## Domain Pluggability

New domains are added by creating a configuration package (no pipeline code changes):

```
domains/<name>/
  domain.yaml              # entity types, relation types, naming standards
  SKILL.md                 # extraction prompt with domain expertise
  epistemic.py             # rules for conflict detection, gap analysis, risk scoring
  workbench/template.yaml  # chat persona, narrator persona, entity colors
  validation/              # optional: molecular/sequence/custom validators
  references/              # auto-generated entity-types.md and relation-types.md
```

Use the wizard (`/epistract:domain`) to auto-generate all of these from a sample corpus, or create them manually. The domain resolver (`core/domain_resolver.py`) loads packages by name or alias from `domains/` at runtime.

## Pipeline Stages

1. **Ingest** — `core/ingest_documents.py` reads the corpus via `sift_kg.ingest.reader` (Kreuzberg backend; 29 text formats, 37 with `--ocr`). Writes per-document text files and a `triage.json` metadata report.
2. **Chunk** — `core/chunk_document.py` splits ingested text with `chonkie.SentenceChunker` — 10,000-char chunks with last-3-sentence overlap (capped at 1,500 chars), preserving sentence boundaries across splits so cross-chunk entities and relations are recovered.
3. **Extract** — Per-document extractor agents (or a direct-call script) read each chunk, produce `DocumentExtraction` JSON constrained by the domain schema, and persist via `core/build_extraction.py`. Pydantic validation runs at write time; `model_used` and `cost_usd` are sourced from CLI flags / env / provenance — never hardcoded.
4. **Normalize** — `core/normalize_extractions.py` renames variant filenames, dedupes same-doc extractions, coerces schema drift, and gates the pipeline: if recovery rate is below `--fail-threshold` (default 0.95), the build aborts before graph construction.
5. **Build** — `core/run_sift.py build` wraps the sift-kg engine: graph construction, community detection via Louvain, entity resolution via LiteLLM, export. Populates `graph_data.json` including `metadata.domain`. Invokes the domain's `validation/run_validation.py` if present — failure is non-fatal (writes `validation_report.json` with status).
6. **Epistemic analysis** — `core/label_epistemic.py` dispatches to `domains/<name>/epistemic.py`. Regex hedging patterns + domain-specific contradiction pairs + CUSTOM_RULES produce `claims_layer.json`. Then the LLM narrator reads the classified graph and the domain persona and writes `epistemic_narrative.md`.
7. **View / Dashboard** — `core/run_sift.py view` renders a static `graph.html`; `/epistract:dashboard` launches the interactive FastAPI workbench (see [WORKBENCH.md](WORKBENCH.md)).

## Data Formats

- **`DocumentExtraction`** — interchange format between Claude extraction and sift-kg graph builder. JSON object with `document_id`, `entities`, `relations`, `chunks_processed`, `extracted_at`, `model_used`, `cost_usd`. Validated against `sift_kg.extract.models.DocumentExtraction`.
- **`graph_data.json`** — NetworkX-compatible graph representation with `nodes`, `links`, and `metadata` (including `domain`). Every node/link carries source provenance (document IDs, evidence quotes).
- **`claims_layer.json`** — Super Domain overlay. `metadata`, `summary.epistemic_status_counts`, `base_domain.asserted_relations`, `super_domain.contradictions`, `super_domain.hypotheses`, `super_domain.contested_claims`, `super_domain.custom_findings`.
- **`epistemic_narrative.md`** — LLM-generated analyst briefing. Markdown. Regenerated on every `/epistract:epistemic` run.
- **`validation_report.json`** — optional, emitted by the domain's validator. Status + per-identifier findings.
- **`triage.json`** — per-document warnings and metadata from ingestion.
- **`communities.json`** — Louvain community assignments, keyed by node name.

## Layers (core / domains / examples)

- **`core/`** — domain-agnostic pipeline engine. `domain_resolver`, `ingest_documents`, `chunk_document`, `build_extraction`, `normalize_extractions`, `run_sift`, `label_epistemic`, `label_communities`, `llm_client`, `domain_wizard`. No domain-specific imports.
- **`domains/`** — pluggable domain configurations. Each is self-contained. Resolved by `core/domain_resolver.py` by name or alias.
- **`examples/`** — consumer applications. `examples/workbench/` (FastAPI dashboard + chat). `examples/telegram_bot/` (Telegram chat interface). These read graph artifacts; they don't modify them.
- **`commands/`** — Claude Code plugin slash-command definitions. Each command is a short skill file that orchestrates `core/` scripts.
- **`agents/`** — extractor/validator/acquirer subagent definitions. Spawned by `/epistract:ingest` and peers.

## Extraction Model Resolution

Extraction uses whatever LLM the caller configures:

- **Subagent dispatch (normal plugin path)** — `/epistract:ingest` spawns `epistract:extractor` subagents; each inherits the parent Claude Code model unless overridden.
- **Direct-call script** — `scripts/extract_corpus.py` uses the openai SDK against OpenRouter's OpenAI-compatible endpoint with `--model` (default `anthropic/claude-sonnet-4.6`). Resume-safe: skips documents whose extraction JSON already exists.

The provenance (`model_used`, `cost_usd`) is captured on every extraction regardless of path.

## LLM Client (chat + narrator)

`core/llm_client.py` provides a synchronous client for pipeline scripts (narrator, future analytical steps). Priority:

1. Azure AI Foundry (`AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` or `AZURE_FOUNDRY_RESOURCE`)
2. Anthropic direct (`ANTHROPIC_API_KEY`)
3. OpenRouter (`OPENROUTER_API_KEY`)

Same priority as the workbench chat (`examples/workbench/api_chat.py:_resolve_api_config`). Credentials missing → narrator skips gracefully; `claims_layer.json` is authoritative.

## Testing

- `tests/test_unit.py` — unit tests for extraction adapters, wizard prompt builders, epistemic rule behaviors, narrator components
- `tests/test_workbench.py` — workbench API and template-loading tests
- `tests/test_e2e.py` — end-to-end regression including FT-009 (24-file Bug-4 reproducer at ≥95% load rate) and FT-010 (below-threshold abort)
- `tests/baselines/v2/expected.json` — pinned V2 scenario baselines that FT-012 compares against; a floor, not a ceiling

See [DEVELOPER.md](../DEVELOPER.md) for more on internals, extending the pipeline, and contributing.
