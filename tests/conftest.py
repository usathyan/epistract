#!/usr/bin/env python3
"""Shared test configuration, fixtures, and path setup for epistract tests.

All path manipulation is centralized here so individual test files
do not need to modify sys.path.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup — centralized for all test files
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"

sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "domains" / "drug-discovery" / "validation"))
sys.path.insert(0, str(PROJECT_ROOT / "domains" / "drug-discovery"))
sys.path.insert(0, str(PROJECT_ROOT / "domains" / "contracts"))

# ---------------------------------------------------------------------------
# Availability flags — importable by test files
# ---------------------------------------------------------------------------
try:
    from sift_kg import load_domain  # noqa: F401

    HAS_SIFTKG = True
except ImportError:
    HAS_SIFTKG = False

try:
    from rdkit import Chem  # noqa: F401

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    from Bio.Seq import Seq  # noqa: F401

    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fixtures_dir():
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_graph_data():
    """Load the sample graph data fixture (contract domain)."""
    path = FIXTURES_DIR / "sample_graph_data.json"
    return json.loads(path.read_text())


@pytest.fixture
def sample_claims_layer():
    """Load the sample claims layer fixture."""
    path = FIXTURES_DIR / "sample_claims_layer.json"
    return json.loads(path.read_text())


@pytest.fixture
def sample_communities():
    """Load the sample communities fixture."""
    path = FIXTURES_DIR / "sample_communities.json"
    return json.loads(path.read_text())


@pytest.fixture
def contract_graph_data():
    """Load the contract domain graph fixture."""
    path = FIXTURES_DIR / "contract_graph_data.json"
    return json.loads(path.read_text())


@pytest.fixture
def contract_claims_layer():
    """Load the contract domain claims layer fixture."""
    path = FIXTURES_DIR / "contract_claims_layer.json"
    return json.loads(path.read_text())


@pytest.fixture
def sample_output_dir(tmp_path):
    """Create a temporary output directory with fixture files and ingested/ subdir.

    Copies sample fixture files into tmp_path for tests that need
    a realistic output directory layout.
    """
    ingested_dir = tmp_path / "ingested"
    ingested_dir.mkdir()

    # Copy fixture files into the temp directory
    for fixture_file in FIXTURES_DIR.glob("*.json"):
        shutil.copy2(fixture_file, tmp_path / fixture_file.name)

    return tmp_path


@pytest.fixture
def client(sample_output_dir):
    """Create a FastAPI TestClient wrapping the workbench app.

    Shared global fixture so test_workbench_security.py and any future
    security/API test files can use it without duplicating setup.
    test_workbench.py defines a local override with the same name — the
    local fixture takes precedence within that file (pytest shadowing).
    """
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(sample_output_dir, domain="contracts")
    return TestClient(app)
