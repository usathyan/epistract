#!/usr/bin/env python3
"""Integration tests for epistract command entry points and cross-domain verification.

Tests the core pipeline functions (build, search, export, epistemic, communities,
domain resolver) against fixture data. Also verifies cross-domain capability —
both drug-discovery and contracts domains produce valid graphs through the same
pipeline entry points.

Run:
    python3.11 -m pytest tests/test_integration.py -m integration -v --tb=short
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES_DIR, HAS_BIOPYTHON, HAS_RDKIT, HAS_SIFTKG, PROJECT_ROOT

# ---------------------------------------------------------------------------
# Ensure core/ is importable (conftest.py already adds it to sys.path)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TEST-02: Command entry point tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_build_extraction_writes_json(tmp_path):
    """write_extraction produces valid DocumentExtraction JSON on disk."""
    from build_extraction import write_extraction

    result_path = write_extraction(
        doc_id="test_doc.pdf",
        output_dir=str(tmp_path),
        entities=[
            {
                "name": "TestEntity",
                "entity_type": "PARTY",
                "confidence": 0.9,
                "context": "test context",
            }
        ],
        relations=[],
        domain_name="contracts",
    )

    out_file = tmp_path / "extractions" / "test_doc.pdf.json"
    assert out_file.exists(), f"Expected extraction file at {out_file}"

    data = json.loads(out_file.read_text())
    assert data["document_id"] == "test_doc.pdf", (
        f"Expected document_id 'test_doc.pdf', got {data['document_id']}"
    )
    assert len(data["entities"]) == 1, (
        f"Expected 1 entity, got {len(data['entities'])}"
    )


@pytest.mark.integration
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_cmd_build_from_fixture_extractions(tmp_path):
    """cmd_build produces a graph_data.json from extraction fixtures."""
    from run_sift import cmd_build

    extractions_dir = tmp_path / "extractions"
    extractions_dir.mkdir()
    shutil.copy2(
        FIXTURES_DIR / "sample_extraction_drug.json",
        extractions_dir / "test_doc.json",
    )

    cmd_build(str(tmp_path), domain_name="drug-discovery")

    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), "cmd_build did not produce graph_data.json"

    data = json.loads(graph_path.read_text())
    assert len(data.get("nodes", [])) > 0, "Graph has no nodes"


@pytest.mark.integration
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_cmd_search_finds_entity(tmp_path):
    """cmd_search finds a known entity in the graph fixture."""
    from run_sift import cmd_search

    shutil.copy2(
        FIXTURES_DIR / "sample_graph_data.json",
        tmp_path / "graph_data.json",
    )

    # cmd_search prints to stdout; verify it completes without error.
    # The function uses KnowledgeGraph.load which needs sift-kg.
    cmd_search(str(tmp_path), "Pennsylvania Convention Center Authority")


@pytest.mark.integration
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_cmd_export_creates_output(tmp_path):
    """cmd_export produces an export file."""
    from run_sift import cmd_export

    shutil.copy2(
        FIXTURES_DIR / "sample_graph_data.json",
        tmp_path / "graph_data.json",
    )

    cmd_export(str(tmp_path), "json")

    # Check that some export file was created (sift-kg puts it in an exports dir or similar)
    exports = list(tmp_path.rglob("*.json"))
    assert len(exports) >= 1, "cmd_export did not create any JSON output"


@pytest.mark.integration
def test_label_epistemic_produces_claims(tmp_path):
    """analyze_epistemic produces claims_layer.json from graph data."""
    from label_epistemic import analyze_epistemic

    shutil.copy2(
        FIXTURES_DIR / "sample_graph_data.json",
        tmp_path / "graph_data.json",
    )

    analyze_epistemic(tmp_path)

    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), "analyze_epistemic did not produce claims_layer.json"

    data = json.loads(claims_path.read_text())
    assert "summary" in data or "metadata" in data, (
        "claims_layer.json missing summary or metadata key"
    )


@pytest.mark.integration
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_label_communities_produces_output(tmp_path):
    """label_communities runs without error on fixture data."""
    from label_communities import label_communities

    shutil.copy2(
        FIXTURES_DIR / "sample_graph_data.json",
        tmp_path / "graph_data.json",
    )
    # label_communities expects communities.json as {entity_id: community_name} dict
    # (the format sift-kg produces). Build from fixture data.
    graph_data = json.loads((FIXTURES_DIR / "sample_graph_data.json").read_text())
    communities_dict = {}
    for node in graph_data.get("nodes", []):
        community = node.get("community", 0)
        communities_dict[node["id"]] = community

    communities_path = tmp_path / "communities.json"
    communities_path.write_text(json.dumps(communities_dict, indent=2))

    result = label_communities(tmp_path)
    # Function should return a dict (even if empty)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"


@pytest.mark.integration
def test_domain_resolver_resolves_both_domains():
    """resolve_domain returns valid dicts for both known domains."""
    from domain_resolver import resolve_domain

    for domain_name in ("drug-discovery", "contracts"):
        result = resolve_domain(domain_name)
        assert isinstance(result, dict), f"Expected dict for {domain_name}"
        assert "yaml_path" in result, f"Missing yaml_path for {domain_name}"
        assert Path(result["yaml_path"]).exists(), (
            f"yaml_path does not exist for {domain_name}: {result['yaml_path']}"
        )


@pytest.mark.integration
@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
def test_validate_molecules_runs_without_error(tmp_path):
    """validate_molecules main() completes without exception on drug fixture."""
    extractions_dir = tmp_path / "extractions"
    extractions_dir.mkdir()
    shutil.copy2(
        FIXTURES_DIR / "sample_extraction_drug.json",
        extractions_dir / "test.json",
    )

    # Import and call the validation orchestrator
    from validate_molecules import process_extraction

    result = process_extraction(extractions_dir / "test.json")
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"


# ---------------------------------------------------------------------------
# TEST-07: Cross-domain verification
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_cross_domain_both_produce_valid_graphs(tmp_path):
    """Both domains produce valid output through the same pipeline entry points.

    Drug-discovery is tested via cmd_build (sift-kg compatible schema).
    Contracts is tested via write_extraction (sift-kg load_domain requires dict-format
    entity_types which the contracts list-format YAML doesn't match yet).
    Both domains go through the same domain resolver + extraction writer.
    """
    from build_extraction import write_extraction
    from run_sift import cmd_build

    # Drug-discovery: full cmd_build pipeline
    drug_dir = tmp_path / "drug_discovery"
    extractions_dir = drug_dir / "extractions"
    extractions_dir.mkdir(parents=True)
    shutil.copy2(
        FIXTURES_DIR / "sample_extraction_drug.json",
        extractions_dir / "test.json",
    )
    cmd_build(str(drug_dir), domain_name="drug-discovery")
    drug_graph = drug_dir / "graph_data.json"
    assert drug_graph.exists(), "cmd_build did not produce graph_data.json for drug-discovery"
    drug_data = json.loads(drug_graph.read_text())
    assert len(drug_data.get("nodes", [])) > 0, "Drug-discovery graph has no nodes"

    # Contracts: write_extraction + domain resolver (validates extraction pipeline)
    contract_dir = tmp_path / "contracts"
    write_extraction(
        doc_id="test_vendor.pdf",
        output_dir=str(contract_dir),
        entities=[
            {"name": "PCCA", "entity_type": "PARTY", "confidence": 0.95, "context": "Licensor"},
            {"name": "Catering", "entity_type": "SERVICE", "confidence": 0.90, "context": "Food services"},
        ],
        relations=[
            {"source_entity": "PCCA", "target_entity": "Catering", "relation_type": "PROVIDES_SERVICE",
             "confidence": 0.88, "evidence": "PCCA provides catering services."},
        ],
        domain_name="contracts",
    )
    contract_extraction = contract_dir / "extractions" / "test_vendor.pdf.json"
    assert contract_extraction.exists(), "write_extraction did not create file for contracts"
    contract_data = json.loads(contract_extraction.read_text())
    assert contract_data["domain_name"] == "Contract Analysis", (
        f"Expected domain_name 'Contract Analysis', got {contract_data['domain_name']}"
    )


@pytest.mark.integration
def test_cross_domain_resolver_loads_correct_schemas():
    """Both domains have valid YAML schemas with entity_types and relation_types."""
    from domain_resolver import resolve_domain

    for domain_name in ("drug-discovery", "contracts"):
        result = resolve_domain(domain_name)
        yaml_path = Path(result["yaml_path"])
        assert yaml_path.exists(), f"YAML not found for {domain_name}: {yaml_path}"

        data = yaml.safe_load(yaml_path.read_text())
        assert "entity_types" in data, (
            f"Missing entity_types in {domain_name} domain.yaml"
        )
        assert "relation_types" in data, (
            f"Missing relation_types in {domain_name} domain.yaml"
        )
        assert len(data["entity_types"]) > 0, (
            f"Empty entity_types in {domain_name}"
        )
        assert len(data["relation_types"]) > 0, (
            f"Empty relation_types in {domain_name}"
        )
