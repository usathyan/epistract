#!/bin/bash
# Epistract setup — installs Python dependencies for the framework.
#
# What this script does NOT do:
#   - Install the Claude Code plugin itself (use `/plugin install epistract@epistract`)
#   - Install Python itself (you must have 3.11, 3.12, or 3.13 — 3.14 is untested)
#   - Install uv (see https://docs.astral.sh/uv/ for install instructions)
#
# What this script DOES:
#   - Verifies Python 3.11-3.13
#   - Verifies uv is available
#   - Creates a project-local .venv via `uv venv` if one doesn't exist
#   - Installs sift-kg into that venv via `uv pip install`
#   - Optionally installs RDKit + Biopython with --all
#
# Usage: scripts/setup.sh [--all] [--check]
set -e

INSTALL_ALL=false
CHECK_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --all) INSTALL_ALL=true ;;
    --check) CHECK_ONLY=true ;;
  esac
done

echo "=== epistract setup ==="
echo ""

# ---------------------------------------------------------------------------
# Prerequisites: uv + compatible Python
# ---------------------------------------------------------------------------

if ! command -v uv >/dev/null 2>&1; then
  cat <<'EOF'
ERROR: uv is not installed.

Epistract requires uv for package management. uv handles the .venv,
dependency resolution, and lockfile in one tool. Install it with:

    curl -LsSf https://astral.sh/uv/install.sh | sh

Or see https://docs.astral.sh/uv/#installation for alternative install paths
(homebrew, pipx, conda, etc.). Then re-run this script.
EOF
  exit 1
fi
UV_VERSION=$(uv --version 2>/dev/null | awk '{print $2}' || echo "unknown")
echo "uv $UV_VERSION"

# ---------------------------------------------------------------------------
# Project root detection + venv creation
# ---------------------------------------------------------------------------

# Resolve project root from this script's location so the script works from
# any cwd (including when invoked via /epistract:setup from Claude Code).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Create project-local .venv if missing. Skip in --check mode so we don't
# mutate the workspace just to verify state.
if [ ! -d ".venv" ]; then
  if [ "$CHECK_ONLY" = true ]; then
    echo "WARN: .venv does not exist (run without --check to create it)"
  else
    echo "Creating .venv via uv venv..."
    uv venv
  fi
fi

# Resolve the venv's python (only if the venv exists). uv pip install
# auto-detects .venv in the project root, so we don't need to activate
# or set VIRTUAL_ENV manually — uv handles it. We just need a python
# binary to run version checks and import probes against.
if [ -d ".venv" ]; then
  VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"
else
  # Fall back to system python3 for the version check in --check mode.
  VENV_PYTHON="$(command -v python3 || true)"
fi

if [ -z "$VENV_PYTHON" ] || [ ! -x "$VENV_PYTHON" ]; then
  echo "ERROR: Could not locate a Python 3 interpreter"
  exit 1
fi

PYTHON_VERSION=$("$VENV_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
PYTHON_MAJOR=$("$VENV_PYTHON" -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$("$VENV_PYTHON" -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
  echo "ERROR: Python >= 3.11 required, found $PYTHON_VERSION"
  echo "Supported: 3.11, 3.12, 3.13. Untested: 3.14+ (see README)."
  exit 1
fi
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 14 ]; then
  echo "WARN: Python $PYTHON_VERSION is newer than the tested range (3.11-3.13)."
  echo "      sift-kg may or may not have prebuilt wheels. Continuing anyway."
fi
echo "Python $PYTHON_VERSION (from $VENV_PYTHON)"

# ---------------------------------------------------------------------------
# sift-kg (required)
# ---------------------------------------------------------------------------

if "$VENV_PYTHON" -c "import sift_kg" 2>/dev/null; then
  SIFT_VERSION=$("$VENV_PYTHON" -c "import importlib.metadata; print(importlib.metadata.version('sift-kg'))" 2>/dev/null || echo "unknown")
  echo "sift-kg $SIFT_VERSION"
else
  if [ "$CHECK_ONLY" = true ]; then
    echo "MISSING: sift-kg (run without --check to install)"
  else
    echo "sift-kg not found, installing via uv..."
    if ! uv pip install sift-kg; then
      cat <<'EOF'

ERROR: uv pip install sift-kg failed.

Common causes:
  1. Corporate SSL inspection proxy — uv needs to trust the proxy cert.
     Set SSL_CERT_FILE or REQUESTS_CA_BUNDLE to your corporate CA bundle.
  2. Network / DNS issue — check that pypi.org is reachable.
  3. Python version mismatch — sift-kg requires Python 3.11-3.13.

Re-run this script after fixing the underlying issue. This script does
not fall back to plain pip because pip doesn't respect the project venv
by default and silent cross-env installs cause hard-to-debug problems.
EOF
    exit 1
  fi
    SIFT_VERSION=$("$VENV_PYTHON" -c "import importlib.metadata; print(importlib.metadata.version('sift-kg'))" 2>/dev/null || echo "unknown")
    echo "sift-kg $SIFT_VERSION (installed)"
  fi
fi

# ---------------------------------------------------------------------------
# RDKit (optional)
# ---------------------------------------------------------------------------

if "$VENV_PYTHON" -c "from rdkit import Chem" 2>/dev/null; then
  RDKIT_VERSION=$("$VENV_PYTHON" -c "from rdkit import rdBase; print(rdBase.rdkitVersion)" 2>/dev/null || echo "available")
  echo "RDKit $RDKIT_VERSION"
elif [ "$CHECK_ONLY" = true ]; then
  echo "MISSING: RDKit (optional — run 'scripts/setup.sh --all' to install)"
elif [ "$INSTALL_ALL" = true ]; then
  echo "Installing RDKit via uv..."
  if uv pip install rdkit-pypi; then
    echo "RDKit installed"
  else
    echo "WARN: RDKit install failed (optional — continuing)"
  fi
else
  echo "RDKit not available (optional — install with: uv pip install rdkit-pypi  or re-run with --all)"
fi

# ---------------------------------------------------------------------------
# Biopython (optional)
# ---------------------------------------------------------------------------

if "$VENV_PYTHON" -c "from Bio import Seq" 2>/dev/null; then
  BIO_VERSION=$("$VENV_PYTHON" -c "import importlib.metadata; print(importlib.metadata.version('biopython'))" 2>/dev/null || echo "available")
  echo "Biopython $BIO_VERSION"
elif [ "$CHECK_ONLY" = true ]; then
  echo "MISSING: Biopython (optional — run 'scripts/setup.sh --all' to install)"
elif [ "$INSTALL_ALL" = true ]; then
  echo "Installing Biopython via uv..."
  if uv pip install biopython; then
    echo "Biopython installed"
  else
    echo "WARN: Biopython install failed (optional — continuing)"
  fi
else
  echo "Biopython not available (optional — install with: uv pip install biopython  or re-run with --all)"
fi

echo ""
if [ "$CHECK_ONLY" = true ]; then
  echo "Setup check complete."
else
  echo "Setup complete. Activate the venv with: source .venv/bin/activate"
fi
