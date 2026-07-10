#!/usr/bin/env python3
"""Per-project hybrid search index: SQLite FTS5 (BM25) with rank fusion.

Zero-server local index — one `index.db` file per project under
<root>/.epistract/, following the 2025-26 practitioner consensus for
local hybrid search (SQLite FTS5 + optional vector table + reciprocal
rank fusion; see docs/plans/2026-07-04-multi-project-cli-TODO.md).

What gets indexed:
- Document chunks: every file in <root>/corpus/ and <root>/ingested/.
  Plain-text formats are read directly; other formats go through
  Kreuzberg when available, otherwise they are skipped with a warning.
- Entities: nodes from <root>/graph_data.json when a graph has been built.

Incremental by content hash: `index_project` skips any document whose
sha256 already matches the indexed version (iText2KG-style delta insert,
arXiv 2409.03284) — re-indexing an unchanged project is a no-op.

Search fuses entity hits and chunk hits with reciprocal rank fusion:
    score(item) = sum over lists of 1 / (RRF_K + rank)
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from .registry import STATE_DIRNAME

INDEX_FILENAME = "index.db"
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".text", ".csv", ".json", ".html", ".htm"}
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
RRF_K = 60

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id     TEXT PRIMARY KEY,
    sha256     TEXT NOT NULL,
    source_path TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    indexed_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content, doc_id UNINDEXED, chunk_no UNINDEXED
);
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    name, entity_type UNINDEXED, node_id UNINDEXED
);
"""


def index_path(project: dict) -> Path:
    return Path(project["root"]) / STATE_DIRNAME / INDEX_FILENAME


def open_index(project: dict) -> sqlite3.Connection:
    path = index_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(_SCHEMA)
    return connection


# ---------------------------------------------------------------------------
# Text extraction & chunking
# ---------------------------------------------------------------------------


def _extract_text(path: Path) -> str | None:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="ignore")
    try:
        from kreuzberg import extract_file_sync

        return extract_file_sync(str(path)).content
    except Exception as e:  # noqa: BLE001 — any extraction failure means "skip this file"
        print(f"Warning: cannot extract text from {path.name}: {e}", file=sys.stderr)
        return None


def _split_long(paragraph: str, size: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > size:
            parts.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        parts.append(current)
    return parts


def chunk_text(
    text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Paragraph-packing chunker with sentence-boundary splits and tail overlap.

    Fallback used when chonkie (core/chunk_document.py) is unavailable.
    Chunk START boundaries land on paragraph/sentence edges, but the tail
    overlap is a fixed-size character slice (current[-overlap:]) of the
    previous chunk's end, so the overlap window can begin mid-word.
    """
    pieces: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        pieces.extend(
            _split_long(paragraph, size) if len(paragraph) > size else [paragraph]
        )

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) + 2 > size:
            chunks.append(current)
            current = current[-overlap:] + "\n" + piece if overlap else piece
        else:
            current = f"{current}\n{piece}".strip()
    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


def _candidate_documents(project: dict) -> list[Path]:
    root = Path(project["root"])
    candidates: list[Path] = []
    for subdir in ("corpus", "ingested"):
        directory = root / subdir
        if directory.is_dir():
            candidates.extend(p for p in sorted(directory.rglob("*")) if p.is_file())
    return candidates


def index_project(project: dict, rebuild: bool = False) -> dict:
    """Index new/changed documents, drop deleted ones, refresh entities.

    Returns stats: {"indexed": [...], "skipped": n, "failed": [...],
    "removed": n, "chunks": n, "entities": n}.
    """
    if rebuild and index_path(project).exists():
        index_path(project).unlink()
    db = open_index(project)
    root = Path(project["root"])
    stats = {
        "indexed": [],
        "skipped": 0,
        "failed": [],
        "removed": 0,
        "chunks": 0,
        "entities": 0,
    }

    candidates = _candidate_documents(project)
    candidate_ids = {str(p.relative_to(root)) for p in candidates}

    for path in candidates:
        doc_id = str(path.relative_to(root))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        row = db.execute(
            "SELECT sha256 FROM documents WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        if row and row[0] == digest:
            stats["skipped"] += 1
            continue

        text = _extract_text(path)
        if not text or not text.strip():
            stats["failed"].append(doc_id)
            continue
        chunks = chunk_text(text)
        db.execute("DELETE FROM chunks_fts WHERE doc_id = ?", (doc_id,))
        db.executemany(
            "INSERT INTO chunks_fts (content, doc_id, chunk_no) VALUES (?, ?, ?)",
            [(chunk, doc_id, i) for i, chunk in enumerate(chunks)],
        )
        db.execute(
            "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?)",
            (
                doc_id,
                digest,
                str(path),
                len(chunks),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        stats["indexed"].append(doc_id)
        stats["chunks"] += len(chunks)

    # Reconcile: drop rows for documents whose source files were deleted.
    # Per-id DELETEs (not NOT IN over a literal list) — chunks_fts is an
    # FTS5 virtual table and the stale set is small.
    indexed_ids = {row[0] for row in db.execute("SELECT doc_id FROM documents")}
    stale = indexed_ids - candidate_ids
    for doc_id in stale:
        db.execute("DELETE FROM chunks_fts WHERE doc_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    stats["removed"] = len(stale)

    stats["entities"] = _refresh_entities(db, root / "graph_data.json")
    db.commit()
    db.close()
    return stats


def _refresh_entities(db: sqlite3.Connection, graph_path: Path) -> int:
    if not graph_path.exists():
        return 0
    graph = json.loads(graph_path.read_text())
    nodes = graph.get("nodes", [])
    db.execute("DELETE FROM entities_fts")
    db.executemany(
        "INSERT INTO entities_fts (name, entity_type, node_id) VALUES (?, ?, ?)",
        [
            (
                node.get("name", node.get("id", "")),
                node.get("entity_type", ""),
                node.get("id", ""),
            )
            for node in nodes
        ],
    )
    return len(nodes)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def _fts_query(query: str) -> str | None:
    tokens = re.findall(r"[\w-]+", query)
    if not tokens:
        return None
    return " OR ".join(f'"{token}"' for token in tokens)


def search_index(
    project: dict,
    query: str,
    k: int = 10,
    entity_type: str | None = None,
) -> dict:
    """Hybrid search: BM25 over entities and chunks, fused with RRF."""
    match = _fts_query(query)
    if match is None:
        return {"entities": [], "chunks": [], "fused": []}
    db = open_index(project)

    entity_sql = (
        "SELECT name, entity_type, node_id FROM entities_fts "
        "WHERE entities_fts MATCH ?"
    )
    params: list = [match]
    if entity_type:
        entity_sql += " AND upper(entity_type) = upper(?)"
        params.append(entity_type)
    entity_sql += " ORDER BY rank LIMIT ?"
    params.append(k)
    entities = [
        {"name": name, "entity_type": etype, "node_id": node_id}
        for name, etype, node_id in db.execute(entity_sql, params)
    ]

    chunks = [
        {"doc_id": doc_id, "chunk_no": chunk_no, "snippet": content[:300]}
        for content, doc_id, chunk_no in db.execute(
            "SELECT content, doc_id, chunk_no FROM chunks_fts "
            "WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
            (match, k),
        )
    ]
    db.close()

    fused: list[dict] = []
    for rank, entity in enumerate(entities):
        fused.append({"kind": "entity", "score": 1 / (RRF_K + rank), **entity})
    for rank, chunk in enumerate(chunks):
        fused.append({"kind": "chunk", "score": 1 / (RRF_K + rank), **chunk})
    fused.sort(key=lambda item: item["score"], reverse=True)
    return {"entities": entities, "chunks": chunks, "fused": fused[:k]}
