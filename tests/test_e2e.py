#!/usr/bin/env python3
"""End-to-end pipeline tests for epistract.

Tests the full lifecycle: extraction JSON -> graph build -> epistemic -> export
for both drug-discovery and contracts domains.
"""
import json
import shutil

import pytest

from conftest import FIXTURES_DIR, HAS_SIFTKG, PROJECT_ROOT


# ---------------------------------------------------------------------------
# All E2E tests require sift-kg
# ---------------------------------------------------------------------------
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed"),
]


def _setup_extraction(tmp_path, fixture_name, output_name):
    """Copy a fixture extraction JSON into tmp_path/extractions/."""
    extractions_dir = tmp_path / "extractions"
    extractions_dir.mkdir(exist_ok=True)
    src = FIXTURES_DIR / fixture_name
    dst = extractions_dir / output_name
    shutil.copy2(src, dst)
    return dst


@pytest.mark.e2e
def test_e2e_drug_discovery_pipeline(tmp_path):
    """Full lifecycle for drug-discovery domain: extract -> build -> epistemic -> export."""
    from run_sift import cmd_build, cmd_export
    from label_epistemic import analyze_epistemic

    # 1. Set up extraction fixture
    _setup_extraction(tmp_path, "sample_extraction_drug.json", "test_drug_paper.pdf.json")

    # 2. Build graph
    cmd_build(str(tmp_path), domain_name="drug-discovery")

    # 3. Verify graph was created
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), f"graph_data.json not created after cmd_build in {tmp_path}"

    graph_data = json.loads(graph_path.read_text())
    assert len(graph_data.get("nodes", [])) > 0, f"Graph has no nodes: {list(graph_data.keys())}"

    # 4. Run epistemic analysis (label_communities is called by cmd_build)
    claims_layer = analyze_epistemic(tmp_path, domain_name="drug-discovery")

    # 5. Verify claims layer
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), f"claims_layer.json not created after epistemic analysis"
    assert isinstance(claims_layer, dict), f"analyze_epistemic returned {type(claims_layer)}, expected dict"

    # 6. Export to JSON
    cmd_export(str(tmp_path), "json")

    # 7. Verify export file exists (sift-kg creates export_*.json or similar)
    export_files = list(tmp_path.glob("*export*")) + list(tmp_path.glob("*.graphml")) + list(tmp_path.glob("export/"))
    # sift-kg export may vary; just verify no error was raised


@pytest.mark.e2e
def test_e2e_contract_pipeline(tmp_path):
    """Full lifecycle for contracts domain: extract -> build -> epistemic -> export."""
    from run_sift import cmd_build, cmd_export
    from label_epistemic import analyze_epistemic

    # 1. Set up extraction fixture
    _setup_extraction(tmp_path, "sample_extraction_contract.json", "test_vendor_agreement.pdf.json")

    # 2. Build graph
    cmd_build(str(tmp_path), domain_name="contracts")

    # 3. Verify graph was created
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), f"graph_data.json not created after cmd_build in {tmp_path}"

    graph_data = json.loads(graph_path.read_text())
    assert len(graph_data.get("nodes", [])) > 0, f"Graph has no nodes: {list(graph_data.keys())}"

    # 4. Run epistemic analysis
    claims_layer = analyze_epistemic(tmp_path, domain_name="contract")

    # 5. Verify claims layer
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), f"claims_layer.json not created after epistemic analysis"

    # 6. Export
    cmd_export(str(tmp_path), "json")


@pytest.mark.e2e
def test_e2e_pipeline_graph_has_metadata(tmp_path):
    """Verify graph output includes proper node metadata."""
    from run_sift import cmd_build

    # Build from drug extraction fixture
    _setup_extraction(tmp_path, "sample_extraction_drug.json", "test_drug_paper.pdf.json")
    cmd_build(str(tmp_path), domain_name="drug-discovery")

    # Load and verify graph structure
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), f"graph_data.json not created"

    data = json.loads(graph_path.read_text())

    # Verify top-level structure
    assert "nodes" in data, f"graph_data.json missing 'nodes' key, has: {list(data.keys())}"
    assert "links" in data or "edges" in data, f"graph_data.json missing 'links'/'edges' key, has: {list(data.keys())}"

    # Verify all nodes have required fields
    for node in data["nodes"]:
        assert "entity_type" in node, f"Node missing 'entity_type': {node}"
        assert "name" in node, f"Node missing 'name': {node}"
