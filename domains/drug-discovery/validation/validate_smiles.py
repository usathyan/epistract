#!/usr/bin/env python3
"""RDKit-based SMILES validation and molecular property calculation.

Usage:
    Single:  python validate_smiles.py "CC(=O)Oc1ccccc1C(=O)O"
    Batch:   echo '["CC(=O)O", "invalid"]' | python validate_smiles.py --batch
"""

from __future__ import annotations

import json
import sys

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors

    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


def validate_smiles(smiles: str) -> dict:
    """Validate a SMILES string and compute molecular properties.

    Returns a dict with validation result and, if valid, molecular descriptors
    including Lipinski Rule-of-Five violation count.
    """
    if not RDKIT_AVAILABLE:
        return {
            "valid": None,
            "error": "RDKit not installed. Run: uv pip install rdkit",
        }

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"valid": False, "input": smiles, "error": "Invalid SMILES"}

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    tpsa = Descriptors.TPSA(mol)

    # Lipinski Rule of Five violations
    violations = sum((
        mw > 500,
        logp > 5,
        hbd > 5,
        hba > 10,
    ))

    return {
        "valid": True,
        "input": smiles,
        "canonical_smiles": Chem.MolToSmiles(mol),
        "inchi": Chem.MolToInchi(mol),
        "inchikey": Chem.InchiToInchiKey(Chem.MolToInchi(mol)),
        "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
        "molecular_weight": round(mw, 4),
        "logp": round(logp, 4),
        "hbd": hbd,
        "hba": hba,
        "tpsa": round(tpsa, 4),
        "num_rings": rdMolDescriptors.CalcNumRings(mol),
        "num_rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
        "lipinski_violations": violations,
    }


def main() -> None:
    if "--batch" in sys.argv:
        data = json.load(sys.stdin)
        results = [validate_smiles(s) for s in data]
        print(json.dumps(results, indent=2))
    elif len(sys.argv) > 1:
        smiles = sys.argv[1]
        result = validate_smiles(smiles)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python validate_smiles.py <SMILES>")
        print('       echo \'["CCO", "invalid"]\' | python validate_smiles.py --batch')
        sys.exit(1)


if __name__ == "__main__":
    main()
