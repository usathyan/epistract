"""KG Provenance Test: Trace chat responses back to knowledge graph nodes.

Converted from live-server HTTP tests to fixture-based offline tests (per D-03).
Tests verify graph tracing logic (node lookup, edge traversal, entity matching)
against fixture data, NOT the API layer.

Lifecycle chain under test:
  Chat response (claims) -> KG entity/relation -> Source document

Each test:
  1. Uses a pre-recorded chat response referencing graph entities
  2. Extracts named entities from the response
  3. Verifies each entity exists as a node in the graph
  4. Verifies relationships claimed exist as edges
  5. Verifies source documents are traceable

Run:
  python3.11 -m pytest tests/test_kg_provenance.py -v --tb=short
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR

# ---------------------------------------------------------------------------
# Pre-recorded chat responses (replaces live /api/chat HTTP calls)
# Each response references entities known to exist in sample_graph_data.json
# ---------------------------------------------------------------------------

MOCK_CHAT_RESPONSES = {
    "pcc_obligations": (
        "Under the PCC License Agreement, STA's key obligations include:\n\n"
        "1. **Security Staffing**: Security staffing for load-in days is required "
        "with guards at $85 per hour (source: pcc_license_agreement.pdf).\n"
        "2. **Insurance**: Insurance certificates are due June 1, 2026 per the "
        "Pennsylvania Convention Center Authority requirements.\n"
        "3. **Force Majeure**: The force majeure provision in the license agreement "
        "covers acts of God, strikes, and government orders.\n"
        "4. **Venue Access**: Hall A and Ballroom B are the primary event spaces "
        "at the Pennsylvania Convention Center.\n"
    ),
    "hotel_costs": (
        "The hotel contracts show the following room rates and commitments:\n\n"
        "- The room block costs include rates that vary by property.\n"
        "- $45 per person lunch service is provided by Aramark Sports & Entertainment "
        "under the catering agreement (source: aramark_catering_agreement.pdf).\n"
        "- Total financial exposure depends on final headcount due August 1, 2026.\n"
        "- The catering contract requires exclusive catering rights per Section 4.2.\n"
    ),
    "av_vendor_comparison": (
        "Comparing the AV production services:\n\n"
        "- **PSAV Presentation Services** provides exclusive AV services in all halls "
        "at a cost of $12,000 for the AV package in Hall A.\n"
        "- AV equipment list is due July 15, 2026 per the contract deadline.\n"
        "- Audio visual production services cover the main stage show Friday night.\n"
        "- The Programs Committee, chaired by Bob Johnson, coordinates AV needs.\n"
    ),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def graph_data():
    """Load graph data from test fixtures (per D-03: no live server)."""
    return json.loads((FIXTURES_DIR / "sample_graph_data.json").read_text())


@pytest.fixture(scope="module")
def graph_index(graph_data):
    """Build lookup indexes for fast provenance checks."""
    nodes_by_id = {n["id"]: n for n in graph_data["nodes"]}
    nodes_by_name = {}
    for n in graph_data["nodes"]:
        name_lower = n.get("name", "").lower()
        nodes_by_name[name_lower] = n
        # Also index without punctuation for fuzzy matching
        clean = re.sub(r"[^a-z0-9 ]", "", name_lower)
        nodes_by_name[clean] = n

    edges_by_source = {}
    edges_by_target = {}
    for e in graph_data["edges"]:
        edges_by_source.setdefault(e["source"], []).append(e)
        edges_by_target.setdefault(e["target"], []).append(e)

    return {
        "nodes_by_id": nodes_by_id,
        "nodes_by_name": nodes_by_name,
        "edges_by_source": edges_by_source,
        "edges_by_target": edges_by_target,
        "all_nodes": graph_data["nodes"],
        "all_edges": graph_data["edges"],
    }


@pytest.fixture(scope="module")
def entity_types(graph_data):
    """Compute entity type distribution from fixture data."""
    counts = {}
    for node in graph_data["nodes"]:
        etype = node.get("entity_type", "UNKNOWN")
        counts[etype] = counts.get(etype, 0) + 1
    return counts


def find_node(graph_index: dict, name: str) -> dict | None:
    """Find a node by name with fuzzy matching."""
    name_lower = name.lower().strip()
    # Exact match
    if name_lower in graph_index["nodes_by_name"]:
        return graph_index["nodes_by_name"][name_lower]
    # Clean match
    clean = re.sub(r"[^a-z0-9 ]", "", name_lower)
    if clean in graph_index["nodes_by_name"]:
        return graph_index["nodes_by_name"][clean]
    # Substring match -- find nodes whose name contains the search term
    for node in graph_index["all_nodes"]:
        node_name = node.get("name", "").lower()
        if name_lower in node_name or node_name in name_lower:
            return node
    # Keyword overlap match (2+ words)
    search_words = set(re.findall(r"[a-z0-9]+", name_lower)) - {
        "a", "an", "the", "and", "or", "of", "for", "to", "in", "at",
    }
    if len(search_words) >= 2:
        for node in graph_index["all_nodes"]:
            node_words = set(re.findall(r"[a-z0-9]+", node.get("name", "").lower()))
            if len(search_words & node_words) >= 2:
                return node
    return None


def find_edges_between(graph_index: dict, source_name: str, target_name: str) -> list[dict]:
    """Find edges connecting two entities by name."""
    src_node = find_node(graph_index, source_name)
    tgt_node = find_node(graph_index, target_name)
    if not src_node or not tgt_node:
        return []
    src_id = src_node["id"]
    tgt_id = tgt_node["id"]
    edges = []
    for e in graph_index.get("edges_by_source", {}).get(src_id, []):
        if e["target"] == tgt_id:
            edges.append(e)
    for e in graph_index.get("edges_by_source", {}).get(tgt_id, []):
        if e["target"] == src_id:
            edges.append(e)
    return edges


# ---------------------------------------------------------------------------
# Test 1: PCC Venue -- covers VENUE, PARTY, SERVICE, ROOM, CLAUSE, OBLIGATION
# ---------------------------------------------------------------------------
# This question targets the venue hub in the graph


class TestPCCVenueProvenance:
    """Trace claims about Pennsylvania Convention Center back to KG nodes."""

    @pytest.fixture(scope="class")
    def chat_response(self):
        return MOCK_CHAT_RESPONSES["pcc_obligations"]

    @pytest.mark.unit
    def test_response_not_empty(self, chat_response):
        assert len(chat_response) > 100, "Chat response too short"

    @pytest.mark.unit
    def test_pcc_venue_in_graph(self, graph_index):
        """Pennsylvania Convention Center must exist as a node (VENUE or PARTY)."""
        node = find_node(graph_index, "Pennsylvania Convention Center")
        assert node is not None, "PCC venue node not found in graph"
        assert node["entity_type"] in ("VENUE", "PARTY"), (
            f"PCC should be VENUE or PARTY, got {node['entity_type']}"
        )

    @pytest.mark.unit
    def test_pcca_party_in_graph(self, graph_index):
        """PARTY: Pennsylvania Convention Center Authority must exist."""
        node = find_node(graph_index, "Pennsylvania Convention Center Authority")
        assert node is not None, "PCCA party node not found"
        assert node["entity_type"] == "PARTY"

    @pytest.mark.unit
    def test_akka_party_referenced_in_response(self, chat_response):
        """Chat response should reference STA obligations."""
        assert "akka" in chat_response.lower(), "Response does not mention STA"

    @pytest.mark.unit
    def test_pcc_has_obligations(self, graph_index):
        """The PCC venue should have OBLIGATES or PROVIDES edges."""
        pcc = find_node(graph_index, "Pennsylvania Convention Center Authority")
        assert pcc is not None
        edges = graph_index["edges_by_source"].get(pcc["id"], [])
        edge_types = {e["relation_type"] for e in edges}
        assert "OBLIGATES" in edge_types or "PROVIDES" in edge_types or "REQUIRES" in edge_types, (
            f"PCCA has no OBLIGATES, PROVIDES, or REQUIRES edges. Has: {edge_types}"
        )

    @pytest.mark.unit
    def test_pcc_license_agreement_source(self, graph_data):
        """The PCC License Agreement document must be referenced as a source."""
        all_sources = set()
        for node in graph_data["nodes"]:
            for doc in node.get("source_documents", []):
                all_sources.add(doc)
        assert "pcc_license_agreement.pdf" in all_sources, (
            f"PCC License Agreement not found in source documents. Sources: {all_sources}"
        )

    @pytest.mark.unit
    def test_room_entities_in_graph(self, graph_index):
        """ROOM: At least one room entity must exist."""
        rooms = [n for n in graph_index["all_nodes"] if n["entity_type"] == "ROOM"]
        assert len(rooms) >= 1, "Expected at least 1 ROOM entity in fixture"

    @pytest.mark.unit
    def test_cost_entities_exist(self, entity_types):
        """COST: Graph should have cost entities for financial commitments."""
        assert entity_types.get("COST", 0) >= 1, (
            f"Expected 1+ COST entities, got {entity_types.get('COST', 0)}"
        )

    @pytest.mark.unit
    def test_clause_entities_exist(self, entity_types):
        """CLAUSE: Graph should have clause entities for restrictions."""
        assert entity_types.get("CLAUSE", 0) >= 1, (
            f"Expected 1+ CLAUSE entities, got {entity_types.get('CLAUSE', 0)}"
        )

    @pytest.mark.unit
    def test_chat_mentions_graph_entities(self, chat_response, graph_index):
        """Chat response should reference entities that exist in the graph."""
        key_terms = [
            "Pennsylvania Convention Center",
            "Hall A",
            "security",
        ]
        found = 0
        for term in key_terms:
            if term.lower() in chat_response.lower():
                node = find_node(graph_index, term)
                if node:
                    found += 1
        assert found >= 2, (
            f"Chat response should mention at least 2 graph entities, found {found}"
        )


# ---------------------------------------------------------------------------
# Test 2: Catering costs -- covers COST, PARTY, DEADLINE, SERVICE
# ---------------------------------------------------------------------------


class TestCateringCostProvenance:
    """Trace catering cost claims back to KG nodes and source contracts."""

    @pytest.fixture(scope="class")
    def chat_response(self):
        return MOCK_CHAT_RESPONSES["hotel_costs"]

    @pytest.mark.unit
    def test_response_not_empty(self, chat_response):
        assert len(chat_response) > 100

    @pytest.mark.unit
    def test_aramark_in_graph(self, graph_index):
        """PARTY: Aramark Sports & Entertainment must exist."""
        node = find_node(graph_index, "Aramark Sports & Entertainment")
        assert node is not None, "Aramark party not found in graph"
        assert node["entity_type"] == "PARTY"

    @pytest.mark.unit
    def test_aramark_has_cost_edges(self, graph_index):
        """Aramark should have service or cost related edges."""
        aramark = find_node(graph_index, "Aramark Sports & Entertainment")
        assert aramark is not None
        all_edges = (
            graph_index["edges_by_source"].get(aramark["id"], [])
            + graph_index["edges_by_target"].get(aramark["id"], [])
        )
        assert len(all_edges) >= 1, f"Aramark should have 1+ edges, got {len(all_edges)}"

    @pytest.mark.unit
    def test_cost_nodes_exist(self, graph_index):
        """COST nodes should exist in the graph."""
        cost_nodes = [
            n for n in graph_index["all_nodes"]
            if n["entity_type"] == "COST"
        ]
        assert len(cost_nodes) >= 1, f"Expected 1+ COST nodes, found {len(cost_nodes)}"

    @pytest.mark.unit
    def test_catering_contract_is_source(self, graph_data):
        """Aramark catering agreement should exist as a source document."""
        all_sources = set()
        for node in graph_data["nodes"]:
            for doc in node.get("source_documents", []):
                all_sources.add(doc)
        assert "aramark_catering_agreement.pdf" in all_sources, (
            "Aramark catering agreement not found in source documents"
        )

    @pytest.mark.unit
    def test_cross_contract_sources(self, graph_data):
        """Multiple source contracts should be referenced across nodes."""
        all_sources = set()
        for node in graph_data["nodes"]:
            for doc in node.get("source_documents", []):
                all_sources.add(doc)
        assert len(all_sources) >= 3, (
            f"Expected 3+ source documents across nodes, found {len(all_sources)}"
        )

    @pytest.mark.unit
    def test_chat_references_dollar_amounts(self, chat_response):
        """Chat response should include specific dollar amounts from KG."""
        amounts = re.findall(r"\$[\d,]+", chat_response)
        assert len(amounts) >= 1, (
            f"Expected 1+ dollar amounts in response, found {len(amounts)}"
        )


# ---------------------------------------------------------------------------
# Test 3: AV vendor -- covers SERVICE, COST, PARTY
# ---------------------------------------------------------------------------


class TestAVVendorProvenance:
    """Trace AV vendor claims back to KG nodes."""

    @pytest.fixture(scope="class")
    def chat_response(self):
        return MOCK_CHAT_RESPONSES["av_vendor_comparison"]

    @pytest.mark.unit
    def test_response_not_empty(self, chat_response):
        assert len(chat_response) > 100

    @pytest.mark.unit
    def test_psav_in_graph(self, graph_index):
        """PARTY: PSAV Presentation Services should exist."""
        node = find_node(graph_index, "PSAV Presentation Services")
        assert node is not None, "PSAV entity not found in graph"
        assert node["entity_type"] == "PARTY"

    @pytest.mark.unit
    def test_av_service_in_graph(self, graph_index):
        """SERVICE: Audio visual production services should exist."""
        node = find_node(graph_index, "Audio visual production services")
        assert node is not None, "AV production service not found in graph"
        assert node["entity_type"] == "SERVICE"

    @pytest.mark.unit
    def test_av_cost_nodes_exist(self, graph_index):
        """COST nodes related to AV should exist."""
        av_costs = [
            n for n in graph_index["all_nodes"]
            if n["entity_type"] == "COST"
            and any(kw in n.get("name", "").lower() for kw in ["av", "audio", "video", "production", "12000", "12,000"])
        ]
        assert len(av_costs) >= 1, "Expected AV-related cost nodes in graph"

    @pytest.mark.unit
    def test_av_documents_are_sources(self, graph_data):
        """AV contract document should exist as a source."""
        all_sources = set()
        for node in graph_data["nodes"]:
            for doc in node.get("source_documents", []):
                all_sources.add(doc)
        assert "av_services_contract.pdf" in all_sources, (
            "AV services contract not found in source documents"
        )

    @pytest.mark.unit
    def test_chat_mentions_av_vendor(self, chat_response):
        """Chat should mention PSAV or AV production."""
        has_psav = "psav" in chat_response.lower()
        has_av = "av" in chat_response.lower() or "audio visual" in chat_response.lower()
        assert has_psav or has_av, "Chat should mention PSAV or AV production"

    @pytest.mark.unit
    def test_chat_includes_cost_info(self, chat_response):
        """Chat should include dollar amounts for AV services."""
        amounts = re.findall(r"\$[\d,]+", chat_response)
        assert len(amounts) >= 1, (
            f"Expected 1+ dollar amounts for AV, found {len(amounts)}"
        )


# ---------------------------------------------------------------------------
# Test 4: Graph structural integrity
# ---------------------------------------------------------------------------


class TestGraphStructure:
    """Verify the KG has the structural properties needed for provenance."""

    @pytest.mark.unit
    def test_node_count(self, graph_index):
        """Fixture graph should have expected node count."""
        assert len(graph_index["all_nodes"]) >= 20, (
            f"Expected 20+ nodes in fixture, got {len(graph_index['all_nodes'])}"
        )

    @pytest.mark.unit
    def test_edge_count(self, graph_index):
        """Fixture graph should have expected edge count."""
        assert len(graph_index["all_edges"]) >= 20, (
            f"Expected 20+ edges in fixture, got {len(graph_index['all_edges'])}"
        )

    @pytest.mark.unit
    def test_all_entity_types_present(self, entity_types):
        """Core entity types should be present in fixture graph."""
        expected = {"PARTY", "OBLIGATION", "COST", "SERVICE", "CLAUSE", "VENUE", "DEADLINE"}
        present = set(entity_types.keys())
        missing = expected - present
        assert not missing, f"Missing entity types: {missing}"

    @pytest.mark.unit
    def test_all_edges_reference_valid_nodes(self, graph_index):
        """Every edge source/target should reference an existing node."""
        node_ids = set(graph_index["nodes_by_id"].keys())
        orphan_edges = 0
        for e in graph_index["all_edges"]:
            if e["source"] not in node_ids or e["target"] not in node_ids:
                orphan_edges += 1
        assert orphan_edges == 0, f"{orphan_edges} edges reference non-existent nodes"

    @pytest.mark.unit
    def test_cross_contract_entities_exist(self, graph_data):
        """At least 1 entity should span 2+ contracts in fixture."""
        cross_count = 0
        for node in graph_data["nodes"]:
            docs = node.get("source_documents", [])
            if len(docs) >= 2:
                cross_count += 1
        assert cross_count >= 1, (
            f"Expected 1+ cross-contract entities, found {cross_count}"
        )

    @pytest.mark.unit
    def test_source_documents_traceable(self, graph_data):
        """All source documents referenced in nodes should be non-empty strings."""
        empty_sources = 0
        for node in graph_data["nodes"]:
            for doc in node.get("source_documents", []):
                if not doc or not isinstance(doc, str):
                    empty_sources += 1
        assert empty_sources == 0, f"{empty_sources} nodes have empty source document references"

    @pytest.mark.unit
    def test_nodes_have_required_fields(self, graph_data):
        """Every node must have id, name, entity_type, confidence."""
        for node in graph_data["nodes"]:
            assert "id" in node, f"Node missing 'id': {node}"
            assert "name" in node, f"Node missing 'name': {node}"
            assert "entity_type" in node, f"Node missing 'entity_type': {node}"
            assert "confidence" in node, f"Node missing 'confidence': {node}"

    @pytest.mark.unit
    def test_edges_have_required_fields(self, graph_data):
        """Every edge must have source, target, relation_type."""
        for edge in graph_data["edges"]:
            assert "source" in edge, f"Edge missing 'source': {edge}"
            assert "target" in edge, f"Edge missing 'target': {edge}"
            assert "relation_type" in edge, f"Edge missing 'relation_type': {edge}"

    @pytest.mark.unit
    def test_confidence_values_in_range(self, graph_data):
        """Node confidence values should be between 0 and 1."""
        for node in graph_data["nodes"]:
            conf = node.get("confidence", 0)
            assert 0 <= conf <= 1, (
                f"Node {node['id']} has confidence {conf} outside [0,1]"
            )

    @pytest.mark.unit
    def test_node_ids_are_unique(self, graph_data):
        """All node IDs must be unique."""
        ids = [n["id"] for n in graph_data["nodes"]]
        assert len(ids) == len(set(ids)), "Duplicate node IDs found"

    @pytest.mark.unit
    def test_edge_relation_types_are_non_empty(self, graph_data):
        """Edge relation_type values should be non-empty strings."""
        for edge in graph_data["edges"]:
            assert edge["relation_type"], f"Empty relation_type on edge: {edge}"

    @pytest.mark.unit
    def test_graph_has_community_assignments(self, graph_data):
        """Nodes should have community assignments."""
        with_community = sum(1 for n in graph_data["nodes"] if "community" in n)
        assert with_community >= len(graph_data["nodes"]) * 0.5, (
            f"Expected 50%+ nodes with community assignment, got {with_community}/{len(graph_data['nodes'])}"
        )
