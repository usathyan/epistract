#!/bin/bash
set -e

echo "=== epistract setup ==="
echo ""

# Check Python >= 3.11
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
  echo "ERROR: Python >= 3.11 required, found $PYTHON_VERSION"
  exit 1
fi
echo "Python $PYTHON_VERSION"

# Check/install sift-kg
if ! python3 -c "import sift" 2>/dev/null; then
  echo "sift-kg not found, installing..."
  uv pip install sift-kg 2>/dev/null || pip install sift-kg
fi
SIFT_VERSION=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('sift-kg'))" 2>/dev/null || echo "unknown")
echo "sift-kg $SIFT_VERSION"

# Check RDKit
if python3 -c "from rdkit import Chem" 2>/dev/null; then
  RDKIT_VERSION=$(python3 -c "from rdkit import rdBase; print(rdBase.rdkitVersion)" 2>/dev/null || echo "available")
  echo "RDKit $RDKIT_VERSION"
else
  echo "RDKit not available (optional, install with: uv pip install rdkit-pypi)"
fi

# Check Biopython
if python3 -c "from Bio import Seq" 2>/dev/null; then
  BIO_VERSION=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('biopython'))" 2>/dev/null || echo "available")
  echo "Biopython $BIO_VERSION"
else
  echo "Biopython not available (optional, install with: uv pip install biopython)"
fi

echo ""
echo "Setup complete."
