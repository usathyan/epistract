"""Graph data API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("")
async def get_graph(request: Request, entity_type: str | None = None):
    """Return full graph data or filtered by entity_type."""
    data = request.app.state.data
    if entity_type:
        nodes = data.get_nodes(entity_type=entity_type)
        # Filter edges to only include nodes in the filtered set
        node_ids = {n["id"] for n in nodes}
        edges = [
            e
            for e in data.get_edges()
            if e.get("source") in node_ids or e.get("target") in node_ids
        ]
        return {"nodes": nodes, "edges": edges}
    return {"nodes": data.get_nodes(), "edges": data.get_edges()}


@router.get("/node/{node_id:path}")
async def get_node(request: Request, node_id: str):
    """Return a single node with its connections."""
    data = request.app.state.data
    node = data.get_node_by_id(node_id)
    if not node:
        return {"error": f"Node not found: {node_id}"}, 404
    # Find connected edges and neighbor nodes
    edges = [
        e
        for e in data.get_edges()
        if e.get("source") == node_id or e.get("target") == node_id
    ]
    neighbor_ids = set()
    for e in edges:
        neighbor_ids.add(e["source"] if e["target"] == node_id else e["target"])
    neighbors = [n for n in data.get_nodes() if n["id"] in neighbor_ids]
    return {"node": node, "edges": edges, "neighbors": neighbors}


@router.get("/claims")
async def get_claims(request: Request):
    """Return claims layer data (conflicts, gaps, risks)."""
    data = request.app.state.data
    return data.claims_layer


@router.get("/communities")
async def get_communities(request: Request):
    """Return community assignments."""
    data = request.app.state.data
    return data.communities


@router.get("/entity-types")
async def get_entity_types(request: Request):
    """Return list of entity types with counts."""
    data = request.app.state.data
    type_counts: dict[str, int] = {}
    for node in data.get_nodes():
        t = node.get("entity_type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1
    return {"entity_types": type_counts}
