# Pipeline Capacity & Limits

This reflects the v3.0 state of the pipeline. For deeper detail on propagation contracts, see [known-limitations.md](known-limitations.md).

## Document Ingestion

| Feature | Value | Notes |
|---------|-------|-------|
| Formats supported (text class) | 29 extensions via `sift_kg.ingest.reader.create_extractor(backend="kreuzberg").supported_extensions()` | Runtime-resolved — no hardcoded allowlist (FIDL-04) |
| Formats supported (with `--ocr`) | 37 extensions | Image formats (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`) gated behind the flag |
| Archives | `.zip` excluded | Breaks per-document provenance |
| Triage warnings | `warnings[]` per doc in `triage.json` | `extraction_failed:*` and `empty_text` are surfaced, never silently dropped |
| Large docs | 12–31 MB PDFs supported | Kreuzberg backend with optional OCR fallback |

**Known limits:** Binary formats without a Kreuzberg backend fall through with a surfaced warning, not silent skip.

## Wizard Schema Discovery

| Feature | Value | Notes |
|---------|-------|-------|
| Multi-excerpt window | 3 × 4,000-char excerpts (head + midpoint-centered middle + tail) for docs > 12,000 chars | Documents ≤ 12,000 chars pass through as full text (FIDL-05) |
| Per-Pass-1 token cost | ~2,631 input tokens measured on a 60,200-char fixture | Method: tiktoken cl100k_base; soft budget ~24,000 (~9× headroom) |
| LLM bypass | `python -m core.domain_wizard --schema <file.json> --name <slug>` | Skips 3-pass discovery entirely; asserted LLM-free by UT-054 (FIDL-08) |
| PDF reading | `sift_kg.ingest.reader.read_document` | Full text extraction — never raw bytes (FIDL-01) |
| Slug safety | `generate_slug` normalizes via NFKD + ASCII-strip | Pure non-Latin input raises `ValueError`; no transliteration (FIDL-08) |

**Known limits:** "Shoulder" regions between the head/middle/tail excerpts are not sent in Pass-1 for very long documents. Pure non-Latin domain names require explicit Latin `--name`.

## Extraction & Graph Build

| Feature | Value | Notes |
|---------|-------|-------|
| Chunk size | 10,000 characters (paragraph-aware flush) | Chunker: `chonkie.SentenceChunker` with character tokenizer |
| Chunk overlap | Last 3 sentences of previous chunk, capped at 1,500 chars | Sentence-boundary preserving; never mid-sentence (FIDL-03) |
| Extraction contract | `DocumentExtraction` Pydantic model | Fails loud on malformed input (FIDL-02c) |
| Normalization pass-rate gate | ≥ 0.95 default (`--fail-threshold`) | Pipeline aborts before graph build if below threshold |
| Model metadata | `model_used`, `cost_usd` persisted per extraction | Sourced from CLI/env; never hardcoded |
| Domain awareness | `graph_data.json metadata.domain` is the source of truth | Precedence: explicit `--domain` > metadata > generic fallback (FIDL-06) |

**Known limits:** Chunks at the 10,000-char boundary split deterministically; the sentence-aware overlap recovers most but not all cross-chunk relations. Legacy graphs without `metadata.domain` fall back to the generic template with a one-shot stderr warning.

## Epistemic Layer

| Feature | Value | Notes |
|---------|-------|-------|
| Built-in hedging patterns | 12 regex rules (hypothesized, speculative, prophetic, negative) | Applied to evidence text in first-match-wins order |
| Document type inference | `patent`, `preprint`, `paper`, `structural`, `unknown` | `structural` covers PDB / X-ray / cryo-EM reports (FIDL-07) |
| High-confidence structural short-circuit | `doc_type == "structural"` AND confidence ≥ 0.9 → `asserted` | Runs before the hedging scan — crystallography reports facts |
| Custom rules | `CUSTOM_RULES: list[callable]` in domain `epistemic.py` | Per-rule try/except isolates failures; one bad rule cannot break the layer (FIDL-07) |
| Per-domain validators | `domains/<name>/validation/run_validation.py` auto-invoked post-build | Writes `validation_report.json`; failure is non-fatal (FIDL-07) |
| Workbench per-domain template | `domains/<name>/workbench/template.yaml` | Emitted automatically by the wizard; Pydantic-validated against `WorkbenchTemplate` (FIDL-08) |
| Automatic analyst narrator | `/epistract:epistemic` runs the rule engine → then calls LLM with the domain `persona` → writes `epistemic_narrative.md` alongside `claims_layer.json` | Opt-out via `--no-narrate`; non-fatal on API/credential error (`claims_layer.json` is authoritative) |
| Persona = single source of truth | `domains/<name>/workbench/template.yaml:persona` | Same string drives the narrator (proactive) and the workbench chat prompt (reactive); upgrade once, both improve |

**Known limits:** `CUSTOM_RULES` execute in list order with no dependency graph. Validator failures log but do not abort `cmd_build` (build health > validator health). Structural doctype signals live in drug-discovery only for v3.0. The narrator is LLM-non-deterministic; the rule-based `claims_layer.json` is the reproducible artifact. For the full propagation contract, see [known-limitations.md](known-limitations.md).
