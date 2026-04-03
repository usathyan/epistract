# Phase 2: Document Ingestion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 02-document-ingestion
**Areas discussed:** Contract data location, Large PDF handling, Triage report format, Folder-to-category mapping, Output directory structure, Ingestion script design, Progress reporting, XLS/EML handling

---

## Contract Data Location

| Option | Description | Selected |
|--------|-------------|----------|
| Local path outside repo | Files live elsewhere on machine. Pipeline reads at runtime. | ✓ |
| Symlink into data/ub/ | Create gitignored symlink | |
| Copy into repo (gitignored) | Self-contained but large | |
| Configurable path | Env var or config entry | |

**User's choice:** Local path outside repo
**Notes:** No files committed to git.

| Option | Description | Selected |
|--------|-------------|----------|
| CLI argument | User passes path to /epistract-ingest | ✓ |
| Environment variable | EPISTRACT_CORPUS_PATH | |
| Config file entry | epistract.json | |

**User's choice:** CLI argument (existing `path` arg in ingest.md)

| Option | Description | Selected |
|--------|-------------|----------|
| Provide at runtime | Don't hardcode any path | ✓ |
| Share path now | Document in CONTEXT.md | |

**User's choice:** Provide at runtime

| Option | Description | Selected |
|--------|-------------|----------|
| Fixture PDFs | Small synthetic contract PDFs in tests/fixtures/ | ✓ |
| Skip parse tests | Mock text only | |
| Real contract subset | Copy real contracts (gitignored) | |

**User's choice:** Fixture PDFs for testing

---

## Large PDF Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Kreuzberg for all | Single code path, OCR fallback via Tesseract | ✓ |
| Size-based routing | Different parsers by file size | |
| Parallel extraction | Same engine, concurrent processing | |

**User's choice:** Kreuzberg for all

| Option | Description | Selected |
|--------|-------------|----------|
| Log and skip | Record failure, continue with remaining | ✓ |
| Fail entire run | Stop on any failure | |
| Interactive prompt | Ask user per failure | |

**User's choice:** Log and skip

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-OCR via Kreuzberg | Tesseract automatically for scanned pages | ✓ |
| Flag only, no OCR | Detect but don't OCR | |
| OCR with quality gate | OCR with confidence threshold | |

**User's choice:** Auto-OCR via Kreuzberg

---

## Triage Report Format

| Option | Description | Selected |
|--------|-------------|----------|
| JSON manifest | Single triage.json, machine-readable | ✓ |
| Markdown summary | Human-readable tables | |
| Both JSON + Markdown | Two files | |

**User's choice:** JSON manifest

| Option | Description | Selected |
|--------|-------------|----------|
| Core fields | filename, path, size, pages, category, parse_type, text_length, errors | ✓ |
| Content preview | First 500 chars of text | |
| Hash for dedup | SHA-256 per file | |
| Extraction readiness score | 0-1 quality estimate | ✓ |

**User's choice:** Core fields + Extraction readiness score (multiselect)

---

## Folder-to-Category Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-detect from path | Parse top-level folder name | ✓ |
| Category mapping file | Explicit categories.yaml | |
| Flat — ignore folders | Category from content later | |

**User's choice:** Auto-detect from path

| Option | Description | Selected |
|--------|-------------|----------|
| Recursive scan | Walk all subdirectories | ✓ |
| Single level only | Direct children only | |

**User's choice:** Recursive scan

---

## Output Directory Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Per-doc text files | ingested/<doc_id>.txt + triage.json | ✓ |
| Single combined JSON | One big ingestion.json | |
| Reuse extractions/ pattern | Mix with extraction output | |

**User's choice:** Per-doc text files

| Option | Description | Selected |
|--------|-------------|----------|
| Sanitized filename | Strip ext, lowercase, underscores | ✓ |
| Category prefix + filename | catering__aramark_contract | |
| Sequential numbering | doc_001, doc_002 | |

**User's choice:** Sanitized filename

---

## Ingestion Script Design

| Option | Description | Selected |
|--------|-------------|----------|
| New scripts/ingest_documents.py | Standalone script, follows existing pattern | ✓ |
| Extend run_sift.py | Add ingest subcommand | |
| Library in scripts/lib/ | Reusable module | |

**User's choice:** New standalone script

---

## Progress Reporting

| Option | Description | Selected |
|--------|-------------|----------|
| Rich progress bar | Per-file status with progress bar | ✓ |
| Per-file log lines | One line per file | |
| Summary only | Silent until end | |

**User's choice:** Rich progress bar

---

## XLS/EML Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Same Kreuzberg path | Run through same pipeline | ✓ |
| Format-specific parsers | openpyxl for XLS, email.parser for EML | |
| Skip for now | Focus on PDFs first | |

**User's choice:** Same Kreuzberg path

---

## Claude's Discretion

- Internal implementation of extraction readiness score heuristic
- Exact triage.json schema beyond specified fields
- Error message format
- Threading/async strategy (single-threaded acceptable)

## Deferred Ideas

None — discussion stayed within phase scope.
