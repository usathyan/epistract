#!/usr/bin/env python3
"""Pre-process extraction JSON files for contract entity resolution.

Runs BEFORE sift-kg build to normalize legal entity names and resolve aliases.
Modifies extraction files in-place.

Usage:
    python entity_resolution.py <output_dir>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEGAL_SUFFIXES = [
    "llc", "l.l.c.", "inc", "inc.", "incorporated",
    "corp", "corp.", "corporation", "co.", "company",
    "ltd", "ltd.", "limited", "lp", "l.p.",
    "llp", "l.l.p.", "pllc", "p.l.l.c.",
]

PROTECTED_NAMES = {"pennsylvania convention center authority"}

DEFINED_TERM_PATTERN = re.compile(
    r'(?:hereinafter|hereafter|referred to as|known as)\s+["\u201c]([^"\u201d]+)["\u201d]',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_party_name(name: str) -> str:
    """Strip legal suffixes and normalize party names.

    Handles LLC, Inc, Corp, Co., Ltd, LP, LLP, PLLC suffixes.
    Preserves names in PROTECTED_NAMES (e.g., "Authority" in proper names).

    Args:
        name: Raw party name from extraction.

    Returns:
        Normalized party name with legal suffixes removed.
    """
    normalized = name.strip()
    lower = normalized.lower()

    # Check protected names first
    if lower in PROTECTED_NAMES:
        return normalized

    for suffix in LEGAL_SUFFIXES:
        if lower.endswith(suffix):
            normalized = normalized[: -len(suffix)].rstrip(" ,.")
            break

    return normalized.strip()


def extract_defined_aliases(text: str) -> list[str]:
    """Extract defined-term aliases from contract text.

    Finds patterns like 'hereinafter referred to as "Caterer"' and
    returns the alias names.

    Args:
        text: Contract text to search.

    Returns:
        List of alias names found.
    """
    return [m.group(1) for m in DEFINED_TERM_PATTERN.finditer(text)]


def merge_chunk_extractions(chunks: list[dict], doc_id: str) -> dict:
    """Merge chunk-level extractions into one document extraction.

    Deduplicates entities by (name.lower(), entity_type) key, taking
    the maximum confidence across occurrences. Relations are preserved
    without deduplication.

    Args:
        chunks: List of chunk extraction dicts (each has entities + relations).
        doc_id: Document identifier.

    Returns:
        Merged dict with entities, relations, and chunks_processed count.
    """
    all_entities: list[dict] = []
    all_relations: list[dict] = []
    seen_entities: dict[tuple[str, str], int] = {}  # key -> index in all_entities

    for chunk in chunks:
        for entity in chunk.get("entities", []):
            key = (entity["name"].lower(), entity["entity_type"])
            if key not in seen_entities:
                seen_entities[key] = len(all_entities)
                all_entities.append(dict(entity))
            else:
                # Update confidence to max across chunks
                idx = seen_entities[key]
                all_entities[idx]["confidence"] = max(
                    all_entities[idx]["confidence"],
                    entity["confidence"],
                )
                # Merge attributes if present
                if "attributes" in entity and "attributes" in all_entities[idx]:
                    all_entities[idx]["attributes"].update(entity["attributes"])
                elif "attributes" in entity:
                    all_entities[idx]["attributes"] = dict(entity["attributes"])

        all_relations.extend(chunk.get("relations", []))

    return {
        "entities": all_entities,
        "relations": all_relations,
        "chunks_processed": len(chunks),
    }


def preprocess_extractions(output_dir: Path) -> dict:
    """Pre-process all extraction files for contract entity resolution.

    Normalizes PARTY entity names via normalize_party_name. Modifies
    extraction JSON files in-place.

    Args:
        output_dir: Base output directory containing extractions/.

    Returns:
        Stats dict with counts of normalizations performed.
    """
    extractions_dir = output_dir / "extractions"
    files_processed = 0
    names_normalized = 0

    if not extractions_dir.exists():
        return {"files_processed": 0, "names_normalized": 0}

    for path in sorted(extractions_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        modified = False

        for entity in data.get("entities", []):
            if entity.get("entity_type") == "PARTY":
                original = entity["name"]
                normalized = normalize_party_name(original)
                if normalized != original:
                    entity["name"] = normalized
                    names_normalized += 1
                    modified = True

        if modified:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        files_processed += 1

    return {
        "files_processed": files_processed,
        "names_normalized": names_normalized,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python entity_resolution.py <output_dir>")
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"Error: directory {output_dir} does not exist")
        sys.exit(1)

    stats = preprocess_extractions(output_dir)
    print(json.dumps(stats, indent=2))
