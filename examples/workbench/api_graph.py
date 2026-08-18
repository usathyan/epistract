"""Graph data API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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
        # See api_sources.py — a bare (body, status) tuple is a Flask idiom that
        # FastAPI serializes verbatim, producing HTTP 200 with an array body.
        return JSONResponse(
            status_code=404, content={"error": f"Node not found: {node_id}"}
        )
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
    """Return claims layer data (conflicts, gaps, risks, custom findings).

    Reshapes the nested claims_layer structure into the flat format
    the frontend expects: {conflicts, gaps, risks, cross_references,
    custom_findings, findings}.

    `custom_findings` is the channel both the per-domain `CUSTOM_RULES` hook
    (`core/label_epistemic.py`) and the cross-domain rules engine
    (`core/cross_domain.py`) write to, keyed by rule name. It was dropped
    here until now, which made every custom rule's output invisible over the
    API. `findings` is the same data flattened into one severity-bearing list
    so the dashboard can render it without knowing the rule names in advance.
    """
    data = request.app.state.data
    cl = data.claims_layer
    sd = cl.get("super_domain", {})
    custom_findings = sd.get("custom_findings", {}) or {}

    flattened: list[dict] = []
    for rule_name, rule_findings in custom_findings.items():
        if not isinstance(rule_findings, list):
            continue
        for f in rule_findings:
            if isinstance(f, dict):
                flattened.append({"rule_name": rule_name, **f})

    return {
        "conflicts": sd.get("conflicts", []),
        "gaps": sd.get("coverage_gaps", []),
        "risks": sd.get("risks", []),
        "cross_references": sd.get("cross_contract_entities", []),
        "custom_findings": custom_findings,
        "findings": flattened,
    }


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
