#!/usr/bin/env python3
"""Scan text for molecular identifiers using regex patterns.

Detects SMILES strings, InChI/InChIKey identifiers, CAS numbers,
DNA/RNA sequences, amino acid sequences, clinical trial numbers,
and patent references.

Usage:
    python scan_patterns.py <text_file>
    python scan_patterns.py --extraction <extraction_json>
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Pattern definitions: (name, regex, entity_type)
# Order matters: more specific patterns should come before less specific ones
# so that overlap detection gives priority to the right match.
PATTERNS: list[tuple[str, re.Pattern, str]] = [
    (
        "InChIKey",
        re.compile(r"\b[A-Z]{14}-[A-Z]{10}-[A-Z]\b"),
        "CHEMICAL_IDENTIFIER",
    ),
    (
        "InChI",
        re.compile(r"InChI=1S?/[A-Za-z0-9/\.\+\-\(\),]+"),
        "CHEMICAL_IDENTIFIER",
    ),
    (
        "CAS_NUMBER",
        re.compile(r"\b\d{2,7}-\d{2}-\d\b"),
        "CHEMICAL_IDENTIFIER",
    ),
    (
        "SMILES",
        re.compile(
            r"(?:SMILES:\s*)"
            r"([A-Za-z0-9@\+\-\[\]\(\)\\\/=#\$\.\%\:\~\*]{5,})"
        ),
        "CHEMICAL_STRUCTURE",
    ),
    (
        "NCT_NUMBER",
        re.compile(r"\bNCT\d{8}\b"),
        "CLINICAL_TRIAL",
    ),
    (
        "US_PATENT",
        re.compile(r"\bUS\s?\d{1,2}[,\s]?\d{3}[,\s]?\d{3}\s?[A-Z]?\d?\b"),
        "PATENT",
    ),
    (
        "PCT_PATENT",
        re.compile(r"\bPCT/[A-Z]{2}\d{4}/\d{6}\b"),
        "PATENT",
    ),
    (
        "SEQ_ID_NO",
        re.compile(r"\bSEQ\s+ID\s+NO[:\s]*\d+\b", re.IGNORECASE),
        "SEQUENCE_REFERENCE",
    ),
    (
        "DNA_SEQUENCE",
        re.compile(r"\b[ATGCatgc]{15,}\b"),
        "NUCLEOTIDE_SEQUENCE",
    ),
    (
        "RNA_SEQUENCE",
        re.compile(r"\b[AUGCaugc]{15,}\b"),
        "NUCLEOTIDE_SEQUENCE",
    ),
    (
        "AMINO_ACID_SEQ",
        re.compile(r"\b[ACDEFGHIKLMNPQRSTVWY]{10,}\b"),
        "PROTEIN_SEQUENCE",
    ),
    # Standalone SMILES last: requires at least one bracket, ring digit pattern,
    # or = sign to distinguish from normal words.
    (
        "SMILES_STANDALONE",
        re.compile(
            r"(?<![A-Za-z])"
            r"(?=[A-Za-z0-9@\+\-\[\]\(\)\\\/=#\$]*[\[\]\(\)=#@\\\/])"
            r"[A-Za-z0-9@\+\-\[\]\(\)\\\/=#\$]{8,}"
            r"(?![A-Za-z0-9\-])"
        ),
        "CHEMICAL_STRUCTURE",
    ),
]


def scan_text(text: str) -> list[dict]:
    """Scan text for molecular identifiers using regex patterns.

    Args:
        text: The input text to scan.

    Returns:
        List of match dicts with keys: pattern_type, value, start, end,
        entity_type, context.
    """
    results: list[dict] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern_name, pattern, entity_type in PATTERNS:
        for match in pattern.finditer(text):
            # For SMILES with prefix, use group(1) if it exists
            if match.lastindex and match.lastindex >= 1:
                value = match.group(1)
                start = match.start(1)
                end = match.end(1)
            else:
                value = match.group(0)
                start = match.start()
                end = match.end()

            # Skip overlapping spans (first pattern wins)
            span = (start, end)
            if any(
                s <= start < e or s < end <= e for s, e in seen_spans
            ):
                continue

            # DNA vs RNA disambiguation: if it contains U but no T, it's RNA
            if pattern_name == "DNA_SEQUENCE" and "U" in value.upper() and "T" not in value.upper():
                continue
            if pattern_name == "RNA_SEQUENCE" and "T" in value.upper() and "U" not in value.upper():
                continue

            # SMILES_STANDALONE: skip if it looks like a plain English word
            if pattern_name == "SMILES_STANDALONE":
                upper_ratio = sum(1 for c in value if c.isupper()) / len(value)
                has_special = any(c in value for c in "[]()=#@+\\/")
                if upper_ratio < 0.15 and not has_special:
                    continue

            # Build context (50 chars before and after)
            ctx_start = max(0, start - 50)
            ctx_end = min(len(text), end + 50)
            context = text[ctx_start:ctx_end]

            seen_spans.add(span)
            results.append({
                "pattern_type": pattern_name.replace("_STANDALONE", ""),
                "value": value,
                "start": start,
                "end": end,
                "entity_type": entity_type,
                "context": context,
            })

    # Sort by position
    results.sort(key=lambda r: r["start"])
    return results


def scan_extraction(extraction_data: dict) -> list[dict]:
    """Scan context and evidence fields in an extraction JSON object."""
    all_results: list[dict] = []
    fields_to_scan = ["context", "evidence", "text", "description", "notes"]

    def _recurse(obj: object, path: str = "") -> None:
        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, str) and key.lower() in fields_to_scan:
                    matches = scan_text(val)
                    for m in matches:
                        m["source_field"] = f"{path}.{key}" if path else key
                    all_results.extend(matches)
                else:
                    _recurse(val, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _recurse(item, f"{path}[{i}]")

    _recurse(extraction_data)
    return all_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan text for molecular identifiers using regex patterns."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "text_file",
        nargs="?",
        help="Path to a plain text file to scan.",
    )
    group.add_argument(
        "--extraction",
        metavar="JSON_FILE",
        help="Path to an extraction JSON file (scans context/evidence fields).",
    )
    args = parser.parse_args()

    if args.extraction:
        path = Path(args.extraction)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        data = json.loads(path.read_text(encoding="utf-8"))
        results = scan_extraction(data)
    else:
        path = Path(args.text_file)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        results = scan_text(text)

    if not results:
        print("No molecular identifiers found.")
        sys.exit(0)

    print(json.dumps(results, indent=2))
    print(f"\n--- {len(results)} pattern(s) found ---")


if __name__ == "__main__":
    main()
