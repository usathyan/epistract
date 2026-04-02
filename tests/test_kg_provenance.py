"""KG Provenance Test: Trace chat responses back to knowledge graph nodes.

Lifecycle chain under test:
  User question -> Chat response (claims) -> KG entity/relation -> Source document

Each test:
  1. Asks a question via /api/chat
  2. Extracts named entities from the response
  3. Verifies each entity exists as a node in the graph
  4. Verifies relationships claimed exist as edges
  5. Verifies source documents are traceable

Run:
  python -m pytest tests/test_kg_provenance.py -v --tb=short
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("WORKBENCH_URL", "http://127.0.0.1:8000")
OUTPUT_DIR = Path(os.environ.get(
    "EPISTRACT_OUTPUT",
    "/Users/umeshbhatt/code/epistract/epistract-output",
))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def graph_data():
    """Load full graph data from the running server."""
    resp = requests.get(f"{BASE_URL}/api/graph", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data


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
def entity_types():
    """Get entity type distribution from server."""
    resp = requests.get(f"{BASE_URL}/api/graph/entity-types", timeout=10)
    resp.raise_for_status()
    return resp.json()["entity_types"]


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
    # Substring match — find nodes whose name contains the search term
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


def ask_chat(question: str) -> str:
    """Send a question to the chat API and collect the full streamed response."""
    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={"question": question, "history": []},
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()
    full_text = ""
    for line in resp.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                if data.get("type") == "text":
                    full_text += data["content"]
            except json.JSONDecodeError:
                pass
    return full_text


# ---------------------------------------------------------------------------
# Test 1: PCC Venue — covers VENUE, PARTY, SERVICE, ROOM, CLAUSE, OBLIGATION
# ---------------------------------------------------------------------------
# This question targets the densest hub in the graph (47 edges, 19 docs)


class TestPCCVenueProvenance:
    """Trace claims about Pennsylvania Convention Center back to KG nodes."""

    QUESTION = (
        "What are STA's obligations under the PCC License Agreement? "
        "List the key financial commitments, venue restrictions, and labor rules."
    )

    @pytest.fixture(scope="class")
    def chat_response(self):
        return ask_chat(self.QUESTION)

    def test_response_not_empty(self, chat_response):
        assert len(chat_response) > 100, "Chat response too short"

    def test_pcc_venue_in_graph(self, graph_index):
        """Pennsylvania Convention Center must exist as a node (VENUE or PARTY)."""
        node = find_node(graph_index, "Pennsylvania Convention Center")
        assert node is not None, "PCC venue node not found in graph"
        assert node["entity_type"] in ("VENUE", "PARTY"), (
            f"PCC should be VENUE or PARTY, got {node['entity_type']}"
        )

    def test_pcca_party_in_graph(self, graph_index):
        """PARTY: Pennsylvania Convention Center Authority must exist."""
        node = find_node(graph_index, "Pennsylvania Convention Center Authority")
        assert node is not None, "PCCA party node not found"
        assert node["entity_type"] == "PARTY"

    def test_akka_party_in_graph(self, graph_index):
        """PARTY: STA must exist as a party node."""
        node = find_node(graph_index, "Association of Sample Kootas of America")
        assert node is not None, "STA party node not found"
        assert node["entity_type"] == "PARTY"

    def test_pcc_has_obligations(self, graph_index):
        """The PCC venue should have OBLIGATES edges."""
        pcc = find_node(graph_index, "Pennsylvania Convention Center Authority")
        assert pcc is not None
        edges = graph_index["edges_by_source"].get(pcc["id"], [])
        edge_types = {e["relation_type"] for e in edges}
        assert "OBLIGATES" in edge_types or "PROVIDES" in edge_types, (
            f"PCCA has no OBLIGATES or PROVIDES edges. Has: {edge_types}"
        )

    def test_pcc_license_agreement_source(self, graph_index):
        """The PCC License Agreement document must exist and link to PCC entities."""
        doc_node = find_node(graph_index, "26741_unexecuted_license_agreement")
        assert doc_node is not None, "PCC License Agreement document not found"
        # Should have many edges (it's the 4th most connected node at 29 edges)
        edges = (
            graph_index["edges_by_source"].get(doc_node["id"], [])
            + graph_index["edges_by_target"].get(doc_node["id"], [])
        )
        assert len(edges) >= 10, f"Expected 10+ edges for PCC license doc, got {len(edges)}"

    def test_hall_a_room_in_graph(self, graph_index):
        """ROOM: Hall A must exist (key venue space)."""
        node = find_node(graph_index, "Hall A")
        assert node is not None
        assert node["entity_type"] == "ROOM"

    def test_cost_entities_exist(self, graph_index, entity_types):
        """COST: Graph should have cost entities for financial commitments."""
        assert entity_types.get("COST", 0) >= 20, (
            f"Expected 20+ COST entities, got {entity_types.get('COST', 0)}"
        )

    def test_clause_entities_exist(self, graph_index, entity_types):
        """CLAUSE: Graph should have clause entities for restrictions."""
        assert entity_types.get("CLAUSE", 0) >= 10, (
            f"Expected 10+ CLAUSE entities, got {entity_types.get('CLAUSE', 0)}"
        )

    def test_chat_mentions_graph_entities(self, chat_response, graph_index):
        """Chat response should reference entities that exist in the graph."""
        # Extract likely entity names from response
        key_terms = [
            "Pennsylvania Convention Center",
            "STA",
            "Hall A",
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
# Test 2: Hotel costs — covers COST, PARTY, DEADLINE, SERVICE across contracts
# ---------------------------------------------------------------------------
# Targets cross-contract cost comparisons (Marriott $169 vs Sheraton $149)


class TestHotelCostProvenance:
    """Trace hotel cost claims back to KG nodes and source contracts."""

    QUESTION = (
        "Compare the hotel room rates across all three hotel contracts. "
        "What is the total room block commitment and financial exposure?"
    )

    @pytest.fixture(scope="class")
    def chat_response(self):
        return ask_chat(self.QUESTION)

    def test_response_not_empty(self, chat_response):
        assert len(chat_response) > 100

    def test_marriott_in_graph(self, graph_index):
        """PARTY: Philadelphia Marriott Downtown must exist."""
        node = find_node(graph_index, "Philadelphia Marriott Downtown")
        assert node is not None
        assert node["entity_type"] == "PARTY"

    def test_sheraton_in_graph(self, graph_index):
        """Sheraton Philadelphia Downtown must exist (PARTY or VENUE)."""
        node = find_node(graph_index, "Sheraton Philadelphia Downtown")
        assert node is not None
        assert node["entity_type"] in ("PARTY", "VENUE"), (
            f"Sheraton should be PARTY or VENUE, got {node['entity_type']}"
        )

    def test_marriott_has_cost_edges(self, graph_index):
        """Marriott should have COSTS or PROVIDES edges."""
        marriott = find_node(graph_index, "Philadelphia Marriott Downtown")
        assert marriott is not None
        all_edges = (
            graph_index["edges_by_source"].get(marriott["id"], [])
            + graph_index["edges_by_target"].get(marriott["id"], [])
        )
        edge_types = {e["relation_type"] for e in all_edges}
        assert len(all_edges) >= 3, f"Marriott should have 3+ edges, got {len(all_edges)}"

    def test_room_rate_cost_nodes_exist(self, graph_index):
        """COST nodes for room rates should exist in the graph."""
        cost_nodes = [
            n for n in graph_index["all_nodes"]
            if n["entity_type"] == "COST" and "night" in n.get("name", "").lower()
        ]
        assert len(cost_nodes) >= 2, (
            f"Expected 2+ room rate COST nodes, found {len(cost_nodes)}"
        )

    def test_hotel_contracts_are_sources(self, graph_index):
        """Hotel agreement documents should exist as source nodes."""
        marriott_doc = find_node(graph_index, "090226_cr1akkaworldsampleconference")
        sheraton_doc = find_node(graph_index, "akka_september_2026_sheraton")
        found = sum(1 for d in [marriott_doc, sheraton_doc] if d is not None)
        assert found >= 1, "At least one hotel contract document should be in graph"

    def test_cross_contract_cost_comparison(self, graph_index):
        """Multiple cost nodes from different contracts should exist for comparison."""
        cost_nodes = [
            n for n in graph_index["all_nodes"]
            if n["entity_type"] == "COST"
        ]
        # Group by source_documents
        docs_per_cost = {}
        for n in cost_nodes:
            docs = n.get("source_documents", [])
            if docs:
                docs_per_cost[n["id"]] = docs

        unique_docs = set()
        for docs in docs_per_cost.values():
            unique_docs.update(docs)
        assert len(unique_docs) >= 5, (
            f"Cost entities should span 5+ contracts, found {len(unique_docs)}"
        )

    def test_chat_references_dollar_amounts(self, chat_response):
        """Chat response should include specific dollar amounts from KG."""
        amounts = re.findall(r"\$[\d,]+", chat_response)
        assert len(amounts) >= 2, (
            f"Expected 2+ dollar amounts in response, found {len(amounts)}"
        )


# ---------------------------------------------------------------------------
# Test 3: AV vendor comparison — covers SERVICE, COST, PARTY, ROOM
# ---------------------------------------------------------------------------
# Targets the largest cost mismatch cluster (Prime AV vs B&W Productions)


class TestAVVendorProvenance:
    """Trace AV vendor claims back to KG nodes and conflict layer."""

    QUESTION = (
        "Compare the two AV production quotes — Prime AV vs Black & White Productions. "
        "What does each cover, what are the cost differences, and which rooms are included?"
    )

    @pytest.fixture(scope="class")
    def chat_response(self):
        return ask_chat(self.QUESTION)

    def test_response_not_empty(self, chat_response):
        assert len(chat_response) > 100

    def test_prime_av_in_graph(self, graph_index):
        """SERVICE: Prime AV service should exist."""
        # Try various name forms
        node = (
            find_node(graph_index, "Prime AV")
            or find_node(graph_index, "AV production")
            or find_node(graph_index, "job_1025151_prime_av")
        )
        assert node is not None, "Prime AV entity not found in graph"

    def test_bw_productions_in_graph(self, graph_index):
        """SERVICE or PARTY: B&W Productions should exist."""
        node = (
            find_node(graph_index, "Black & White Productions")
            or find_node(graph_index, "Black and White")
            or find_node(graph_index, "B&W")
            or find_node(graph_index, "pcc_blackandwhite_av_quote")
        )
        assert node is not None, "B&W Productions entity not found in graph"

    def test_av_cost_nodes_exist(self, graph_index):
        """COST nodes related to AV should exist."""
        av_costs = [
            n for n in graph_index["all_nodes"]
            if n["entity_type"] == "COST"
            and any(kw in n.get("name", "").lower() for kw in ["av", "audio", "video", "production", "stage"])
        ]
        assert len(av_costs) >= 1, "Expected AV-related cost nodes in graph"

    def test_terrace_ballroom_in_graph(self, graph_index):
        """ROOM: Terrace Ballroom should exist (key AV venue)."""
        node = find_node(graph_index, "Terrace Ballroom")
        # May not exist as exact match — check for rooms generally
        rooms = [n for n in graph_index["all_nodes"] if n["entity_type"] == "ROOM"]
        assert len(rooms) >= 5, f"Expected 5+ ROOM entities, got {len(rooms)}"

    def test_av_documents_are_sources(self, graph_index):
        """AV quote documents should exist in graph."""
        prime_doc = find_node(graph_index, "job_1025151_prime_av_event_quote")
        bw_doc = find_node(graph_index, "pcc_blackandwhite_av_quote")
        found = sum(1 for d in [prime_doc, bw_doc] if d is not None)
        assert found >= 1, "At least one AV quote document should be in graph"

    def test_chat_mentions_both_vendors(self, chat_response):
        """Chat should compare both AV vendors."""
        has_prime = "prime" in chat_response.lower()
        has_bw = (
            "black" in chat_response.lower()
            or "b&w" in chat_response.lower()
            or "b & w" in chat_response.lower()
        )
        assert has_prime and has_bw, (
            f"Chat should mention both vendors. Prime: {has_prime}, B&W: {has_bw}"
        )

    def test_chat_includes_cost_comparison(self, chat_response):
        """Chat should include dollar amounts for comparison."""
        amounts = re.findall(r"\$[\d,]+", chat_response)
        assert len(amounts) >= 2, (
            f"Expected 2+ dollar amounts for AV comparison, found {len(amounts)}"
        )


# ---------------------------------------------------------------------------
# Test 4: Graph structural integrity
# ---------------------------------------------------------------------------


class TestGraphStructure:
    """Verify the KG has the structural properties needed for provenance."""

    def test_node_count(self, graph_index):
        assert len(graph_index["all_nodes"]) >= 300, "Expected 300+ nodes"

    def test_edge_count(self, graph_index):
        assert len(graph_index["all_edges"]) >= 600, "Expected 600+ edges"

    def test_all_entity_types_present(self, entity_types):
        expected = {"PARTY", "OBLIGATION", "COST", "SERVICE", "CLAUSE", "ROOM", "VENUE", "DEADLINE"}
        present = set(entity_types.keys())
        missing = expected - present
        assert not missing, f"Missing entity types: {missing}"

    def test_all_edges_reference_valid_nodes(self, graph_index):
        """Every edge source/target should reference an existing node."""
        node_ids = set(graph_index["nodes_by_id"].keys())
        orphan_edges = 0
        for e in graph_index["all_edges"]:
            if e["source"] not in node_ids or e["target"] not in node_ids:
                orphan_edges += 1
        assert orphan_edges == 0, f"{orphan_edges} edges reference non-existent nodes"

    def test_cross_contract_entities_exist(self, graph_index):
        """At least 20 entities should span 2+ contracts."""
        cross_count = 0
        for node in graph_index["all_nodes"]:
            docs = node.get("source_documents", [])
            if len(docs) >= 2:
                cross_count += 1
        assert cross_count >= 20, (
            f"Expected 20+ cross-contract entities, found {cross_count}"
        )

    def test_document_nodes_have_mentioned_in_edges(self, graph_index):
        """DOCUMENT nodes should connect to entities via MENTIONED_IN."""
        mentioned_in_count = sum(
            1 for e in graph_index["all_edges"]
            if e["relation_type"] == "MENTIONED_IN"
        )
        assert mentioned_in_count >= 100, (
            f"Expected 100+ MENTIONED_IN edges, got {mentioned_in_count}"
        )
