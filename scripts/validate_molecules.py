#!/usr/bin/env python3
"""Orchestrate molecular validation across all extraction JSONs in an output directory.

Scans extraction files for molecular identifiers (SMILES, sequences, CAS numbers,
clinical trial IDs, patents) and validates them with optional RDKit/Biopython support.

Usage:
    python validate_molecules.py <output_dir>
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Import validation helpers from the validation-scripts directory
# ---------------------------------------------------------------------------
VALIDATION_SCRIPTS = Path(__file__).parent.parent / "skills" / "drug-discovery-extraction" / "validation-scripts"
sys.path.insert(0, str(VALIDATION_SCRIPTS))

from scan_patterns import scan_text  # noqa: E402

# Optional: RDKit-based SMILES validation
try:
    from validate_smiles import validate_smiles

    HAS_RDKIT = True
except Exception:
    HAS_RDKIT = False
    validate_smiles = None  # type: ignore[assignment]

# Optional: Biopython-based sequence validation
try:
    from validate_sequences import validate_sequence

    HAS_BIOPYTHON = True
except Exception:
    HAS_BIOPYTHON = False
    validate_sequence = None  # type: ignore[assignment]

# Pattern types that map to each validator
SMILES_TYPES = {"SMILES", "SMILES_STANDALONE"}
SEQUENCE_TYPES = {"DNA_SEQUENCE", "RNA_SEQUENCE", "AMINO_ACID_SEQ"}
REPORT_ONLY_TYPES = {"CAS_NUMBER", "NCT_NUMBER", "US_PATENT", "PCT_PATENT", "InChI", "InChIKey", "SEQ_ID_NO"}


def collect_texts(extraction: dict) -> list[tuple[str, str]]:
    """Collect (field_path, text) pairs from entity context and relation evidence."""
    texts: list[tuple[str, str]] = []

    for i, entity in enumerate(extraction.get("entities", [])):
        ctx = entity.get("context", "")
        if ctx:
            texts.append((f"entities[{i}].context", ctx))

    for i, relation in enumerate(extraction.get("relations", [])):
        evidence = relation.get("evidence", "")
        if evidence:
            texts.append((f"relations[{i}].evidence", evidence))

    return texts


def validate_match(match: dict) -> dict:
    """Run appropriate validator on a pattern match and return enriched result."""
    result = {
        "pattern_type": match["pattern_type"],
        "value": match["value"],
        "entity_type": match["entity_type"],
        "context": match.get("context", ""),
    }

    ptype = match["pattern_type"]

    if ptype in SMILES_TYPES:
        if HAS_RDKIT and validate_smiles is not None:
            validation = validate_smiles(match["value"])
            result["validation"] = validation
            valid_flag = validation.get("valid")
            if valid_flag is True:
                result["status"] = "valid"
            elif valid_flag is False:
                result["status"] = "invalid"
            else:
                result["status"] = "unvalidated"
        else:
            result["validation"] = None
            result["status"] = "unvalidated"
            result["note"] = "RDKit not available"

    elif ptype in SEQUENCE_TYPES:
        if HAS_BIOPYTHON and validate_sequence is not None:
            # Map pattern type to sequence type hint
            type_hint = None
            if ptype == "DNA_SEQUENCE":
                type_hint = "DNA"
            elif ptype == "RNA_SEQUENCE":
                type_hint = "RNA"
            elif ptype == "AMINO_ACID_SEQ":
                type_hint = "protein"
            validation = validate_sequence(match["value"], type_hint)
            result["validation"] = validation
            valid_flag = validation.get("valid")
            if valid_flag is True:
                result["status"] = "valid"
            elif valid_flag is False:
                result["status"] = "invalid"
            else:
                result["status"] = "unvalidated"
        else:
            result["validation"] = None
            result["status"] = "unvalidated"
            result["note"] = "Biopython not available"

    elif ptype in REPORT_ONLY_TYPES:
        result["validation"] = None
        result["status"] = "found"

    else:
        result["validation"] = None
        result["status"] = "found"

    return result


def process_extraction(filepath: Path) -> dict:
    """Process a single extraction JSON file and return validation results."""
    data = json.loads(filepath.read_text(encoding="utf-8"))
    texts = collect_texts(data)

    matches: list[dict] = []
    for field_path, text in texts:
        for match in scan_text(text):
            match["source_field"] = field_path
            matches.append(match)

    validated: list[dict] = []
    for match in matches:
        result = validate_match(match)
        result["source_file"] = filepath.name
        result["source_field"] = match.get("source_field", "")
        validated.append(result)

    return {
        "file": filepath.name,
        "document_id": data.get("document_id", ""),
        "matches_found": len(validated),
        "results": validated,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output_dir>", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    extractions_dir = output_dir / "extractions"

    if not extractions_dir.is_dir():
        print(f"Error: extractions directory not found: {extractions_dir}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(extractions_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {extractions_dir}", file=sys.stderr)
        sys.exit(1)

    all_results: list[dict] = []
    stats = {
        "files_scanned": 0,
        "total_matches": 0,
        "valid": 0,
        "invalid": 0,
        "unvalidated": 0,
        "found": 0,
        "by_type": {},
    }

    for filepath in json_files:
        try:
            file_result = process_extraction(filepath)
        except Exception as exc:
            file_result = {
                "file": filepath.name,
                "document_id": "",
                "matches_found": 0,
                "results": [],
                "error": str(exc),
            }

        all_results.append(file_result)
        stats["files_scanned"] += 1
        stats["total_matches"] += file_result["matches_found"]

        for r in file_result["results"]:
            status = r.get("status", "found")
            if status in stats:
                stats[status] += 1
            else:
                stats[status] = 1

            ptype = r.get("pattern_type", "unknown")
            stats["by_type"][ptype] = stats["by_type"].get(ptype, 0) + 1

    # Add availability info
    stats["rdkit_available"] = HAS_RDKIT
    stats["biopython_available"] = HAS_BIOPYTHON

    # Save results
    validation_dir = output_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "stats": stats,
        "files": all_results,
    }

    results_path = validation_dir / "results.json"
    results_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")

    # Print summary stats to stdout
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
