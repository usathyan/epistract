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
# Required dependency: chonkie (Phase 14 FIDL-03, D-08, D-09)
# ---------------------------------------------------------------------------
# chonkie is REQUIRED for sentence-aware chunking with overlap. If missing
# we raise at import time — no silent fallback, because running the chunker
# without overlap IS the bug this module fixes. /epistract:setup installs it
# as a required dep.

try:
    from chonkie import SentenceChunker  # noqa: F401  re-exported via _make_chunker
    HAS_CHONKIE = True
except ImportError as e:  # pragma: no cover — covered by UT-035 with stubbed import
    raise ImportError(
        "chonkie is required for chunk overlap (Phase 14 FIDL-03). "
        "Install it with: uv pip install 'chonkie>=1.0'  "
        "or run /epistract:setup which installs it as a required dep. "
        "No silent fallback — running without overlap silently is the bug "
        "this module fixes."
    ) from e


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CHUNK_SIZE = 10000
MIN_CHUNK_SIZE = 500

# Overlap parameters (Phase 14 FIDL-03, D-02, D-03). Hardcoded per D-06/D-07
# — no CLI flag, no env var. Three sentences captures enough antecedent
# context for pronoun and multi-sentence relations; 1500 chars prevents a
# pathological "whereas…" block from dominating the next chunk.
OVERLAP_SENTENCES = 3
OVERLAP_MAX_CHARS = 1500

# Sentence boundary regex — matches chonkie's default delim set
# (`. `, `! `, `? `, `\n`). Used only by _tail_sentences, which runs on
# short tails; chonkie owns all chunk-level segmentation.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")

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

def _make_chunker(max_size: int = MAX_CHUNK_SIZE) -> SentenceChunker:
    """Return a configured chonkie SentenceChunker.

    Centralizes the chunker configuration so both Plan 14-03 call sites
    (`_merge_small_sections::_flush` on oversized sections, and
    `_split_fixed` end-to-end for the no-structure fallback) get identical
    behavior, and so future phases can tweak the chunker's shape in one
    place.

    Args:
        max_size: Soft upper bound on chunk size, in characters.

    Returns:
        SentenceChunker with character tokenizer, OVERLAP_MAX_CHARS overlap,
        min_sentences_per_chunk=1.
    """
    return SentenceChunker(
        tokenizer="character",
        chunk_size=max_size,
        chunk_overlap=OVERLAP_MAX_CHARS,
        min_sentences_per_chunk=1,
    )


def _tail_sentences(
    text: str,
    n: int = OVERLAP_SENTENCES,
    max_chars: int = OVERLAP_MAX_CHARS,
) -> str:
    """Return the last n sentences of `text`, capped at `max_chars`.

    Used by `_merge_small_sections::_flush` to carry overlap across
    hard-flush boundaries (ARTICLE transitions, small-section merges) that
    chonkie's intra-chunk overlap cannot span. Within an oversized section,
    `_make_chunker(...).chunk(body)` handles overlap directly — this helper
    is NOT called in that path.

    Sentence segmentation uses a regex matching chonkie's default delim
    set (`. `, `! `, `? `, `\\n`). This is an intentional approximation
    (chonkie's internal segmenter is slightly more robust to edge cases
    like "Dr. Smith"), but: (a) the helper operates on already-buffered
    section bodies which are typically structured prose, not dialogue,
    (b) mismatched sentence detection between here and chonkie can at
    most misattribute a sentence boundary at a cross-flush transition —
    a minor provenance wobble, not a correctness bug, (c) the helper is
    pure and side-effect-free, callable in hot paths without chonkie setup
    overhead.

    Behavior (Phase 14 D-02, D-03):
      - Empty `text` → returns "".
      - Fewer than n sentences → returns all sentences.
      - Cumulative length of last-n sentences ≤ max_chars → returns those
        n sentences.
      - Cumulative length > max_chars → returns the most-recent whole
        sentences that fit under the cap; NEVER mid-sentence truncation.
      - A single sentence longer than max_chars → returns "".

    The helper is pure: no side effects, no I/O, no module-state mutation.

    Args:
        text: Source text to pull a sentence-level tail from.
        n: Maximum number of trailing sentences to include.
        max_chars: Hard cap on the returned string's length.

    Returns:
        Overlap tail ending on a sentence boundary, or "".
    """
    if not text:
        return ""

    # Find sentence spans. We split on boundaries and keep the punctuation
    # attached to the sentence preceding it, matching chonkie's
    # "include_delim=prev" default.
    spans: list[tuple[int, int]] = []
    prev_end = 0
    for m in _SENTENCE_BOUNDARY.finditer(text):
        spans.append((prev_end, m.start()))
        prev_end = m.end()
    tail_end = len(text.rstrip())
    if prev_end < tail_end:
        spans.append((prev_end, tail_end))

    # Drop any empty spans (can happen at string start/end)
    spans = [(s, e) for s, e in spans if text[s:e].strip()]
    if not spans:
        return ""

    # Take up to the last n sentences.
    tail = spans[-n:]

    # Walk right-to-left, accumulating sentences that fit under max_chars.
    selected: list[tuple[int, int]] = []
    total = 0
    for start, end in reversed(tail):
        piece_len = end - start
        added = piece_len if not selected else piece_len + 1  # +1 for join space
        if total + added > max_chars:
            break
        selected.append((start, end))
        total += added

    if not selected:
        # Single sentence larger than cap — refuse mid-sentence cut.
        return ""

    # Re-reverse to document order, slice original text between first.start
    # and last.end so intra-tail whitespace is preserved exactly.
    selected.reverse()
    return text[selected[0][0] : selected[-1][1]]


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
    """Merge consecutive small sections and split oversized ones via chonkie.

    Oversized sections are handed to `_make_chunker(max_size).chunk(buffer_text)`
    which emits sentence-boundary-preserving sub-chunks with OVERLAP_MAX_CHARS
    of intra-flush overlap. Cross-flush overlap (ARTICLE boundaries, merge
    transitions) is carried by a nonlocal `_pending_tail` cache populated
    from the RAW body via `_tail_sentences` (M-1/M-2 invariant).

    Args:
        sections: List of (header, body_text, char_offset) tuples.
        doc_id: Document identifier for chunk_id generation.
        max_size: Maximum chunk size in characters (before overlap prefix).

    Returns:
        List of chunk dicts with keys: chunk_id, text, section_header,
        char_offset, overlap_prev_chars, overlap_next_chars, is_overlap_region.
    """
    chunks: list[dict] = []
    buffer_header = ""
    buffer_text = ""
    buffer_offset = 0
    # Cross-flush overlap cache (Phase 14 M-1/M-2). Holds the tail of the
    # PREVIOUS flush's RAW body so the next flush can prepend it WITHOUT
    # re-reading an already-overlap-prefixed chunk text (which would
    # chain overlaps across flushes).
    _pending_tail = ""

    def _flush() -> None:
        nonlocal buffer_header, buffer_text, buffer_offset, _pending_tail
        if not buffer_text.strip():
            return

        incoming = _pending_tail  # from nonlocal cache, NOT chunks[-1]["text"]

        if len(buffer_text) > max_size:
            # Oversized section: delegate to chonkie for sentence-aware splitting.
            chunker = _make_chunker(max_size)
            sub_chunks = chunker.chunk(buffer_text)
            # Fall-back safety: if chonkie returns zero chunks (shouldn't happen
            # for non-empty input, but defensive), emit the whole buffer as one.
            if not sub_chunks:
                text_with_overlap = (
                    incoming + "\n\n" + buffer_text if incoming else buffer_text
                )
                chunks.append({
                    "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
                    "text": text_with_overlap,
                    "section_header": buffer_header,
                    "char_offset": buffer_offset,
                    "overlap_prev_chars": len(incoming),
                    "overlap_next_chars": len(_tail_sentences(buffer_text)),
                    # is_overlap_region reserved for sub-region annotation
                    # (D-10, Deferred Ideas §5). Always False at chunk level.
                    "is_overlap_region": False,
                })
            else:
                for j, cc in enumerate(sub_chunks):
                    # Chunk body from chonkie (already contains intra-flush
                    # overlap prefix when j > 0).
                    body = cc.text

                    # Incoming overlap size:
                    # - j == 0: _pending_tail from previous flush (if any)
                    # - j > 0: delta between this sub-chunk's start and
                    #          previous sub-chunk's end (chonkie-computed overlap)
                    if j == 0:
                        sub_incoming = incoming
                        text_with_overlap = (
                            sub_incoming + "\n\n" + body if sub_incoming else body
                        )
                        overlap_prev = len(sub_incoming)
                    else:
                        prev_end = sub_chunks[j - 1].end_index
                        this_start = cc.start_index
                        overlap_prev = max(0, prev_end - this_start)
                        text_with_overlap = body  # overlap already embedded

                    # Outgoing overlap size:
                    # - j < len-1: delta between next sub-chunk's start and this end
                    # - j == len-1: _tail_sentences(body) — this flush's contribution
                    #               to the NEXT flush; post-loop corrects to 0
                    #               if this is the final chunk of the doc.
                    if j < len(sub_chunks) - 1:
                        this_end = cc.end_index
                        next_start = sub_chunks[j + 1].start_index
                        overlap_next = max(0, this_end - next_start)
                    else:
                        overlap_next = len(_tail_sentences(body))

                    chunks.append({
                        "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
                        "text": text_with_overlap,
                        "section_header": (
                            buffer_header if j == 0 else f"{buffer_header} (cont.)"
                        ),
                        # Honest per-sub-chunk offset (D-11): chonkie's start_index
                        # is relative to buffer_text; add buffer_offset for absolute.
                        "char_offset": buffer_offset + cc.start_index,
                        "overlap_prev_chars": overlap_prev,
                        "overlap_next_chars": overlap_next,
                        # is_overlap_region reserved for sub-region annotation
                        # (D-10, Deferred Ideas §5). Always False at chunk level.
                        "is_overlap_region": False,
                    })
        else:
            # Small section: single chunk, optional incoming prefix.
            text_with_overlap = (
                incoming + "\n\n" + buffer_text if incoming else buffer_text
            )
            outgoing = _tail_sentences(buffer_text)
            chunks.append({
                "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
                "text": text_with_overlap,
                "section_header": buffer_header,
                "char_offset": buffer_offset,
                "overlap_prev_chars": len(incoming),
                "overlap_next_chars": len(outgoing),
                # is_overlap_region reserved for sub-region annotation
                # (D-10, Deferred Ideas §5). Always False at chunk level.
                "is_overlap_region": False,
            })

        # Update cross-flush cache from RAW body (M-1/M-2 invariant).
        _pending_tail = _tail_sentences(buffer_text)

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

    # Final chunk has no "next" — D-10 honest provenance.
    if chunks:
        chunks[-1]["overlap_next_chars"] = 0

    return chunks


def _split_fixed(text: str, doc_id: str, max_size: int) -> list[dict]:
    """Split text at sentence boundaries into ~max_size chunks with overlap.

    Fallback when no clause structure is detected. Uses the same
    SentenceChunker (Phase 14 D-05 — one library reused) as the clause-aware
    path, so boundary-straddling entities and relations are recovered here too.

    Args:
        text: Full document text.
        doc_id: Document identifier.
        max_size: Maximum chunk size in characters (before overlap prefix).

    Returns:
        List of chunk dicts with keys: chunk_id, text, section_header (""),
        char_offset (honest per-chunk), overlap_prev_chars, overlap_next_chars,
        is_overlap_region.
    """
    if not text.strip():
        return []

    chunker = _make_chunker(max_size)
    sub_chunks = chunker.chunk(text)
    if not sub_chunks:
        return []

    chunks: list[dict] = []
    for i, cc in enumerate(sub_chunks):
        if i == 0:
            overlap_prev = 0
        else:
            overlap_prev = max(0, sub_chunks[i - 1].end_index - cc.start_index)

        if i < len(sub_chunks) - 1:
            overlap_next = max(0, cc.end_index - sub_chunks[i + 1].start_index)
        else:
            overlap_next = 0  # final chunk

        chunks.append({
            "chunk_id": f"{doc_id}_chunk_{len(chunks):03d}",
            "text": cc.text,
            "section_header": "",
            "char_offset": cc.start_index,
            "overlap_prev_chars": overlap_prev,
            "overlap_next_chars": overlap_next,
            # is_overlap_region reserved for sub-region annotation
            # (D-10, Deferred Ideas §5). Always False at chunk level.
            "is_overlap_region": False,
        })

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
