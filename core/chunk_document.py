#!/usr/bin/env python3
"""Clause-aware document chunker for contract text.

Splits ingested text at legal section boundaries (Article, Section, numbered
clauses) to keep legal context intact. Falls back to paragraph-based ~10K
character chunks when no clause structure is detected.

Usage:
    python chunk_document.py <doc_id> <output_dir>
    python chunk_document.py <doc_id> <output_dir> --max-size 10000
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CHUNK_SIZE = 10000
MIN_CHUNK_SIZE = 500

# Regex patterns for section headers (ordered by specificity)
SECTION_PATTERNS = [
    re.compile(r"^(ARTICLE\s+[IVXLCDM\d]+[.:]\s*.*)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(Section\s+\d+[\.\d]*[.:]\s*.*)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(\d+\.\d+[\.\d]*\s+[A-Z].*)$", re.MULTILINE),
    re.compile(r"^([A-Z][A-Z\s]{3,}:?\s*)$", re.MULTILINE),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_at_sections(text: str) -> list[tuple[str, str, int]]:
    """Find section boundaries and split text.

    Returns:
        List of (header, body_text, char_offset) tuples.
        Preamble (text before first header) has header="".
    """
    # Collect all matches across all patterns
    matches: list[tuple[int, str]] = []
    for pattern in SECTION_PATTERNS:
        for m in pattern.finditer(text):
            matches.append((m.start(), m.group(1).strip()))

    if not matches:
        return [("", text, 0)]

    # Sort by position
    matches.sort(key=lambda x: x[0])

    # Deduplicate overlapping matches (keep earliest at each position)
    deduped: list[tuple[int, str]] = []
    for pos, header in matches:
        if not deduped or pos > deduped[-1][0]:
            deduped.append((pos, header))

    sections: list[tuple[str, str, int]] = []

    # Preamble before first header
    if deduped[0][0] > 0:
        preamble = text[: deduped[0][0]].strip()
        if preamble:
            sections.append(("", preamble, 0))

    # Each section: from this header to the next
    for i, (pos, header) in enumerate(deduped):
        if i + 1 < len(deduped):
            body = text[pos : deduped[i + 1][0]].strip()
        else:
            body = text[pos:].strip()
        sections.append((header, body, pos))

    return sections


def _merge_small_sections(
    sections: list[tuple[str, str, int]],
    doc_id: str,
    max_size: int,
) -> list[dict]:
    """Merge consecutive small sections and split oversized ones.

    Args:
        sections: List of (header, body_text, char_offset) tuples.
        doc_id: Document identifier for chunk_id generation.
        max_size: Maximum chunk size in characters.

    Returns:
        List of chunk dicts.
    """
    chunks: list[dict] = []
    buffer_header = ""
    buffer_text = ""
    buffer_offset = 0

    def _flush() -> None:
        nonlocal buffer_header, buffer_text, buffer_offset
        if not buffer_text.strip():
            return
        if len(buffer_text) > max_size:
            # Split oversized section at paragraph boundaries
            sub_chunks = _split_at_paragraphs(buffer_text, max_size)
            for j, sub in enumerate(sub_chunks):
                chunks.append({
                    "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
                    "text": sub,
                    "section_header": buffer_header if j == 0 else f"{buffer_header} (cont.)",
                    "char_offset": buffer_offset,
                })
        else:
            chunks.append({
                "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
                "text": buffer_text,
                "section_header": buffer_header,
                "char_offset": buffer_offset,
            })
        buffer_header = ""
        buffer_text = ""
        buffer_offset = 0

    # Check if header is a major section (ARTICLE-level) boundary
    _major_re = re.compile(r"^ARTICLE\s+", re.IGNORECASE)

    for header, body, offset in sections:
        is_major = bool(_major_re.match(header))

        if not buffer_text:
            buffer_header = header
            buffer_text = body
            buffer_offset = offset
        elif is_major:
            # Always flush at major (ARTICLE) boundaries
            _flush()
            buffer_header = header
            buffer_text = body
            buffer_offset = offset
        elif len(buffer_text) + len(body) < max_size:
            # Merge sub-sections within the same article
            buffer_text = buffer_text + "\n\n" + body
        else:
            _flush()
            buffer_header = header
            buffer_text = body
            buffer_offset = offset

    _flush()
    return chunks


def _split_at_paragraphs(text: str, max_size: int) -> list[str]:
    """Split text at paragraph boundaries (double newline) up to max_size."""
    paragraphs = re.split(r"\n\n+", text)
    result: list[str] = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) + 2 > max_size:
            result.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        result.append(current.strip())

    return result if result else [text]


def _split_fixed(text: str, doc_id: str, max_size: int) -> list[dict]:
    """Split text at paragraph boundaries into fixed-size chunks.

    Used as fallback when no clause structure is detected.

    Args:
        text: Full document text.
        doc_id: Document identifier.
        max_size: Maximum chunk size in characters.

    Returns:
        List of chunk dicts with section_header="".
    """
    parts = _split_at_paragraphs(text, max_size)
    chunks: list[dict] = []
    offset = 0

    for part in parts:
        chunks.append({
            "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
            "text": part,
            "section_header": "",
            "char_offset": offset,
        })
        offset += len(part)

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_document(
    text: str,
    doc_id: str,
    max_size: int = MAX_CHUNK_SIZE,
) -> list[dict]:
    """Split document text into chunks at clause boundaries.

    Tries clause-aware splitting first. If no section structure is detected,
    falls back to paragraph-based fixed-size chunks.

    Args:
        text: Full document text from ingested/<doc_id>.txt.
        doc_id: Document identifier.
        max_size: Maximum chunk size in characters.

    Returns:
        List of chunk dicts with keys: chunk_id, text, section_header, char_offset.
    """
    sections = _split_at_sections(text)
    if len(sections) > 1:
        return _merge_small_sections(sections, doc_id, max_size)
    # Fallback: paragraph-based fixed-size chunks
    return _split_fixed(text, doc_id, max_size)


def chunk_document_to_files(
    doc_id: str,
    output_dir: str | Path,
    max_size: int = MAX_CHUNK_SIZE,
) -> Path:
    """Read ingested text and write chunk files to disk.

    Reads: {output_dir}/ingested/{doc_id}.txt
    Writes: {output_dir}/ingested/{doc_id}_chunks/chunk_NNN.json

    Args:
        doc_id: Document identifier.
        output_dir: Base output directory.
        max_size: Maximum chunk size in characters.

    Returns:
        Path to the chunks directory.
    """
    output_dir = Path(output_dir)
    source = output_dir / "ingested" / f"{doc_id}.txt"
    text = source.read_text(encoding="utf-8")

    chunks = chunk_document(text, doc_id, max_size)

    chunk_dir = output_dir / "ingested" / f"{doc_id}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    for chunk in chunks:
        path = chunk_dir / f"{chunk['chunk_id']}.json"
        path.write_text(json.dumps(chunk, indent=2), encoding="utf-8")

    return chunk_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python chunk_document.py <doc_id> <output_dir> [--max-size N]")
        sys.exit(1)

    doc_id = sys.argv[1]
    output_dir = sys.argv[2]
    max_size = MAX_CHUNK_SIZE

    if "--max-size" in sys.argv:
        idx = sys.argv.index("--max-size")
        max_size = int(sys.argv[idx + 1])

    chunk_dir = chunk_document_to_files(doc_id, output_dir, max_size)
    chunk_count = len(list(chunk_dir.glob("*.json")))

    result = {
        "doc_id": doc_id,
        "chunks": chunk_count,
        "chunk_dir": str(chunk_dir),
    }
    print(json.dumps(result, indent=2))
