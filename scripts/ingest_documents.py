#!/usr/bin/env python3
"""Document ingestion pipeline for cross-domain knowledge graph framework.

Discovers, parses, and triages documents from a local corpus directory.
Produces per-document text files and a triage.json metadata report.

Usage:
    python ingest_documents.py /path/to/corpus --output ./output --domain contract
    python ingest_documents.py /path/to/corpus --output ./output --triage-only
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from sift_kg.ingest.reader import read_document

    HAS_SIFT_READER = True
except ImportError:
    HAS_SIFT_READER = False

try:
    from rich.progress import Progress

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
KNOWN_CATEGORIES = {"hotel", "pcc", "av", "catering", "security", "ems"}
SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".xls",
    ".xlsx",
    ".eml",
    ".doc",
    ".docx",
    ".txt",
    ".html",
    ".htm",
}

# Regex for detecting section headers and numbered clauses
_STRUCTURE_RE = re.compile(
    r"(^section\s+\d+|^\d+\.\s+|^article\s+\d+|^[A-Z][A-Z\s]{3,}$)",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def discover_corpus(corpus_path: Path) -> list[Path]:
    """Recursively discover all supported files under corpus_path.

    Args:
        corpus_path: Root directory to scan.

    Returns:
        Sorted list of Path objects for files with supported extensions.
    """
    corpus_path = Path(corpus_path)
    files = [
        p
        for p in corpus_path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def sanitize_doc_id(filename: str) -> str:
    """Convert a filename to a sanitized document ID.

    Strips extension, lowercases, replaces non-alphanumeric chars with underscore.

    Args:
        filename: Original filename (e.g. 'Aramark Contract.pdf').

    Returns:
        Sanitized ID string (e.g. 'aramark_contract').
    """
    name = Path(filename).stem
    sanitized = re.sub(r"[^a-z0-9_]", "_", name.lower())
    return sanitized.lstrip("_")


def detect_category(file_path: Path, corpus_root: Path) -> str:
    """Detect document category from its top-level folder name.

    Args:
        file_path: Path to the document file.
        corpus_root: Root corpus directory.

    Returns:
        Lowercase category string, or 'uncategorized' if not recognized.
    """
    try:
        relative = Path(file_path).relative_to(Path(corpus_root))
    except ValueError:
        return "uncategorized"

    parts = relative.parts
    if len(parts) < 2:
        # File is directly in corpus_root, no subfolder
        return "uncategorized"

    top_folder = parts[0].lower()
    if top_folder in KNOWN_CATEGORIES:
        return top_folder
    return "uncategorized"


def parse_document(file_path: Path) -> str | dict:
    """Parse a document and extract its text content.

    Uses sift-kg's read_document when available, with a plain-text fallback
    for .txt files.

    Args:
        file_path: Path to the document file.

    Returns:
        Extracted text string on success, or error dict on failure.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return {"error": f"File not found: {file_path}", "file": str(file_path)}

    if HAS_SIFT_READER:
        try:
            text = read_document(file_path)
            return text if isinstance(text, str) else str(text)
        except Exception as e:
            return {"error": str(e), "file": str(file_path)}

    # Fallback: plain text for .txt files
    if file_path.suffix.lower() == ".txt":
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": str(e), "file": str(file_path)}

    return {
        "error": "sift-kg reader not available and file is not .txt",
        "file": str(file_path),
    }


def compute_readiness_score(text: str, file_size: int) -> float:
    """Compute a heuristic extraction-readiness score for a document.

    Score components (0.0-1.0):
    - Text density: text_length / file_size ratio (weight 0.4)
    - Structure signals: section headers / numbered clauses (weight 0.3)
    - Minimum length threshold (weight 0.3)

    Args:
        text: Extracted document text.
        file_size: File size in bytes.

    Returns:
        Readiness score rounded to 2 decimal places.
    """
    if file_size <= 0:
        return 0.0

    # Text density (capped at 1.0)
    density = min(len(text) / file_size, 1.0) * 0.4

    # Structure signals
    structure_matches = len(_STRUCTURE_RE.findall(text))
    structure_score = min(structure_matches / 10.0, 1.0) * 0.3

    # Minimum length threshold
    if len(text) > 500:
        length_score = 0.3
    elif len(text) > 100:
        length_score = 0.15
    else:
        length_score = 0.0

    return round(density + structure_score + length_score, 2)


def classify_parse_type(text: str, file_size: int) -> str:
    """Classify the parse type based on text density.

    Args:
        text: Extracted document text.
        file_size: File size in bytes.

    Returns:
        'text' for text-native, 'scanned' for OCR-heavy, 'mixed' otherwise.
    """
    if file_size <= 0:
        return "text"

    density = len(text) / file_size
    if density > 0.1:
        return "text"
    elif density < 0.01:
        return "scanned"
    return "mixed"


def build_document_metadata(
    file_path: Path,
    corpus_root: Path,
    text: str | dict,
    doc_id: str,
) -> dict:
    """Build per-document metadata dict.

    Args:
        file_path: Path to the document file.
        corpus_root: Root corpus directory.
        text: Extracted text (str) or error dict.
        doc_id: Sanitized document ID.

    Returns:
        Metadata dictionary with parse status, category, readiness score, etc.
    """
    file_path = Path(file_path)
    file_size = file_path.stat().st_size if file_path.exists() else 0

    return {
        "doc_id": doc_id,
        "filename": file_path.name,
        "file_path": str(file_path),
        "file_size_bytes": file_size,
        "page_count": None,
        "category": detect_category(file_path, corpus_root),
        "parse_type": classify_parse_type(text, file_size)
        if isinstance(text, str)
        else "failed",
        "text_length": len(text) if isinstance(text, str) else 0,
        "parse_errors": text.get("error", None) if isinstance(text, dict) else None,
        "extraction_readiness_score": compute_readiness_score(text, file_size)
        if isinstance(text, str)
        else 0.0,
    }


def ingest_corpus(
    corpus_path: Path,
    output_dir: Path,
    domain_name: str | None = None,
) -> dict:
    """Ingest a corpus of documents: discover, parse, save text, produce triage report.

    Args:
        corpus_path: Root directory containing documents.
        output_dir: Output directory for ingested text and triage.json.
        domain_name: Optional domain name for metadata.

    Returns:
        Triage dict with counts and per-document metadata.
    """
    corpus_path = Path(corpus_path)
    output_dir = Path(output_dir)

    if not corpus_path.exists():
        print(f"Error: corpus path does not exist: {corpus_path}", file=sys.stderr)
        return {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "documents": [],
        }

    ingested_dir = output_dir / "ingested"
    ingested_dir.mkdir(parents=True, exist_ok=True)

    files = discover_corpus(corpus_path)
    documents: list[dict] = []
    successful = 0
    failed = 0

    if HAS_RICH:
        progress = Progress()
        task = progress.add_task("Ingesting documents...", total=len(files))
        progress.start()
    else:
        progress = None

    for file_path in files:
        doc_id = sanitize_doc_id(file_path.name)
        text = parse_document(file_path)
        metadata = build_document_metadata(file_path, corpus_path, text, doc_id)
        documents.append(metadata)

        if isinstance(text, str):
            txt_path = ingested_dir / f"{doc_id}.txt"
            txt_path.write_text(text, encoding="utf-8")
            successful += 1
        else:
            print(
                f"Warning: failed to parse {file_path.name}: {text.get('error', 'unknown')}",
                file=sys.stderr,
            )
            failed += 1

        if progress is not None:
            progress.advance(task)

    if progress is not None:
        progress.stop()

    triage = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "corpus_path": str(corpus_path),
        "domain": domain_name,
        "total_files": len(files),
        "successful": successful,
        "failed": failed,
        "documents": documents,
    }

    triage_path = output_dir / "triage.json"
    triage_path.write_text(json.dumps(triage, indent=2), encoding="utf-8")

    print(
        f"\nIngestion complete: {successful} succeeded, {failed} failed out of {len(files)} files"
    )
    print(f"Triage report: {triage_path}")

    return triage


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    corpus = Path(sys.argv[1])
    output = (
        Path(sys.argv[sys.argv.index("--output") + 1])
        if "--output" in sys.argv
        else Path("./epistract-output")
    )
    domain = (
        sys.argv[sys.argv.index("--domain") + 1] if "--domain" in sys.argv else None
    )

    result = ingest_corpus(corpus, output, domain)
    print(
        json.dumps(
            {
                "status": "complete",
                "total": result["total_files"],
                "successful": result["successful"],
                "failed": result["failed"],
            },
            indent=2,
        )
    )
