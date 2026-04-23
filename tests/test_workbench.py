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
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(sample_output_dir, domain="contracts")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Data Loader Tests
# ---------------------------------------------------------------------------


def test_data_loader_loads_graph(sample_output_dir):
    """WorkbenchData loads graph_data.json nodes and edges."""
    from examples.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    assert len(data.get_nodes()) >= 20, f"Expected >= 20 nodes, got {len(data.get_nodes())}"
    assert len(data.get_edges()) >= 20, f"Expected >= 20 edges, got {len(data.get_edges())}"


def test_data_loader_filters_by_type(sample_output_dir):
    """WorkbenchData.get_nodes filters by entity_type."""
    from examples.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    parties = data.get_nodes(entity_type="PARTY")
    assert all(n["entity_type"] == "PARTY" for n in parties)
    assert len(parties) >= 1, f"Expected >= 1 PARTY node, got {len(parties)}"


def test_data_loader_loads_claims(sample_output_dir):
    """WorkbenchData loads claims_layer.json."""
    from examples.workbench.data_loader import WorkbenchData

    data = WorkbenchData(sample_output_dir)
    assert "conflicts" in data.claims_layer
    assert "gaps" in data.claims_layer
    assert "risks" in data.claims_layer


def test_data_loader_lists_documents(sample_output_dir):
    """WorkbenchData discovers ingested text files."""
    from examples.workbench.data_loader import WorkbenchData

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


def test_chat_stream_mock(client, monkeypatch):
    """POST /api/chat returns SSE stream with mocked response (D-26).

    Tests chat endpoint wiring without requiring a live API key.
    Mocks httpx to return a canned SSE stream.
    """
    import httpx
    import examples.workbench.api_chat as chat_module

    # Set a fake API key so the endpoint doesn't short-circuit
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-mock-key")

    # Build a mock httpx response that yields SSE lines
    mock_lines = [
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello from mock"}}',
        "data: [DONE]",
    ]

    class MockAsyncByteStream:
        async def __aiter__(self):
            for line in mock_lines:
                yield (line + "\n").encode()

        async def aclose(self):
            pass

    class MockResponse:
        status_code = 200
        headers = {}
        stream = MockAsyncByteStream()

        async def aiter_lines(self):
            for line in mock_lines:
                yield line

        async def aread(self):
            return b""

        async def aclose(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def stream(self, method, url, **kwargs):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    resp = client.post(
        "/api/chat",
        json={"question": "What are the catering costs?", "history": []},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Hello from mock" in body or "text" in body


# ---------------------------------------------------------------------------
# Template API Tests
# ---------------------------------------------------------------------------


def test_template_api_endpoint(client):
    """GET /api/template returns domain template for contracts."""
    resp = client.get("/api/template")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Sample Contract Analysis Workbench"
    assert "persona" in body
    assert "starter_questions" in body


def test_template_api_generic(sample_output_dir):
    """GET /api/template returns generic template when no domain."""
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(sample_output_dir, domain=None)
    generic_client = TestClient(app)
    resp = generic_client.get("/api/template")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Knowledge Graph Explorer"


# ---------------------------------------------------------------------------
# Template Tests
# ---------------------------------------------------------------------------


def test_template_loading_contracts():
    """load_template('contracts') returns STA title."""
    from examples.workbench.template_loader import load_template

    t = load_template("contracts")
    assert t["title"] == "Sample Contract Analysis Workbench", f"Got: {t['title']}"


def test_template_loading_drug_discovery():
    """load_template('drug-discovery') returns drug discovery title."""
    from examples.workbench.template_loader import load_template

    t = load_template("drug-discovery")
    assert "Drug Discovery" in t["title"], f"Got: {t['title']}"


def test_template_generic_fallback():
    """load_template('nonexistent') returns generic defaults."""
    from examples.workbench.template_loader import load_template

    t = load_template("nonexistent")
    assert t["title"] == "Knowledge Graph Explorer", f"Got: {t['title']}"


def test_template_none_fallback():
    """load_template(None) returns generic defaults."""
    from examples.workbench.template_loader import load_template

    t = load_template(None)
    assert t["title"] == "Knowledge Graph Explorer", f"Got: {t['title']}"


def test_auto_generate_starters():
    """auto_generate_starters with entity types returns 3+ questions."""
    from examples.workbench.template_loader import auto_generate_starters

    starters = auto_generate_starters(["COMPOUND", "GENE"])
    assert len(starters) >= 3, f"Expected >= 3, got {len(starters)}"
    # Should mention entity types
    combined = " ".join(starters).lower()
    assert "compound" in combined, "Expected 'compound' in starters"


def test_auto_generate_starters_empty():
    """auto_generate_starters([]) returns single fallback."""
    from examples.workbench.template_loader import auto_generate_starters

    starters = auto_generate_starters([])
    assert len(starters) == 1, f"Expected 1, got {len(starters)}"


def test_template_schema_validation():
    """WorkbenchTemplate validates contracts template content."""
    from examples.workbench.template_schema import WorkbenchTemplate

    import yaml
    from pathlib import Path

    yaml_path = Path("domains/contracts/workbench/template.yaml")
    if not yaml_path.exists():
        pytest.skip("contracts template.yaml not yet created")
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    model = WorkbenchTemplate(**data)
    assert model.title == "Sample Contract Analysis Workbench"


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


# ---------------------------------------------------------------------------
# FT-018 — FIDL-06 end-to-end: domain auto-detection through /api/template
# ---------------------------------------------------------------------------


def _ft018_build_stub_graph(tmp_dir: Path, domain_name: str | None) -> None:
    """Write a minimal graph_data.json that matches sift-kg's schema + has metadata.domain."""
    import json as _json

    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / "graph_data.json").write_text(_json.dumps({
        "metadata": {
            "created_at": "2026-04-21T00:00:00+00:00",
            "updated_at": "2026-04-21T00:00:00+00:00",
            "entity_count": 0,
            "relation_count": 0,
            "document_count": 0,
            "entity_type_summary": {},
            "sift_kg_version": "0.9.0-stub",
            "domain": domain_name,
        },
        "nodes": [],
        "links": [],
    }))


def test_ft018_domain_autodetect_through_api_contracts(tmp_path):
    """FT-018 (half 1): contracts graph → /api/template returns contracts template (no explicit --domain)."""
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    out = tmp_path / "contract_out"
    _ft018_build_stub_graph(out, "contracts")

    app = create_app(out, domain=None)  # no explicit → must auto-detect
    client = TestClient(app)
    resp = client.get("/api/template")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Sample Contract Analysis Workbench", (
        f"Expected contracts title, got {body['title']!r}"
    )
    assert body.get("analysis_patterns") is not None, (
        "Contracts template must ship analysis_patterns per Plan 17-02 Task 1"
    )
    assert (
        body["analysis_patterns"]["cross_references_heading"]
        == "CROSS-CONTRACT REFERENCES"
    )


def test_ft018_domain_autodetect_through_api_drug_discovery(tmp_path):
    """FT-018 (half 2): drug-discovery graph → /api/template returns drug-discovery template."""
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    out = tmp_path / "dd_out"
    _ft018_build_stub_graph(out, "drug-discovery")

    app = create_app(out, domain=None)
    client = TestClient(app)
    resp = client.get("/api/template")
    assert resp.status_code == 200
    body = resp.json()
    assert "Drug Discovery" in body["title"], (
        f"Expected drug-discovery title, got {body['title']!r}"
    )
    assert body.get("analysis_patterns") is not None
    assert (
        body["analysis_patterns"]["cross_references_heading"]
        == "CROSS-STUDY REFERENCES"
    )


def test_ft018_explicit_beats_metadata(tmp_path):
    """FT-018 (D-09 regression): explicit --domain overrides graph_data.json metadata."""
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    out = tmp_path / "mixed"
    _ft018_build_stub_graph(out, "contracts")  # graph says contracts

    app = create_app(out, domain="drug-discovery")  # user says drug-discovery
    client = TestClient(app)
    resp = client.get("/api/template")
    assert resp.status_code == 200
    assert "Drug Discovery" in resp.json()["title"], (
        "D-09: explicit --domain must beat metadata.domain"
    )


def test_ft018_legacy_graph_no_metadata_domain(tmp_path):
    """FT-018 (D-08 regression): legacy graph without metadata.domain → generic fallback."""
    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    out = tmp_path / "legacy"
    _ft018_build_stub_graph(out, None)  # writes "domain": null

    app = create_app(out, domain=None)
    client = TestClient(app)
    resp = client.get("/api/template")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Knowledge Graph Explorer", (
        f"D-08: legacy graph must fall back to generic, got {body['title']!r}"
    )
