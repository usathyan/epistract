# Phase 2: Document Ingestion - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse and triage 62+ contract documents (PDFs, XLS, EML) from a local corpus directory into per-document text files with metadata, ready for entity extraction in Phase 3. Covers document discovery, text extraction, triage classification, and metadata capture. Does NOT include entity extraction, graph building, or any analysis — those are Phase 3+.

</domain>

<decisions>
## Implementation Decisions

### Contract Data Location
- **D-01:** Contract files live outside the repo on the user's local machine. No files committed to git.
- **D-02:** Pipeline discovers files via the existing CLI `path` argument to `/epistract-ingest`. No new env vars or config entries needed.
- **D-03:** For development testing, create 2-3 small synthetic contract PDFs in `tests/fixtures/` to test parsing logic without real data.

### Large PDF Handling
- **D-04:** Use Kreuzberg for ALL document formats — single code path. No size-based routing or format-specific parsers.
- **D-05:** On parse failure (corrupted, encrypted, unsupported): log the error in triage.json and skip the file. Do not fail the entire run.
- **D-06:** Scanned PDFs are auto-OCR'd via Kreuzberg's Tesseract backend. Requires tesseract installed on the system.

### Triage Report
- **D-07:** Triage output is a single `triage.json` in the output directory. Machine-readable, queryable by downstream phases.
- **D-08:** Per-document metadata fields: `filename`, `file_path`, `file_size_bytes`, `page_count`, `category` (from folder), `parse_type` (text/scanned/mixed), `text_length`, `parse_errors`, `extraction_readiness_score` (0-1 based on text density, structure detection, OCR confidence).
- **D-09:** No separate Markdown triage report — JSON is the single source.

### Folder-to-Category Mapping
- **D-10:** Auto-detect category from folder path. Top-level folder under corpus root becomes the category. Known folders: Hotel, PCC, AV, Catering, Security, EMS. Unknown folders get "uncategorized".
- **D-11:** Recursive scan — walk all subdirectories. Category comes from the top-level folder under corpus root regardless of nesting depth.

### Output Directory Structure
- **D-12:** Per-document text files stored as `ingested/<doc_id>.txt` in the output directory. Clean separation from extractions/.
- **D-13:** Document IDs are sanitized filenames: strip extension, lowercase, replace spaces/special chars with underscores. E.g., "Aramark Contract.pdf" → "aramark_contract".

### Ingestion Script Design
- **D-14:** New standalone `scripts/ingest_documents.py` following existing script pattern (like run_sift.py, build_extraction.py). CLI: `python scripts/ingest_documents.py /path/to/corpus --output ./output --domain contract`.

### Progress Reporting
- **D-15:** Use Rich progress bar (already a dependency) during batch processing. Shows file count and current filename. Summary printed at end.

### XLS/EML Handling
- **D-16:** XLS and EML files go through the same Kreuzberg pipeline as PDFs. No format-specific parsers. Triage report notes the file format.

### Claude's Discretion
- Internal implementation of extraction readiness score heuristic
- Exact triage.json schema beyond the fields specified above
- Error message format in triage.json
- Whether to use async/threading for parsing (single-threaded is fine for 62 files)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Pipeline
- `commands/ingest.md` — Current ingestion pipeline flow (7 steps). Step 1 (document reading) is the focus of this phase.
- `scripts/run_sift.py` — sift-kg wrapper. Ingestion script should follow its CLI pattern.
- `scripts/build_extraction.py` — Extraction JSON builder. Ingestion feeds into this in Phase 3.
- `scripts/domain_resolver.py` — Domain resolution (from Phase 1). Ingestion script uses `--domain` flag.

### Document Parsing
- `sift_kg.ingest.reader.read_document()` — Kreuzberg-based document reader. Supports 75+ formats including PDF, XLS, EML with OCR.

### Domain Schema
- `skills/contract-extraction/domain.yaml` — Contract domain (7 entity types, 7 relation types). Not consumed by ingestion directly but informs what text needs to be extractable.

### Requirements
- `.planning/REQUIREMENTS.md` — INGS-01 through INGS-04 define Phase 2 acceptance criteria, plus new INGS-05 through INGS-10 from this discussion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sift_kg.ingest.reader.read_document(Path)` — Kreuzberg reader available and tested. Returns text string from any supported format.
- `Rich` library — Already a project dependency. Use `rich.progress` for progress bar.
- `scripts/domain_resolver.py` — `resolve_domain()` and `list_domains()` for domain-aware operation.

### Established Patterns
- CLI pattern: `sys.argv` parsing with `--flag value` (no argparse). See `run_sift.py`.
- Module structure: docstring, imports, constants, functions, `__main__` guard. See `build_extraction.py`.
- Error handling: return error dicts, don't raise. Log and continue.
- Path handling: `pathlib.Path` throughout, never `os.path`.
- JSON output: `json.dumps(data, indent=2)` with ISO timestamps.

### Integration Points
- `commands/ingest.md` Step 1 — currently delegates to sift-kg reader. New `ingest_documents.py` replaces/enhances this step.
- Output `ingested/` directory feeds into Step 3 (extraction) in Phase 3.
- `triage.json` consumed by extraction phase for document selection and quality awareness.

</code_context>

<specifics>
## Specific Ideas

- User wants all discussion decisions captured as formal requirements in REQUIREMENTS.md
- Extraction readiness score is a forward-looking signal for Phase 3 — helps prioritize which documents to extract first and which may need manual review

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-document-ingestion*
*Context gathered: 2026-03-29*
