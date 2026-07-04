#!/usr/bin/env python3
"""Graph-expansion retrieval via personalized PageRank (HippoRAG 2 pattern).

Given seed entities (typically hybrid-search hits from index_db), spread
activation through the knowledge graph so multi-hop-related entities are
surfaced even when they never co-occur with the query terms. This is the
retrieval core of HippoRAG 2 (arXiv 2502.14802) implemented as a
dependency-free power iteration over graph_data.json, so it works
wherever the plugin runs.

Usage (library):
    from graph_retrieval import expand_from_seeds
    results = expand_from_seeds(Path("graph_data.json"), ["node_a"], top_k=10)
"""

from __future__ import annotations

import json
from pathlib import Path

DAMPING = 0.85
ITERATIONS = 40
TOLERANCE = 1e-9


def load_graph(graph_path: Path) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Load graph_data.json into (nodes by id, undirected adjacency).

    sift-kg writes relationships under "links"; older exports may use
    "edges" — accept both.
    """
    data = json.loads(Path(graph_path).read_text())
    nodes = {node["id"]: node for node in data.get("nodes", []) if "id" in node}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for link in data.get("links", data.get("edges", [])):
        source, target = link.get("source"), link.get("target")
        if source in adjacency and target in adjacency:
            adjacency[source].append(target)
            adjacency[target].append(source)
    return nodes, adjacency


def personalized_pagerank(
    adjacency: dict[str, list[str]],
    seeds: list[str],
    damping: float = DAMPING,
    iterations: int = ITERATIONS,
) -> dict[str, float]:
    """Power-iteration PPR restarting at the seed set."""
    seed_set = [s for s in seeds if s in adjacency]
    if not seed_set:
        return {}
    restart = {node: 0.0 for node in adjacency}
    for seed in seed_set:
        restart[seed] += 1.0 / len(seed_set)

    scores = dict(restart)
    for _ in range(iterations):
        next_scores = {node: (1 - damping) * restart[node] for node in adjacency}
        dangling = 0.0
        for node, score in scores.items():
            neighbors = adjacency[node]
            if not neighbors:
                dangling += score
                continue
            share = damping * score / len(neighbors)
            for neighbor in neighbors:
                next_scores[neighbor] += share
        if dangling:
            # Dangling mass restarts at the seeds, keeping scores seed-anchored.
            for node, weight in restart.items():
                next_scores[node] += damping * dangling * weight
        delta = sum(abs(next_scores[n] - scores[n]) for n in adjacency)
        scores = next_scores
        if delta < TOLERANCE:
            break
    return scores


def expand_from_seeds(
    graph_path: Path,
    seeds: list[str],
    top_k: int = 10,
    include_seeds: bool = False,
) -> list[dict]:
    """Rank graph entities by PPR relevance to the seed entities."""
    nodes, adjacency = load_graph(graph_path)
    scores = personalized_pagerank(adjacency, seeds)
    seed_set = set(seeds)
    ranked = [
        {
            "id": node_id,
            "name": nodes[node_id].get("name", node_id),
            "entity_type": nodes[node_id].get("entity_type", ""),
            "score": round(score, 6),
        }
        for node_id, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        if score > 0 and (include_seeds or node_id not in seed_set)
    ]
    return ranked[:top_k]
