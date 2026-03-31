"""Tests for the Sample Contract Analysis Workbench."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_output_dir(tmp_path):
    """Create a temporary output directory mimicking extraction output."""
    # Copy sample graph data
    gd_src = FIXTURES_DIR / "sample_graph_data.json"
    if gd_src.exists():
        shutil.copy(gd_src, tmp_path / "graph_data.json")

    cl_src = FIXTURES_DIR / "sample_claims_layer.json"
    if cl_src.exists():
        shutil.copy(cl_src, tmp_path / "claims_layer.json")

    cm_src = FIXTURES_DIR / "sample_communities.json"
    if cm_src.exists():
        shutil.copy(cm_src, tmp_path / "communities.json")

    # Copy sample ingested texts
    ingested = tmp_path / "ingested"
    ingested.mkdir()
    src_ingested = FIXTURES_DIR / "sample_ingested"
    if src_ingested.exists():
        for txt in src_ingested.glob("*.txt"):
            shutil.copy(txt, ingested / txt.name)

    return tmp_path


@pytest.fixture
def client(sample_output_dir):
    """Create a FastAPI TestClient."""
    from scripts.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(sample_output_dir)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Data Loader Tests
# ---------------------------------------------------------------------------


def test_data_loader_loads_graph(sample_output_dir):
    """WorkbenchData loads graph_data.json nodes and edges."""
    from scripts.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    assert len(data.get_nodes()) >= 20, f"Expected >= 20 nodes, got {len(data.get_nodes())}"
    assert len(data.get_edges()) >= 20, f"Expected >= 20 edges, got {len(data.get_edges())}"


def test_data_loader_filters_by_type(sample_output_dir):
    """WorkbenchData.get_nodes filters by entity_type."""
    from scripts.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    parties = data.get_nodes(entity_type="PARTY")
    assert all(n["entity_type"] == "PARTY" for n in parties)
    assert len(parties) >= 1, f"Expected >= 1 PARTY node, got {len(parties)}"


def test_data_loader_loads_claims(sample_output_dir):
    """WorkbenchData loads claims_layer.json."""
    from scripts.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    assert "conflicts" in data.claims_layer
    assert "gaps" in data.claims_layer
    assert "risks" in data.claims_layer


def test_data_loader_lists_documents(sample_output_dir):
    """WorkbenchData discovers ingested text files."""
    from scripts.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    assert len(data.documents) >= 1, f"Expected >= 1 document, got {len(data.documents)}"
    assert "doc_id" in data.documents[0]


# ---------------------------------------------------------------------------
# API Tests
# ---------------------------------------------------------------------------


def test_health_endpoint(client):
    """GET /api/health returns server status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["nodes"] >= 20


def test_graph_api(client):
    """GET /api/graph returns nodes and edges."""
    resp = client.get("/api/graph")
    assert resp.status_code == 200
    body = resp.json()
    assert "nodes" in body
    assert "edges" in body
    assert len(body["nodes"]) >= 20


def test_entity_filter(client):
    """GET /api/graph?entity_type=PARTY returns only PARTY nodes."""
    resp = client.get("/api/graph?entity_type=PARTY")
    assert resp.status_code == 200
    body = resp.json()
    assert all(n["entity_type"] == "PARTY" for n in body["nodes"])


def test_entity_types_endpoint(client):
    """GET /api/graph/entity-types returns type counts."""
    resp = client.get("/api/graph/entity-types")
    assert resp.status_code == 200
    body = resp.json()
    assert "PARTY" in body["entity_types"]


def test_claims_endpoint(client):
    """GET /api/graph/claims returns claims layer."""
    resp = client.get("/api/graph/claims")
    assert resp.status_code == 200
    body = resp.json()
    assert "conflicts" in body


def test_sources_list(client):
    """GET /api/sources returns document list."""
    resp = client.get("/api/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["documents"]) >= 1


def test_source_text(client):
    """GET /api/sources/{doc_id} returns document text."""
    # Get first document ID
    list_resp = client.get("/api/sources")
    doc_id = list_resp.json()["documents"][0]["doc_id"]

    resp = client.get(f"/api/sources/{doc_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "text" in body
    assert len(body["text"]) > 0


def test_schema_expansion():
    """Domain schema includes new entity types per D-20."""
    schema_path = Path("skills/contract-extraction/domain.yaml")
    if not schema_path.exists():
        pytest.skip("contract-extraction domain.yaml not yet created (Plan 01)")

    import yaml

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    entity_types = list(schema["entity_types"].keys())
    for expected in ["COMMITTEE", "PERSON", "EVENT", "STAGE", "ROOM"]:
        assert expected in entity_types, f"Missing entity type: {expected}"

    relation_types = list(schema["relation_types"].keys())
    for expected in [
        "CHAIRED_BY",
        "RESPONSIBLE_FOR",
        "HOSTED_AT",
        "REQUIRES",
        "SCHEDULED",
    ]:
        assert expected in relation_types, f"Missing relation type: {expected}"
