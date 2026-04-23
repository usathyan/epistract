#!/usr/bin/env python3
"""Post-extraction validation entry point for the drug-discovery domain.

FIDL-07 (D-04): Convention entry point auto-discovered by
``core.domain_resolver.get_validation_dir`` and invoked by
``core.run_sift.cmd_build`` after graph build + community labeling.

Iterates extraction JSON files in ``<output_dir>/extractions/`` (the
convention directory written by ``core.build_extraction.write_extraction``),
walks each extraction's entities, validates any CHEMICAL_STRUCTURE entity's
SMILES via the sibling ``validate_smiles.validate_smiles()``, and aggregates
results.

Non-fatal: when RDKit is missing, returns ``{"status": "skipped", ...}``
rather than raising. Callers (``cmd_build``) persist the return dict to
``validation_report.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    from .validate_smiles import RDKIT_AVAILABLE, validate_smiles
except ImportError:
    # Fallback for script-style / spec_from_file_location loading where
    # the package context is not set. Expose the sibling file directly.
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).parent))
    from validate_smiles import RDKIT_AVAILABLE, validate_smiles  # type: ignore


def run_validation(output_dir: Path) -> dict:
    """Aggregate SMILES validation across all extraction JSONs.

    Args:
        output_dir: Build output directory. Extractions are expected at
            ``<output_dir>/extractions/*.json`` (per
            ``build_extraction.write_extraction``).

    Returns:
        Dict with keys:
        - ``status``: ``"ok"`` | ``"skipped"`` | ``"error"``
        - ``documents_validated``: int
        - ``total_smiles_checked``: int
        - ``invalid_smiles``: list of
          ``{document_id, entity_name, smiles, error}``
        - ``errors``: list of per-file read / parse error strings
    """
    if not RDKIT_AVAILABLE:
        return {
            "status": "skipped",
            "reason": "RDKit not installed",
            "documents_validated": 0,
            "total_smiles_checked": 0,
            "invalid_smiles": [],
            "errors": [],
        }

    out = Path(output_dir)
    extractions_dir = out / "extractions"
    if not extractions_dir.is_dir():
        # No extractions to validate — return ok with zero counts.
        return {
            "status": "ok",
            "documents_validated": 0,
            "total_smiles_checked": 0,
            "invalid_smiles": [],
            "errors": [],
        }

    docs_validated = 0
    smiles_checked = 0
    invalid: list[dict] = []
    errors: list[str] = []

    for extraction_path in sorted(extractions_dir.glob("*.json")):
        try:
            data = json.loads(extraction_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            errors.append(f"{extraction_path.name}: {e}")
            continue

        docs_validated += 1
        doc_id = data.get("document_id", extraction_path.stem)
        for entity in data.get("entities", []):
            if entity.get("entity_type") != "CHEMICAL_STRUCTURE":
                continue
            attrs = entity.get("attributes") or {}
            smi = attrs.get("smiles") or attrs.get("canonical_smiles")
            if not smi:
                continue
            smiles_checked += 1
            result = validate_smiles(smi)
            if not result.get("valid"):
                invalid.append(
                    {
                        "document_id": doc_id,
                        "entity_name": entity.get("name", ""),
                        "smiles": smi,
                        "error": result.get("error", "unknown"),
                    }
                )

    return {
        "status": "ok",
        "documents_validated": docs_validated,
        "total_smiles_checked": smiles_checked,
        "invalid_smiles": invalid,
        "errors": errors,
    }
