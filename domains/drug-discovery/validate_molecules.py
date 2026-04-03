#!/usr/bin/env python3
"""Orchestrate molecular validation across all extraction JSONs in an output directory.

Scans extraction files for molecular identifiers (SMILES, sequences, CAS numbers,
clinical trial IDs, patents) and validates them with optional RDKit/Biopython support.

Phase 1.5: When --enrich is enabled (default), validated molecules become graph nodes
(CHEMICAL_STRUCTURE, NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE) with HAS_STRUCTURE/HAS_SEQUENCE
relations linking them to parent entities.

Usage:
    python validate_molecules.py <output_dir> [--domain <name>]
    python validate_molecules.py <output_dir> --no-enrich
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Import validation helpers via domain resolver
# ---------------------------------------------------------------------------
VALIDATION_SCRIPTS = Path(__file__).parent / "validation"
sys.path.insert(0, str(VALIDATION_SCRIPTS))

# Domain-aware validation scripts (default: drug-discovery)
_domain_name: str | None = None  # Set via --domain flag in __main__
VALIDATION_SCRIPTS_DIR = get_validation_scripts_dir(_domain_name)

if VALIDATION_SCRIPTS_DIR:
    sys.path.insert(0, str(VALIDATION_SCRIPTS_DIR))

    from scan_patterns import scan_text  # noqa: E402

    # Optional: RDKit-based SMILES validation
    try:
        from validate_smiles import validate_smiles

        HAS_RDKIT = True
    except ImportError:
        HAS_RDKIT = False
        validate_smiles = None  # type: ignore[assignment]

    # Optional: Biopython-based sequence validation
    try:
        from validate_sequences import validate_sequence

        HAS_BIOPYTHON = True
    except ImportError:
        HAS_BIOPYTHON = False
        validate_sequence = None  # type: ignore[assignment]
else:
    # Domain has no validation scripts -- skip all molecular validation
    scan_text = None  # type: ignore[assignment]
    HAS_RDKIT = False
    validate_smiles = None  # type: ignore[assignment]
    HAS_BIOPYTHON = False
    validate_sequence = None  # type: ignore[assignment]

# Pattern types that map to each validator
SMILES_TYPES = {"SMILES", "SMILES_STANDALONE"}
SEQUENCE_TYPES = {"DNA_SEQUENCE", "RNA_SEQUENCE", "AMINO_ACID_SEQ"}


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


def _status_from_validation(validation: dict) -> str:
    """Derive a status string from a validation result dict."""
    valid_flag = validation.get("valid")
    if valid_flag is True:
        return "valid"
    if valid_flag is False:
        return "invalid"
    return "unvalidated"


# Map pattern types to sequence type hints for Biopython validation
_SEQUENCE_TYPE_HINTS: dict[str, str] = {
    "DNA_SEQUENCE": "DNA",
    "RNA_SEQUENCE": "RNA",
    "AMINO_ACID_SEQ": "protein",
}


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
            result["status"] = _status_from_validation(validation)
        else:
            result["validation"] = None
            result["status"] = "unvalidated"
            result["note"] = "RDKit not available"

    elif ptype in SEQUENCE_TYPES:
        if HAS_BIOPYTHON and validate_sequence is not None:
            type_hint = _SEQUENCE_TYPE_HINTS.get(ptype)
            validation = validate_sequence(match["value"], type_hint)
            result["validation"] = validation
            result["status"] = _status_from_validation(validation)
        else:
            result["validation"] = None
            result["status"] = "unvalidated"
            result["note"] = "Biopython not available"

    else:
        result["validation"] = None
        result["status"] = "found"

    return result


def process_extraction(filepath: Path) -> dict:
    """Process a single extraction JSON file and return validation results."""
    if scan_text is None:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return {
            "file": filepath.name,
            "document_id": data.get("document_id", ""),
            "matches_found": 0,
            "results": [],
            "note": "No validation scripts for this domain, skipping",
        }

    data = json.loads(filepath.read_text(encoding="utf-8"))
    texts = collect_texts(data)

    validated: list[dict] = []
    for field_path, text in texts:
        for match in scan_text(text):
            result = validate_match(match)
            result["source_file"] = filepath.name
            result["source_field"] = field_path
            validated.append(result)

    return {
        "file": filepath.name,
        "document_id": data.get("document_id", ""),
        "matches_found": len(validated),
        "results": validated,
    }


# ---------------------------------------------------------------------------
# Phase 1.5: Structural Enrichment
# ---------------------------------------------------------------------------

def _find_nearest_entity(
    entities: list[dict],
    match_context: str,
    target_types: set[str],
) -> dict | None:
    """Find the nearest entity of a given type by checking if entity name appears in context."""
    for entity in entities:
        if entity.get("entity_type") in target_types:
            name = entity.get("name", "")
            if name and name.lower() in match_context.lower():
                return entity
    # Fallback: return first entity of the target type
    for entity in entities:
        if entity.get("entity_type") in target_types:
            return entity
    return None


def _build_smiles_entity(result: dict) -> dict | None:
    """Build a CHEMICAL_STRUCTURE entity from a validated SMILES match."""
    validation = result.get("validation")
    if not validation or not validation.get("valid"):
        return None

    name = validation.get("inchikey") or validation.get("canonical_smiles", result["value"])

    return {
        "name": name,
        "entity_type": "CHEMICAL_STRUCTURE",
        "attributes": {
            "canonical_smiles": validation.get("canonical_smiles", ""),
            "inchi": validation.get("inchi", ""),
            "inchikey": validation.get("inchikey", ""),
            "molecular_formula": validation.get("molecular_formula", ""),
            "molecular_weight": validation.get("molecular_weight"),
            "logp": validation.get("logp"),
            "hbd": validation.get("hbd"),
            "hba": validation.get("hba"),
            "tpsa": validation.get("tpsa"),
            "lipinski_violations": validation.get("lipinski_violations"),
            "notation_type": "SMILES",
            "validated": True,
        },
        "confidence": 1.0,
        "context": result.get("context", ""),
    }


def _build_sequence_entity(result: dict) -> dict | None:
    """Build a NUCLEOTIDE_SEQUENCE or PEPTIDE_SEQUENCE entity from a validated sequence match."""
    validation = result.get("validation")
    if not validation or not validation.get("valid"):
        return None

    seq_type = validation.get("type", "unknown")
    sequence = result["value"]
    seq_len = validation.get("length", len(sequence))

    if seq_type in ("DNA", "RNA"):
        entity_type = "NUCLEOTIDE_SEQUENCE"
        name = f"{seq_type}_{seq_len}nt"
        attributes: dict = {
            "sequence": sequence[:100],
            "sequence_type": seq_type,
            "length": seq_len,
            "validated": True,
        }
        if validation.get("gc_content") is not None:
            attributes["gc_content"] = validation["gc_content"]
    elif seq_type.lower() == "protein":
        entity_type = "PEPTIDE_SEQUENCE"
        name = f"peptide_{seq_len}aa"
        attributes = {
            "sequence": sequence[:100],
            "sequence_type": "protein",
            "length": seq_len,
            "validated": True,
        }
        if validation.get("molecular_weight") is not None:
            attributes["molecular_weight"] = validation["molecular_weight"]
    else:
        return None

    return {
        "name": name,
        "entity_type": entity_type,
        "attributes": attributes,
        "confidence": 1.0,
        "context": result.get("context", ""),
    }


def enrich_extraction(
    extraction_path: Path,
    results: list[dict],
    output_dir: Path,
) -> dict:
    """Enrich an extraction JSON with structural entities and relations.

    Args:
        extraction_path: Path to the extraction JSON file.
        results: Validated match results from process_extraction().
        output_dir: Root output directory (unused here, kept for API consistency).

    Returns:
        Dict of enrichment stats.
    """
    data = json.loads(extraction_path.read_text(encoding="utf-8"))
    entities = data.setdefault("entities", [])
    relations = data.setdefault("relations", [])

    stats = {"entities_added": 0, "relations_added": 0, "inchikeys": []}

    # Track existing entity names to avoid duplicates
    existing_names = {e.get("name") for e in entities}

    for result in results:
        ptype = result.get("pattern_type", "")
        status = result.get("status", "")

        if status != "valid":
            continue

        new_entity = None
        relation_type = None
        parent_types: set[str] = set()

        if ptype in SMILES_TYPES:
            new_entity = _build_smiles_entity(result)
            relation_type = "HAS_STRUCTURE"
            parent_types = {"COMPOUND", "DRUG", "MOLECULE"}
            # Collect InChIKey for dedup
            inchikey = (result.get("validation") or {}).get("inchikey")
            if inchikey:
                stats["inchikeys"].append(inchikey)

        elif ptype in SEQUENCE_TYPES:
            new_entity = _build_sequence_entity(result)
            relation_type = "HAS_SEQUENCE"
            parent_types = {"GENE", "PROTEIN", "COMPOUND"}

        if new_entity is None:
            continue

        entity_name = new_entity["name"]
        if entity_name in existing_names:
            continue

        entities.append(new_entity)
        existing_names.add(entity_name)
        stats["entities_added"] += 1

        # Find parent entity and create relation
        parent = _find_nearest_entity(entities, result.get("context", ""), parent_types)
        if parent and relation_type:
            relation = {
                "relation_type": relation_type,
                "source_entity": parent["name"],
                "target_entity": entity_name,
                "confidence": 0.95,
                "evidence": result.get("context", ""),
            }
            relations.append(relation)
            stats["relations_added"] += 1

    # Write enriched extraction back to disk
    extraction_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return stats


def build_dedup_report(
    all_inchikeys: dict[str, list[dict]],
    output_dir: Path,
) -> dict:
    """Build and save InChIKey deduplication report.

    Args:
        all_inchikeys: Mapping of InChIKey -> list of {name, document} dicts.
        output_dir: Root output directory.

    Returns:
        The dedup report dict.
    """
    matches = []
    for inchikey, compounds in sorted(all_inchikeys.items()):
        if len(compounds) > 1:
            matches.append({
                "inchikey": inchikey,
                "compounds": compounds,
            })

    report = {"inchikey_matches": matches}

    validation_dir = output_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    dedup_path = validation_dir / "dedup_candidates.json"
    dedup_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global _domain_name, VALIDATION_SCRIPTS_DIR, scan_text, HAS_RDKIT, validate_smiles, HAS_BIOPYTHON, validate_sequence

    # Parse arguments
    args = sys.argv[1:]
    enrich = True

    # Domain flag -- must be parsed before validation scripts are loaded
    if "--domain" in args:
        idx = args.index("--domain")
        _domain_name = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

        # Re-resolve validation scripts for the specified domain
        VALIDATION_SCRIPTS_DIR = get_validation_scripts_dir(_domain_name)
        if VALIDATION_SCRIPTS_DIR:
            sys.path.insert(0, str(VALIDATION_SCRIPTS_DIR))
            from scan_patterns import scan_text as _scan_text  # noqa: E402
            scan_text = _scan_text
            try:
                from validate_smiles import validate_smiles as _vs
                HAS_RDKIT = True
                validate_smiles = _vs
            except ImportError:
                HAS_RDKIT = False
                validate_smiles = None  # type: ignore[assignment]
            try:
                from validate_sequences import validate_sequence as _vseq
                HAS_BIOPYTHON = True
                validate_sequence = _vseq
            except ImportError:
                HAS_BIOPYTHON = False
                validate_sequence = None  # type: ignore[assignment]
        else:
            scan_text = None  # type: ignore[assignment]
            HAS_RDKIT = False
            validate_smiles = None  # type: ignore[assignment]
            HAS_BIOPYTHON = False
            validate_sequence = None  # type: ignore[assignment]

    if "--no-enrich" in args:
        enrich = False
        args.remove("--no-enrich")
    elif "--enrich" in args:
        enrich = True
        args.remove("--enrich")

    if len(args) != 1:
        print(f"Usage: {sys.argv[0]} <output_dir> [--no-enrich]", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args[0])

    # If no validation scripts for this domain, report and exit gracefully
    if scan_text is None:
        domain_label = _domain_name or "default"
        print(json.dumps({
            "message": f"No validation scripts for domain '{domain_label}', skipping molecular validation",
            "files_scanned": 0,
            "total_matches": 0,
        }, indent=2))
        return

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

    # InChIKey dedup tracking: inchikey -> [{name, document}]
    inchikey_map: dict[str, list[dict]] = defaultdict(list)
    enrichment_stats = {
        "entities_added": 0,
        "relations_added": 0,
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

        # Phase 1.5: Enrich extraction with structural entities
        if enrich and file_result["results"]:
            try:
                enrich_result = enrich_extraction(
                    filepath, file_result["results"], output_dir
                )
                enrichment_stats["entities_added"] += enrich_result["entities_added"]
                enrichment_stats["relations_added"] += enrich_result["relations_added"]

                # Collect InChIKeys for dedup
                doc_id = file_result.get("document_id", filepath.stem)
                for inchikey in enrich_result.get("inchikeys", []):
                    # Find compound name from results
                    compound_name = None
                    for r in file_result["results"]:
                        v = r.get("validation") or {}
                        if v.get("inchikey") == inchikey:
                            # Find parent compound name from context
                            data = json.loads(filepath.read_text(encoding="utf-8"))
                            parent = _find_nearest_entity(
                                data.get("entities", []),
                                r.get("context", ""),
                                {"COMPOUND", "DRUG", "MOLECULE"},
                            )
                            if parent:
                                compound_name = parent["name"]
                            break
                    inchikey_map[inchikey].append({
                        "name": compound_name or "unknown",
                        "document": doc_id,
                    })
            except Exception as exc:
                print(f"Warning: enrichment failed for {filepath.name}: {exc}", file=sys.stderr)

    # Add availability info
    stats["rdkit_available"] = HAS_RDKIT
    stats["biopython_available"] = HAS_BIOPYTHON

    if enrich:
        stats["enrichment"] = enrichment_stats

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

    # Phase 1.5: Build dedup report
    if enrich and inchikey_map:
        dedup_report = build_dedup_report(dict(inchikey_map), output_dir)
        dedup_count = len(dedup_report.get("inchikey_matches", []))
        if dedup_count > 0:
            stats["dedup_candidates"] = dedup_count

    # Print summary stats to stdout
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
