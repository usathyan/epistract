#!/usr/bin/env python3
"""Biopython-based nucleotide and amino acid sequence validation.

Provides auto-detection and validation of DNA, RNA, and protein sequences
with detailed property calculations when Biopython is available.

Usage:
    # Single sequence
    python validate_sequences.py ATCGATCGATCG

    # With type hint
    python validate_sequences.py --type DNA ATCGATCGATCG

    # Batch mode (JSON array from stdin)
    echo '[{"sequence": "ATCG", "type": "DNA"}]' | python validate_sequences.py --batch
"""

from __future__ import annotations

import argparse
import json
import sys

try:
    from Bio.Seq import Seq
    from Bio.SeqUtils import gc_fraction, molecular_weight
    from Bio.SeqUtils.ProtParam import ProteinAnalysis

    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False

DNA_CHARS = set("ATGCNRYWSMKHBVD")
RNA_CHARS = set("AUGCNRYWSMKHBVD")
PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYX*")


def detect_type(seq: str) -> str:
    """Auto-detect whether a sequence is DNA, RNA, or protein from its character set.

    Returns one of: "DNA", "RNA", "protein", or "unknown".
    """
    upper = seq.upper().strip()
    if not upper:
        return "unknown"

    chars = set(upper)

    # If it contains U but not T, likely RNA
    if "U" in chars and "T" not in chars and chars <= RNA_CHARS:
        return "RNA"

    # If it contains T but not U, likely DNA
    if "T" in chars and "U" not in chars and chars <= DNA_CHARS:
        return "DNA"

    # Pure AGCN (no T or U) — default to DNA
    if chars <= (DNA_CHARS & RNA_CHARS):
        return "DNA"

    # Check if valid protein
    if chars <= PROTEIN_CHARS:
        return "protein"

    return "unknown"


def validate_sequence(seq: str, seq_type: str | None = None) -> dict:
    """Validate a biological sequence and return properties.

    Args:
        seq: The sequence string.
        seq_type: Optional type hint ("DNA", "RNA", or "protein").
                  If None, auto-detected.

    Returns:
        Dictionary with validation results and computed properties.
    """
    if not BIOPYTHON_AVAILABLE:
        return {
            "valid": None,
            "error": "Biopython not installed. Run: uv pip install biopython",
        }

    seq = seq.strip()
    if not seq:
        return {"valid": False, "error": "Empty sequence"}

    upper = seq.upper()

    if seq_type is None:
        seq_type = detect_type(upper)

    seq_type = seq_type.upper() if seq_type else "UNKNOWN"

    if seq_type == "DNA":
        return _validate_dna(upper)
    elif seq_type == "RNA":
        return _validate_rna(upper)
    elif seq_type == "PROTEIN":
        return _validate_protein(upper)
    else:
        return {"valid": False, "error": f"Unknown or unsupported sequence type: {seq_type}"}


def _validate_dna(seq: str) -> dict:
    chars = set(seq)
    if not chars <= DNA_CHARS:
        invalid = chars - DNA_CHARS
        return {"valid": False, "error": f"Invalid DNA characters: {sorted(invalid)}"}

    bio_seq = Seq(seq)
    result = {
        "valid": True,
        "type": "DNA",
        "length": len(seq),
        "gc_content": round(gc_fraction(bio_seq), 4),
        "complement": str(bio_seq.complement()),
        "reverse_complement": str(bio_seq.reverse_complement()),
    }

    if len(seq) % 3 == 0 and len(seq) >= 3:
        try:
            result["translation"] = str(bio_seq.translate())
        except Exception:
            result["translation"] = None

    return result


def _validate_rna(seq: str) -> dict:
    chars = set(seq)
    if not chars <= RNA_CHARS:
        invalid = chars - RNA_CHARS
        return {"valid": False, "error": f"Invalid RNA characters: {sorted(invalid)}"}

    return {
        "valid": True,
        "type": "RNA",
        "length": len(seq),
    }


def _validate_protein(seq: str) -> dict:
    # Remove stop codon marker for analysis
    analysis_seq = seq.replace("*", "")
    chars = set(seq)
    if not chars <= PROTEIN_CHARS:
        invalid = chars - PROTEIN_CHARS
        return {"valid": False, "error": f"Invalid protein characters: {sorted(invalid)}"}

    if not analysis_seq:
        return {"valid": True, "type": "protein", "length": len(seq)}

    result = {
        "valid": True,
        "type": "protein",
        "length": len(seq),
    }

    try:
        bio_seq = Seq(analysis_seq)
        result["molecular_weight"] = round(molecular_weight(bio_seq, seq_type="protein"), 2)
    except Exception:
        result["molecular_weight"] = None

    try:
        pa = ProteinAnalysis(analysis_seq)
        result["isoelectric_point"] = round(pa.isoelectric_point(), 4)
        result["aromaticity"] = round(pa.aromaticity(), 4)
        result["instability_index"] = round(pa.instability_index(), 4)
        result["gravy"] = round(pa.gravy(), 4)
    except Exception:
        result.setdefault("isoelectric_point", None)
        result.setdefault("aromaticity", None)
        result.setdefault("instability_index", None)
        result.setdefault("gravy", None)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate biological sequences (DNA, RNA, protein)"
    )
    parser.add_argument("sequence", nargs="?", help="Sequence string to validate")
    parser.add_argument(
        "--type",
        choices=["DNA", "RNA", "protein"],
        default=None,
        help="Sequence type hint (auto-detected if omitted)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help='Read JSON array from stdin: [{"sequence": "...", "type": "..."}]',
    )

    args = parser.parse_args()

    if args.batch:
        data = json.load(sys.stdin)
        results = []
        for entry in data:
            seq = entry.get("sequence", "")
            stype = entry.get("type")
            results.append(validate_sequence(seq, stype))
        print(json.dumps(results, indent=2))
    elif args.sequence:
        result = validate_sequence(args.sequence, args.type)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
