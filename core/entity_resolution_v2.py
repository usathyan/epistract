#!/usr/bin/env python3
"""Domain-agnostic two-stage entity resolution (block → cluster → verify).

Implements the ComEM cost structure (arXiv 2405.16884) and the 2025 ER
consensus recipe: cheap blocking → embedding/lexical similarity clustering →
LLM verification of ONLY the borderline candidate merges. Unlike the existing
`core/entity_resolution.py` (hard-coded contract party names), this module is
domain-agnostic and merges any entity type.

Layers, each optional and injectable so the module runs offline and tests
without network/model access:
  - blocking:   group candidates that share a type + a normalized token key
  - similarity: `embed_fn(names) -> vectors` for cosine, else token Jaccard
  - verify:     `verify_fn(a, b) -> bool` (LLM "same entity?") for pairs in
                the ambiguous similarity band [low, high]

Returns a merge map {duplicate_id -> canonical_id} plus a report.
"""

from __future__ import annotations

import re
import unicodedata
from itertools import combinations

_SUFFIX_NOISE = re.compile(
    r"\b(inc|llc|ltd|corp|corporation|company|co|plc|gmbh|sa|nv|the)\b", re.I
)


def normalize_name(name: str) -> str:
    """Lowercase, strip accents/punctuation/legal-suffix noise.

    Periods and commas are *deleted* (not spaced) so dotted acronyms like
    "S.A." collapse to a matchable token before legal-suffix removal.
    """
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[.,]", "", text)  # "s.a." -> "sa", "inc." -> "inc"
    text = _SUFFIX_NOISE.sub(" ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_set(name: str) -> set[str]:
    return {t for t in normalize_name(name).split() if t}


def _trigrams(name: str) -> set[str]:
    """Character trigrams of the space-collapsed normalized name.

    Robust to hyphenation/spacing differences ("GLP-1" vs "GLP1") that
    defeat token-set Jaccard.
    """
    compact = normalize_name(name).replace(" ", "")
    if len(compact) < 3:
        return {compact} if compact else set()
    return {compact[i : i + 3] for i in range(len(compact) - 2)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _lexical_similarity(name_a: str, name_b: str) -> float:
    """Max of token-set and character-trigram Jaccard."""
    return max(
        _jaccard(_token_set(name_a), _token_set(name_b)),
        _jaccard(_trigrams(name_a), _trigrams(name_b)),
    )


def _cosine(u: list[float], v: list[float]) -> float:
    dot = sum(x * y for x, y in zip(u, v))
    nu = sum(x * x for x in u) ** 0.5
    nv = sum(y * y for y in v) ** 0.5
    return dot / (nu * nv) if nu and nv else 0.0


def _block_key(entity: dict) -> str:
    """Block on entity_type only — high recall.

    A tighter key (e.g. first token) is precision-oriented and would
    prevent comparing exactly the surface-form variants ER must catch
    ("GLP-1" vs "GLP1", "heart attack" vs "myocardial infarction"). All
    same-type entities are compared pairwise; for the small-to-medium
    corpora this tool targets (see docs/ARCHITECTURE.md) the within-type
    O(n^2) is negligible.
    """
    return (entity.get("entity_type") or "").upper()


def resolve_entities(
    entities: list[dict],
    embed_fn=None,
    verify_fn=None,
    high: float = 0.85,
    low: float = 0.55,
    skip_types: frozenset[str] = frozenset({"DOCUMENT"}),
) -> dict:
    """Cluster duplicate entities and return a merge map.

    similarity >= high      -> auto-merge
    low <= similarity < high -> ask verify_fn (if given), else no merge
    similarity < low        -> never merge

    Args:
        entities: list of {id, name, entity_type, ...}.
        embed_fn: optional names->vectors; enables cosine similarity.
        verify_fn: optional (entity_a, entity_b)->bool for the ambiguous band.
        high/low: similarity thresholds.
        skip_types: entity types (upper-cased) excluded from resolution
            entirely — never blocked, clustered, or merged. Defaults to
            {"DOCUMENT"}: document nodes are provenance anchors whose ids/names
            are filenames, so name-similarity merging would corrupt
            MENTIONED_IN provenance.

    Returns {"merge_map": {dup_id: canonical_id}, "clusters": [...],
    "verified": n, "auto_merged": n}.
    """
    by_id = {
        str(e.get("id") or e.get("name") or ""): e
        for e in entities
        if (e.get("entity_type") or "").upper() not in skip_types
    }
    ids = list(by_id)

    # Optional embeddings, computed once.
    vectors = None
    if embed_fn is not None:
        names = [by_id[i].get("name", i) for i in ids]
        vectors = dict(zip(ids, embed_fn(names)))

    def similarity(id_a: str, id_b: str) -> float:
        if vectors is not None:
            return _cosine(vectors[id_a], vectors[id_b])
        return _lexical_similarity(
            by_id[id_a].get("name", id_a), by_id[id_b].get("name", id_b)
        )

    # Stage 1: blocking.
    blocks: dict[str, list[str]] = {}
    for eid in ids:
        blocks.setdefault(_block_key(by_id[eid]), []).append(eid)

    # Stage 2+3: within-block similarity, verify borderline band.
    parent = {eid: eid for eid in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            # Canonical = the id whose name is longer (more specific).
            keep, drop = sorted(
                (rx, ry), key=lambda i: len(by_id[i].get("name", "")), reverse=True
            )
            parent[drop] = keep

    auto_merged = 0
    verified = 0
    for members in blocks.values():
        for a, b in combinations(members, 2):
            sim = similarity(a, b)
            if sim >= high:
                union(a, b)
                auto_merged += 1
            elif sim >= low and verify_fn is not None:
                verified += 1
                if verify_fn(by_id[a], by_id[b]):
                    union(a, b)

    # Build merge map + clusters.
    clusters: dict[str, list[str]] = {}
    for eid in ids:
        clusters.setdefault(find(eid), []).append(eid)
    merge_map = {
        eid: root
        for root, members in clusters.items()
        for eid in members
        if eid != root
    }
    return {
        "merge_map": merge_map,
        "clusters": [m for m in clusters.values() if len(m) > 1],
        "auto_merged": auto_merged,
        "verified": verified,
    }


def apply_merge_map(graph_data: dict, merge_map: dict) -> dict:
    """Rewrite node ids and link endpoints per the merge map (returns new dict).

    Duplicate nodes are dropped; links are repointed to canonical ids and
    self-loops created by merging are removed.
    """
    if not merge_map:
        return graph_data

    def canon(node_id):
        return merge_map.get(node_id, node_id)

    nodes = []
    seen = set()
    for node in graph_data.get("nodes", []):
        nid = canon(node.get("id"))
        if nid in seen:
            continue
        seen.add(nid)
        nodes.append({**node, "id": nid})

    link_key = "links" if "links" in graph_data else "edges"
    links = []
    for link in graph_data.get(link_key, []):
        src, tgt = canon(link.get("source")), canon(link.get("target"))
        if src == tgt:
            continue
        links.append({**link, "source": src, "target": tgt})

    result = dict(graph_data)
    result["nodes"] = nodes
    result[link_key] = links
    return result
